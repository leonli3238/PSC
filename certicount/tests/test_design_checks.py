"""Step 1a of the design loop: reader, repair hints, noise-aware gate, GS growth check, transcript tags."""

from __future__ import annotations

import asyncio
import json
import random
import re
import sys
from pathlib import Path
from typing import Any

import pytest
from agentscope.model import ChatModelBase, ChatResponse

from psc.models import ModelConfig, create_formatter
from certicount.dsl.designer import (
    TRUNCATED_FEEDBACK, DesignOptions, _text, bound_slack, check_draft, design_program, design_prompt,
    design_reference_params, design_with_restarts, draft_stage, dsl_reference, falsifier_feedback, growth_feedback,
    normalize_source, read_draft, repair_hint,
)
from certicount.dsl.prompt_spec import LEGACY_V0, V0, PromptSpec, load_spec
from certicount.dsl.ground_truth import reference_program
from certicount.dsl.lang import DSLError, Env, Interpreter, parse_program
from certicount.dsl.library import analyst_prompt
from certicount.dsl.matrix import table_matrix
from certicount.dsl.noisy_gate import NoisyGate, holme_kim, noise_free_check, public_test_graphs
from certicount.dsl.sensitivity import PublicParams, derive

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_design_certification import calls_by_design  # noqa: E402

FMT = create_formatter(ModelConfig())
N = 200  # public graph size of the gate tests (the experiments use the real n)
GATE = NoisyGate(N, reps=4)
GATE_NODE = NoisyGate(N, node_bounds=True, alpha=5.0, reps=4)


# ---------------------------------------------------------------- reader: several for clauses
def test_several_for_clauses_are_nested_sums():
    flat = parse_program("Q = project(P, D)\nreturn sum(A(j, k) for j in Q for k in Q)", "total / 6")
    nested = parse_program("Q = project(P, D)\nreturn sum(sum(A(j, k) for k in Q) for j in Q)", "total / 6")
    assert flat.ret == nested.ret
    p = PublicParams(40, D=6, dmax=6, eps1=1.0)
    assert derive(flat, p).gs == pytest.approx(derive(nested, p).gs)
    rnd = random.Random(3)
    vals = {(j, k): rnd.choice((-0.58, 1.58)) for j in range(9) for k in range(j + 1, 9)}
    env = Env(frozenset({1, 2, 4, 5, 7}), 0, {}, 9, D=6, dmax=6, matrix=table_matrix(vals))
    assert Interpreter(flat).local(env) == pytest.approx(Interpreter(nested).local(env))


def test_inner_domain_may_use_the_outer_variable_and_conditions_stay_rejected():
    parse_program("return sum(size(N(v)) for u in P for v in N(u))")
    with pytest.raises(DSLError, match="without conditions"):
        parse_program("return sum(1 for a in P for b in P if a < b)")
    with pytest.raises(DSLError, match="shadows"):
        parse_program("return sum(1 for a in P for a in P)")


# ---------------------------------------------------------------- reader: reasoning and truncation
def test_program_is_read_after_the_reasoning_block():
    reply = ("<think>draft:\n```dsl\nreturn size(N(self))\n```\naggregate: total / n\nno, use P</think>\n"
             "```dsl\nreturn size(P)\n```\naggregate: total / n")
    prog, _ = read_draft(reply)
    assert prog is not None and prog.source.strip() == "return size(P)"
    prog, entry = read_draft("<think>```dsl\nreturn size(P)\n```</think>\nI give up.")
    assert prog is None and draft_stage(entry["feedback"]) == "parse"


def test_truncated_reasoning_is_its_own_stage():
    prog, entry = read_draft("<think>let me add 4.2 + 99.1 = 103.3, then ...")
    assert prog is None and entry["truncated"] and entry["feedback"] == TRUNCATED_FEEDBACK
    assert draft_stage(entry["feedback"]) == "truncated"


