"""A4: why CertiCount must certify the curator's programs (offline, no model call).

Input: a design-evaluation directory of ``scripts/run_dsl_design_eval.py`` (serial
designs, so ``transcripts.jsonl`` holds the curator calls in the order of
``designs.jsonl``, ``llm_calls`` per design). Every draft the curator wrote is
re-parsed and classified by the first check it fails, in the order of the design
loop (:func:`certicount.dsl.designer.check_draft`):

    parse        no valid DSL program in the reply
    duplicate    identical to an earlier draft of the same loop
    gs_failed    the deriver cannot bound the sensitivity
    gs_loose     a bound exists but is flagged too loose
    semantic     the utility test finds a wrong count on public test graphs
    refuted      the falsifier finds a flip above the derived GS
    accepted     certified

Counterfactual without certification (what PSC does): run the draft and calibrate
the noise with the task's reference GS (the library value, as PSC's rule-based
privacy controller does). The falsifier measures the largest change of the draft's
local count over single neighbour flips on small public graphs (every symmetric
graph with n = 5, dmax = 3, and 300 random ones with n = 7, dmax = 4). A change
Δ above the reference GS breaks the guarantee: the privacy loss of that pair is
Δ / GS_ref · ε3 > ε3 (a lower bound, found by search). Semantic errors are also
reported: without the utility test the system would publish a wrong statistic.

    ../.venv/bin/python scripts/analyze_design_certification.py results/dsl_eval/A3_pm_design_8bthink_d10
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401  (puts ../psc on sys.path)
from certicount.dsl.designer import read_draft  # noqa: E402
from certicount.dsl.falsifier import _all_symmetric_graphs, max_delta, random_symmetric_graphs  # noqa: E402
from certicount.dsl.library import HAND_GS  # noqa: E402
from certicount.dsl.sensitivity import PublicParams, SensitivityError, derive  # noqa: E402
from certicount.dsl.utility import utility_test  # noqa: E402

CHECKS = ((5, 3, None), (7, 4, 300))
ORDER = ("parse", "duplicate", "gs_failed", "gs_loose", "semantic", "refuted", "accepted")


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def empirical_delta(program, task: str) -> dict:
    """Largest flip change found, its ratio to the task's reference GS, and the deriver's own
    bound at the very same (n, D) — so ``unsound`` compares like with like."""
    out = {"max_delta": 0.0, "ratio": 0.0, "error": None, "witness": None,
           "unsound": False, "derived_gs": None, "reference_gs": None, "looser": None}
    for n, dmax, samples in CHECKS:
        graphs = ([[frozenset() for _ in range(n)]] if not program.uses_rows else
                  _all_symmetric_graphs(n, dmax) if samples is None else random_symmetric_graphs(n, dmax, samples))
        params = PublicParams(n, D=dmax, dmax=dmax)
        try:
            der_gs = derive(program, params).gs
        except SensitivityError:
            der_gs = None
        try:
            ce = max_delta(program, n, dmax, graphs, D=dmax)
        except (ArithmeticError, ValueError, TypeError, KeyError) as exc:
            out["error"] = f"{type(exc).__name__}: {exc} (n={n})"
            return out
        if der_gs is not None and ce.max_delta > der_gs + 1e-9:
            out["unsound"] = True
        ref = HAND_GS[task](params)
        ratio = ce.max_delta / ref if ref > 0 else (float("inf") if ce.max_delta > 0 else 0.0)
        if ratio > out["ratio"]:
            out.update(max_delta=ce.max_delta, ratio=ratio, reference_gs=ref, derived_gs=der_gs, n=n, dmax=dmax,
                       looser=None if der_gs is None else der_gs > ref + 1e-9,
                       witness={"private": list(ce.private), "vertex": ce.vertex})
    return out


def classify(program, seen: set, task: str, public_n: int, params: PublicParams) -> str:
    if program.digest in seen:
        return "duplicate"
    seen.add(program.digest)
    try:
        der = derive(program, params)
    except SensitivityError:
        return "gs_failed"
    if any("loose" in w for w in der.warnings):
        return "gs_loose"
    if not utility_test(program, task, count=30, public_n=public_n).passed:
        return "semantic"
    from certicount.dsl.designer import falsifier_feedback

    return "refuted" if falsifier_feedback(program) else "accepted"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--out", default=None, help="default: <run_dir>/certification_ablation")
    a = ap.parse_args()
    d = Path(a.run_dir)
    designs, calls = load_jsonl(d / "designs.jsonl"), load_jsonl(d / "transcripts.jsonl")
    need = sum(int(r["llm_calls"]) for r in designs)
    if need > len(calls):
        sys.exit(f"{d}: designs need {need} transcripts, only {len(calls)} (run still in progress?)")
    from certicount.dsl.designer import design_reference_params

    out = Path(a.out) if a.out else d / "certification_ablation"
    out.mkdir(parents=True, exist_ok=True)
    drafts, pos = [], 0
    public_n = {}
    for r in designs:
        task = r["task"]
        if r["dataset"] not in public_n:
            from psc.graph import load_dataset

            public_n[r["dataset"]] = load_dataset(str(certicount.DATA_DIR), r["dataset"])["degree"].vertex_num
        n = public_n[r["dataset"]]
        params = design_reference_params(n)
        seen: set = set()
        for it in range(int(r["llm_calls"])):
            text = calls[pos]["reply"]
            pos += 1
            program, entry = read_draft(text)
            row = {"dataset": r["dataset"], "task": task, "design": r["design"], "iteration": it + 1,
                   "recorded_feedback": r["feedback"][it] if it < len(r["feedback"]) else None}
            if program is None:
                row.update(stage="parse", program=entry.get("program"))
            else:
                row.update(stage=classify(program, seen, task, n, params), program=program.text())
                if row["stage"] != "duplicate":
                    emp = empirical_delta(program, task)
                    ref_design = HAND_GS[task](params)
                    try:
                        gs_design = derive(program, params).gs
                    except SensitivityError:
                        gs_design = None
                    row.update(empirical=emp,
                               uncertified_violation=emp["error"] is None and emp["ratio"] > 1 + 1e-9,
                               eps_ratio=emp["ratio"], certificate_unsound=emp["unsound"],
                               gs_design=gs_design, reference_gs_design=ref_design,
                               looser_than_reference=None if gs_design is None else gs_design > ref_design + 1e-9)
            drafts.append(row)
    with (out / "drafts.jsonl").open("w", encoding="utf-8") as f:
        for row in drafts:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    by_task: dict[str, list[dict]] = defaultdict(list)
    for row in drafts:
        by_task[row["task"]].append(row)
    table = []
    for task, rows in list(by_task.items()) + [("all", drafts)]:
        c = Counter(r["stage"] for r in rows)
        runnable = [r for r in rows if "empirical" in r and r["empirical"]["error"] is None]
        viol = [r for r in runnable if r["uncertified_violation"]]
        rejected = [r for r in rows if r["stage"] not in ("accepted", "duplicate")]
        table.append({
            "task": task, "drafts": len(rows), **{k: c.get(k, 0) for k in ORDER},
            "rejected_share": round(len(rejected) / len(rows), 4) if rows else None,
            "runnable": len(runnable),
            "uncertified_violations": len(viol),
            "uncertified_violation_share": round(len(viol) / len(runnable), 4) if runnable else None,
            "max_eps_ratio": max((r["eps_ratio"] for r in runnable), default=None),
            "certificate_unsound": sum(bool(r["empirical"].get("unsound")) for r in runnable),
            "accepted_looser_than_reference": sum(
                bool(r.get("looser_than_reference")) for r in rows if r["stage"] == "accepted"),
            "semantic_errors_published_without_check": c.get("semantic", 0),
        })
    summary = {"run_dir": str(d), "checks": CHECKS, "drafts": len(drafts), "designs": len(designs), "table": table}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    cols = ["task", "drafts", *ORDER, "rejected_share", "runnable", "uncertified_violations",
            "uncertified_violation_share", "max_eps_ratio", "certificate_unsound",
            "accepted_looser_than_reference", "semantic_errors_published_without_check"]
    md = ["# A4: certification ablation of the curator's drafts", "",
          f"Source `{d}` ({len(designs)} designs, {len(drafts)} drafts). Stage = first failed check of the design "
          "loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds "
          "the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise "
          "Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = "
          "Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds "
          "the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. "
          "`accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound "
          "(valid but less accurate, a cost of the design step, not a privacy break). "
          "`semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that "
          "would be published if the test were skipped.", "",
          "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for t in table:
        md.append("| " + " | ".join("-" if t[c] is None else f"{t[c]:.3g}" if isinstance(t[c], float) else str(t[c])
                                    for c in cols) + " |")
    (out / "table.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
