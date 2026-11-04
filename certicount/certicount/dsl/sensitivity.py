"""Static sensitivity derivation for DSL programs (verification layer L3).

For a flip of one bit of the private set ``P`` (add or remove a vertex ``v``;
under degree projection the coupled projected sets differ by a replacement),
the deriver bounds ``|f(P) - f(P')|`` by abstract interpretation:

* a set is described by its maximum size, the maximum symmetric difference
  ``dsym`` and the maximum size change ``dsize`` between neighbouring inputs;
* a number by its change ``delta`` and its range ``[lo, hi]``.

Three public facts about the projected noisy graph ``G'`` make the bound tight
and can be switched off to show what each one buys:

* ``symmetric_rows``     -- ``j in N(i)`` iff ``i in N(j)`` (symmetric projection);
* ``self_not_in_private`` -- ``self`` never belongs to ``P``;
* ``rows_bounded``        -- every row has at most ``dmax`` entries.

``G'`` has no self-loops, so ``self`` is never in ``N(self)`` either. In a sum
over ``P & N(self)`` the new summand ``j = v`` (the flipped vertex, ``v`` in
``N(self)``) has ``self`` in its row ``N(v)``: only a set that excludes ``self``
meets ``N(v)`` in at most ``dmax - 1`` vertices; ``N(v)`` itself may have
``dmax``.

The certificate is only as strong as the rules below; the falsifier
(:mod:`certicount.dsl.falsifier`) searches small graphs for counterexamples, and
the derived values are checked against the hand derivations of the library
tasks (``1``, ``C(D-1, 2)``, ``dmax - 1``) in ``tests/test_dsl.py``.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

from .lang import BinOp, Call, Const, Expr, Name, Neg, Program, Sum

INF = math.inf


class SensitivityError(ValueError):
    """The program has no finite sensitivity bound; ``str()`` is the feedback."""


@dataclass(frozen=True)
class PublicParams:
    """Public values the node knows before it executes the program.

    ``D`` / ``dmax`` are ``None`` when no degree bound was published (no GS
    optimisation): the noisy rows are then only bounded by ``n - 1``.
    """

    n: int
    D: int | None = None
    dmax: int | None = None

    def value(self, name: str) -> float:
        v = getattr(self, name)
        if v is None:
            raise SensitivityError(f"the program reads {name} but no degree bound was published")
        return float(v)


@dataclass(frozen=True)
class Facts:
    symmetric_rows: bool = True
    self_not_in_private: bool = True
    rows_bounded: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SetInfo:
    private: bool
    max_size: float
    dsym: float
    dsize: float


@dataclass(frozen=True)
class _Row:
    """What is known of ``N(j)`` for a loop variable ``j``: ``|N(j)| <= bound``,
    and (``has_self``) ``self in N(j)``."""

    bound: float
    has_self: bool = False


@dataclass(frozen=True)
class NumInfo:
    private: bool
    delta: float
    lo: float
    hi: float
    integer: bool

    @property
    def magnitude(self) -> float:
        return max(abs(self.lo), abs(self.hi))

    @property
    def constant(self) -> bool:
        return self.delta == 0 and self.lo == self.hi


@dataclass
class Derivation:
    gs: float
    params: PublicParams
    facts: Facts
    trace: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    facts_used: set[str] = field(default_factory=set)

    def to_dict(self) -> dict:
        return {
            "gs": self.gs, "params": asdict(self.params), "facts": self.facts.to_dict(),
            "facts_used": sorted(self.facts_used), "trace": self.trace, "warnings": self.warnings,
        }


@dataclass(frozen=True)
class Certificate:
    """What a curator ships with a program and what the node re-derives."""

    program_digest: str
    params: PublicParams
    facts: Facts
    gs: float
    trace: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "program_digest": self.program_digest, "params": asdict(self.params), "facts": self.facts.to_dict(),
            "gs": self.gs, "trace": list(self.trace), "warnings": list(self.warnings),
        }


class _Deriver:
    def __init__(self, program: Program, params: PublicParams, facts: Facts) -> None:
        self.program = program
        self.p = params
        self.facts = facts
        self.trace: list[str] = []
        self.warnings: list[str] = []
        self.facts_used: set[str] = set()
        self.cache: dict[str, SetInfo | NumInfo] = {}

    # -- helpers -------------------------------------------------------------
    @property
    def row_max(self) -> float:
        if self.facts.rows_bounded and self.p.dmax is not None:
            return float(min(self.p.dmax, self.p.n - 1))
        return float(self.p.n - 1)

    def resolve(self, e: Expr) -> Expr:
        while isinstance(e, Name) and self.program.lookup(e.id) is not None:
            e = self.program.lookup(e.id)
        return e

    def is_private_set(self, e: Expr) -> bool:
        e = self.resolve(e)
        return isinstance(e, Name) and e.id == "P"

    def is_row_of(self, e: Expr, var: str) -> bool:
        e = self.resolve(e)
        return isinstance(e, Call) and e.func == "N" and isinstance(e.args[0], Name) and e.args[0].id == var

    def is_private_row(self, e: Expr, var: str) -> bool:
        """``P & N(var)`` (either order)."""
        e = self.resolve(e)
        return isinstance(e, BinOp) and e.op == "&" and (
            (self.is_private_set(e.left) and self.is_row_of(e.right, var))
            or (self.is_private_set(e.right) and self.is_row_of(e.left, var))
        )

    def local_in(self, e: Expr, var: str) -> bool:
        """Every use of ``P`` in ``e`` is ``P & N(var)``: then ``e`` changes only
        when the flipped vertex is in ``N(var)``."""
        if self.is_private_row(e, var):
            return True
        if isinstance(e, Name):
            if e.id == "P":
                return False
            sub = self.program.lookup(e.id)
            return True if sub is None else self.local_in(sub, var)
        if isinstance(e, Const):
            return True
        if isinstance(e, BinOp):
            return self.local_in(e.left, var) and self.local_in(e.right, var)
        if isinstance(e, Neg):
            return self.local_in(e.operand, var)
        if isinstance(e, Call):
            return all(self.local_in(a, var) for a in e.args)
        return self.local_in(e.body, var) and self.local_in(e.domain, var)

    def public_value(self, e: Expr, what: str) -> float:
        info = self.num(e, {})
        if info.private or not info.constant:
            raise SensitivityError(f"{what} must be a public constant expression (e.g. D or 3)")
        return info.lo

    def excludes_self(self, e: Expr) -> bool:
        """``self`` is never an element of the set ``e``."""
        e = self.resolve(e)
        if isinstance(e, Name):
            return e.id == "P" and self.facts.self_not_in_private
        if isinstance(e, Call):
            if e.func == "N":  # no self-loops in G'
                return isinstance(e.args[0], Name) and e.args[0].id == "self"
            return e.func == "project" and self.excludes_self(e.args[0])
        if isinstance(e, BinOp):
            if e.op == "&":
                return self.excludes_self(e.left) or self.excludes_self(e.right)
            if e.op == "|":
                return self.excludes_self(e.left) and self.excludes_self(e.right)
            return self.excludes_self(e.left)
        return False

    def row_without_self(self, e: BinOp, rows: dict[str, _Row]) -> float | None:
        """Bound of ``S & N(j)`` when ``self`` is in ``N(j)`` but not in ``S``."""
        for side, other in ((e.left, e.right), (e.right, e.left)):
            side = self.resolve(side)
            if isinstance(side, Call) and side.func == "N" and isinstance(side.args[0], Name):
                row = rows.get(side.args[0].id)
                if row is not None and row.has_self and self.excludes_self(other):
                    return max(0.0, row.bound - 1)
        return None

    # -- sets ----------------------------------------------------------------
    def set(self, e: Expr, rows: dict[str, _Row]) -> SetInfo:
        if isinstance(e, Name):
            if e.id == "P":
                return SetInfo(True, float(self.p.n - 1), 1.0, 1.0)
            sub = self.program.lookup(e.id)
            if sub is None:
                raise SensitivityError(f"{e.id!r} is not a set")
            return self.set(sub, rows)
        if isinstance(e, Call) and e.func == "N":
            arg = e.args[0]
            row = rows.get(arg.id) if isinstance(arg, Name) else None
            bound = row.bound if row is not None else self.row_max
            if self.facts.rows_bounded and self.p.dmax is not None:
                self.facts_used.add("rows_bounded")
            return SetInfo(False, bound, 0.0, 0.0)
        if isinstance(e, Call) and e.func == "project":
            s = self.set(e.args[0], rows)
            k = self.public_value(e.args[1], "the projection threshold")
            # the interpreter keeps int(k) elements (none if k < 0); min(|S|, k) is
            # 1-Lipschitz in |S|; the coupled projections differ by a replacement
            size = min(s.max_size, max(0.0, float(math.floor(k))))
            return SetInfo(s.private, size, min(2.0 * s.dsym, 2.0 * size), min(s.dsize, size))
        if isinstance(e, BinOp):
            a, b = self.set(e.left, rows), self.set(e.right, rows)
            dsym = a.dsym + b.dsym
            if e.op == "&":
                size = min(a.max_size, b.max_size)
                without_self = self.row_without_self(e, rows)
                if without_self is not None:
                    size = min(size, without_self)
            elif e.op == "|":
                size = min(a.max_size + b.max_size, float(self.p.n))
            else:
                size = a.max_size
            return SetInfo(a.private or b.private, size, dsym, min(dsym, size) if size < INF else dsym)
        raise SensitivityError(f"cannot analyse set expression {type(e).__name__}")

    # -- numbers -------------------------------------------------------------
    def num(self, e: Expr, rows: dict[str, _Row]) -> NumInfo:
        if isinstance(e, Const):
            v = e.value
            return NumInfo(False, 0.0, v, v, float(v).is_integer())
        if isinstance(e, Name):
            if e.id in ("D", "dmax", "n"):
                v = self.p.value(e.id)
                return NumInfo(False, 0.0, v, v, True)
            sub = self.program.lookup(e.id)
            if sub is None:
                raise SensitivityError(f"{e.id!r} is not a number")
            return self.num(sub, rows)
        if isinstance(e, Neg):
            a = self.num(e.operand, rows)
            return NumInfo(a.private, a.delta, -a.hi, -a.lo, a.integer)
        if isinstance(e, BinOp):
            return self.binop(e, rows)
        if isinstance(e, Sum):
            return self.sum(e, rows)
        if isinstance(e, Call):
            return self.call(e, rows)
        raise SensitivityError(f"cannot analyse {type(e).__name__}")

    def binop(self, e: BinOp, rows: dict[str, _Row]) -> NumInfo:
        a, b = self.num(e.left, rows), self.num(e.right, rows)
        priv = a.private or b.private
        if e.op in ("+", "-"):
            lo, hi = (a.lo + b.lo, a.hi + b.hi) if e.op == "+" else (a.lo - b.hi, a.hi - b.lo)
            return NumInfo(priv, a.delta + b.delta, lo, hi, a.integer and b.integer)
        if e.op == "*":
            corners = [x * y for x in (a.lo, a.hi) for y in (b.lo, b.hi)]
            delta = a.delta * b.magnitude + b.delta * a.magnitude + a.delta * b.delta
            if a.constant:
                delta = abs(a.lo) * b.delta
            elif b.constant:
                delta = abs(b.lo) * a.delta
            return NumInfo(priv, delta, min(corners), max(corners), a.integer and b.integer)
        # division
        if b.private or b.delta > 0:
            raise SensitivityError(
                "division by a private quantity has no finite sensitivity; release the numerator "
                "and the denominator as separate programs and divide during aggregation",
            )
        if b.lo <= 0 <= b.hi:
            raise SensitivityError("the divisor may be 0")
        m = min(abs(b.lo), abs(b.hi))
        corners = [x / y for x in (a.lo, a.hi) for y in (b.lo, b.hi)]
        return NumInfo(priv, a.delta / m, min(corners), max(corners), False)

    def call(self, e: Call, rows: dict[str, _Row]) -> NumInfo:
        f = e.func
        if f == "size":
            s = self.set(e.args[0], rows)
            return NumInfo(s.private, s.dsize, 0.0, s.max_size, True)
        if f in ("comb", "pow"):
            x = self.num(e.args[0], rows)
            k = int(e.args[1].value)  # checked by the parser
            if not x.integer:
                raise SensitivityError(f"{f} needs an integer argument (e.g. size(...))")
            if x.lo < 0:
                raise SensitivityError(f"{f} needs a nonnegative argument")
            if not math.isfinite(x.hi):
                raise SensitivityError(f"{f}: the argument has no upper bound")

            def g(t: float) -> float:
                t = max(0, int(t))
                return float(math.comb(t, k)) if f == "comb" else float(t) ** k

            hi = int(x.hi)
            step = math.ceil(x.delta - 1e-12)
            delta = g(hi) - g(max(int(x.lo), hi - step)) if step > 0 else 0.0
            if x.private and x.hi >= self.p.n - 1 and k >= 2:
                self.warnings.append(
                    f"{f}(..., {k}) of a count bounded only by n-1 = {self.p.n - 1}: the bound is loose; "
                    "apply project(P, D) first",
                )
            self.trace.append(f"{f}(x, {k}) with x in [{x.lo:g}, {x.hi:g}], |dx| <= {x.delta:g}: delta = {delta:g}")
            return NumInfo(x.private, delta, g(x.lo), g(x.hi), True)
        if f == "clip":
            x = self.num(e.args[0], rows)
            lo = self.public_value(e.args[1], "clip's lower bound")
            hi = self.public_value(e.args[2], "clip's upper bound")
            if hi < lo:
                raise SensitivityError("clip: upper bound below lower bound")
            return NumInfo(x.private, min(x.delta, hi - lo), lo, hi, x.integer and lo.is_integer() and hi.is_integer())
        if f in ("min", "max"):
            a, b = self.num(e.args[0], rows), self.num(e.args[1], rows)
            fn = min if f == "min" else max
            return NumInfo(a.private or b.private, max(a.delta, b.delta), fn(a.lo, b.lo), fn(a.hi, b.hi), a.integer and b.integer)
        raise SensitivityError(f"{f}(...) is not a number")

    def sum(self, e: Sum, rows: dict[str, _Row]) -> NumInfo:
        dom = self.set(e.domain, rows)
        body = self.num(e.body, {**rows, e.var: _Row(self.row_max)})
        lo = min(0.0, body.lo * dom.max_size)
        hi = max(0.0, body.hi * dom.max_size)
        if not body.private:
            delta = dom.dsym * body.magnitude
            self.trace.append(
                f"sum over {e.var}: public summand |.| <= {body.magnitude:g}, {dom.dsym:g} membership change(s): delta = {delta:g}",
            )
            return NumInfo(dom.private, delta, lo, hi, body.integer)

        local = self.facts.symmetric_rows and self.local_in(e.body, e.var)
        # number of summands whose value can change: those j with v in N(j), i.e. j in N(v)
        changing = min(dom.max_size, self.row_max) if local else dom.max_size
        if local:
            self.facts_used.add("symmetric_rows")
        if self.facts.symmetric_rows and self.is_private_row(e.domain, "self"):
            # the summation range P & N(self) changes only if v in N(self); then self in N(v)
            self.facts_used.add("symmetric_rows")
            if self.facts.self_not_in_private:
                self.facts_used.add("self_not_in_private")
                # the new summand j = v: self is in N(v) (only sets without self lose one vertex)
                body_v = self.num(e.body, {**rows, e.var: _Row(self.row_max, has_self=True)})
                inner = max(0.0, changing - 1) if local else changing
            else:
                body_v, inner = body, changing
            case_in = body_v.magnitude + inner * body.delta
            case_out = changing * body.delta
            delta = max(case_in, case_out)
            self.trace.append(
                f"sum over {e.var} in P & N(self): v in N(self): {body_v.magnitude:g} + {inner:g}*{body.delta:g} = {case_in:g}; "
                f"v not in N(self): {changing:g}*{body.delta:g} = {case_out:g}",
            )
        else:
            delta = dom.dsym * body.magnitude + changing * body.delta
            self.trace.append(
                f"sum over {e.var}: {dom.dsym:g} membership change(s) * {body.magnitude:g} + "
                f"{changing:g} changing summand(s) * {body.delta:g} = {delta:g}",
            )
        return NumInfo(True, delta, lo, hi, body.integer)


def derive(program: Program, params: PublicParams, facts: Facts | None = None) -> Derivation:
    """Derive ``GS`` of the local program; raises :class:`SensitivityError`."""
    facts = facts or Facts()
    d = _Deriver(program, params, facts)
    info = d.num(program.ret, {})
    if not math.isfinite(info.delta):
        raise SensitivityError("no finite sensitivity bound could be derived")
    if not info.private:
        d.warnings.append("the program does not read private data")
    d.trace.append(f"GS = {info.delta:g}")
    return Derivation(info.delta, params, facts, d.trace, d.warnings, d.facts_used)


def certify(program: Program, params: PublicParams, facts: Facts | None = None) -> Certificate:
    der = derive(program, params, facts)
    return Certificate(program.digest, params, der.facts, der.gs, tuple(der.trace), tuple(der.warnings))


def verify_certificate(cert: Certificate, program: Program, params: PublicParams) -> tuple[bool, str]:
    """Node-side check of a curator's certificate: same program, same public
    parameters, and a claimed GS no smaller than the node's own derivation."""
    if cert.program_digest != program.digest:
        return False, "certificate is for a different program"
    if cert.params != params:
        return False, f"certificate parameters {asdict(cert.params)} differ from the public values {asdict(params)}"
    try:
        own = derive(program, params, cert.facts)
    except SensitivityError as exc:
        return False, f"program rejected: {exc}"
    if cert.gs + 1e-9 < own.gs:
        return False, f"claimed GS {cert.gs:g} is below the derived GS {own.gs:g}"
    return True, f"GS = {own.gs:g}"