# ---------------------------------------------------------------- repair hints
@pytest.mark.parametrize("source, needle", [
    ("name = size(P)\nreturn name * (name - 1) // 2", "'/' instead of '//'"),
    ("return sum(size(N(v) & {w}) for v in P)", "no literals"),
    ("return sum(size(N(v) & N(u)) for v in N(u))", "'u' is not defined"),
    ("degree = project(P, D)\nreturn comb(degree, 2)", "comb(size(S), k)"),
    ("Q = project(N(self), D)\nreturn sum(sum(A(v, w) for w in Q) for v in Q)", "N(self) is only a randomized copy"),
    ("name = size(P)\nname = comb(name, 2)\nreturn name", "assign each name once"),
    ("<program>\nreturn comb(size(N(self)), 3)", "placeholder"),
    ("neighbors = A(self)\nreturn 0", "two nodes"),
])
def test_rejections_carry_a_repair_hint(source, needle):
    prog, entry = read_draft(f"```dsl\n{source}\n```\naggregate: total")
    assert prog is None and draft_stage(entry["feedback"]) == "parse"
    assert "Hint:" in entry["feedback"] and needle in entry["feedback"]


def test_hints_never_contain_a_code_fence_or_a_task_program():
    for msg in ("no code block found", "sum supports 'for <name> in <set>' without conditions",
                "a program reads either the noisy rows N(...) or the unbiased matrix A(...), not both"):
        hint = repair_hint(msg) or ""
        assert "```" not in hint and "A(j, k)" not in hint


# ---------------------------------------------------------------- GS growth check
@pytest.mark.parametrize("source, aggregate", [
    ("stars = size(P) * (size(P) - 1) * (size(P) - 2) / 6\nreturn stars", "total"),
    ("name = sum(A(j, k) for j in P for k in P) / 2\nreturn name", "total / 3"),
])
def test_gs_growing_with_n_is_rejected(source, aggregate):
    params = design_reference_params(453)
    fb = check_draft(parse_program(source, aggregate), None, params, falsifier=False)
    assert fb is not None and "grows with the number of nodes" in fb and draft_stage(fb) == "gs_loose"


@pytest.mark.parametrize("node_bounds", [False, True])
@pytest.mark.parametrize("task", ["degree", "2-star", "3-star", "triangle", "degree-moment2"])
def test_references_have_n_independent_gs(task, node_bounds):
    assert growth_feedback(reference_program(task, node_bounds), design_reference_params(453)) is None


# ---------------------------------------------------------------- noise-aware gate
def test_public_graphs_are_deterministic_heavy_tailed_and_clustered():
    a, b = public_test_graphs(N), public_test_graphs(N)
    assert [g.edges for _, g in a] == [g.edges for _, g in b]
    import numpy as np

    g = holme_kim(N, 4, 0.6, np.random.default_rng(1))
    degs = [len(g.adj[i]) for i in range(N)]
    from certicount.dsl.utility import reference_counter

    assert max(degs) > 5 * (sum(degs) / N) and reference_counter("triangle")(g) > 50


@pytest.mark.parametrize("gate", [GATE, GATE_NODE], ids=["psc", "node"])
@pytest.mark.parametrize("task", ["degree", "2-star", "3-star", "triangle"])
def test_gate_accepts_the_references(task, gate):
    rep = noise_free_check(reference_program(task, gate.node_bounds), task, gate)
    assert rep.passed, rep.rows


@pytest.mark.parametrize("source, aggregate, task", [
    ("return comb(size(N(self)), 3)", "total", "3-star"),
    ("return comb(size(N(self)), 2)", "total", "2-star"),
    ("s = project(N(self), D)\nreturn sum(size(N(v) & s) for v in s) / 2", "total / 3", "triangle"),
])
def test_gate_rejects_the_release_read_as_the_graph(source, aggregate, task):
    rep = noise_free_check(parse_program(source, aggregate), task, GATE)
    assert not rep.passed and "noise-free check failed" in rep.feedback() and "times the exact answer" in rep.feedback()
    assert draft_stage(rep.feedback()) == "noisy"


