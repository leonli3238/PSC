"""Independent parameter, noise-path and experiment-contract checks."""
import argparse
import asyncio
import math
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from psc.dp import laplace_noise, split_budget
from psc.framework import PSCFramework
from psc.graph import Graph, TaskRecord, task_prompt
from psc.experiments import run_ground_truth
from psc.ground_truth import TRITR_BUDGETS, gt_psc, gt_tritr, tritr_budget
from psc.library import get_dp_framework
from psc.mechanism import MECHANISMS, get_mechanism
from psc.models import ModelConfig
from scripts.run_experiments import pilot_runs


def record(g, task):
    return TaskRecord(1, task_prompt(task, g.n), g.edge_string(), g.n, g.m, g.ground_truth(task), task, "toy")


def test_tight_sensitivity_is_max_single_bit_difference():
    p = get_mechanism("floor_tight")
    for n in range(1, 12):
        for k in (2, 3):
            for D in range(n):
                counts = [math.comb(min(d, D), k) for d in range(n)]
                differences = [abs(a - b) for a, b in zip(counts, counts[1:])]
                expected = max(differences, default=0)
                assert p.kstar_sensitivity(k, n, D) == expected
            assert p.kstar_sensitivity(k, n, None) == math.comb(max(0, n-2), k-1)


def test_continuous_maximum_and_physical_bounds():
    reports = [3.75, -2, 1, 1, 0, 2]
    b = get_mechanism("continuous_bound").degree_bound(reports, "3-star")
    assert b.projection_degree == 3 and b.sensitivity_degree == 3.75
    assert get_dp_framework("3-star").sensitivity(6, 3, "continuous_bound", 3.75) == 3.75*2.75/2
    for name in MECHANISMS[1:]:
        p = get_mechanism(name)
        assert p.degree_bound([-8, -4, -1], "2-star").projection_degree == 0
        assert p.degree_bound([100, 0, 0], "2-star").projection_degree == 2
        assert p.kstar_sensitivity(3, 3, 0, .5) >= 0
    with pytest.raises(ValueError):
        get_mechanism("floor_tight").degree_bound([float("nan")], "2-star")


@pytest.mark.parametrize("profile", MECHANISMS)
@pytest.mark.parametrize("optimized", [False, True])
def test_gt_and_agents_share_noise_and_parameters(profile, optimized):
    g = Graph.from_edges(7, [(0, i) for i in range(1, 7)] + [(1,2),(2,3)])
    for task in ("2-star", "3-star"):
        for seed in (0, 7):
            trace = gt_psc(g, task, 2, np.random.default_rng(seed), gs_optimization=optimized, mechanism=profile, return_trace=True)
            fw = PSCFramework(ModelConfig(provider="mock"), gs_optimization=optimized, mechanism=profile)
            agent = asyncio.run(fw.run(record(g, task), 2, np.random.default_rng(seed)))
            assert agent.d_hat_max == trace.d_hat_max
            assert agent.sensitivity == trace.sensitivity
            assert agent.split == trace.split.as_tuple()
            assert agent.extra["mechanism_trace"]["raw_counts"] == trace.raw_counts
            assert agent.extra["mechanism_trace"]["noisy_counts"] == trace.noisy_counts
            assert math.isclose(agent.extra["validation"]["rule_estimate"], trace.result, abs_tol=1e-10)


def test_legacy_kstar_matches_independent_original_formula():
    g = Graph.from_edges(8, [(0,i) for i in range(1,8)])
    for k in (2,3):
        for seed in range(10):
            rng = np.random.default_rng(seed)
            reports = [d+rng.laplace(0,2.5) for d in g.degrees()]
            D = max(1, math.ceil(max(reports)))
            raw=[]
            for i,d in enumerate(g.degrees()):
                if d>D:
                    rng.choice(sorted(g.adj[i]),size=D,replace=False)
                raw.append(math.comb(min(d,D),k))
            noisy = [c+rng.laplace(0,math.comb(D,k-1)/1.6) for c in raw]
            tr = gt_psc(g,f"{k}-star",2,np.random.default_rng(seed),mechanism="legacy",return_trace=True)
            assert tr.d_hat_max==D and tr.noisy_counts==noisy
            assert tr.result==max(0,sum(noisy))


def test_other_tasks_do_not_change_with_profile_and_trace_does_not_consume_rng():
    g=Graph.from_edges(6,[(0,1),(1,2),(2,0),(2,3),(3,4),(4,2)])
    for task in ("degree","triangle"):
        base=gt_psc(g,task,2,np.random.default_rng(17),mechanism="legacy")
        for profile in MECHANISMS:
            rng=np.random.default_rng(17)
            tr=gt_psc(g,task,2,rng,mechanism=profile,return_trace=True)
            assert tr.result==base
            state=repr(rng.bit_generator.state)
            tr.audit_dict()
            assert repr(rng.bit_generator.state)==state


