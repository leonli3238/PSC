"""Production GT-PSC with the 2-star per-node threshold also applied to 3-star.

Run: .venv/bin/python results/audit/2026-10-02/adaptive_3star_gt.py
Uses an ad-hoc profile (not registered in psc.mechanism) so the default and
registered profiles are unchanged. Same seed/runs as the official GT tables.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from psc.experiments import DATASETS, run_ground_truth
from psc.mechanism import get_mechanism

PROFILE = replace(
    get_mechanism("adaptive_2star"), name="adaptive_both",
    description="adaptive_2star with the same per-node margin also applied to 3-star (diagnostic only).",
    node_margin=(("2-star", 2.0), ("3-star", 2.0)),
)


def main():
    rows = {}
    for profile in ("floor_tight", PROFILE):
        name = profile if isinstance(profile, str) else profile.name
        rows[name] = run_ground_truth(ROOT / "data", DATASETS, ["3-star"], [2.0], 1000, seed=0,
                                      methods=["GT-PSC"], mechanism=profile, log=lambda _: None)
    table = ["| 3-star GT-PSC | " + " | ".join(DATASETS) + " | Avg. |", "|---|" + "---|" * (len(DATASETS) + 1)]
    paper = [r["paper"] for r in rows["floor_tight"]]
    table.append("| *paper* | " + " | ".join(f"*{p:.4f}*" for p in paper) + f" | *{sum(paper) / 6:.4f}* |")
    for name, rs in rows.items():
        re = [r["avg_relative_error"] for r in rs]
        table.append(f"| {name} | " + " | ".join(f"{x:.4f} ({x / p - 1:+.0%})" for x, p in zip(re, paper))
                     + f" | {sum(re) / 6:.4f} |")
    md = "\n".join(table)
    print(md)
    out = Path(__file__).with_suffix("")
    out.with_suffix(".json").write_text(json.dumps(rows, indent=1))
    out.with_suffix(".md").write_text(md + "\n")


if __name__ == "__main__":
    main()