def test_gate_rejects_degree_from_the_noisy_row_in_the_node_architecture():
    rep = noise_free_check(parse_program("return size(N(self))", "total / n"), "degree", GATE_NODE)
    assert not rep.passed


class _Script(ChatModelBase):
    """Curator that answers a fixed sequence of replies."""

    def __init__(self, replies: list[str]) -> None:
        super().__init__(model_name="script", stream=False)
        self.replies = list(replies)

    async def __call__(self, messages: list[dict], **kwargs: Any) -> ChatResponse:  # type: ignore[override]
        return _text(self.replies.pop(0))


def test_design_loop_rejects_the_shortcut_with_the_gate_and_accepts_the_rewrite():
    bad = "```dsl\nreturn comb(size(N(self)), 3)\n```\naggregate: total"
    good = "```dsl\nreturn comb(size(project(P, D)), 3)\n```\naggregate: total"
    params = design_reference_params(N)
    res = asyncio.run(design_program(_Script([bad]), FMT, analyst_prompt("3-star", N), N, params, "3-star", 1))
    assert res.accepted  # without the gate the shortcut is accepted (GS 0, exact utility test passes)
    res = asyncio.run(design_program(_Script([bad, good]), FMT, analyst_prompt("3-star", N), N, params, "3-star", 2,
                                     noisy=GATE))
    assert res.accepted and res.iterations == 2
    assert [draft_stage(h["feedback"]) for h in res.history] == ["noisy", "accepted"]


# ---------------------------------------------------------------- transcript grouping
def test_calls_are_grouped_by_design_tag_or_by_position():
    designs = [{"dataset": "PM", "task": "t", "design": k, "llm_calls": c} for k, c in ((0, 2), (1, 1))]
    tagged = [{"dataset": "PM", "task": "t", "design": 1, "reply": "b0"},
              {"dataset": "PM", "task": "t", "design": 0, "reply": "a0"},
              {"dataset": "PM", "task": "t", "design": 0, "reply": "a1"}]
    assert [[c["reply"] for c in g] for g in calls_by_design(designs, tagged)] == [["a0", "a1"], ["b0"]]
    serial = [{"reply": r} for r in ("a0", "a1", "b0")]
    assert [[c["reply"] for c in g] for g in calls_by_design(designs, serial)] == [["a0", "a1"], ["b0"]]


# ---------------------------------------------------------------- prompt cores
RECORDED = Path(__file__).resolve().parents[1] / "results" / "dsl_eval" / "cs5_eval_psc_v0" / "transcripts.jsonl"


@pytest.mark.skipif(not RECORDED.exists(), reason="recorded CS5 transcripts not available")
def test_legacy_core_reproduces_the_recorded_first_prompts():
    from psc.graph import load_dataset
    from certicount import DATA_DIR
    from certicount.dsl.quality import task_record
    from psc.prompts import strip_structured
    recs = load_dataset(DATA_DIR, "PM")
    calls = [json.loads(x) for x in RECORDED.read_text(encoding="utf-8").splitlines() if x.strip()]
    first = [c for c in calls if "previous attempts" not in c["user"]]
    assert first
    for c in first:
        rec = task_record(recs, "PM", c["task"])
        assert strip_structured(design_prompt(rec.input_prompt, rec.vertex_num, [], False, LEGACY_V0)) == c["user"]
    assert load_spec("legacy") is LEGACY_V0
    manifest = json.loads((RECORDED.parent / "manifest.json").read_text(encoding="utf-8"))
    recorded = manifest.get("settings", manifest).get("prompt_spec") or manifest.get("prompt_spec")
    if recorded:
        assert recorded["digest"] == LEGACY_V0.digest


