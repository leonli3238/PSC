"""A restricted DSL for node-local counting programs (research content 4, Improvement 2).

The curator LLM writes the local computation of a counting task as a program in
this language; :mod:`certicount.dsl.sensitivity` derives its global sensitivity,
and every node executes it with a deterministic interpreter on its own data,
so the reported count never comes from an LLM.

Syntax (a subset of Python, parsed with :mod:`ast`, never executed by Python)::

    S = P & N(self)
    return 0.5 * sum(size(P & N(j)) for j in S)

Names
    ``P``      the node's private (real) neighbour set; never contains ``self``
    ``self``   the node id
    ``D``      public projection threshold, ``dmax`` public maximum degree of the
               projected noisy graph, ``n`` number of nodes
    assigned variables and loop variables
Functions
    ``N(x)``             public neighbour row of ``x`` in the projected noisy graph ``G'``
    ``size(S)``          ``|S|``
    ``project(S, k)``    at most ``k`` elements of ``S`` (degree projection)
    ``comb(x, k)``, ``pow(x, k)``   binomial coefficient / power with a constant ``k``
    ``clip(x, lo, hi)``  clamp to public bounds (runtime fallback for loose bounds)
    ``min(a, b)``, ``max(a, b)``
    ``sum(e for j in S)``
Operators
    sets: ``&`` (intersection), ``|`` (union), ``-`` (difference)
    numbers: ``+ - *`` and ``/`` (the divisor must be public)

The aggregation step is a separate expression over ``total`` (the sum of the noisy
reports) and ``n``; it is post-processing and has no sensitivity requirement.
"""

from __future__ import annotations

import ast
import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import Callable, Mapping

SET, NUM, NODE = "set", "num", "node"
PUBLIC_NUMS = ("D", "dmax", "n")
FUNCTIONS = ("N", "size", "project", "comb", "pow", "clip", "min", "max", "sum")


class DSLError(ValueError):
    """The program is not in the language; the message is shown to the designer."""


# ---------------------------------------------------------------------------
# AST
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Name:
    id: str


@dataclass(frozen=True)
class Const:
    value: float


@dataclass(frozen=True)
class BinOp:
    op: str  # + - * / & |  ("-" on sets is the difference)
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class Neg:
    operand: "Expr"


@dataclass(frozen=True)
class Call:
    func: str
    args: tuple


@dataclass(frozen=True)
class Sum:
    body: "Expr"
    var: str
    domain: "Expr"


Expr = Name | Const | BinOp | Neg | Call | Sum


@dataclass(frozen=True)
class Program:
    """A parsed local program plus its aggregation expression."""

    source: str
    assigns: tuple[tuple[str, Expr], ...]
    ret: Expr
    aggregate_source: str = "total"
    aggregate: Expr = Name("total")
    clamp_nonnegative: bool = True
    types: Mapping[str, str] = field(default_factory=dict, compare=False, repr=False)
    # Optional budget fractions (r1, r2) of split_budget chosen by the designer; None -> framework default
    budget: tuple[float, float] | None = None

    @property
    def digest(self) -> str:
        text = f"{self.source.strip()}\n--aggregate--\n{self.aggregate_source.strip()}\n{self.clamp_nonnegative}"
        if self.budget is not None:
            text += f"\n--budget--\n{self.budget[0]:g},{self.budget[1]:g}"
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def lookup(self, name: str) -> Expr | None:
        for k, v in self.assigns:
            if k == name:
                return v
        return None

    def names_used(self) -> set[str]:
        out: set[str] = set()
        for _, e in self.assigns:
            out |= _names(e)
        return out | _names(self.ret)

    @property
    def uses_rows(self) -> bool:
        """Reads the public noisy graph (needs ``eps1`` and the RR graph)."""
        return any(_calls(e, "N") for _, e in self.assigns) or _calls(self.ret, "N")

    @property
    def uses_threshold(self) -> bool:
        """Reads ``D`` / ``dmax`` explicitly."""
        return bool(self.names_used() & {"D", "dmax"})

    @property
    def needs_degree_bound(self) -> bool:
        """Needs ``eps2`` and the GS optimisation: it reads the threshold, or the
        noisy rows, whose projection to ``dmax`` bounds the sensitivity."""
        return self.uses_threshold or self.uses_rows

    def text(self) -> str:
        out = f"{self.source.strip()}\naggregate: {self.aggregate_source.strip()}"
        if self.budget is not None:
            out += f"\nbudget: r1={self.budget[0]:g}, r2={self.budget[1]:g}"
        return out

    def budget_fractions(self, r1: float, r2: float) -> tuple[float, float]:
        """``(r1, r2)`` of the budget split: the program's own choice, else the defaults."""
        return self.budget if self.budget is not None else (r1, r2)


