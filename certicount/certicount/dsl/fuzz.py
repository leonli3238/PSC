"""Random DSL programs for differential testing of the sensitivity deriver.

:func:`random_source` draws a well-typed program of :mod:`certicount.dsl.lang`:
assignments, set algebra, projections with public thresholds, nested sums,
``comb`` / ``pow`` / ``clip`` / ``min`` / ``max`` and public divisors. The
choices favour the shapes the deriver treats specially: sums over
``P & N(self)``, and the row ``N(j)`` of the loop variable inside the summand
(alone, met with ``P`` or ``N(self)``, minus ``P``, under a projection).

:func:`fuzz` checks every program with
:func:`certicount.dsl.falsifier.check_derivation`: the GS derived at small
public parameters against the largest change the falsifier finds with the same
parameters. A sound deriver is never refuted, so a refutation is a bug of the
deriver (or of the interpreter), not of the program. ``tests/test_fuzz.py``
runs a few hundred programs; ``scripts/run_dsl_fuzz.py`` runs campaigns.
"""

from __future__ import annotations

import random
import statistics as st
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Sequence

from .falsifier import DerivationCheck, check_derivation
from .lang import parse_program

Setting = tuple[int, int, int | None]  # (n, dmax, random symmetric graphs; None = every graph)
DEFAULT_SETTINGS: tuple[Setting, ...] = ((5, 3, None),)

LOOP_VARS = ("j", "k", "u")
THRESHOLDS = ("D", "dmax", "D - 1", "D + 1", "D * 0.5", "n - 4", "0", "1", "2", "-1")
DIVISORS = ("2", "3", "-2", "0.5", "D", "(D + 1)", "n")
CLIP_BOUNDS = (("0", "1"), ("0", "D"), ("1", "n"), ("-1", "2"), ("0", "0.5"), ("0", "D * D"))
SCALARS = ("0.5", "2", "-1", "3")


