"""Merge the runs.jsonl of interrupted and make-up agent runs, then rebuild the tables.

Rows are keyed by (dataset, task, method, eps, run). When a key appears in
several sources the first source listed wins, so pass the original directory
first. Run ``i`` uses the noise stream ``default_rng([seed, i-1])`` regardless
of which invocation executed it, so make-up runs with the same seed are
interchangeable with the missing ones.

Example::

    python scripts/merge_runs.py results/exp1/hy3_exp1_r10 results/exp1/hy3_exp1_pm_rest \\
        --out results/exp1/hy3_exp1_r10_merged
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from psc.artifacts import append_run  # noqa: E402
from psc.events import count_errors  # noqa: E402
from psc.experiments import (  # noqa: E402
    ALL_METHODS,
    DATASETS,
    NON_DP_METHODS,
    RETRY_KINDS,
    error_statistics,
    paper_value,
    save_json,
    save_results,
    table2_markdown,
    validation_summary,
    with_llm_error_table,
)
from psc.framework import RunResult  # noqa: E402
from psc.graph import TASKS, load_dataset  # noqa: E402

CONSISTENT_SETTINGS = ("provider", "node_model", "curator_model", "seed", "temperature", "structured_input")


def _read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _key(row: dict) -> tuple:
    return row["dataset"], row["task"], row["method"], row["eps"], row["extra"]["run"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="+", type=Path, help="result directories containing runs.jsonl; earlier wins")
    ap.add_argument("--out", required=True, type=Path, help="new directory for the merged results")
    ap.add_argument("--data", default="data")
    ap.add_argument("--runs", type=int, default=None, help="expected runs per cell (default: first manifest)")
    ap.add_argument("--datasets", default=None, help="comma separated; keep only these datasets (default: all found)")
    args = ap.parse_args()
    keep_datasets = set(args.datasets.split(",")) if args.datasets else None
    if keep_datasets and keep_datasets - set(DATASETS):
        ap.error("unknown dataset")

    manifests = []
    for src in args.sources:
        if not (src / "runs.jsonl").is_file():
            ap.error(f"{src}/runs.jsonl not found")
        m = src / "manifest.json"
        manifests.append(json.loads(m.read_text(encoding="utf-8")) if m.is_file() else {})
    first = manifests[0].get("settings", {})
    for src, man in zip(args.sources[1:], manifests[1:]):
        s = man.get("settings", {})
        diff = [k for k in CONSISTENT_SETTINGS if k in s and k in first and s[k] != first[k]]
        if man.get("mechanism", {}).get("name") != manifests[0].get("mechanism", {}).get("name"):
            diff.append("mechanism")
        if diff:
            ap.error(f"{src} differs from {args.sources[0]} in {diff}; refusing to merge")

    try:
        args.out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        ap.error(f"{args.out} already exists; choose a new --out")

    merged: dict[tuple, dict] = {}
    provenance = []
    for src in args.sources:
        kept = dropped = 0
        for row in _read_rows(src / "runs.jsonl"):
            if keep_datasets and row["dataset"] not in keep_datasets:
                continue
            if _key(row) in merged:
                dropped += 1
                continue
            merged[_key(row)] = row
            kept += 1
        provenance.append({"source": str(src), "kept": kept, "dropped_duplicates": dropped})
        print(f"{src}: kept {kept}, dropped {dropped} duplicates")

    task_order = {t: i for i, t in enumerate(TASKS)}
    method_order = {m: i for i, m in enumerate(ALL_METHODS)}
    rows = sorted(
        merged.values(),
        key=lambda r: (DATASETS.index(r["dataset"]), task_order[r["task"]], method_order[r["method"]], r["eps"], r["extra"]["run"]),
    )
    for row in rows:
        append_run(args.out / "runs.jsonl", row)

    cells: dict[tuple, list[RunResult]] = {}
    for row in rows:
        cells.setdefault((row["dataset"], row["task"], row["eps"], row["method"]), []).append(RunResult(**row))

    expected = args.runs or first.get("runs")
    loaded = {ds: load_dataset(args.data, ds) for ds in {k[0] for k in cells}}
    summary = []
    for (ds, task, eps, method), results in cells.items():
        rec = loaded[ds][task]
        runs = sorted(r.extra["run"] for r in results)
        if isinstance(expected, int) and runs != list(range(1, expected + 1)):
            print(f"WARNING: {ds} {task} {method} has runs {runs}, expected 1..{expected}")
        failed = sum(count_errors(r.extra["errors"], "call_failed") for r in results)
        if failed:
            print(f"note: {ds} {task} {method} contains {failed} failed model calls")
        summary.append(
            {
                "method": method,
                "dataset": ds,
                "task": task,
                "eps": eps if method not in NON_DP_METHODS else None,
                "runs": len(results),
                "truth": rec.answer,
                "mean_estimate": float(np.mean([r.estimate for r in results])),
                **error_statistics(
                    [r.estimate for r in results], rec.answer, rec.vertex_num,
                    paper_value(task, method, ds) if eps in (0.0, 2.0) else None,
                ),
                "mechanism": results[0].extra.get("mechanism"),
                "seed": results[0].extra.get("seed"),
                "llm_calls_per_run": float(np.mean([r.llm_calls for r in results])),
                "parse_failures": int(sum(r.parse_failures for r in results)),
                "api_retries": sum(count_errors(r.extra["errors"], *RETRY_KINDS) for r in results),
                "failed_calls": failed,
                "paper": paper_value(task, method, ds) if (eps == 2.0 or method in NON_DP_METHODS) else None,
                "provider": first.get("provider"),
                "node_model": first.get("node_model"),
                "curator_model": first.get("curator_model"),
                "r1": first.get("r1", 0.5),
                "r2": first.get("r2", 0.2),
                **validation_summary(results, rec.vertex_num),
            },
        )

    datasets = [d for d in DATASETS if d in loaded]
    methods = [m for m in ALL_METHODS if any(k[3] == m for k in cells)]
    eps_values = sorted({k[2] for k in cells if k[3] not in NON_DP_METHODS})
    md = table2_markdown(summary, datasets, methods, eps=eps_values[0] if len(eps_values) == 1 else 2.0)
    md = with_llm_error_table(md, summary)
    save_results(args.out, summary, [r.to_dict() for rs in cells.values() for r in rs], md)
    save_json({"sources": provenance, "manifests": manifests}, args.out / "merge.json")
    print("\n" + md)
    print(f"\nsaved runs.jsonl, runs.json, summary.json, table.md, merge.json in {args.out}/")


if __name__ == "__main__":
    main()
