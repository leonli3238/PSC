"""CS9 summary: prompt-core ablation (does the curator still design triangle / open-wedge programs
when the prompt shows no program of them?) and extension tasks (statistics PSC never ran).
Reads result directories only; nothing is recomputed except the paired differences.

    ../.venv/bin/python scripts/summarize_cs9.py --out results/reports/cs9_summary.md

Arms (scripts/run_cs9.sh): G1 generic x {triangle, open-wedge}, G2 generic x extension tasks,
G3 generic x 4-cycle, G4 v1-alt x open-wedge; the v1-alt triangle arm is CS7/CS8 (same settings).
Every design run is paired with the code references of ``--gt`` (run_gt_select.py) on the same
run index: ``cc_minus_select`` = RE(CertiCount) - RE(GT-Select), ``cc_minus_naive`` likewise.
Accuracy is over accepted designs only: read it together with the accept rate.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from certicount.artifacts import markdown_table  # noqa: E402
from certicount.dsl.prompt_spec import core_leak_check  # noqa: E402

RES = ROOT / "results"
DATASETS = ("PM", "CU", "Do", "ML", "CS", "EE")
V1ALT_TRIANGLE = ("cs7_node_v1alt_sim", "cs7_node_v1alt_sim_cudo", "cs8_node_v1alt_sim_mlcsee")
EXTENSION = ("degree-ge3", "triangle-edge", "triangle-node")


def load_json(p: Path) -> dict | None:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def load_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class Arm:
    """One or more dsl_eval directories of the same prompt core."""

    def __init__(self, tags: tuple[str, ...]):
        self.tags = tuple(t for t in tags if (RES / "dsl_eval" / t / "summary.json").exists())
        self.missing = tuple(t for t in tags if t not in self.tags)
        self.summary = {(r["dataset"], r["task"]): r for t in self.tags
                        for r in load_json(RES / "dsl_eval" / t / "summary.json")["summary"]}
        self.runs: dict[tuple, list[dict]] = defaultdict(list)
        self.designs: dict[tuple, list[dict]] = defaultdict(list)
        for t in self.tags:
            for r in load_jsonl(RES / "dsl_eval" / t / "runs.jsonl"):
                self.runs[(r["dataset"], r["task"])].append(r)
            for d in load_jsonl(RES / "dsl_eval" / t / "designs.jsonl"):
                self.designs[(d["dataset"], d["task"])].append(d)
        cores = {(load_json(RES / "dsl_eval" / t / "manifest.json") or {}).get("settings", {})
                 .get("prompt_spec", {}).get("core", "v1") for t in self.tags}
        self.core = "/".join(sorted(cores)) if cores else "-"
        self.leaked = sorted({lk["task"] for c in cores for lk in core_leak_check(c)})

    def cert(self) -> list[dict]:
        out = []
        for t in self.tags:
            c = load_json(RES / "dsl_eval" / t / "certification_ablation" / "summary.json")
            row = next((r for r in (c or {}).get("table", []) if r.get("task") == "all"), None)
            errors = len(load_jsonl(RES / "dsl_eval" / t / "errors.jsonl"))
            out.append({"tag": t, "core": self.core, "drafts": row and row["drafts"], "accepted": row and row["accepted"],
                        "certificate_unsound": row and row["certificate_unsound"],
                        "uncertified_violations": row and row["uncertified_violations"],
                        "api_errors": errors, "ablation": "yes" if c else "missing"})
        return out


def gt_index(tag: str) -> tuple[dict, dict]:
    runs = {(r["dataset"], r["task"], r["run"]): r for r in load_jsonl(RES / "execution" / tag / "runs.jsonl")}
    main = {(r["dataset"], r["task"]): r for r in (load_json(RES / "execution" / tag / "summary.json") or {}).get("main", [])}
    return runs, main


def paired(cc: list[dict], gt: dict, method: str) -> tuple[float | None, float | None, float | None]:
    """(mean RE of the method on the paired runs, mean paired difference CertiCount - method, se)."""
    pairs = [(r, gt[(r["dataset"], r["task"], r["run"])]) for r in cc if (r["dataset"], r["task"], r["run"]) in gt]
    pairs = [(a, b[method]) for a, b in pairs if b.get(method) is not None]
    if not pairs:
        return None, None, None
    d = np.array([a["relative_error"] - b["relative_error"] for a, b in pairs])
    ref = float(np.mean([b["relative_error"] for _, b in pairs]))
    return ref, float(d.mean()), (float(d.std(ddof=1) / math.sqrt(len(d))) if len(d) > 1 else None)


def design_row(arm: Arm, ds: str, task: str, gt: dict, main: dict) -> dict:
    s = arm.summary.get((ds, task))
    cc = arm.runs.get((ds, task), [])
    sel_ref, d_sel, se_sel = paired(cc, gt, "GT-Select")
    naive_ref, d_naive, se_naive = paired(cc, gt, "GT-Naive")
    m = main.get((ds, task), {})
    row = {"dataset": ds, "task": task, "core": arm.core, "leaked": "yes" if task in arm.leaked else "no",
           "designs": s and s["designs"], "accept_rate": s and s["accept_rate"],
           "first_try_rate": s and s["first_try_rate"], "mean_llm_calls": s and s["mean_llm_calls"],
           "distinct_programs": s and s["distinct_programs"], "same_as_reference": s and s["same_as_reference"],
           "CertiCount": float(np.mean([r["relative_error"] for r in cc])) if cc else None,
           "GT-Select": sel_ref, "cc_minus_select": d_sel, "se_select": se_sel,
           "GT-Naive": naive_ref, "cc_minus_naive": d_naive, "se_naive": se_naive,
           "GT-DSL-node": m.get("GT-DSL-node"), "design_choice": m.get("design_choice"),
           "truth": m.get("truth"), "n": m.get("n")}
    if row["truth"] is not None and row["n"]:
        row["truth_per_n"] = row["truth"] / row["n"]
    return row


def rejection_row(arm: Arm, ds: str, task: str) -> dict:
    ds_ = arm.designs.get((ds, task), [])
    stages = Counter(st for d in ds_ for st in d.get("stages", []))
    scores = [c["score"] for d in ds_ for c in (d.get("selection") or {}).get("candidates", []) if c.get("score") is not None]
    usable = [c.get("usable") for d in ds_ for c in (d.get("selection") or {}).get("candidates", [])]
    return {"dataset": ds, "task": task, "designs": len(ds_), "accepted": sum(1 for d in ds_ if d.get("accepted")),
            "candidates": len(usable), "usable_candidates": sum(1 for u in usable if u),
            "median_sim_score": float(np.median(scores)) if scores else None,
            "stages": dict(stages.most_common(6))}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--g1", default="cs9_node_generic_sim_tri_ow")
    ap.add_argument("--g2", default="cs9_node_generic_sim_ext")
    ap.add_argument("--g3", default="cs9_node_generic_sim_4cycle")
    ap.add_argument("--g4", default="cs9_node_v1alt_sim_ow")
    ap.add_argument("--gt", default="cs9_gt_select_r1000")
    ap.add_argument("--out", default=str(RES / "reports" / "cs9_summary.md"))
    a = ap.parse_args()

    g1, g2, g3, g4 = Arm((a.g1,)), Arm((a.g2,)), Arm((a.g3,)), Arm((a.g4,))
    tri_alt = Arm(V1ALT_TRIANGLE)
    gt, gmain = gt_index(a.gt)
    missing = [t for arm in (g1, g2, g3, g4, tri_alt) for t in arm.missing] + ([a.gt] if not gmain else [])

    md = ["# CS9 summary (per-node architecture, ε = 2, Qwen3-8B thinking curator, simulated choice, α = 5)", "",
          "Mean relative error, lower is better; CertiCount = all runs of the accepted designs (100 per design). "
          "`GT-Select` / `GT-Naive`: the code references of `results/execution/" + a.gt + "` on the same run indices; "
          "`cc_minus_*` = paired mean of RE(CertiCount) − RE(reference) with its standard error. `leaked = yes`: the prompt "
          "core shows a program of the task (`prompt_spec.core_leak_check`).", ""]
    if missing:
        md += ["Missing result directories (not run yet or not finished): " + ", ".join(f"`{t}`" for t in missing), ""]

    cols = ["dataset", "task", "core", "leaked", "designs", "accept_rate", "first_try_rate", "mean_llm_calls",
            "distinct_programs", "same_as_reference", "CertiCount", "GT-Select", "cc_minus_select", "se_select",
            "GT-Naive", "cc_minus_naive"]
    abl = []
    for task, arms in (("triangle", (tri_alt, g1)), ("open-wedge", (g4, g1))):
        for ds in DATASETS:
            for arm in arms:
                if arm.tags:
                    abl.append(design_row(arm, ds, task, gt, gmain))
    md += ["## 1. Prompt-core ablation: v1-alt (shows the rows programs) vs generic (shows none)", "",
           "Same settings except the core; the v1-alt triangle rows are CS7/CS8 (" + ", ".join(V1ALT_TRIANGLE) + ").", "",
           markdown_table(abl, cols), ""]

    ext = [design_row(g2, ds, task, gt, gmain) for task in EXTENSION for ds in DATASETS if g2.tags]
    md += ["## 2. Extension tasks (generic core, PSC has no rule for them)", "",
           "`truth_per_n` close to 1: the statistic is saturated (almost every node counts), an easy target for GT-Naive.", "",
           markdown_table(ext, ["dataset", "task", "n", "truth", "truth_per_n", "designs", "accept_rate", "first_try_rate",
                                "CertiCount", "GT-Naive", "cc_minus_naive", "se_naive", "GT-DSL-node", "GT-Select",
                                "cc_minus_select", "se_select", "design_choice"]), ""]

    four = [rejection_row(g3, ds, "4-cycle") | {"gt_choice": gmain.get((ds, "4-cycle"), {}).get("design_choice"),
                                                 "GT-Naive": gmain.get((ds, "4-cycle"), {}).get("GT-Naive"),
                                                 "GT-DSL-node": gmain.get((ds, "4-cycle"), {}).get("GT-DSL-node")}
            for ds in ("CU", "ML", "EE") if g3.tags]
    md += ["## 3. Boundary case: 4-cycle (certified, GS about D·dmax)", "",
           "`usable_candidates`: certified programs whose simulated score is below the release threshold; `gt_choice = "
           "refused`: the reference program itself is not released. `stages`: design-loop outcomes of all drafts.", "",
           markdown_table(four, ["dataset", "task", "designs", "accepted", "candidates", "usable_candidates",
                                 "median_sim_score", "gt_choice", "GT-Naive", "GT-DSL-node", "stages"]), ""]

    certs = [r for arm in (g1, g2, g3, g4) for r in arm.cert()]
    md += ["## 4. Certification and model errors", "",
           "`certificate_unsound` must be 0 (run_cs9.sh stops otherwise); `api_errors`: lines of errors.jsonl "
           "(timeouts are retried, a design whose calls all fail counts as not accepted).", "",
           markdown_table(certs, ["tag", "core", "drafts", "accepted", "certificate_unsound", "uncertified_violations",
                                  "api_errors", "ablation"]), ""]

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
