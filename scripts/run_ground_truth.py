"""Compute GT-Naive / GT-PSC / GT-PSC-B (pure-Python DP algorithms).

The paper executes each Python algorithm 1,000 times and reports the average
relative error (Section 4.1).

Examples::

    # Table 2 ground truth (eps = 2, all datasets, 1000 runs)
    python scripts/run_ground_truth.py --runs 1000

    # Exp2: vary eps on CU and Do
    python scripts/run_ground_truth.py --datasets CU,Do --eps 1.0,1.5,2.0,2.5,3.0 --tag exp2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from psc.experiments import (  # noqa: E402
    DATASETS,
    generic_markdown,
    run_ground_truth,
    save_results,
    table2_markdown,
)
from psc.graph import DEFAULT_TASKS, TASKS  # noqa: E402
from psc.mechanism import DEFAULT_MECHANISM, MECHANISMS  # noqa: E402
from psc.artifacts import append_run, new_run_directory, write_manifest  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="results", help="results go to <out>/ground_truth/<tag>/")
    ap.add_argument("--datasets", default=",".join(DATASETS))
    ap.add_argument("--tasks", default=",".join(DEFAULT_TASKS), help=f"comma separated, from {','.join(TASKS)}")
    ap.add_argument("--eps", default="2.0", help="comma separated privacy budgets")
    ap.add_argument("--runs", type=int, default=1000)
    ap.add_argument("--mechanism", choices=MECHANISMS, default=DEFAULT_MECHANISM)
    ap.add_argument("--trace", action="store_true", help="save per-run estimates, degree reports and count noise to runs.jsonl")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--methods", default="GT-Naive,GT-PSC,GT-PSC-B")
    ap.add_argument("--r1", type=float, default=0.5, help="eps1 = r1 * eps")
    ap.add_argument("--r2", type=float, default=0.2, help="eps2 = r2 * (eps - eps1)")
    ap.add_argument("--tag", default=None, help="new result directory; default includes mechanism and timestamp")
    args = ap.parse_args()

    datasets = args.datasets.split(",")
    tasks = args.tasks.split(",")
    eps_values = [float(x) for x in args.eps.split(",")]
    methods = args.methods.split(",")
    if args.runs < 1 or set(datasets) - set(DATASETS) or set(tasks) - set(TASKS):
        ap.error("positive runs and known datasets/tasks are required")
    if set(methods) - {"GT-Naive", "GT-PSC", "GT-PSC-B"}:
        ap.error("unknown GT method")
    try:
        out_dir = new_run_directory(Path(args.out) / "ground_truth", args.tag, f"table2_{args.mechanism}")
    except (FileExistsError, ValueError) as exc:
        ap.error(f"{exc}; choose a new --tag")
    write_manifest(out_dir, args.mechanism, args.data, datasets, {
        "datasets": datasets, "tasks": tasks, "methods": methods, "eps": eps_values,
        "runs": args.runs, "seed": args.seed, "r1": args.r1, "r2": args.r2,
    })

    rows = run_ground_truth(
        args.data, datasets, tasks, eps_values, args.runs, args.seed, methods, args.r1, args.r2,
        mechanism=args.mechanism,
        on_result=(lambda row: append_run(out_dir / "runs.jsonl", row)) if args.trace else None,
    )

    if eps_values == [2.0]:
        md = table2_markdown(rows, datasets, methods)
    else:
        md = generic_markdown(rows, ["method", "dataset", "task", "eps", "avg_relative_error", "mean_estimate", "truth"])
    save_results(out_dir, rows, markdown=md)
    print("\n" + md)
    print(f"\nsaved summary.json, table.md in {out_dir}/")


if __name__ == "__main__":
    main()
