"""LLM-designed program pools (certicount.dsl.pool) and the adaptive pool mode of the framework."""

from __future__ import annotations

import asyncio
import json
import math

import numpy as np
import pytest

from psc.experiments import run_rng
from psc.models import ModelConfig, create_formatter

from certicount.dsl.adaptive import SelectOptions, choose, default_index, pool_space, release_degrees, run_streams, select
from certicount.dsl.lang import parse_program, parse_program_text
from certicount.dsl.library import PROGRAMS
from certicount.dsl.pool import (
    BudgetedModel, CallBudgetExceeded, Draft, MockPoolModel, PoolOptions, Scorer, admit, deploy, design_pool,
    fingerprint, random_design, read_drafts,
)
from certicount.framework import TrustedPSCFramework, TrustOptions

from test_dsl_eval import CU  # noqa: F401  (dataset records shared with the other tests)

FMT = create_formatter(ModelConfig())
FAST = PoolOptions(rounds=2, sims_rows=2, sims_degrees=50, sizes=(60,), profiles=("sparse", "hubs"))
TRI = "S = P & N(self)\nreturn 0.5 * sum(size(P & N(j)) for j in S)"


def _draft(src: str, agg: str) -> Draft:
    return Draft("llm", 1, parse_program(src, agg), f"{src}\naggregate: {agg}")


def test_budgeted_model_counts_every_request_and_stops_the_design():
    model = BudgetedModel(MockPoolModel(), 1)
    res = asyncio.run(design_pool(model, FMT, "3-star", FAST))
    assert model.requests == 1 and res.calls == 1 and res.stopped == "call budget"
    with pytest.raises(CallBudgetExceeded):
        asyncio.run(model([{"role": "user", "content": "x"}]))
    assert model.requests == 1


def test_several_programs_are_read_from_one_reply():
    text = ("Idea one.\n```dsl\nreturn size(P)\n```\naggregate: total / n\n\n"
            "**Idea two.**\n```dsl\nreturn size(P - {self})\n```\naggregate: total\n")
    drafts = read_drafts(text, "llm", 1, 4)
    assert [d.idea for d in drafts] == ["Idea one.", "Idea two."]
    assert drafts[0].program is not None and drafts[0].program.aggregate_source == "total / n"
    assert drafts[1].program is None and "not a valid program" in drafts[1].reason
    assert read_drafts("no code", "llm", 1, 4)[0].category == "parse"


def test_gates_reject_rewrites_inexact_and_nonlinear_programs():
    scorer = Scorer("triangle", FAST)
    hand = Draft("hand", 0, parse_program(TRI, "total / 3"), TRI, status="certified")
    hand.fingerprint, hand.noise = fingerprint(hand.program), (1.0, 3.0, 13.0)
    drafts = [hand]
    rewrite = admit(_draft("S = N(self) & P\nreturn sum(size(N(j) & P) for j in S) / 2", "total / 3"), "triangle", FAST,
                    scorer, drafts)
    assert rewrite.status == "rejected" and rewrite.category == "duplicate"
    double = admit(_draft(TRI.replace("0.5 * ", ""), "total / 3"), "triangle", FAST, scorer, drafts)
    assert double.category == "inexact"
    square = admit(_draft(TRI, "total * total"), "triangle", FAST, scorer, drafts)
    assert square.category == "aggregate"
    new = admit(_draft("return 0.5 * sum(size(P & N(j)) for j in P)", "total / 3"), "triangle", FAST, scorer, drafts)
    assert new.status == "certified" and new.score is not None and len(new.score.errors) == len(scorer.scenarios)


def test_fingerprint_sees_through_rewriting():
    a = parse_program(TRI, "total / 3")
    b = parse_program("S = P & N(self)\nreturn sum(size(P & N(j)) for j in S)", "total / 6")
    c = parse_program("return 0.5 * sum(size(P & N(j)) for j in P)", "total / 3")
    assert fingerprint(a) == fingerprint(b) != fingerprint(c)