def _names(e: Expr) -> set[str]:
    if isinstance(e, Name):
        return {e.id}
    if isinstance(e, Const):
        return set()
    if isinstance(e, BinOp):
        return _names(e.left) | _names(e.right)
    if isinstance(e, Neg):
        return _names(e.operand)
    if isinstance(e, Call):
        return set().union(*(_names(a) for a in e.args)) if e.args else set()
    return _names(e.body) | _names(e.domain)


def _calls(e: Expr, func: str) -> bool:
    if isinstance(e, Call):
        return e.func == func or any(_calls(a, func) for a in e.args)
    if isinstance(e, BinOp):
        return _calls(e.left, func) or _calls(e.right, func)
    if isinstance(e, Neg):
        return _calls(e.operand, func)
    if isinstance(e, Sum):
        return _calls(e.body, func) or _calls(e.domain, func)
    return False


# ---------------------------------------------------------------------------
# Parser and type checker
# ---------------------------------------------------------------------------

_BINOPS = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.BitAnd: "&", ast.BitOr: "|"}
_ARITY = {"N": 1, "size": 1, "project": 2, "comb": 2, "pow": 2, "clip": 3, "min": 2, "max": 2}


class _Checker:
    def __init__(self, scope: dict[str, str]) -> None:
        self.scope = dict(scope)

    def expr(self, node: ast.AST) -> tuple[Expr, str]:
        where = f" (line {getattr(node, 'lineno', '?')})"
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return Const(float(node.value)), NUM
        if isinstance(node, ast.Name):
            if node.id not in self.scope:
                raise DSLError(f"unknown name {node.id!r}{where}")
            return Name(node.id), self.scope[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            e, t = self.expr(node.operand)
            if t != NUM:
                raise DSLError(f"unary minus needs a number{where}")
            return Neg(e), NUM
        if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
            op = _BINOPS[type(node.op)]
            left, lt = self.expr(node.left)
            right, rt = self.expr(node.right)
            if lt == rt == SET and op in ("&", "|", "-"):
                return BinOp(op, left, right), SET
            if lt == rt == NUM and op in ("+", "-", "*", "/"):
                return BinOp(op, left, right), NUM
            raise DSLError(f"operator {op!r} is not defined for {lt} {op} {rt}{where}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
                raise DSLError(f"unknown function{where}; allowed: {', '.join(FUNCTIONS)}")
            if node.keywords:
                raise DSLError(f"keyword arguments are not allowed{where}")
            f = node.func.id
            if f == "sum":
                return self._sum(node, where)
            if len(node.args) != _ARITY[f]:
                raise DSLError(f"{f} takes {_ARITY[f]} argument(s){where}")
            parsed = [self.expr(a) for a in node.args]
            args = tuple(e for e, _ in parsed)
            types = [t for _, t in parsed]
            want = {
                "N": [NODE], "size": [SET], "project": [SET, NUM], "comb": [NUM, NUM], "pow": [NUM, NUM],
                "clip": [NUM, NUM, NUM], "min": [NUM, NUM], "max": [NUM, NUM],
            }[f]
            if types != want:
                raise DSLError(f"{f} expects ({', '.join(want)}), got ({', '.join(types)}){where}")
            if f in ("comb", "pow") and not (isinstance(args[1], Const) and args[1].value.is_integer() and args[1].value >= 0):
                raise DSLError(f"the second argument of {f} must be a nonnegative integer constant{where}")
            return Call(f, args), {"N": SET, "project": SET}.get(f, NUM)
        raise DSLError(f"unsupported syntax {type(node).__name__}{where}")

    def _sum(self, node: ast.Call, where: str) -> tuple[Expr, str]:
        if len(node.args) != 1 or not isinstance(node.args[0], ast.GeneratorExp):
            raise DSLError(f"sum takes one generator: sum(<expr> for <var> in <set>){where}")
        gen = node.args[0]
        if len(gen.generators) != 1:
            raise DSLError(f"sum supports a single 'for' clause{where}")
        comp = gen.generators[0]
        if comp.ifs or comp.is_async or not isinstance(comp.target, ast.Name):
            raise DSLError(f"sum supports 'for <name> in <set>' without conditions{where}")
        var = comp.target.id
        if var in self.scope:
            raise DSLError(f"loop variable {var!r} shadows an existing name{where}")
        domain, dt = self.expr(comp.iter)
        if dt != SET:
            raise DSLError(f"sum must iterate over a set{where}")
        inner = _Checker({**self.scope, var: NODE})
        body, bt = inner.expr(gen.elt)
        if bt != NUM:
            raise DSLError(f"the summand must be a number{where}")
        return Sum(body, var, domain), NUM


def _strip_fence(source: str) -> str:
    lines = [ln for ln in source.strip().splitlines() if not ln.strip().startswith("```")]
    return "\n".join(lines)


def parse_budget(text: str | None) -> tuple[float, float] | None:
    """``"r1=0.3, r2=0.2"`` -> ``(0.3, 0.2)``; ``None`` / empty -> ``None``.

    ``r1``: share of ε for the RR noisy graph (if the program reads ``N``);
    ``r2``: share of the rest for the noisy degree bound (if it needs one).
    """
    if text is None or not text.strip():
        return None
    vals: dict[str, float] = {}
    for part in re.split(r"[,;\s]+", text.strip().strip("`")):
        if not part:
            continue
        m = re.fullmatch(r"(r1|r2)\s*=\s*([0-9]*\.?[0-9]+)", part)
        if not m:
            raise DSLError(f"budget: expected 'r1=<x>, r2=<y>', got {text.strip()!r}")
        vals[m.group(1)] = float(m.group(2))
    if set(vals) != {"r1", "r2"}:
        raise DSLError("budget: give both r1 and r2, e.g. 'budget: r1=0.5, r2=0.2'")
    for k, v in vals.items():
        if not 0.05 <= v <= 0.95:
            raise DSLError(f"budget: {k} must be in [0.05, 0.95], got {v:g}")
    return vals["r1"], vals["r2"]


def parse_program(source: str, aggregate: str = "total", clamp_nonnegative: bool = True,
                  budget: tuple[float, float] | str | None = None) -> Program:
    """Parse and type-check a local program, its aggregation expression and
    (optionally) its budget fractions."""
    if isinstance(budget, str) or budget is None:
        budget = parse_budget(budget)
    else:
        budget = parse_budget(f"r1={budget[0]}, r2={budget[1]}")
    source = _strip_fence(source)
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise DSLError(f"syntax error: {exc.msg} (line {exc.lineno})") from None
    checker = _Checker({"P": SET, "self": NODE, "D": NUM, "dmax": NUM, "n": NUM})
    assigns: list[tuple[str, Expr]] = []
    ret: Expr | None = None
    for i, stmt in enumerate(tree.body):
        last = i == len(tree.body) - 1
        if isinstance(stmt, ast.Assign) and not last:
            if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
                raise DSLError(f"line {stmt.lineno}: assign to a single name")
            name = stmt.targets[0].id
            if name in checker.scope:
                raise DSLError(f"line {stmt.lineno}: {name!r} is already defined")
            e, t = checker.expr(stmt.value)
            checker.scope[name] = t
            assigns.append((name, e))
        elif isinstance(stmt, ast.Return) and last and stmt.value is not None:
            e, t = checker.expr(stmt.value)
            if t != NUM:
                raise DSLError("the program must return a number")
            ret = e
        else:
            raise DSLError(f"line {stmt.lineno}: only 'name = <expr>' lines followed by one final 'return <expr>'")
    if ret is None:
        raise DSLError("the program must end with 'return <expr>'")
    agg = _parse_aggregate(aggregate)
    return Program(source, tuple(assigns), ret, aggregate.strip(), agg, clamp_nonnegative, dict(checker.scope), budget)


def _parse_aggregate(text: str) -> Expr:
    try:
        tree = ast.parse(text.strip(), mode="eval")
    except SyntaxError as exc:
        raise DSLError(f"aggregate: syntax error: {exc.msg}") from None
    e, t = _Checker({"total": NUM, "n": NUM}).expr(tree.body)
    if t != NUM or _calls(e, "N") or _calls(e, "sum"):
        raise DSLError("aggregate must be an arithmetic expression over total and n")
    return e


# ---------------------------------------------------------------------------
# Interpreter (compiled to closures for speed)
# ---------------------------------------------------------------------------

Projector = Callable[[frozenset, int], frozenset]


def smallest_projector(s: frozenset, k: int) -> frozenset:
    """Deterministic projection: keep the ``k`` smallest ids."""
    return s if len(s) <= k else frozenset(sorted(s)[: max(0, int(k))])


@dataclass
class Env:
    """Inputs of one node: private ``P`` and public rows / parameters."""

    private: frozenset
    node: int
    rows: Mapping[int, frozenset] | Callable[[int], frozenset]
    n: int
    D: int = 0
    dmax: int = 0
    projector: Projector = smallest_projector

    def row(self, j: int) -> frozenset:
        if callable(self.rows):
            return frozenset(self.rows(j))
        return frozenset(self.rows.get(j, ()))


def _compile(e: Expr) -> Callable[[dict, Env], object]:
    if isinstance(e, Const):
        v = e.value
        return lambda s, env: v
    if isinstance(e, Name):
        k = e.id
        if k == "P":
            return lambda s, env: env.private
        if k == "self":
            return lambda s, env: env.node
        if k in PUBLIC_NUMS:
            return lambda s, env: float(getattr(env, k))
        return lambda s, env: s[k]
    if isinstance(e, Neg):
        f = _compile(e.operand)
        return lambda s, env: -f(s, env)
    if isinstance(e, BinOp):
        a, b = _compile(e.left), _compile(e.right)
        op = e.op
        if op == "+":
            return lambda s, env: a(s, env) + b(s, env)
        if op == "-":
            return lambda s, env: a(s, env) - b(s, env)
        if op == "*":
            return lambda s, env: a(s, env) * b(s, env)
        if op == "/":
            return lambda s, env: a(s, env) / b(s, env)
        if op == "&":
            return lambda s, env: a(s, env) & b(s, env)
        return lambda s, env: a(s, env) | b(s, env)
    if isinstance(e, Sum):
        body, dom, var = _compile(e.body), _compile(e.domain), e.var

        def run_sum(s, env):
            total = 0.0
            for j in sorted(dom(s, env)):
                s[var] = j
                total += body(s, env)
            s.pop(var, None)
            return total

        return run_sum
    args = [_compile(a) for a in e.args]
    f = e.func
    if f == "N":
        return lambda s, env: env.row(int(args[0](s, env)))
    if f == "size":
        return lambda s, env: float(len(args[0](s, env)))
    if f == "project":
        return lambda s, env: env.projector(frozenset(args[0](s, env)), int(args[1](s, env)))
    if f == "comb":
        return lambda s, env: float(math.comb(max(0, int(args[0](s, env))), int(args[1](s, env))))
    if f == "pow":
        return lambda s, env: float(args[0](s, env)) ** int(args[1](s, env))
    if f == "clip":
        return lambda s, env: min(max(args[0](s, env), args[1](s, env)), args[2](s, env))
    if f == "min":
        return lambda s, env: min(args[0](s, env), args[1](s, env))
    return lambda s, env: max(args[0](s, env), args[1](s, env))


class Interpreter:
    """Deterministic executor of a program on the node's local server."""

    def __init__(self, program: Program) -> None:
        self.program = program
        self._steps = [(k, _compile(e)) for k, e in program.assigns]
        self._ret = _compile(program.ret)
        self._agg = _compile(program.aggregate)

    def local(self, env: Env) -> float:
        scope: dict = {}
        for k, f in self._steps:
            scope[k] = f(scope, env)
        return float(self._ret(scope, env))

    def aggregate(self, total: float, n: int) -> float:
        value = self.aggregate_raw(total, n)
        return max(0.0, value) if self.program.clamp_nonnegative else value

    def aggregate_raw(self, total: float, n: int) -> float:
        """The aggregation expression before the clamp at 0."""
        return float(self._agg({"total": total}, _AggEnv(n)))

    def aggregate_coefficient(self, n: int) -> float:
        """Slope of the aggregation in ``total`` (``estimate ≈ c · total + b``):
        the final Laplace noise is the report noise scaled by ``|c|``."""
        return self.aggregate_raw(1.0, n) - self.aggregate_raw(0.0, n)


class _AggEnv:
    """Aggregate expressions read ``total`` from the scope and ``n`` from here."""

    def __init__(self, n: int) -> None:
        self.n = n


def format_program(program: Program) -> str:
    return program.text()