class _Generator:
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.sets: list[str] = []  # assigned set names
        self.nums: list[str] = []  # assigned number names

    def pick(self, options: Sequence[str]) -> str:
        return self.rng.choice(list(options))

    # -- sets ------------------------------------------------------------------
    def row(self, var: str) -> str:
        """A set built on the row of a loop variable."""
        return self.pick((
            f"N({var})", f"(P & N({var}))", f"(N({var}) & P)", f"(N({var}) - P)", f"(P - N({var}))",
            f"(N({var}) & N(self))", f"(N({var}) | P)", f"(project(P, D) & N({var}))", f"project(N({var}), D - 1)",
        ))

    def set(self, depth: int, loops: tuple[str, ...]) -> str:
        r = self.rng.random()
        if loops and r < 0.3:
            return self.row(self.pick(loops))
        if depth <= 0 or r < 0.5:
            return self.pick(["P", "P", "N(self)", "(P & N(self))", *self.sets, *(f"N({v})" for v in loops)])
        a, b = self.set(depth - 1, loops), self.set(depth - 1, loops)
        if r < 0.65:
            return f"({a} & {b})"
        if r < 0.72:
            return f"({a} | {b})"
        if r < 0.8:
            return f"({a} - {b})"
        return f"project({a}, {self.pick(THRESHOLDS)})"

    # -- numbers ---------------------------------------------------------------
    def count(self, depth: int, loops: tuple[str, ...]) -> str:
        """A nonnegative integer (a valid argument of comb and pow)."""
        r = self.rng.random()
        if depth <= 0 or r < 0.4:
            return f"size({self.set(depth - 1, loops)})"
        if r < 0.55:
            return f"comb({self.count(depth - 1, loops)}, {self.rng.randint(0, 3)})"
        if r < 0.62:
            return f"pow({self.count(depth - 1, loops)}, {self.rng.randint(0, 2)})"
        if r < 0.7:
            return f"{self.pick(('min', 'max'))}({self.count(depth - 1, loops)}, {self.count(depth - 1, loops)})"
        if r < 0.8:
            return f"({self.count(depth - 1, loops)} {self.pick('+*')} {self.count(depth - 1, loops)})"
        if r < 0.85:
            return self.pick(("0", "1", "2", "D", "n"))
        return self.sum(depth - 1, loops, integer=True)

    def num(self, depth: int, loops: tuple[str, ...]) -> str:
        r = self.rng.random()
        if depth <= 0 or r < 0.3:
            return self.pick(self.nums) if self.nums and r < 0.05 else self.count(depth, loops)

        def sub() -> str:
            return self.num(depth - 1, loops)

        if r < 0.5:
            return self.sum(depth - 1, loops)
        if r < 0.6:
            return f"({sub()} {self.pick('+-*')} {sub()})"
        if r < 0.67:
            return f"({sub()}) / {self.pick(DIVISORS)}"
        if r < 0.72:
            return f"-({sub()})"
        if r < 0.8:
            return f"{self.pick(SCALARS)} * {sub()}"
        if r < 0.88:
            lo, hi = self.rng.choice(CLIP_BOUNDS)
            return f"clip({sub()}, {lo}, {hi})"
        if r < 0.95:
            return f"{self.pick(('min', 'max'))}({sub()}, {sub()})"
        return self.pick(("0", "1", "0.5", "D", "dmax", "n"))

    def sum(self, depth: int, loops: tuple[str, ...], integer: bool = False) -> str:
        free = [v for v in LOOP_VARS if v not in loops]
        if not free:
            return self.count(0, loops) if integer else self.num(0, loops)
        var = free[0]
        if self.rng.random() < 0.8:
            domain = self.pick([
                "(P & N(self))", "(P & N(self))", "(N(self) & P)", "P", "N(self)", "project(P, D)", *self.sets,
                *(f"(P & N({v}))" for v in loops), *(f"N({v})" for v in loops),
            ])
        else:
            domain = self.set(depth, loops)
        inner = loops + (var,)
        body = self.count(depth, inner) if integer or self.rng.random() < 0.6 else self.num(depth, inner)
        if self.rng.random() < 0.5:  # let the summand read the row of its own variable
            body = f"({body} {self.pick('+*' if integer else '+-*')} size({self.row(var)}))"
        return f"sum({body} for {var} in {domain})"

    def local_row(self, var: str) -> str:
        """A set on the row of a loop variable that reads ``P`` only as ``P & N(var)``."""
        return self.pick((
            f"N({var})", f"(P & N({var}))", f"(N({var}) & P)", f"(N({var}) & N(self))",
            f"((P & N({var})) & N(self))", f"project((P & N({var})), 2)",
        ))

    def row_term(self, var: str) -> str:
        t = f"size({self.local_row(var)})"
        r = self.rng.random()
        if r < 0.15:
            return f"comb({t}, 2)"
        if r < 0.25:
            return f"{self.pick(SCALARS)} * {t}"
        return t

    def row_sum(self, depth: int, loops: tuple[str, ...]) -> str:
        """A sum of a private row ``P & N(var)`` and other rows of ``var`` (and
        nested sums of the same kind). Their bounds are close to tight, so an
        off-by-one in a rule is not hidden by the slack of the rest of the program
        (a public summand would not even reach the private-summand rules)."""
        var = next(v for v in LOOP_VARS if v not in loops)
        inner = loops + (var,)
        domain = self.pick(["(P & N(self))", "(P & N(self))", "(N(self) & P)", "P", "N(self)", "project(P, D)",
                            *self.sets, *(f"N({v})" for v in loops), *(self.local_row(v) for v in loops)])
        terms = [self.pick((f"size(P & N({var}))", f"size(N({var}) & P)")), self.row_term(var)]
        if self.rng.random() < 0.3:
            terms.append(self.row_term(var))
        if depth > 0 and len(inner) < len(LOOP_VARS) and self.rng.random() < 0.35:
            terms.append(self.row_sum(depth - 1, inner))
        self.rng.shuffle(terms)
        op = f" {self.pick('++*')} "
        return f"sum({op.join(terms)} for {var} in {domain})"


