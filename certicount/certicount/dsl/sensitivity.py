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

``A(j, k)`` (the NAM-DPRD unbiased matrix, :mod:`certicount.dsl.matrix`) is a
public number in ``[-1/(e^ε1 - 1), e^ε1/(e^ε1 - 1)]`` with ``A(j, j) = 0``. Two
sound refinements of ``sum`` make its bound tight:

* zero diagonal -- in ``sum(A(j, k) for k in S)`` with ``j`` itself ranging over
  ``S``, the term ``k = j`` is 0, so at most ``|S| - 1`` terms count;
* replacement coupling -- when the domain changes by one vertex in and one
  out (``dsym = 2``, ``dsize <= 1``, e.g. ``project(P, D)``), the entering and
  the leaving summand differ by at most ``hi - lo`` instead of ``2 * |.|``;
  if moreover the summand reads private data only through the domain set
  itself, it changes only when the domain does, and at most ``|S| - 1``
  summands are common to both sides.

The certificate is only as strong as the rules below; the falsifier
(:mod:`certicount.dsl.falsifier`) searches small graphs for counterexamples, and
the derived values are checked against the hand derivations of the library
tasks (``1``, ``C(D-1, 2)``, ``dmax - 1``) in ``tests/test_dsl.py``.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

from .lang import BinOp, Call, Const, Expr, Name, Neg, Program, Sum
from .matrix import rr_constants

INF = math.inf


class SensitivityError(ValueError):
    """The program has no finite sensitivity bound; ``str()`` is the feedback."""


class _NotUnivariate(Exception):
    """The expression is not a public function of one private count."""


def _names_in(e: Expr) -> set[str]:
    if isinstance(e, Name):
        return {e.id}
    if isinstance(e, BinOp):
        return _names_in(e.left) | _names_in(e.right)
    if isinstance(e, Neg):
        return _names_in(e.operand)
    if isinstance(e, Call):
        return set().union(*(_names_in(a) for a in e.args)) if e.args else set()
    if isinstance(e, Sum):
        return _names_in(e.body) | _names_in(e.domain)
    return set()


