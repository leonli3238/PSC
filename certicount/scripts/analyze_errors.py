"""Content 1: mechanism vs execution error of the reproduction's LLM runs.

Reads every ``runs.jsonl`` under ``../psc-reproduction/results/exp1`` (or the
given directories) and reports per cell the LLM error, the paired rule value on
the same noise (mechanism error), execution exactness, lucky gain / LLM harm,
and the coverage of the curator's post-processing confidence interval.
No model calls.

    ../.venv/bin/python scripts/analyze_errors.py --tag exp1_decomposition
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from psc.graph import load_dataset  # noqa: E402
from certicount import REPRO_ROOT  # noqa: E402
from certicount.artifacts import markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.evaluation import cells, decompose, find_run_dirs, load_runs  # noqa: E402

COLUMNS = [
    "source", "dataset", "task", "method", "runs", "relative_error", "rule_relative_error", "delta_signed",
    "se_delta_signed", "exec_exact", "lucky_gain", "llm_harm", "node_e2e_acc", "aggregate_acc",
    "ci_covers_truth", "ci_covers_zero",
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="*", help="result directories (default: all of ../psc-reproduction/results/exp1)")
    ap.add_argument("--keep-failed", action="store_true", help="keep runs with exhausted model retries")
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    base = REPRO_ROOT / "results" / "exp1"
    dirs = [Path(d) for d in args.dirs] or find_run_dirs(base)
    rows = []
    for d in dirs:
        runs = load_runs(d)
        for (ds, task, method), rs in sorted(cells(runs).items()):
            n = rs[0]["extra"].get("validation", {}).get("nodes") or None
            if n is None:
                n = load_dataset(REPRO_ROOT / "data", ds)[task].vertex_num
            stats = decompose(rs, n, drop_failed=not args.keep_failed)
            if stats:
                src = d.relative_to(base) if d.is_relative_to(base) else d
                rows.append({"source": str(src), "dataset": ds, "task": task, "method": method, **stats})
    out = out_dir("evaluation", args.tag, "decomposition")
    write_json({"dirs": [str(d) for d in dirs], "rows": rows}, out / "summary.json")
    md = ["# Mechanism vs execution error", "",
          "relative_error = rule_relative_error + delta_signed; delta_signed = llm_harm - lucky_gain (paired, same noise).", "",
          markdown_table(rows, COLUMNS), ""]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")
    write_manifest(out, vars(args))
    print(f"{len(rows)} cells from {len(dirs)} directories; results in {out}")


if __name__ == "__main__":
    main()
