"""CS7 summary: deriver fuzzing (A programs, own bounds), offline replay, online arms (per-node architecture).

    ../.venv/bin/python scripts/summarize_cs7.py --out results/cs7_summary.md

Missing result directories are listed as missing; nothing is recomputed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from certicount.artifacts import markdown_table  # noqa: E402

RES = ROOT / "results"
ARMS = ("cs7_node_v1alt_gate", "cs7_node_v1alt_sim", "cs7_node_v1alt_sim-noown", "cs7_node_v1alt_sim_cudo")
FUZZ = ("cs7_fuzz_matrix", "cs7_fuzz_node_rows")
BASELINES = ("cs5_eval_node_v0", "cs5_eval_node_v0-r2", "cs5_eval_node_evolved")


def load(p: Path) -> dict | None:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(RES / "cs7_summary.md"))
    args = ap.parse_args()
    md = ["# CS7 summary (per-node architecture, PM, ε = 2, held-out tasks)", ""]

    md += ["## Deriver fuzzing: programs that read A, own bounds D != dmax", ""]
    rows = []
    for tag in FUZZ:
        s = load(RES / "dsl" / tag / "summary.json")
        if s is None:
            md.append(f"- {tag}: missing")
            continue
        for r in s["summary"]:
            rows.append({"campaign": tag, **r})
        md.append(f"- {tag}: {s['count']} programs, {s['failures']} refuted or failing")
    if rows:
        md += ["", markdown_table(rows, ["campaign", "n", "dmax", "D", "graphs", "programs", "reads_matrix", "derived",
                                         "refuted", "tight", "median_gs_over_max", "max_gs_over_max"])]
    md.append("")

    rep = load(RES / "dsl_eval" / "cs7_offline_replay" / "summary.json")
    md += ["## Offline replay of the CS4/CS5 per-node runs (no model call)", ""]
    if rep is None:
        md.append("missing")
    else:
        md.append(markdown_table(rep["table"], ["task", "designs", "pairs", "reference_re", "recorded_accept",
                                                "recorded_re", "recorded_own_row", "nogate_accept", "single_accept",
                                                "single_re", "pair_accept", "pair_first_re", "pair_choice_re",
                                                "pair_reads"]))
        agree = [r for r in rep["ranks"] if r.get("rank_agreement") is not None]
        if agree:
            md += ["", "Design-time simulated score against the real error: " + "; ".join(
                f"{r['task']} {r['rank_agreement']:.2f} ({r['pairs_compared']} program pairs)" for r in agree)]
    md.append("")

    md += ["## Online arms", ""]
    rows = []
    for tag in (*BASELINES, *ARMS):
        s = load(RES / "dsl_eval" / tag / "summary.json")
        if s is None:
            if tag in ARMS:
                md.append(f"- {tag}: missing")
            continue
        for r in s["summary"]:
            rows.append({"arm": tag, **{k: r.get(k) for k in (
                "task", "designs", "accept_rate", "accept_ci95", "mean_llm_calls", "relative_error",
                "median_relative_error", "gt_dsl_relative_error", "design_error", "gs_ratio", "noise_ratio",
                "mean_candidates", "runs_matrix")}})
    rows.sort(key=lambda r: (r["task"], r["arm"]))
    if rows:
        md += ["", markdown_table(rows, ["task", "arm", "designs", "accept_rate", "accept_ci95", "mean_llm_calls",
                                         "relative_error", "median_relative_error", "gt_dsl_relative_error",
                                         "design_error", "gs_ratio", "noise_ratio", "mean_candidates", "runs_matrix"])]
        md += ["", "cs5_* rows: CS5 per-node arms (prompt v0 / evolved, gate on; their gs_ratio is the raw ratio of "
                   "the local GS)."]
    Path(args.out).write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