def test_v1_core_has_no_angle_bracket_placeholders_and_a_new_digest():
    for matrix in (False, True):
        ref = dsl_reference("v1", matrix)
        assert not re.search(r"<[a-z_ ]+>", ref)
        assert "<" in dsl_reference("legacy", matrix)
    assert "sum(sum(" in dsl_reference("v1") and "//" in dsl_reference("v1")
    assert V0.core == "v1" and V0.digest != LEGACY_V0.digest
    assert PromptSpec.from_dict({"name": "old", "rules": []}).core == "legacy"  # specs written before cores


# ---------------------------------------------------------------- format normalisation
TAGGED = ("```dsl\n<program>\nd = size(project(P, D))\nreturn d * (d - 1) // 2\naggregate: total\n</program>\n```")


def test_normalisation_repairs_only_the_format():
    prog, entry = read_draft(TAGGED)
    assert prog is None and draft_stage(entry["feedback"]) == "parse"
    prog, entry = read_draft(TAGGED, normalize=True)
    assert prog is not None and prog.aggregate_source.strip() == "total"
    assert prog.source.strip() == "d = size(project(P, D))\nreturn d * (d - 1) / 2"
    assert len(entry["normalized"]) == 3
    src, agg, notes = normalize_source("return size(P)")
    assert (src, agg, notes) == ("return size(P)", None, [])


def test_normalised_draft_is_accepted_and_the_note_reaches_the_next_prompt():
    model = _Script([TAGGED])
    res = asyncio.run(design_program(model, FMT, analyst_prompt("2-star", N), N, design_reference_params(N),
                                     "2-star", 1))
    assert res.accepted and res.history[0]["normalized"]
    off = asyncio.run(design_program(_Script([TAGGED]), FMT, analyst_prompt("2-star", N), N,
                                     design_reference_params(N), "2-star", 1, options=DesignOptions(normalize=False)))
    assert not off.accepted


# ---------------------------------------------------------------- tighter deriver (must stay sound)
P10 = PublicParams(200, D=10, dmax=10, eps1=1.0)


@pytest.mark.parametrize("source, aggregate, gs", [
    ("d = size(project(P, D))\nreturn d * (d - 1) * (d - 2) / 6", "total", 36.0),  # = comb(D, 2), was 45
    ("s = size(project(P, D))\nreturn s * s", "total / n", 19.0),  # = 2D - 1, was 21
    ("Q = project(P, D)\nreturn sum(size(Q & N(v)) for v in Q)", "total / 6", 18.0),  # |Q & N(v)| <= |Q| - 1
    ("Q = project(P, D)\nreturn 0.5 * sum(size(Q - N(j)) - 1 for j in Q)", "total", 9.0),  # size >= 1 for j in Q
])
def test_deriver_is_exact_on_single_count_and_member_rows(source, aggregate, gs):
    prog = parse_program(source, aggregate)
    assert derive(prog, P10).gs == pytest.approx(gs)
    assert falsifier_feedback(prog) is None
    assert bound_slack(prog).ratio == pytest.approx(1.0)


def test_deriver_stays_sound_on_products_of_different_counts():
    prog = parse_program("Q = project(P, D)\nreturn size(Q) * size(Q & N(self)) + size(Q - N(self)) * 2")
    assert derive(prog, P10).gs > 0 and falsifier_feedback(prog) is None


# ---------------------------------------------------------------- tighten round, early stop, min-GS selection
LOOSE_TRI = "```dsl\nQ = project(P, D)\nreturn sum(size(P & N(v)) for v in Q)\n```\naggregate: total / 6"
TIGHT_TRI = "```dsl\nQ = project(P, D)\nreturn sum(size(Q & N(v)) for v in Q)\n```\naggregate: total / 6"


