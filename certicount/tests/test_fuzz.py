"""Soundness of the sensitivity deriver: regressions and differential tests on random programs."""

from __future__ import annotations

import pytest

from certicount.dsl import designer, sensitivity
from certicount.dsl.designer import check_draft, design_reference_params
from certicount.dsl.falsifier import check_derivation
from certicount.dsl.fuzz import fuzz, summarize
from certicount.dsl.lang import Call, Name, parse_program
from certicount.dsl.sensitivity import PublicParams, derive

# Sums over P & N(self) whose summand reads the row N(j) other than as P & N(j).
# For the new summand j = v (v in N(self)) self is in N(v); the deriver used to
# bound every use of N(v) by dmax - 1, which only holds for sets without self.
# Value: the GS at n = 5, dmax = 3 (tight: the falsifier reaches it).
REFUTED_BEFORE = {
    "bare row": ("S = P & N(self)\nreturn sum(size(P & N(j)) + size(N(j)) for j in S)", 7.0),
    "row times private row": ("S = P & N(self)\nreturn sum(size(N(j)) * size(P & N(j)) for j in S)", 12.0),
}


def _restore_old_row_rule(monkeypatch) -> None:
    """Put back the pre-fix rule: every use of the new summand's row has at most dmax - 1 vertices."""
    original = sensitivity._Deriver.set

    def old_set(self, e, rows):
        if isinstance(e, Call) and e.func == "N" and isinstance(e.args[0], Name):
            row = rows.get(e.args[0].id)
            if row is not None and row.has_self:
                return sensitivity.SetInfo(False, max(0.0, row.bound - 1), 0.0, 0.0)
        return original(self, e, rows)

    monkeypatch.setattr(sensitivity._Deriver, "set", old_set)
    monkeypatch.setattr(designer, "_FALSIFIER_CACHE", {})


@pytest.mark.parametrize("name", list(REFUTED_BEFORE))
def test_the_row_of_the_new_summand_contains_self(name, monkeypatch):
    src, gs = REFUTED_BEFORE[name]
    chk = check_derivation(parse_program(src), n=5, dmax=3)
    assert not chk.refuted and chk.tight and chk.gs == gs
    _restore_old_row_rule(monkeypatch)
    old = check_derivation(parse_program(src), n=5, dmax=3)
    assert old.refuted and old.gs < gs


def test_sets_without_self_keep_the_tighter_bound():
    # P & N(v) and N(v) & N(self) (no self-loops in G') still have at most dmax - 1 vertices
    p = PublicParams(49, 16, 16)
    assert derive(parse_program("S = P & N(self)\nreturn 0.5 * sum(size(P & N(j)) for j in S)"), p).gs == 15
    prog = parse_program("S = P & N(self)\nreturn sum(size(P & N(j)) * size(N(j) & N(self)) for j in S)")
    assert derive(prog, PublicParams(5, 3, 3)).gs == 10  # 2*2 + 2*3 for v in N(self), not 3*2 + 2*3


def test_projection_threshold_is_rounded_down_and_never_negative():
    for k, size in (("D * 0.5", 1), ("-1", 0), ("D", 3)):
        der = derive(parse_program(f"return size(project(P, {k}))"), PublicParams(49, 3, 3))
        assert der.gs == (1 if size else 0)
        chk = check_derivation(parse_program(f"return comb(size(project(P, {k})), 2)"), n=5, dmax=3)
        assert not chk.refuted and chk.tight


def test_random_programs_never_refute_the_deriver():
    settings = ((5, 3, None), (7, 4, 30))
    cases = list(fuzz(120, seed=0, settings=settings))
    bad = [c.to_dict() for c in cases if c.refuted or c.failed]
    assert not bad, bad[:2]
    exhaustive = summarize(cases, settings)[0]
    assert exhaustive["derived"] >= 0.9 * len(cases) and exhaustive["tight"] >= 0.25 * len(cases)
    # the generator keeps reaching the rule for sums over P & N(self)
    special = sum(any("in P & N(self)" in t for t in derive(parse_program(c.source), PublicParams(5, 3, 3)).trace)
                  for c in cases)
    assert special >= 0.25 * len(cases)


def test_random_programs_catch_the_old_rule(monkeypatch):
    _restore_old_row_rule(monkeypatch)
    assert any(c.refuted for c in fuzz(40, seed=0))


def test_design_check_rejects_a_draft_the_falsifier_refutes(monkeypatch):
    prog = parse_program(REFUTED_BEFORE["bare row"][0])
    params = design_reference_params(49)
    assert check_draft(prog, None, params) is None
    _restore_old_row_rule(monkeypatch)
    assert check_draft(prog, None, params, falsifier=False) is None  # the old deriver alone accepts it
    feedback = check_draft(prog, None, params)
    assert feedback is not None and "certification failed" in feedback


def test_check_is_skipped_where_the_deriver_rejects_the_program():
    chk = check_derivation(parse_program("return size(P) / (D - 3)"), n=5, dmax=3)
    assert chk.skipped and chk.witness is None and not chk.refuted
    assert check_draft(parse_program("return size(P) / (D - 3)"), None, design_reference_params(49)) is None