def test_pool_starts_with_the_library_program_and_keeps_only_gains():
    res = asyncio.run(design_pool(MockPoolModel(), FMT, "triangle", FAST))
    assert res.pool[0] == 0 and res.programs[0].digest == PROGRAMS["triangle"].parse().digest
    best = np.min([res.drafts[i].score.errors for i in res.pool], axis=0)
    assert np.all(best <= np.array(res.drafts[0].score.errors) + 1e-12)
    pool = deploy(res.drafts, FAST)
    assert pool == res.pool  # deterministic
    tight = deploy(res.drafts, PoolOptions(min_gain=10.0))
    assert tight == [0]


def test_random_baseline_uses_the_same_gates():
    res = random_design("3-star", 200, seed=0, opts=FAST)
    assert res.pool[0] == 0 and res.calls == 0
    assert res.stats["proposed"] == 200 and sum(v for k, v in res.stats.items() if k != "proposed") == 200
    assert all(d.status == "certified" for d in res.drafts)


def test_one_scoring_of_the_union_selects_every_pool():
    g = CU["triangle"].graph()
    n = g.n
    lib = PROGRAMS["triangle"].parse()
    other = parse_program("return 0.5 * sum(size(P & N(j)) for j in P)", "total / 3")
    st = run_streams(n, 0, 1)
    rel = release_degrees(g, 0.2, st, "triangle")
    opts = SelectOptions(sims=1, margin=0.0)
    union = pool_space([lib, other], rel.D, 2.0, 0.2)
    d = default_index(union, rel.D, 1.0)
    full = select(rel, n, 2.0, union, lib, np.random.default_rng(5), opts, default=d)
    alone = pool_space([lib], rel.D, 2.0, 0.2)
    sub = select(rel, n, 2.0, alone, lib, np.random.default_rng(5), opts, default=default_index(alone, rel.D, 1.0))
    subset = [k for k, c in enumerate(union) if c.program.digest == lib.digest]
    assert np.allclose(full.scores[subset], sub.scores)
    assert union[choose(full.scores, subset, d, 0.0)[0]].key[1:] == alone[sub.index].key[1:]


def test_program_text_round_trip():
    for src in PROGRAMS.values():
        p = src.parse()
        assert parse_program_text(p.text()).digest == p.digest
    b = parse_program("return size(P)", "total / n", budget="r1=0.3, r2=0.1")
    assert parse_program_text(b.text()).digest == b.digest


@pytest.mark.parametrize("source", ["library", "design", "file"])
def test_framework_adaptive_mode(source, tmp_path):
    pool_file = tmp_path / "pools.json"
    lib = PROGRAMS["triangle"].parse()
    other = parse_program("return 0.5 * sum(size(P & N(j)) for j in P)", "total / 3")
    pool_file.write_text(json.dumps({"pools": {"llm": {"triangle": [lib.text(), other.text()]}}}), encoding="utf-8")
    opts = TrustOptions(execution="program", adaptive=True, pool_source=source, pool_file=str(pool_file),
                        pool={"rounds": 1, "sims_rows": 2, "sizes": [60], "profiles": ["sparse"]},
                        select={"sims": 1, "samples": 100})
    fw = TrustedPSCFramework(ModelConfig(provider="mock"), opts)
    a, b = (asyncio.run(fw.run(CU["triangle"], 2.0, rng=run_rng(0, i))) for i in range(2))
    for r in (a, b):
        sel = r.extra["trust"]["selection"]
        assert math.isfinite(r.estimate) and r.extra["node_llm_calls"] == 0 and not r.extra["trust"]["violations"]
        assert sum(r.split) == pytest.approx(2.0) and r.split[1] == pytest.approx(0.2)
        assert r.sensitivity == r.extra["trust"]["certificate"]["gs"] and sel["bound"] <= sel["D"]
        assert len(sel["pool"]) == (1 if source == "library" else 2 if source == "file" else len(sel["pool"]))
    assert a.llm_calls == (1 if source == "design" else 0) and b.llm_calls == 0
    assert fw.name == "PSC[program+adaptive]"
