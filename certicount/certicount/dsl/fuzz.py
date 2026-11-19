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

# (n, dmax, random symmetric graphs; None = every graph[, D: the node's own bound, default dmax])
Setting = tuple[int, ...] | tuple
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


class _MatrixGenerator(_Generator):
    """Programs of the per-node architecture that read the unbiased matrix ``A`` (never ``N``):
    sets built from ``P`` only, numbers that include entries and sums of ``A``."""

    BASE_SETS = ("P", "project(P, D)", "project(P, D)", "project(P, dmax)", "project(P, D - 1)", "project(P, 2)")

    def row(self, var: str) -> str:  # no rows in this architecture: a P-only set
        return self.set(1, ())

    def set(self, depth: int, loops: tuple[str, ...]) -> str:
        r = self.rng.random()
        if depth <= 0 or r < 0.5:
            return self.pick([*self.BASE_SETS, *self.sets])
        a, b = self.set(depth - 1, loops), self.set(depth - 1, loops)
        if r < 0.65:
            return f"({a} & {b})"
        if r < 0.72:
            return f"({a} | {b})"
        if r < 0.85:
            return f"({a} - {b})"
        return f"project({a}, {self.pick(THRESHOLDS)})"

    def sum(self, depth: int, loops: tuple[str, ...], integer: bool = False) -> str:
        free = [v for v in LOOP_VARS if v not in loops]
        if not free:
            return self.count(0, loops) if integer else self.num(0, loops)
        var = free[0]
        inner = loops + (var,)
        body = self.count(depth, inner) if integer or self.rng.random() < 0.5 else self.num(depth, inner)
        return f"sum({body} for {var} in {self.set(depth, loops)})"

    def entry(self, loops: tuple[str, ...]) -> str:
        nodes = ["self", *loops, *loops]
        return f"A({self.pick(nodes)}, {self.pick(nodes)})"

    def num(self, depth: int, loops: tuple[str, ...]) -> str:
        r = self.rng.random()
        if r < 0.2:
            return self.entry(loops)
        if r < 0.45:
            return self.matrix_sum(depth - 1, loops)
        return super().num(depth, loops)

    def matrix_sum(self, depth: int, loops: tuple[str, ...]) -> str:
        free = [v for v in LOOP_VARS if v not in loops]
        if not free:
            return self.entry(loops)
        var = free[0]
        inner = loops + (var,)
        domain = self.set(depth, loops)
        r = self.rng.random()
        if r < 0.4:
            body = self.entry(inner)
        elif r < 0.6:
            body = f"{self.entry(inner)} * {self.pick(SCALARS)}"
        elif r < 0.8 and depth > 0:
            body = self.matrix_sum(depth - 1, inner)
        else:
            body = f"({self.entry(inner)} {self.pick('+-*')} {self.num(depth - 1, inner)})"
        return f"sum({body} for {var} in {domain})"


MATRIX_SETS = ("project(P, D)", "project(P, D - 1)", "project(P, 2)", "P", "project(P, dmax)")


def matrix_shape_source(rng: random.Random) -> str:
    """The ``A`` programs LLM curators write in the per-node architecture: pair sums over
    one or two bounded sets (triangles), degree estimates ``sum(A(self, j))`` and their
    powers, pair counts minus pair sums (open wedges), with the diagonal and repeated
    entries the deriver's zero-diagonal rule must handle."""
    s, t = rng.choice(MATRIX_SETS), rng.choice(MATRIX_SETS)
    pair = rng.choice((
        "sum(sum(A(j, k) for k in Q) for j in Q)", "sum(sum(A(k, j) for k in Q) for j in Q)",
        "sum(sum(A(j, k) for k in T) for j in Q)", "sum(sum(A(j, k) * A(j, k) for k in Q) for j in Q)",
        "sum(sum(A(j, k) * A(self, k) for k in Q) for j in Q)", "sum(A(self, j) for j in Q)",
        "sum(A(j, self) * size(Q) for j in Q)", "sum(sum(A(j, k) for k in (Q - T)) for j in Q)",
        "sum(sum(A(j, k) for k in (Q | T)) for j in (Q & T))", "sum(A(j, j) + A(self, j) for j in Q)",
    ))
    body = rng.choice(("comb(size(Q), 2) - 0.5 * x", "x * x", "x * (x - 1) * (x - 2) / 6", "clip(x, 0, D * D)",
                       "x * size(Q)", "x", "0.5 * x", "-1 * x", "x + size(T)"))
    lines = [f"Q = {s}"] + ([f"T = {t}"] if "T" in pair or "T" in body else []) + [f"x = {pair}", f"return {body}"]
    return "\n".join(lines)


def random_source(rng: random.Random, depth: int = 3, focus: float = 0.5, shapes: float = 0.0,
                  matrix: float = 0.0) -> str:
    """The local part of one random program (the aggregate plays no part in the
    GS); with probability ``focus`` a program around a sum of rows, with probability
    ``shapes`` (checked first; ``0`` keeps the sequences of earlier campaigns) one of
    the shapes of :func:`shape_source`. ``matrix`` (checked before ``shapes``; ``0`` keeps
    the earlier sequences): share of programs that read ``A`` (half of them shapes of
    :func:`matrix_shape_source`, half random :class:`_MatrixGenerator` programs)."""
    if matrix and rng.random() < matrix:
        if rng.random() < 0.5:
            return matrix_shape_source(rng)
        g = _MatrixGenerator(rng)
        lines = []
        for i in range(rng.choice((0, 1, 1, 2))):
            if rng.random() < 0.5:
                lines.append(f"S{i} = {g.set(depth - 1, ())}")
                g.sets.append(f"S{i}")
            else:
                lines.append(f"x{i} = {g.num(depth - 1, ())}")
                g.nums.append(f"x{i}")
        lines.append(f"return {g.matrix_sum(depth - 1, ()) if rng.random() < 0.5 else g.num(depth, ())}")
        return "\n".join(lines)
    if shapes and rng.random() < shapes:
        return shape_source(rng)
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