@dataclass(frozen=True)
class PublicParams:
    """Public values the node knows before it executes the program.

    ``D`` / ``dmax`` are ``None`` when no degree bound was published (no GS
    optimisation): the noisy rows are then only bounded by ``n - 1``.
    ``eps1`` is the RR budget of the unbiased matrix ``A`` (its value range).
    """

    n: int
    D: int | None = None
    dmax: int | None = None
    eps1: float | None = None

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
        # loop variable -> canonical domain it ranges over (while its summand is analysed)
        self.members: dict[str, Expr] = {}

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

    def canon(self, e: Expr) -> Expr:
        """``e`` with every assigned name replaced by its definition (structural key)."""
        if isinstance(e, Name):
            sub = self.program.lookup(e.id)
            return e if sub is None else self.canon(sub)
        if isinstance(e, BinOp):
            return BinOp(e.op, self.canon(e.left), self.canon(e.right))
        if isinstance(e, Neg):
            return Neg(self.canon(e.operand))
        if isinstance(e, Call):
            return Call(e.func, tuple(self.canon(a) for a in e.args))
        if isinstance(e, Sum):
            return Sum(self.canon(e.body), e.var, self.canon(e.domain))
        return e

    def only_via(self, e: Expr, target: Expr) -> bool:
        """Every read of ``P`` in ``e`` is inside the set ``target`` (canonical form):
        then ``e`` can change only when ``target`` does."""
        if self.canon(e) == target:
            return True
        if isinstance(e, Name):
            if e.id == "P":
                return False
            sub = self.program.lookup(e.id)
            return True if sub is None else self.only_via(sub, target)
        if isinstance(e, Const):
            return True
        if isinstance(e, BinOp):
            return self.only_via(e.left, target) and self.only_via(e.right, target)
        if isinstance(e, Neg):
            return self.only_via(e.operand, target)
        if isinstance(e, Call):
            return all(self.only_via(a, target) for a in e.args)
        return self.only_via(e.body, target) and self.only_via(e.domain, target)

    def zero_diagonal_pair(self, body: Expr, var: str, domain: Expr) -> bool:
        """``body`` is ``A(j, var)`` / ``A(var, j)`` with ``j`` ranging over the same
        ``domain`` as ``var``: the term ``var = j`` is ``A(j, j) = 0``."""
        b = self.canon(body)
        if not (isinstance(b, Call) and b.func == "A" and all(isinstance(a, Name) for a in b.args)):
            return False
        ids = [a.id for a in b.args]
        if var not in ids:
            return False
        others = [x for x in ids if x != var]
        return len(others) == 1 and self.members.get(others[0]) == domain

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
                own = self.row_of_member(e, a, b)
                if own is not None:
                    size = min(size, own)
            elif e.op == "|":
                size = min(a.max_size + b.max_size, float(self.p.n))
            else:
                size = a.max_size
            dsize = min(dsym, size) if size < INF else dsym
            fixed = self.fixed_side_dsize(a, b)
            if fixed is not None:
                dsize = min(dsize, fixed)
            return SetInfo(a.private or b.private, size, dsym, dsize)
        raise SensitivityError(f"cannot analyse set expression {type(e).__name__}")

    @staticmethod
    def fixed_side_dsize(a: SetInfo, b: SetInfo) -> float | None:
        """Size change of ``A op B`` (``&``, ``|``, ``-``) when one side does not change.

        If ``B`` is fixed and ``A`` gains ``x`` and loses ``y`` elements (``x + y <= dsym(A)``,
        ``|x - y| <= dsize(A)``), the size of ``A op B`` changes by at most
        ``max(x, y) <= (dsym(A) + dsize(A)) / 2``. E.g. a projection that swaps one vertex
        (``dsym = 2``, ``dsize = 1``) changes ``|project(P, D) & N(j)|`` by at most 1, not 2."""
        if a.dsym == 0:
            a, b = b, a
        if b.dsym != 0 or not (math.isfinite(a.dsym) and math.isfinite(a.dsize)):
            return None
        return float(math.floor((a.dsym + a.dsize) / 2 + 1e-9))

    def holds_member(self, e: Expr, var: str) -> bool:
        """The loop variable ``var`` is an element of the set ``e`` (in the summand of its sum):
        ``e`` is ``var``'s domain, or built from it with ``&`` / ``|`` / ``- N(var)`` (no self-loops)."""
        if var not in self.members:
            return False
        if self.canon(e) == self.members[var]:
            return True
        e = self.resolve(e)
        if isinstance(e, BinOp):
            if e.op == "&":
                return self.holds_member(e.left, var) and self.holds_member(e.right, var)
            if e.op == "|":
                return self.holds_member(e.left, var) or self.holds_member(e.right, var)
            return self.holds_member(e.left, var) and self.is_row_of(e.right, var)
        return False

    def row_of_member(self, e: BinOp, a: SetInfo, b: SetInfo) -> float | None:
        """Bound of ``S & N(j)`` when the loop variable ``j`` ranges over ``S`` itself: ``j``
        is in ``S`` but not in ``N(j)`` (``G'`` has no self-loops), so at most ``|S| - 1``."""
        for side, other, info in ((e.left, e.right, b), (e.right, e.left, a)):
            side = self.resolve(side)
            if isinstance(side, Call) and side.func == "N" and isinstance(side.args[0], Name):
                var = side.args[0].id
                if var in self.members and self.members[var] == self.canon(other):
                    self.trace.append(f"{var} ranges over S and N({var}) has no self-loop: |S & N({var})| <= |S| - 1")
                    return max(0.0, info.max_size - 1)
        return None

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
            return self.univariate(e, rows, self.binop(e, rows))
        if isinstance(e, Sum):
            return self.sum(e, rows)
        if isinstance(e, Call):
            info = self.call(e, rows)
            return self.univariate(e, rows, info) if e.func in ("comb", "pow", "clip", "min", "max") else info
        raise SensitivityError(f"cannot analyse {type(e).__name__}")

    # -- one private count ------------------------------------------------------
    UNIVARIATE_MAX_RANGE = 20000
    UNIVARIATE_MAX_STEP = 64

    def univariate(self, e: Expr, rows: dict[str, _Row], info: NumInfo) -> NumInfo:
        """Exact bound for an expression that reads private data only through one count.

        If every read of ``P`` in ``e`` is inside one subexpression ``X = size(S)`` (an
        integer in ``[lo, hi]`` that changes by at most ``dx``), then ``e = g(X)`` for a
        public function ``g`` and ``|e(P) - e(P')| <= max |g(x) - g(y)|`` over integers
        ``x, y`` in ``[lo, hi]`` with ``|x - y| <= dx``, which is evaluated exactly. This
        makes equivalent forms agree: ``d * (d - 1) * (d - 2) / 6`` gets the bound of
        ``comb(d, 3)`` and ``s * s`` the bound of ``pow(s, 2)``; the interval rules for
        products bound each factor separately and are looser."""
        if not info.private or info.delta == 0:
            return info
        target = self._private_count(e)
        if target is None or not self.only_via(e, target):
            return info
        x = self.num(target, rows)
        if not (x.integer and math.isfinite(x.lo) and math.isfinite(x.hi)):
            return info
        lo, hi, step = math.ceil(x.lo - 1e-9), math.floor(x.hi + 1e-9), math.ceil(x.delta - 1e-9)
        if hi < lo or hi - lo > self.UNIVARIATE_MAX_RANGE or step > self.UNIVARIATE_MAX_STEP:
            return info
        try:
            values = [self._eval_at(e, target, float(t)) for t in range(lo, hi + 1)]
        except (_NotUnivariate, ArithmeticError, ValueError, OverflowError):
            return info
        if not all(math.isfinite(v) for v in values):
            return info
        delta = 0.0
        for i, v in enumerate(values):
            for w in values[i + 1: i + 1 + step]:
                delta = max(delta, abs(v - w))
        if delta < info.delta:
            self.trace.append(f"{type(e).__name__} reads P only through one count in [{lo}, {hi}] with change <= "
                              f"{step}: exact delta = {delta:g} (interval rules: {info.delta:g})")
            return NumInfo(True, delta, max(info.lo, min(values)), min(info.hi, max(values)), info.integer)
        return info

    def _private_count(self, e: Expr) -> Expr | None:
        """The canonical form of the first ``size(...)`` in ``e`` that reads ``P``."""
        c = self.canon(e)
        stack = [c]
        while stack:
            cur = stack.pop()
            if isinstance(cur, Call) and cur.func == "size" and "P" in _names_in(cur):
                return cur
            if isinstance(cur, BinOp):
                stack += [cur.right, cur.left]
            elif isinstance(cur, Neg):
                stack.append(cur.operand)
            elif isinstance(cur, Call):
                stack += list(reversed(cur.args))
        return None

    def _eval_at(self, e: Expr, target: Expr, x: float) -> float:
        """``g(x)``: ``e`` with the count ``target`` set to ``x`` (the interpreter's semantics)."""
        if self.canon(e) == target:
            return x
        if isinstance(e, Const):
            return float(e.value)
        if isinstance(e, Name):
            if e.id in ("D", "dmax", "n"):
                return self.p.value(e.id)
            sub = self.program.lookup(e.id)
            if sub is None:
                raise _NotUnivariate(e.id)
            return self._eval_at(sub, target, x)
        if isinstance(e, Neg):
            return -self._eval_at(e.operand, target, x)
        if isinstance(e, BinOp) and e.op in ("+", "-", "*", "/"):
            a, b = self._eval_at(e.left, target, x), self._eval_at(e.right, target, x)
            return a + b if e.op == "+" else a - b if e.op == "-" else a * b if e.op == "*" else a / b
        if isinstance(e, Call) and e.func in ("comb", "pow", "clip", "min", "max"):
            args = [self._eval_at(a, target, x) for a in e.args]
            if e.func == "comb":
                return float(math.comb(max(0, int(args[0])), int(args[1])))
            if e.func == "pow":
                return float(args[0]) ** int(args[1])
            if e.func == "clip":
                return min(max(args[0], args[1]), args[2])
            return min(args) if e.func == "min" else max(args)
        raise _NotUnivariate(type(e).__name__)

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
        if f == "A":
            if self.p.eps1 is None:
                raise SensitivityError("the program reads A(...) but no unbiased matrix (eps1) was published")
            low, high = rr_constants(self.p.eps1)
            return NumInfo(False, 0.0, low, high, False)
        if f == "size":
            s = self.set(e.args[0], rows)
            lo = 1.0 if s.max_size >= 1 and any(self.holds_member(e.args[0], v) for v in self.members) else 0.0
            return NumInfo(s.private, s.dsize, lo, s.max_size, True)
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
        key = self.canon(e.domain)
        outer = self.members.get(e.var)
        self.members[e.var] = key
        try:
            body = self.num(e.body, {**rows, e.var: _Row(self.row_max)})
            return self._sum(e, rows, dom, key, body)
        finally:
            if outer is None:
                self.members.pop(e.var, None)
            else:
                self.members[e.var] = outer

    def _sum(self, e: Sum, rows: dict[str, _Row], dom: SetInfo, key: Expr, body: NumInfo) -> NumInfo:
        # terms that can be non-zero: the diagonal A(j, j) of a pair over one set is 0
        terms = dom.max_size
        if self.zero_diagonal_pair(e.body, e.var, key):
            terms = max(0.0, dom.max_size - 1)
            self.trace.append(f"sum over {e.var}: the term {e.var} = its outer variable is A(j, j) = 0")
        lo = min(0.0, body.lo * terms)
        hi = max(0.0, body.hi * terms)
        # one vertex in and one out (e.g. project(P, D)): entering and leaving summand differ by <= hi - lo
        replacement = dom.dsym == 2 and dom.dsize <= 1
        swap = max(body.magnitude, body.hi - body.lo) if replacement else dom.dsym * body.magnitude
        if not body.private:
            delta = swap
            self.trace.append(
                f"sum over {e.var}: public summand in [{body.lo:g}, {body.hi:g}], {dom.dsym:g} membership "
                f"change(s){' (one in, one out)' if replacement else ''}: delta = {delta:g}",
            )
            return NumInfo(dom.private, delta, lo, hi, body.integer)

        if dom.private and self.only_via(e.body, key):
            # the summand reads P only through the domain set: it changes only when the domain changes,
            # and then at most |S| - 1 summands are on both sides
            common = max(0.0, dom.max_size - 1)
            delta = swap + common * body.delta
            self.trace.append(
                f"sum over {e.var}: summand private only through its domain: {swap:g} + "
                f"{common:g} common summand(s) * {body.delta:g} = {delta:g}",
            )
            return NumInfo(True, delta, lo, hi, body.integer)

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


