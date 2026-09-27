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
from psc.graph import TASKS  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="results", help="results go to <out>/ground_truth/<tag>/")
    ap.add_argument("--datasets", default=",".join(DATASETS))
    ap.add_argument("--tasks", default=",".join(TASKS))
    ap.add_argument("--eps", default="2.0", help="comma separated privacy budgets")
    ap.add_argument("--runs", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--methods", default="GT-Naive,GT-PSC,GT-PSC-B")
    ap.add_argument("--r1", type=float, default=0.5, help="eps1 = r1 * eps")
    ap.add_argument("--r2", type=float, default=0.2, help="eps2 = r2 * (eps - eps1)")
    ap.add_argument("--tag", default="table2")
    args = ap.parse_args()

    datasets = args.datasets.split(",")
    tasks = args.tasks.split(",")
    eps_values = [float(x) for x in args.eps.split(",")]
    methods = args.methods.split(",")

    rows = run_ground_truth(args.data, datasets, tasks, eps_values, args.runs, args.seed, methods, args.r1, args.r2)

    if eps_values == [2.0]:
        md = table2_markdown(rows, datasets, methods)
    else:
        md = generic_markdown(rows, ["method", "dataset", "task", "eps", "avg_relative_error", "mean_estimate", "truth"])
    out_dir = save_results(Path(args.out) / "ground_truth" / args.tag, rows, markdown=md)
    print("\n" + md)
    print(f"\nsaved summary.json, table.md in {out_dir}/")


if __name__ == "__main__":
    main()