def test_zero_noise_and_invalid_budgets():
    assert laplace_noise(0, 1.6, np.random.default_rng(0))==0
    for eps in (0,-1,float("nan"),float("inf")):
        with pytest.raises(ValueError):
            laplace_noise(1,eps,np.random.default_rng(0))
    with pytest.raises(ValueError):
        split_budget(2,False,True,r2=0)


def test_pilot_ten_runs_applies_to_both_methods():
    assert pilot_runs(argparse.Namespace(runs=10,naive_runs=None))=={"PSC":10,"Naive":10}
    assert pilot_runs(argparse.Namespace(runs=None,naive_runs=None))=={"PSC":10,"Naive":10}
    assert pilot_runs(argparse.Namespace(runs=10,naive_runs=3))=={"PSC":10,"Naive":3}


def test_output_directory_cannot_overwrite_and_statistics_use_mean_error(tmp_path):
    from psc.artifacts import new_run_directory
    from psc.experiments import error_statistics, paper_value
    new_run_directory(tmp_path,"run","prefix")
    with pytest.raises(FileExistsError):
        new_run_directory(tmp_path,"run","prefix")
    s=error_statistics([50,150],100,49,.5)
    assert s["avg_relative_error"]==.5 and s["se_relative_error"]==0
    assert s["paper_relative_gap"]==0
    assert paper_value("2-star","GT-PSC-B","CU")==.4487


def test_gt_trace_recording_does_not_change_estimates():
    from psc.experiments import run_ground_truth
    data=Path(__file__).resolve().parents[1]/"data"
    recorded=[]
    args=(data,["CU"],["2-star","3-star"],[2.0],3)
    plain=run_ground_truth(*args,methods=["GT-PSC"],mechanism="floor_tight",log=lambda _:None)
    traced=run_ground_truth(*args,methods=["GT-PSC"],mechanism="floor_tight",log=lambda _:None,on_result=recorded.append)
    assert plain==traced and len(recorded)==6
    for row in recorded:
        t=row["trace"]
        assert t["result"]==max(0,sum(t["noisy_counts"]))
        assert t["mechanism"]=="floor_tight"


def test_adaptive_2star_matches_independent_formula_and_keeps_other_tasks():
    g = Graph.from_edges(9, [(0, i) for i in range(1, 9)] + [(1, 2), (3, 4), (5, 6)])
    for seed in range(10):
        rng = np.random.default_rng(seed)
        reports = [d + rng.laplace(0, 2.5) for d in g.degrees()]
        D = math.floor(min(max(max(reports), 0), g.n - 1))
        limits = [min(D, max(0, math.floor(y + 2 * 2.5))) for y in reports]
        raw = []
        for i, d in enumerate(g.degrees()):
            if d > limits[i]:
                rng.choice(sorted(g.adj[i]), size=limits[i], replace=False)
            raw.append(math.comb(min(d, limits[i]), 2))
        noisy = [c + rng.laplace(0, max(0, L - 1) / 1.6) for c, L in zip(raw, limits)]
        tr = gt_psc(g, "2-star", 2, np.random.default_rng(seed), mechanism="adaptive_2star", return_trace=True)
        assert tr.d_hat_max == D and tr.node_projection_degrees == limits
        assert tr.noisy_counts == noisy and tr.result == max(0, sum(noisy))
    for task in ("degree", "3-star", "triangle"):
        for seed in (0, 3):
            a = gt_psc(g, task, 2, np.random.default_rng(seed), mechanism="floor_tight")
            b = gt_psc(g, task, 2, np.random.default_rng(seed), mechanism="adaptive_2star")
            assert a == b


def test_adaptive_2star_node_transcript_is_eps_edge_ldp():
    """Exact log-likelihood ratio of one node's (y, z) for degrees d and d+1."""
    eps2, eps3, n, D = .4, 1.6, 30, 20
    p = get_mechanism("adaptive_2star")

    def log_density(d, y, z):
        Di = int(p.node_projection_degrees([y], D, "2-star", eps2)[0])
        gs = p.kstar_sensitivity(2, n, Di)
        count = math.comb(min(d, Di), 2)
        ly = math.log(eps2 / 2) - eps2 * abs(y - d)
        if gs == 0:
            return ly, count  # z is the constant count (always 0 here)
        return ly + math.log(eps3 / (2 * gs)) - eps3 * abs(z - count) / gs, None

    for d in range(0, D + 3):
        for y in np.linspace(-10, D + 10, 157):
            for z in np.linspace(-50, 250, 61):
                a, ca = log_density(d, y, z)
                b, cb = log_density(d + 1, y, z)
                assert ca == cb  # zero-noise branches release the same constant
                assert abs(a - b) <= eps2 + eps3 + 1e-9


def test_zero_degree_bound_produces_constant_zero_count():
    class AllNegativeDegreeNoise:
        def laplace(self, location, scale):
            return -100.0 if scale else 0.0

        def choice(self, neighbors, size, replace):
            assert size==0
            return np.array([],dtype=int)

    g=Graph.from_edges(4,[(0,1),(0,2),(0,3)])
    for task in ("2-star","3-star"):
        trace=gt_psc(g,task,2,AllNegativeDegreeNoise(),mechanism="floor_tight",return_trace=True)
        assert trace.d_hat_max==0 and trace.sensitivity==0 and trace.result==0
        assert trace.raw_counts==trace.noisy_counts==[0.0]*g.n