SHAPE_SETS = ("project(P, D)", "project(P, D - 1)", "project(P, 2)", "P", "(P & N(self))",
              "project((P & N(self)), D)", "(project(P, D) - N(self))", "(project(P, D) | N(self))")


def shape_source(rng: random.Random) -> str:
    """Programs for the rules that bound one private count exactly and the rows of a
    loop variable over its own domain (:meth:`certicount.dsl.sensitivity._Deriver.univariate`,
    ``row_of_member``, ``fixed_side_dsize``): polynomials / clips of one ``size(S)``, and
    sums over ``S`` of ``|S & N(j)|`` (the pair counts LLM curators write)."""
    s = rng.choice(SHAPE_SETS)
    if rng.random() < 0.5:
        a, b = rng.randint(0, 3), rng.choice((1, 2, 6, -3))
        body = rng.choice((
            f"d * (d - {a})", f"d * (d - 1) * (d - {a}) / {b}", f"(d - {a}) * (d - {a})", f"d * d - {a} * d",
            f"clip(d * d - D, 0, D * D)", f"min(d * (d - 1), D) + comb(d, 2)", f"-(d * (d + {a})) / {b}",
            f"pow(d - {a}, 2) + d", f"max(d * d, {a} * D) - comb(d, 3)",
        ))
        return f"d = size({s})\nreturn {body}"
    j, k = "j", "k"
    row = rng.choice((f"(N({j}) & Q)", f"(Q & N({j}))", f"(N({j}) & Q & N(self))", f"(Q - N({j}))",
                      f"(N({j}) | Q)", f"project((N({j}) & Q), 2)"))
    body = rng.choice((f"size({row})", f"comb(size({row}), 2)", f"size({row}) * size({row})", f"size({row}) - 1",
                       f"size({row}) + size(P & N({j}))", f"sum(size(N({k}) & Q) for {k} in (N({j}) & Q))",
                       f"size((Q - N({j})) & (Q | N({j})))"))
    scale = rng.choice(("", "0.5 * ", "-1 * "))
    return f"Q = {s}\nreturn {scale}sum({body} for {j} in Q)"


def sources(count: int, seed: int = 0, depth: int = 3, focus: float = 0.5, shapes: float = 0.0,
            matrix: float = 0.0) -> list[str]:
    rng = random.Random(seed)
    return [random_source(rng, depth, focus, shapes, matrix) for _ in range(count)]


def unpack(setting: Sequence) -> tuple[int, int, int | None, int | None]:
    """``(n, dmax, samples, D)`` of a setting; ``D`` (the node's own bound of the per-node
    architecture) is optional and ``None`` means ``D = dmax``."""
    n, dmax, samples, *rest = setting
    return n, dmax, samples, (rest[0] if rest else None)


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
    checks = []
    for s in settings:
        n, dmax, samples, D = unpack(s)
        checks.append(check_derivation(program, n, dmax, samples, seed, D=D))
    return FuzzCase(index, source, checks)


def fuzz(count: int, seed: int = 0, depth: int = 3, settings: Sequence[Setting] = DEFAULT_SETTINGS,
         focus: float = 0.5, shapes: float = 0.0, matrix: float = 0.0) -> Iterator[FuzzCase]:
    for i, src in enumerate(sources(count, seed, depth, focus, shapes, matrix)):
        yield run_case(i, src, settings, seed)


def summarize(cases: Iterable[FuzzCase], settings: Sequence[Setting]) -> list[dict]:
    """Per setting: programs the deriver bounds, refutations, interpreter errors and
    how tight the bounds are (``gs / max_delta`` over programs with ``max_delta > 0``)."""
    cases = list(cases)
    rows = []
    for k, s in enumerate(settings):
        n, dmax, samples, D = unpack(s)
        checks = [c.checks[k] for c in cases]
        checked = [c for c in checks if c.witness is not None]
        ratios = [c.gs / c.witness.max_delta for c in checked if c.witness.max_delta > 0]
        rows.append({
            "n": n, "dmax": dmax, "D": dmax if D is None else D,
            "graphs": "every" if samples is None else f"{samples} random",
            "programs": len(checks), "derived": sum(c.gs is not None for c in checks),
            "reads_matrix": sum(parse_program(c.source).uses_matrix for c in cases),
            "rejected_by_deriver": sum(c.skipped is not None for c in checks),
            "interpreter_errors": sum(c.error is not None for c in checks),
            "falsified": len(checked), "refuted": sum(c.refuted for c in checked),
            "tight": sum(c.tight for c in checked),
            "median_gs_over_max": st.median(ratios) if ratios else None,
            "max_gs_over_max": max(ratios) if ratios else None,
            "zero_change": sum(c.witness.max_delta == 0 for c in checked),
        })
    return rows
