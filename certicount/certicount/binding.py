"""Node-side binding of task -> local function -> projection -> GS (research content 3.1).

In PSC the untrusted curator writes the send / update rules that node agents
execute on their private neighbour lists, while the privacy controller sets the
noise scale separately; nothing ties the executed function to the GS (the
reproduction only logs a warning when the two disagree on the task). Here the
node owns the binding:

* the task comes from the privacy controller's DP framework, and the rule text,
  the local function and the projection come from the node's own table, never
  from the curator's message;
* the GS is recomputed by the node from the public bound with the same mechanism
  profile (:mod:`psc.mechanism`) the controller uses (single source), and a
  controller claim that differs is refused;
* tasks outside the table can only run as a DSL program with a certificate that
  the node verifies (:func:`certicount.dsl.sensitivity.verify_certificate`).
"""

from __future__ import annotations

from dataclasses import dataclass

from psc.library import AlgorithmSpec, get_algorithm, get_dp_framework
from psc.mechanism import MechanismProfile, get_mechanism

from .dsl.lang import Program
from .dsl.library import PROGRAMS
from .dsl.sensitivity import Certificate, PublicParams, derive, verify_certificate


class BindingViolation(RuntimeError):
    """The node refuses to execute; ``kind`` classifies the reason."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


@dataclass(frozen=True)
class Binding:
    task: str
    local_function: str
    projection: str  # "none" | "truncate_real_list" | "symmetric_noisy_graph"
    gs_formula: str
    algorithm: AlgorithmSpec
    program: Program

    def to_dict(self) -> dict:
        return {
            "task": self.task, "local_function": self.local_function, "projection": self.projection,
            "gs_formula": self.gs_formula, "program": self.program.text(),
        }


def _binding(task: str) -> Binding:
    if task == "degree":
        fn, proj, gs = "|N(i)|", "none", "1"
    elif task == "triangle":
        fn, proj, gs = "1/2 * sum_{j in N(i) & N'(i)} |N(i) & N'(j)|", "symmetric_noisy_graph", "dmax - 1"
    else:
        k = int(task.split("-")[0])
        fn, proj, gs = f"C(min(|N(i)|, D), {k})", "truncate_real_list", f"C(D - 1, {k - 1})"
    return Binding(task, fn, proj, gs, get_algorithm(task), PROGRAMS[task].parse())


BINDINGS: dict[str, Binding] = {t: _binding(t) for t in ("degree", "2-star", "3-star", "triangle")}


def get_binding(task: str) -> Binding:
    try:
        return BINDINGS[task]
    except KeyError:
        raise BindingViolation("unbound_task", f"task {task!r} is not in the binding table; ship a DSL program with a certificate") from None


def node_gs(task: str, n: int, projection_degree: int | None, mechanism: str | MechanismProfile,
            sensitivity_degree: float | None = None) -> float:
    """GS of a bound task from public values, via the controller's own formula."""
    return get_dp_framework(get_binding(task).task).sensitivity(
        n, projection_degree, get_mechanism(mechanism), sensitivity_degree,
    )


def check_algorithm(controller_task: str, algo: AlgorithmSpec) -> Binding:
    """Accept the curator's algorithm only if it is the bound one of the
    controller's task, rule texts included; else raise :class:`BindingViolation`."""
    binding = get_binding(controller_task)
    if algo.task != controller_task:
        raise BindingViolation(
            "task_mismatch",
            f"curator designed {algo.task!r} but the privacy controller calibrated the noise for {controller_task!r}",
        )
    lib = binding.algorithm
    changed = [part for part in ("send", "update", "aggregate") if getattr(algo, part) != getattr(lib, part)]
    if changed:
        raise BindingViolation("rule_tampered", f"curator's {', '.join(changed)} rule differs from the bound rule of {controller_task!r}")
    return binding


def check_gs(claimed: float, own: float) -> None:
    if abs(claimed - own) > 1e-9:
        raise BindingViolation("gs_mismatch", f"controller GS {claimed:g} differs from the node's own GS {own:g}")


def check_program(program: Program, certificate: Certificate, params: PublicParams) -> float:
    """Certificate path of out-of-table tasks; returns the node-derived GS."""
    ok, reason = verify_certificate(certificate, program, params)
    if not ok:
        raise BindingViolation("certificate_rejected", reason)
    return max(certificate.gs, derive(program, params, certificate.facts).gs)
