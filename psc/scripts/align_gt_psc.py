"""Compare paper-grounded k-star profiles against Table 2 and Table 3.

Offline only; no model or author contact. Does not change the default profile.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from psc.alignment import compare_profiles
from psc.artifacts import new_run_directory, write_manifest
from psc.experiments import DATASETS, generic_markdown, save_json
from psc.mechanism import DEFAULT_MECHANISM, MECHANISMS


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data")
    ap.add_argument("--datasets", default=",".join(DATASETS))
    ap.add_argument("--runs", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=9292026)
    ap.add_argument("--confirm-runs", type=int, default=1000)
    ap.add_argument("--confirm-seed", type=int, default=9292027)
    ap.add_argument("--profiles", default=",".join(MECHANISMS))
    ap.add_argument("--out", default="results/alignment")
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()
    datasets, profiles = args.datasets.split(","), args.profiles.split(",")
    if set(datasets) - set(DATASETS) or set(profiles) - set(MECHANISMS):
        ap.error("unknown dataset or profile")
    if args.runs < 2 or args.confirm_runs < 2 or args.seed == args.confirm_seed:
        ap.error("use at least two runs and distinct discovery/confirmation seeds")
    try:
        out = new_run_directory(args.out, args.tag, "gt_psc_profiles")
    except (FileExistsError, ValueError) as exc:
        ap.error(str(exc))
    write_manifest(out, DEFAULT_MECHANISM, args.data, datasets, vars(args))
    rows, ranking = compare_profiles(args.data, datasets, args.runs, args.seed, profiles)
    selected = ranking[0]["mechanism"]
    # Confirm only the selected profile and legacy. No reselection on confirmation.
    confirmation, confirmation_scores = compare_profiles(
        args.data, datasets, args.confirm_runs, args.confirm_seed,
        list(dict.fromkeys(["legacy", selected])),
    )
    save_json(rows, out / "summary.json")
    save_json(ranking, out / "ranking.json")
    save_json(confirmation, out / "confirmation.json")
    save_json({
        "selected": selected, "default": DEFAULT_MECHANISM,
        "selection_rule": "minimum mean absolute log ratio over unique Table 2 and available Table 3 cells",
        "confirmation_scores": confirmation_scores,
        "note": "Selection uses published paper values; no claim of recovering author code. Confirmation uses a new random stream, not unseen datasets.",
    }, out / "selection.json")
    md = generic_markdown(ranking, ["mechanism", "table2_log_gap", "table3_pscb_log_gap", "joint_log_gap", "max_relative_gap"])
    md += "\n\n" + generic_markdown(rows, ["mechanism", "dataset", "task", "method", "runs", "avg_relative_error", "se_relative_error", "paper", "paper_relative_gap"])
    (out / "table.md").write_text(md + "\n")
    print(generic_markdown(ranking, ["mechanism", "joint_log_gap", "max_relative_gap"]))
    print(f"selected={selected}; saved {out}")


if __name__ == "__main__":
    main()