def _random_graph(n, p, seed):
    rng = np.random.default_rng(seed)
    return Graph.from_edges(n, [(u, v) for u in range(n) for v in range(u + 1, n) if rng.random() < p])


@pytest.mark.parametrize("budget", TRITR_BUDGETS)
def test_tritr_budget_sums_to_eps_and_tritr_is_exact_without_noise(budget):
    g = _random_graph(14, .4, 3)
    for task in ("degree", "2-star", "3-star", "triangle"):
        assert math.isclose(tritr_budget(2.0, task, budget).total, 2.0)
        # alpha = 0.5 keeps floor(d~_i) = d_i once the degree noise is negligible
        est = gt_tritr(g, task, 6000.0, np.random.default_rng(0), alpha=.5, budget=budget, clamp=False)
        assert math.isclose(est, g.ground_truth(task), rel_tol=1e-3)
    assert tritr_budget(2.0, "triangle", "nam").as_tuple() == pytest.approx((.9, .2, .9))


def test_tritr_triangle_estimate_is_unbiased_without_projection():
    g = _random_graph(16, .45, 5)
    rng = np.random.default_rng(11)
    ests = np.array([gt_tritr(g, "triangle", 4.0, rng, alpha=g.n, clamp=False) for _ in range(4000)])
    assert abs(ests.mean() - g.ground_truth("triangle")) < 4 * ests.std() / math.sqrt(len(ests))


def test_tritr_degree_coincides_with_gt_psc():
    g = _random_graph(20, .3, 7)
    for seed in range(5):
        a = gt_tritr(g, "degree", 2.0, np.random.default_rng(seed), alpha=3.0)
        b = gt_psc(g, "degree", 2.0, np.random.default_rng(seed), mechanism="floor_tight")
        assert math.isclose(a, b, rel_tol=1e-12)


def test_ground_truth_runner_labels_tritr_rows():
    rows = run_ground_truth(Path(__file__).resolve().parents[1] / "data", ["CU"], ["degree", "triangle"], [2.0], 3,
                            methods=["GT-PSC", "GT-TriTR"], log=lambda _: None, tritr_alpha=2.0)
    assert [(r["task"], r["method"], r["mechanism"]) for r in rows] == [
        ("degree", "GT-PSC", "floor_tight"), ("degree", "GT-TriTR", "tritr_alpha2_psc"),
        ("triangle", "GT-PSC", "floor_tight"), ("triangle", "GT-TriTR", "tritr_alpha2_psc"),
    ]
    assert math.isclose(rows[0]["avg_relative_error"], rows[1]["avg_relative_error"])
    with pytest.raises(ValueError):
        run_ground_truth(Path(__file__).resolve().parents[1] / "data", ["CU"], ["degree"], [2.0], 1, methods=["GT-X"])


def test_agent_tritr_is_exact_without_noise_and_matches_node_rules():
    g = _random_graph(12, .45, 9)
    fw = PSCFramework(ModelConfig(provider="mock"), tritr_alpha=.5)
    assert fw.name == "TriTR" and fw.mechanism_label == "tritr_alpha0.5"
    for task in ("degree", "2-star", "3-star", "triangle"):
        res = asyncio.run(fw.run(record(g, task), 6000.0, np.random.default_rng(1)))
        v = res.extra["validation"]
        assert math.isclose(res.estimate, g.ground_truth(task), rel_tol=1e-3)
        assert v["e2e_exact"] == v["nodes"] and v["rule_estimate"] == pytest.approx(res.estimate)
        if task == "triangle":
            assert v["send_exact"] == v["nodes"]
    with pytest.raises(ValueError):
        PSCFramework(ModelConfig(provider="mock"), gs_optimization=False, tritr_alpha=0.0)


def test_agent_tritr_triangle_report_is_half_the_unbiased_neighbor_sum():
    g = _random_graph(14, .4, 2)
    res = asyncio.run(PSCFramework(ModelConfig(provider="mock"), tritr_alpha=1.0).run(
        record(g, "triangle"), 2.0, np.random.default_rng(4)))
    trace = res.extra["mechanism_trace"]
    eps1 = split_budget(2.0, True, True).eps1
    a_one, a_zero = math.exp(eps1) / math.expm1(eps1), -1 / math.expm1(eps1)
    checked = 0
    for i, D in enumerate(trace["node_projection_degrees"]):
        d = len(g.adj[i])
        if d > D:
            continue  # randomly projected list; covered by the exactness test
        m = trace["raw_counts"][i]  # noisy edges among the neighbors, counted by the node agent
        expected = (2 * m * a_one + (d * (d - 1) - 2 * m) * a_zero) / 2
        assert math.isclose(trace["noisy_counts"][i] - trace["report_noise"][i], expected, rel_tol=1e-9, abs_tol=1e-9)
        checked += 1
    assert checked > 3