def verify_certificate(cert: Certificate, program: Program, params: PublicParams,
                       facts: Facts | None = None) -> tuple[bool, str]:
    """Node-side check of a curator's certificate: same program, same public
    parameters, a claimed GS that is a finite nonnegative number no smaller than
    the node's own derivation. ``facts``: what the node's own environment guarantees
    (default :class:`Facts`, all true); the node derives with these, never with the
    facts the certificate claims, and rejects a certificate that claims more."""
    trusted = facts or Facts()
    if cert.program_digest != program.digest:
        return False, "certificate is for a different program"
    if cert.params != params:
        return False, f"certificate parameters {asdict(cert.params)} differ from the public values {asdict(params)}"
    gs = cert.gs
    if isinstance(gs, bool) or not isinstance(gs, (int, float)) or not math.isfinite(gs) or gs < 0:
        return False, f"claimed GS {gs!r} is not a finite nonnegative number"
    claimed = cert.facts.to_dict() if isinstance(cert.facts, Facts) else None
    if claimed is None:
        return False, "certificate facts are malformed"
    extra = sorted(k for k, v in claimed.items() if v and not getattr(trusted, k))
    if extra:
        return False, f"certificate claims facts this environment does not guarantee: {', '.join(extra)}"
    try:
        own = derive(program, params, trusted)
    except SensitivityError as exc:
        return False, f"program rejected: {exc}"
    if gs + 1e-9 < own.gs:
        return False, f"claimed GS {gs:g} is below the derived GS {own.gs:g}"
    return True, f"GS = {own.gs:g}"
