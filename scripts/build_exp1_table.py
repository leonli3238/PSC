"""Build the Exp1 (paper Table 2) summary from finished result directories.

GT rows come from a pure-Python GT summary; each LLM source is one or more
``runs.jsonl`` files of the same campaign (earlier files win on duplicate
``(dataset, task, method, eps, run)``). Only cells with ``--runs`` complete runs
are shown. ``Avg.`` is taken over CU, Do, ML, CS, EE for every row, the paper's
rows included, because PM is incomplete for the agent runs.

Example::

    python scripts/build_exp1_table.py --out results/exp1/table2
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from psc.events import count_errors  # noqa: E402
from psc.experiments import DATASETS, PAPER_TABLE2, save_json, validation_summary  # noqa: E402
from psc.framework import RunResult  # noqa: E402
from psc.graph import load_dataset  # noqa: E402
from psc.ground_truth import relative_error  # noqa: E402

GT_SUMMARY = "results/ground_truth/gt_all_r1000_floor_tight_20260930/summary.json"
SOURCES = {
    "DeepSeek-V3": ["results/exp1/dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0/runs.jsonl"],
    "hy3-ioa": [
        "results/exp1/hy3_exp1_r10_5ds/runs.jsonl",
        "results/exp1/hy3_exp1_r10/runs.jsonl",
        "results/exp1/hy3_exp1_pm_rest/runs.jsonl",
    ],
}
TABLE_TASKS = ("degree", "2-star", "3-star", "triangle")
AVG_DATASETS = ("CU", "Do", "ML", "CS", "EE")
METHODS = ("Naive", "PSC")


def load_cells(paths: list[str]) -> dict[tuple[str, str, str], list[RunResult]]:
    seen, cells = set(), defaultdict(list)
    for path in paths:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            key = (row["dataset"], row["task"], row["method"], row["eps"], row["extra"]["run"])
            if key in seen or row["eps"] != 2.0:
                continue
            seen.add(key)
            cells[(row["dataset"], row["task"], row["method"])].append(RunResult(**row))
    return cells


def fmt(v: float | None, italic: bool = False) -> str:
    if v is None:
        return "-"
    return f"*{v:.4f}*" if italic else f"{v:.4f}"


def avg(values: dict[str, float | None]) -> float | None:
    vals = [values.get(ds) for ds in AVG_DATASETS]
    return float(np.mean(vals)) if all(v is not None for v in vals) else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="data")
    ap.add_argument("--runs", type=int, default=10, help="runs a cell needs to be shown")
    ap.add_argument("--out", default="results/exp1/table2", help="writes <out>.md and <out>.json")
    args = ap.parse_args()

    records = {ds: load_dataset(args.data, ds) for ds in DATASETS}
    gt = {(r["method"], r["dataset"], r["task"]): r["avg_relative_error"]
          for r in json.loads(Path(GT_SUMMARY).read_text(encoding="utf-8"))}

    # (row label, task) -> dataset -> value
    table: dict[tuple[str, str], dict[str, float | None]] = {}
    partial: set[tuple[str, str, str]] = set()
    decomposition: dict[tuple[str, str, str], dict[str, dict]] = defaultdict(dict)
    notes: list[str] = []
    for label, paths in SOURCES.items():
        for (ds, task, method), cell in sorted(load_cells(paths).items()):
            if method not in METHODS or len(cell) != args.runs:
                continue
            # a call whose retries ran out yields 0, which flatters any over-counting estimator
            results = [r for r in cell if not count_errors(r.extra.get("errors", []), "call_failed")]
            if len(results) < len(cell):
                kept = f"按其余 {len(results)} 次计算" if results else "未列入"
                notes.append(f"{method} · {label} · {ds} · {task}：{len(cell) - len(results)} 次运行的模型调用重试耗尽，{kept}")
            if not results:
                continue
            if len(results) < len(cell):
                partial.add((f"{method} · {label}", task, ds))
            rec = records[ds][task]
            re = [relative_error(r.estimate, r.truth, rec.vertex_num) for r in results]
            table.setdefault((f"{method} · {label}", task), {})[ds] = float(np.mean(re))
            decomposition[(label, method, task)][ds] = validation_summary(results, rec.vertex_num)

    rows_md = [
        "| Task | Method | " + " | ".join(DATASETS) + " | Avg. (CU–EE) |",
        "|" + "---|" * (len(DATASETS) + 3),
    ]
    out_json: dict = {"gt_summary": GT_SUMMARY, "sources": SOURCES, "runs": args.runs, "rows": []}
    def emit(task: str, name: str, values: dict[str, float | None], italic: bool = False) -> None:
        cells = [fmt(values.get(ds), italic) + ("†" if (name, task, ds) in partial else "") for ds in DATASETS]
        rows_md.append(
            f"| {task} | {f'*{name}*' if italic else name} | " + " | ".join(cells) + f" | {fmt(avg(values), italic)} |",
        )
        out_json["rows"].append({"task": task, "row": name, **{ds: values.get(ds) for ds in DATASETS}, "avg_cu_ee": avg(values)})

    for task in TABLE_TASKS:
        for method in ("GT-Naive", "Naive", "GT-PSC", "PSC"):
            if method.startswith("GT-"):
                emit(task, f"{method}（本实现，1000 次）", {ds: gt.get((method, ds, task)) for ds in DATASETS})
            else:
                for label in SOURCES:
                    if (f"{method} · {label}", task) in table:
                        emit(task, f"{method} · {label}", table[(f"{method} · {label}", task)])
            emit(task, f"{method}（论文）", dict(zip(DATASETS, PAPER_TABLE2[task][method])), italic=True)

    decomposition_md = [
        "| Task | Method | 模型 | 平均相对误差 | 同噪声规则值 | 执行正确率 | 凑巧降幅 | 错误增幅 | 去掉运气 | 给足运气 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    out_json["decomposition"] = []
    keys = ("avg_relative_error", "rule_relative_error", "exec_exact", "lucky_gain", "llm_harm",
            "conservative_relative_error", "optimistic_relative_error")
    for task in TABLE_TASKS:
        for method in METHODS:
            for label in SOURCES:
                cells = decomposition.get((label, method, task), {})
                if not all(ds in cells for ds in AVG_DATASETS):
                    continue
                mean = {"avg_relative_error": avg(table[(f"{method} · {label}", task)])}
                mean.update({k: float(np.mean([cells[ds][k] for ds in AVG_DATASETS])) for k in keys[1:]})
                decomposition_md.append(
                    f"| {task} | {method} | {label} | " + " | ".join(f"{mean[k]:.4f}" if k != "exec_exact" else f"{mean[k]:.0%}" for k in keys) + " |",
                )
                out_json["decomposition"].append({"task": task, "method": method, "model": label, **mean})

    ratio_cols = [("本实现 GT（1000 次）", "GT-{}（本实现，1000 次）"), ("论文 GT", "GT-{}（论文）")]
    ratio_cols += [(label, "{} · " + label) for label in SOURCES] + [("论文 LLM", "{}（论文）")]
    by_row = {(r["task"], r["row"]): r["avg_cu_ee"] for r in out_json["rows"]}
    ratio_md = ["| Task | " + " | ".join(c for c, _ in ratio_cols) + " |", "|" + "---|" * (len(ratio_cols) + 1)]
    out_json["naive_over_psc"] = []
    for task in TABLE_TASKS:
        ratios = []
        for _, pattern in ratio_cols:
            naive, psc = by_row.get((task, pattern.format("Naive"))), by_row.get((task, pattern.format("PSC")))
            ratios.append(naive / psc if naive is not None and psc else None)
        ratio_md.append(f"| {task} | " + " | ".join("-" if r is None else f"{r:.1f}×" for r in ratios) + " |")
        out_json["naive_over_psc"].append({"task": task, **{c: r for (c, _), r in zip(ratio_cols, ratios)}})
    decomposition_md += ["", "Naive / PSC 平均相对误差之比（CU–EE 平均）：", "", *ratio_md]

    out_json["notes"] = notes
    note = "".join(f"\n- † {s}" for s in notes)
    md = "\n".join(rows_md) + (f"\n{note}\n" if note else "") + "\n\nLLM 误差分解（CU–EE 平均）：\n\n" + "\n".join(decomposition_md) + "\n"
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".md").write_text(md, encoding="utf-8")
    save_json(out_json, out.with_suffix(".json"))
    print(md)
    print(f"saved {out.with_suffix('.md')} and {out.with_suffix('.json')}")


if __name__ == "__main__":
    main()
