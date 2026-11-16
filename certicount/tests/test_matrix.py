"""Per-node architecture: NAM-DPRD's unbiased matrix ``A`` in the DSL (:mod:`certicount.dsl.matrix`)."""

from __future__ import annotations

import asyncio
import math

import numpy as np
import pytest

from psc.graph import load_dataset
from psc.models import ModelConfig
from certicount import DATA_DIR
from certicount.dsl import parse_program
from certicount.dsl.falsifier import check_derivation, falsify
from certicount.dsl.ground_truth import gt_dsl
from certicount.dsl.lang import DSLError, Env, Interpreter, order_projector
from certicount.dsl.library import TRIANGLE_MATRIX, matrix_triangle_gs, reference_source
from certicount.dsl.matrix import rr_constants, table_matrix, unbiased_matrix
from certicount.dsl.quality import design_quality, task_record
from certicount.dsl.sensitivity import PublicParams, SensitivityError, derive
from certicount.dsl.utility import utility_test
from certicount.framework import TrustedPSCFramework, TrustOptions
from psc.graph import Graph

CU = load_dataset(DATA_DIR, "CU")
TRI = TRIANGLE_MATRIX.parse()


def rng(i: int) -> np.random.Generator:
    return np.random.default_rng([7, i])


def test_unbiased_entries():
    low, high = rr_constants(1.0)
    assert high == pytest.approx(math.e / (math.e - 1)) and low == pytest.approx(-1 / (math.e - 1))
    a = unbiased_matrix(Graph.from_edges(3, [(0, 1)]), 1.0)
    assert (a(0, 1), a(1, 0), a(0, 2), a(1, 1)) == (pytest.approx(high), pytest.approx(high), pytest.approx(low), 0.0)
    # E[A] = bit: (1 - p) * high + p * low = 1 for an edge, p * high + (1 - p) * low = 0 for a non-edge
    p = 1 / (1 + math.e)
    assert (1 - p) * high + p * low == pytest.approx(1.0) and p * high + (1 - p) * low == pytest.approx(0.0)


@pytest.mark.parametrize("eps1", [0.5, 1.0, 2.0])
def test_derived_gs_is_the_hand_derivation(eps1):
    for D in range(0, 13):
        gs = derive(TRI, PublicParams(40, D=D, dmax=D, eps1=eps1)).gs
        assert gs == pytest.approx(matrix_triangle_gs(D, eps1))


def test_falsifier_finds_the_derived_gs_exactly():
    for n, D in ((5, 3), (5, 2)):
        gs = derive(TRI, PublicParams(n, D=D, dmax=D, eps1=1.0)).gs
        refuted, ce = falsify(TRI, gs, n=n, dmax=D)
        assert not refuted and ce.max_delta == pytest.approx(gs)  # sound and tight
    assert not check_derivation(TRI, 7, 4, 200).refuted


def test_nam_dprd_calibration_misses_the_replacement():
    """``2 κ d~`` with ``d~`` just above ``D = 4``: one added neighbour evicts a kept one."""
    low, high = rr_constants(1.0)
    D, n = 4, 6
    values = {(min(5, k), max(5, k)): high for k in (1, 2, 3)} | {(min(4, k), max(4, k)): low for k in (1, 2, 3)}
    proj = order_projector((5, 1, 2, 3, 4, 0))  # one priority order for both sides (fixed before P is read)
    interp = Interpreter(TRI)

    def f(p):
        return interp.local(Env(frozenset(p), 0, {}, n, D=D, dmax=D, projector=proj, matrix=table_matrix(values)))

    delta = abs(f({1, 2, 3, 4, 5}) - f({1, 2, 3, 4}))
    assert delta == pytest.approx(2 * (D - 1) * (high - low)) == pytest.approx(matrix_triangle_gs(D, 1.0))
    assert delta > 2 * high * 4.05  # NAM-DPRD's scale for d~ = 4.05 (D = floor(d~) = 4)


def test_utility_and_quality_of_the_reference():
    assert utility_test(TRI, "triangle", count=40, public_n=49).passed
    q = design_quality(TRI, "triangle", 49, 10, node_bounds=True)
    assert q.same_as_reference and q.split_match and q.semantic_pass and q.sound


def test_language_rules():
    with pytest.raises(DSLError):
        parse_program("return sum(size(N(j)) + A(j, self) for j in P)")
    with pytest.raises(SensitivityError):
        derive(TRI, PublicParams(10, D=3, dmax=3))  # no eps1: no matrix was published
    assert TRI.uses_matrix and TRI.uses_release and not TRI.uses_rows and TRI.needs_degree_bound
    assert reference_source("triangle", node_bounds=True) is TRIANGLE_MATRIX
    assert reference_source("3-star", node_bounds=True) is reference_source("3-star")


@pytest.mark.parametrize("source", ["library", "design"])
def test_framework_equals_code_on_identical_noise(source):
    rec = task_record(CU, "CU", "triangle")
    for alpha in (0.0, 3.0):
        fw = TrustedPSCFramework(ModelConfig(), TrustOptions(execution="program", node_bounds=True,
                                                             clip_alpha=alpha, program_source=source))
        for i in range(3):
            res = asyncio.run(fw.run(rec, 2.0, rng=rng(i)))
            tr = gt_dsl(rec.graph(), "triangle", 2.0, rng(i), node_bounds=True, alpha=alpha)
            assert res.extra["trust"]["design"] is None or "A(j, k)" in res.extra["trust"]["design"]["program"]
            assert tr.counts == pytest.approx(res.extra["mechanism_trace"]["raw_counts"])
            assert tr.estimate == pytest.approx(res.estimate, abs=1e-9)
            assert (tr.gs, tr.split) == (res.sensitivity, res.split)


def test_node_gs_is_the_hand_derivation_at_each_bound():
    g = CU["triangle"].graph()
    for i in range(3):
        tr = gt_dsl(g, "triangle", 2.0, rng(i), node_bounds=True)
        eps1 = tr.split[0]
        hand = {D: matrix_triangle_gs(D, eps1) for D in range(g.n)}
        assert all(any(h == pytest.approx(gs) for h in hand.values()) for gs in tr.node_gs)
        assert tr.gs == max(tr.node_gs)


def test_local_statistic_is_unbiased_without_clipping():
    g = CU["triangle"].graph()
    truth = CU["triangle"].answer
    # alpha far above every degree: no neighbour is clipped, E[sum of counts] / 6 = number of triangles
    est = [sum(gt_dsl(g, "triangle", 2.0, rng(i), node_bounds=True, alpha=1e3).counts) / 6 for i in range(300)]
    assert np.mean(est) == pytest.approx(truth, rel=0.1)