def random_source(rng: random.Random, depth: int = 3, focus: float = 0.5) -> str:
    """The local part of one random program (the aggregate plays no part in the
    GS); with probability ``focus`` a program around a sum of rows."""
    g = _Generator(rng)
    lines = []
    if rng.random() < focus:
        if rng.random() < 0.3:
            lines.append("S0 = P & N(self)")
            g.sets.append("S0")
        ret = g.row_sum(depth - 1, ())
        if rng.random() < 0.3:
            ret = f"{g.pick(SCALARS)} * {ret}"
        return "\n".join([*lines, f"return {ret}"])
    for i in range(rng.choice((0, 0, 1, 1, 2))):
        if rng.random() < 0.6:
            lines.append(f"S{i} = {g.set(depth - 1, ())}")
            g.sets.append(f"S{i}")
        else:
            lines.append(f"x{i} = {g.num(depth - 1, ())}")
            g.nums.append(f"x{i}")
    lines.append(f"return {g.num(depth, ())}")
    return "\n".join(lines)


def sources(count: int, seed: int = 0, depth: int = 3, focus: float = 0.5) -> list[str]:
    rng = random.Random(seed)
    return [random_source(rng, depth, focus) for _ in range(count)]


@dataclass
class FuzzCase:
    index: int
    source: str
    checks: list[DerivationCheck] = field(default_factory=list)  # one per setting

    @property
    def refuted(self) -> bool:
        return any(c.refuted for c in self.checks)

    @property
    def failed(self) -> bool:
        """The interpreter raised on a test graph."""
        return any(c.error for c in self.checks)

    def to_dict(self) -> dict:
        return {"index": self.index, "source": self.source, "checks": [c.to_dict() for c in self.checks]}


def run_case(index: int, source: str, settings: Sequence[Setting] = DEFAULT_SETTINGS, seed: int = 0) -> FuzzCase:
    program = parse_program(source)
    return FuzzCase(index, source, [check_derivation(program, n, dmax, samples, seed) for n, dmax, samples in settings])


def fuzz(count: int, seed: int = 0, depth: int = 3, settings: Sequence[Setting] = DEFAULT_SETTINGS,
         focus: float = 0.5) -> Iterator[FuzzCase]:
    for i, src in enumerate(sources(count, seed, depth, focus)):
        yield run_case(i, src, settings, seed)


def summarize(cases: Iterable[FuzzCase], settings: Sequence[Setting]) -> list[dict]:
    """Per setting: programs the deriver bounds, refutations, interpreter errors and
    how tight the bounds are (``gs / max_delta`` over programs with ``max_delta > 0``)."""
    cases = list(cases)
    rows = []
    for k, (n, dmax, samples) in enumerate(settings):
        checks = [c.checks[k] for c in cases]
        checked = [c for c in checks if c.witness is not None]
        ratios = [c.gs / c.witness.max_delta for c in checked if c.witness.max_delta > 0]
        rows.append({
            "n": n, "dmax": dmax, "graphs": "every" if samples is None else f"{samples} random",
            "programs": len(checks), "derived": sum(c.gs is not None for c in checks),
            "rejected_by_deriver": sum(c.skipped is not None for c in checks),
            "interpreter_errors": sum(c.error is not None for c in checks),
            "falsified": len(checked), "refuted": sum(c.refuted for c in checked),
            "tight": sum(c.tight for c in checked),
            "median_gs_over_max": st.median(ratios) if ratios else None,
            "max_gs_over_max": max(ratios) if ratios else None,
            "zero_change": sum(c.witness.max_delta == 0 for c in checked),
        })
    return rows