def test_tighten_round_replaces_a_loose_program_only_by_a_tighter_one():
    params = design_reference_params(N)
    model = _Script([LOOSE_TRI, TIGHT_TRI])
    res = asyncio.run(design_program(model, FMT, analyst_prompt("triangle", N), N, params, "triangle", 2,
                                     options=DesignOptions(tighten=2)))
    assert res.accepted and res.llm_calls == 2 and "P & N(v)" not in res.program.source
    assert [draft_stage(h["feedback"]) for h in res.history] == ["superseded", "accepted"]
    assert "loose" in res.history[0]["tighten_request"] and res.history[1]["round"] == "tighten"
    res = asyncio.run(design_program(_Script([LOOSE_TRI, LOOSE_TRI]), FMT, analyst_prompt("triangle", N), N, params,
                                     "triangle", 2, options=DesignOptions(tighten=2)))
    assert res.accepted and "P & N(v)" in res.program.source and draft_stage(res.history[-1]["feedback"]) == "not_tighter"
    res = asyncio.run(design_program(_Script([TIGHT_TRI]), FMT, analyst_prompt("triangle", N), N, params,
                                     "triangle", 2, options=DesignOptions(tighten=2)))
    assert res.llm_calls == 1  # already tight: no extra call


def test_early_stop_after_two_rejections_of_the_same_stage():
    bad = "```dsl\nreturn size(P) +\n```\naggregate: total"
    res = asyncio.run(design_program(_Script([bad, bad + " "]), FMT, analyst_prompt("degree", N), N,
                                     design_reference_params(N), "degree", 5,
                                     options=DesignOptions(early_stop=("parse",))))
    assert not res.accepted and res.llm_calls == 2 and res.history[-1]["early_stop"]


# ---------------------------------------------------------------- feedback ablation
class _Recorder(_Script):
    """_Script that also keeps the prompts it was sent."""

    def __init__(self, replies: list[str]) -> None:
        super().__init__(replies)
        self.prompts: list[str] = []

    async def __call__(self, messages: list[dict], **kwargs: Any) -> ChatResponse:  # type: ignore[override]
        user = next(m for m in reversed(messages) if m.get("role") == "user")["content"]
        self.prompts.append(user if isinstance(user, str) else json.dumps(user))
        return await super().__call__(messages, **kwargs)


def test_feedback_modes_change_only_what_the_redraft_prompt_shows():
    loose = "```dsl\nreturn comb(size(P), 3)\n```\naggregate: total"  # unprojected 3-star: rejected as too loose
    good = "```dsl\nreturn comb(size(project(P, D)), 3)\n```\naggregate: total"
    params = design_reference_params(N)
    prompts, stages = {}, {}
    for mode in ("full", "binary", "none"):
        model = _Recorder([loose, good])
        res = asyncio.run(design_program(model, FMT, analyst_prompt("3-star", N), N, params, "3-star", 3,
                                         options=DesignOptions(feedback=mode)))
        assert res.accepted and res.llm_calls == 2
        prompts[mode], stages[mode] = model.prompts, [draft_stage(h["feedback"]) for h in res.history]
    assert stages["full"] == stages["binary"] == stages["none"]  # the same checks in every mode
    assert prompts["full"][0] == prompts["binary"][0] == prompts["none"][0]
    diagnosis = res.history[0]["feedback"].removeprefix("rejected: ")[:40]
    assert diagnosis in prompts["full"][1]
    assert "comb(size(P), 3)" in prompts["binary"][1] and diagnosis not in prompts["binary"][1]
    assert "Result: rejected" in prompts["binary"][1]
    assert prompts["none"][1] == prompts["none"][0]  # an independent sample of the first prompt


def test_feedback_ablation_excludes_tighten_requests():
    with pytest.raises(ValueError):
        DesignOptions(feedback="none", tighten=1)
    with pytest.raises(ValueError):
        DesignOptions(feedback="hints")


