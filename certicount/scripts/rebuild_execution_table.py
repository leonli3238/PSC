"""Rebuild the tables of a saved ``run_execution_compare`` result with the fixed metrics.

No model is called and the original files are not touched. Writes, next to them:

* ``runs_rebuilt.jsonl`` -- the runs with the fixes applied (each changed row has ``rebuilt``);
* ``summary_rebuilt.json`` / ``table_rebuilt.md``.

Fixes (see :mod:`certicount.execution_report`):

1. Naive: the saved reply is parsed again with the current parser (mixed numbers
   such as ``6 and 10/49`` used to be read as ``10/49``).
2. DSL: the paired rule value is the program itself (``llm_error`` = 0); the old
   comparison with the library algorithm is kept under ``validation.library``.
3. DSL: ``noise_ratio`` (final noise ``|c|·GS/ε3`` over the reference's) next to ``gs_ratio``.
4. DSL: ``design_exact`` excludes runs where both estimates are clamped to 0.

    ../.venv/bin/python scripts/rebuild_execution_table.py results/execution/glm_methods_cu_do
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from psc.graph import load_dataset  # noqa: E402
from psc.prompts import extract_json, extract_number  # noqa: E402
from certicount import DATA_DIR  # noqa: E402
from certicount.artifacts import append_jsonl, write_json  # noqa: E402
from certicount.dsl.ground_truth import final_noise_scale, noise_ratio  # noqa: E402
from certicount.dsl.lang import DSLError, Interpreter, parse_program  # noqa: E402
from certicount.dsl.library import PROGRAMS  # noqa: E402
from certicount.dsl.quality import task_record  # noqa: E402
from certicount.evaluation import as_run_result, load_runs  # noqa: E402
from certicount.execution_report import CODE_METHODS, markdown, summarize  # noqa: E402


def parse_reply(text: str) -> float | None:
    """The curator's parser (:meth:`psc.agents.curator_agent.CuratorAgent._parse_result`)."""
    payload = extract_json(text)
    if payload and "result" in payload:
        try:
            return float(payload["result"])
        except (TypeError, ValueError):
            pass
    return extract_number(text)


def program_from_text(text: str):
    local, _, rest = text.partition("\naggregate: ")
    agg, _, budget = rest.partition("\nbudget: ")
    return parse_program(local, agg.strip() or "total", budget=budget.strip() or None)


def fix_naive(row: dict) -> list[str]:
    reply = row.get("extra", {}).get("reply")
    if not reply:
        return []
    value = parse_reply(reply)
    value = 0.0 if value is None else value
    if row.get("estimate") is not None and math.isclose(value, row["estimate"], rel_tol=1e-12, abs_tol=1e-12):
        return []
    row["extra"]["estimate_before_rebuild"] = row["estimate"]
    row["estimate"] = value
    return [f"naive reparse {row['extra']['estimate_before_rebuild']} -> {value}"]


def fix_program(row: dict, n: int) -> list[str]:
    ex = row["extra"]
    if ex.get("rejected") or row.get("estimate") is None:
        return []
    notes = []
    v = ex["validation"]
    if v.get("checked_against") != "program":
        lib = {k: v.get(k) for k in ("e2e_exact", "rule_count_sum", "count_rel_diff", "rule_estimate")}
        count_sum = v.get("llm_count_sum")
        v.update(update_exact=v["nodes"], e2e_exact=v["nodes"], send_checked=0, send_exact=0, rule_count_sum=count_sum,
                 count_rel_diff=0.0, aggregate_exact=True, rule_estimate=row["estimate"], mismatches=[],
                 checked_against="program", library=lib)
        notes.append("validation against the program itself")
    design = ex.get("trust", {}).get("design") or {}
    if row.get("design_noise_ratio") is None and design.get("program") and row.get("sensitivity") is not None:
        try:
            coef = Interpreter(program_from_text(design["program"])).aggregate_coefficient(n)
        except DSLError:
            return notes
        gt = row["paired_gt_dsl"]
        ref_coef = Interpreter(PROGRAMS[row["task"]].parse()).aggregate_coefficient(n)
        mine = final_noise_scale(coef, row["sensitivity"], row["split"][2])
        ref = final_noise_scale(ref_coef, gt["gs"], gt["split"][2])
        row["design_noise_ratio"] = noise_ratio(mine, ref)
        notes.append("noise_ratio")
    return notes


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("result_dir")
    ap.add_argument("--data", default=str(DATA_DIR))
    args = ap.parse_args()
    src = Path(args.result_dir)
    rows = load_runs(src)
    manifest = json.loads((src / "manifest.json").read_text(encoding="utf-8")) if (src / "manifest.json").exists() else {}
    settings = manifest.get("settings", manifest)
    out_runs = src / "runs_rebuilt.jsonl"
    if out_runs.exists():
        out_runs.unlink()

    datasets: dict[str, dict] = {}
    n_of: dict[tuple, int] = {}
    changed = 0
    for row in rows:
        ds, task = row["dataset"], row["task"]
        if (ds, task) not in n_of:
            if ds not in datasets:
                datasets[ds] = load_dataset(args.data, ds)
            n_of[(ds, task)] = task_record(datasets[ds], ds, task).vertex_num
        n = n_of[(ds, task)]
        notes = fix_naive(row) if row.get("mode") == "naive" else fix_program(row, n) if row.get("mode") == "program" else []
        if notes:
            row["rebuilt"] = notes
            changed += 1
        append_jsonl(row, out_runs)

    cells: dict[tuple, list[dict]] = {}
    for row in rows:
        if row.get("mode") == "program":
            row["method"] = "DSL"
        cells.setdefault((row["dataset"], row["task"], row["mode"], row["eps"], row["method"]), []).append(row)
    summary = []
    for (ds, task, mode, eps, method), group in cells.items():
        group.sort(key=lambda r: r["run"])
        results = [as_run_result(r) for r in group]
        summary.append(summarize(ds, task, mode, method, n_of[(ds, task)], eps, results, group, method in CODE_METHODS))
    gt_runs = settings.get("gt_runs") or settings.get("runs")
    header = (f"Rebuilt from `{src.name}` with the fixed metrics ({changed} run(s) changed; see `runs_rebuilt.jsonl`, "
              f"field `rebuilt`). Settings: " + ", ".join(f"{k} = {settings.get(k)}" for k in
                                                          ("provider", "node_model", "curator_model", "eps", "runs", "seed")
                                                          if k in settings) + ".")
    md = markdown(summary, header, gt_runs)
    write_json({"settings": settings, "rows": summary}, src / "summary_rebuilt.json")
    (src / "table_rebuilt.md").write_text(md, encoding="utf-8")
    print(md)
    print(f"{changed} run(s) changed; wrote {out_runs.name}, summary_rebuilt.json, table_rebuilt.md in {src}")


if __name__ == "__main__":
    main()