def test_min_gs_selection_keeps_the_tightest_accepted_program():
    params = design_reference_params(N)
    first = asyncio.run(design_with_restarts(_Script([LOOSE_TRI, TIGHT_TRI]), FMT, analyst_prompt("triangle", N), N,
                                             params, "triangle", 1, restarts=2))
    assert "P & N(v)" in first.program.source and first.restarts == 1
    res = asyncio.run(design_with_restarts(_Script([LOOSE_TRI, TIGHT_TRI]), FMT, analyst_prompt("triangle", N), N,
                                           params, "triangle", 1, restarts=2,
                                           options=DesignOptions(select="min_gs", min_accepted=2)))
    assert res.restarts == 2 and res.selection["chosen_restart"] == 2 and "P & N(v)" not in res.program.source
    assert [c["gs"] for c in res.selection["candidates"]] == [30.0, 18.0]


# ---------------------------------------------------------------- prompt cores of CS6a (A v1 / B v1-repeat3 / C v1-alt)
def _cs6_prompt(core: str, history: list[dict] | None = None) -> str:
    from psc.prompts import strip_structured
    return strip_structured(design_prompt(analyst_prompt("triangle", N), N, history or [], False, load_spec(core)))


def test_core_b_states_the_prohibition_three_times_and_core_c_gives_rewrites():
    from certicount.dsl.designer import ALTERNATIVES, CHECKLIST, NOT_SUPPORTED
    a, b, c = (_cs6_prompt(k) for k in ("v1", "v1-repeat3", "v1-alt"))
    assert NOT_SUPPORTED in a and a.count(NOT_SUPPORTED) == 1
    assert b.count(NOT_SUPPORTED) == 3 and b.startswith(NOT_SUPPORTED) and b.replace(NOT_SUPPORTED, "").strip()
    assert b.index(NOT_SUPPORTED, len(b) // 2) < b.index("Reply with exactly two parts")
    assert c.count(NOT_SUPPORTED) == 1 and ALTERNATIVES in c and c.index(CHECKLIST) < c.index("Reply with")
    assert len({load_spec(k).digest for k in ("v0", "legacy", "v1-repeat3", "v1-alt")}) == 4
    with pytest.raises(ValueError):
        dsl_reference("v2")


@pytest.mark.parametrize("rewrite, expected", [
    ("0.5 * sum(size(P) - 1 for v in P)", lambda S, rows: sum(1 for v in S for w in S if v < w)),
    ("0.5 * sum(size(P & N(v)) for v in P)", lambda S, rows: sum(1 for v in S for w in S if v < w and w in rows[v])),
    ("0.5 * sum(size(P - N(v)) - 1 for v in P)",
     lambda S, rows: sum(1 for v in S for w in S if v < w and w not in rows[v])),
])
def test_the_rewrites_of_core_c_equal_the_python_conditions(rewrite, expected):
    rnd = random.Random(5)
    prog = parse_program(f"return {rewrite}", clamp_nonnegative=False)
    for _ in range(100):
        rows = {i: set() for i in range(9)}
        for a in range(9):
            for b in range(a + 1, 9):
                if rnd.random() < 0.4:
                    rows[a].add(b)
                    rows[b].add(a)
        frozen = {i: frozenset(v) for i, v in rows.items()}
        S = frozenset(rnd.sample(range(1, 9), rnd.randint(0, 6)))
        assert Interpreter(prog).local(Env(S, 0, frozen, 9, D=8, dmax=8)) == pytest.approx(expected(S, frozen))


def test_core_c_hints_give_the_rewrite_and_other_cores_keep_theirs():
    cond = "```dsl\nreturn sum(1 for a in P for b in P if a < b)\n```\naggregate: total"
    power = "```dsl\nreturn size(P) ** 2\n```\naggregate: total"
    assert "0.5 * sum(size(S & N(v)) for v in S)" in read_draft(cond, core="v1-alt")[1]["feedback"]
    assert "remove the 'if' condition" in read_draft(cond)[1]["feedback"]
    assert "pow(x, 2)" in read_draft(power, core="v1-alt")[1]["feedback"]
    assert "Hint" not in read_draft(power, core="v1-repeat3")[1]["feedback"]
