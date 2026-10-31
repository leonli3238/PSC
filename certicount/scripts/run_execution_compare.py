"""P4: compare methods and execution modes on identical DP noise (research contents 3–5).

LLM / agent modes:
  ``naive``     the paper's Naive (RR graph with the whole budget, curator LLM answers)
  ``baseline``  the paper's PSC (curator rules, node LLMs)
  ``bind``      LLM + binding + message validation
  ``guard``     Improvement 1 (prefilter + code guard)
  ``program``   Improvement 2: the curator designs a DSL program, nodes run it (no node LLM)
  ``codecost``  bind + code send + code aggregation
Code-only references (no model call):
  ``gt-naive``  GT-Naive          ``gt-psc``  GT-PSC (same mechanism profile as the agents)
  ``gt-dsl``    GT-DSL: the reference DSL program of the task executed in code

Run i of every mode uses the noise of ``[seed, i]``. Each LLM mode also records
the paired code value on its own noise (``rule_relative_error``: GT-Naive for
Naive, GT-PSC for PSC, the program itself for ``program``), so
``llm_error = relative_error - rule_relative_error`` is the error the LLM adds
at execution time. For ``program`` every run is also paired with GT-DSL on the
same noise: ``design_error = relative_error - gt_dsl_relative_error`` is the
error the LLM designer adds (local function, GS, budget split).

Out-of-library tasks (4-star, 5-star, degree-moment2) only run in ``program``
and ``gt-dsl``. Offline by default (mock models; ``--mock-error-rate`` injects
±1 node errors). A real provider calls paid / remote models: check
``--dry-run`` first.

    ../.venv/bin/python scripts/run_execution_compare.py --datasets CU,EE --runs 10 --mock-error-rate 0.05 --tag p4_mock
    ../.venv/bin/python scripts/run_execution_compare.py --datasets CU --tasks 3-star \\
        --modes gt-naive,naive,gt-psc,baseline,gt-dsl,program --runs 10 --tag cu_3star_methods
"""

from __future__ import annotations

import argparse
import asyncio
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from psc.dp import naive_budget  # noqa: E402
from psc.experiments import run_rng, validation_summary  # noqa: E402
from psc.framework import NaiveFramework, RunResult  # noqa: E402
from psc.graph import TASKS, TaskRecord, load_dataset  # noqa: E402
from psc.ground_truth import gt_naive, gt_psc, relative_error  # noqa: E402
from psc.library import get_algorithm  # noqa: E402
from psc.mechanism import DEFAULT_MECHANISM  # noqa: E402
from psc.models import PROVIDERS, ModelConfig  # noqa: E402
from psc.progress import llm_progress  # noqa: E402
from certicount import DATA_DIR  # noqa: E402
from certicount.artifacts import append_jsonl, markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.cost import calls_per_run  # noqa: E402
from certicount.dsl.ground_truth import gs_ratio, gt_dsl  # noqa: E402
from certicount.dsl.library import OUT_OF_LIBRARY, PROGRAMS  # noqa: E402
from certicount.dsl.quality import finite_mean, task_record  # noqa: E402
from certicount.evaluation import report_interval  # noqa: E402
from certicount.framework import TrustedPSCFramework, TrustOptions, baseline_options  # noqa: E402

MODES = {
    "baseline": baseline_options,
    "bind": lambda: TrustOptions(execution="llm"),
    "guard": lambda: TrustOptions(execution="guard"),
    "program": lambda: TrustOptions(execution="program"),
    "codecost": lambda: TrustOptions(execution="llm", send_by_code=True, aggregate_by_code=True),
}
AGENT_MODES = (*MODES, "naive")
CODE_MODES = {"gt-naive": "GT-Naive", "gt-psc": "GT-PSC", "gt-dsl": "GT-DSL"}
ALL_MODES = (*AGENT_MODES, *CODE_MODES)
DEFAULT_MODES = "baseline,bind,guard,program,codecost"
# paired value of the same run differs from the estimate by more than this -> not exact
EXACT_TOL = 1e-9

# backwards compatible name
record_for = task_record


def supported(mode: str, task: str) -> bool:
    if mode in ("program", "gt-dsl"):
        return task in PROGRAMS
    return task in TASKS


def make_framework(mode: str, cfg: ModelConfig):
    if mode == "naive":
        return NaiveFramework(cfg)
    return TrustedPSCFramework(cfg, MODES[mode]())


def run_code(mode: str, rec: TaskRecord, eps: float, rng: np.random.Generator) -> RunResult:
    """One run of a code-only reference, as a :class:`RunResult`."""
    t0 = time.perf_counter()
    g = rec.graph()
    if mode == "gt-naive":
        est, split, gs, d_hat, extra = gt_naive(g, rec.task, eps, rng), naive_budget(eps).as_tuple(), None, None, {}
    elif mode == "gt-psc":
        tr = gt_psc(g, rec.task, eps, rng, return_trace=True, mechanism=DEFAULT_MECHANISM)
        est, split, gs, d_hat, extra = tr.result, tr.split.as_tuple(), tr.sensitivity, tr.d_hat_max, {}
    else:
        tr = gt_dsl(g, rec.task, eps, rng, mechanism=DEFAULT_MECHANISM)
        est, split, gs, d_hat = tr.estimate, tr.split, tr.gs, tr.d_hat_max
        extra = {"program": PROGRAMS[rec.task].parse().text()}
    return RunResult(
        method=CODE_MODES[mode], dataset=rec.dataset, task=rec.task, eps=eps, estimate=float(est), truth=rec.answer,
        split=tuple(split), sensitivity=gs, d_hat_max=d_hat, noisy_edges=None, llm_calls=0, parse_failures=0,
        elapsed=time.perf_counter() - t0, extra={"code": True, **extra},
    )


def planned_calls(mode: str, task: str, n: int, runs: int) -> int:
    if mode in CODE_MODES:
        return 0
    if mode == "naive":
        return 2 * runs  # task selection + answer
    o = MODES[mode]()
    msgs = get_algorithm(task).needs_messages if task in TASKS else False
    per = calls_per_run(msgs, n, o.execution, o.send_by_code, o.aggregate_by_code, design_calls=0)
    return per["total"] * runs + (o.max_design_iterations if o.execution == "program" else 0)


def summarize(ds: str, task: str, mode: str, method: str, rec: TaskRecord, results: list[RunResult], dicts: list[dict]) -> dict:
    n = rec.vertex_num
    ok = [r for r in results if not r.extra.get("rejected")]
    ok_d = [d for d in dicts if not d["extra"].get("rejected")]
    re_ = [relative_error(r.estimate, r.truth, n) for r in ok]
    v = validation_summary(ok, n) if ok and mode not in CODE_MODES else {}
    trust = [r.extra["trust"] for r in ok if "trust" in r.extra]
    ivs = [iv for iv in (report_interval(r.to_dict()) for r in ok) if iv]
    row = {
        "dataset": ds, "task": task, "mode": mode, "method": method, "runs": len(ok), "rejected": len(results) - len(ok),
        "relative_error": float(np.mean(re_)) if re_ else math.nan,
        "rule_relative_error": v.get("rule_relative_error"), "llm_error": v.get("delta_signed"),
        "exec_exact": v.get("exec_exact"), "node_e2e_acc": v.get("node_e2e_acc"), "aggregate_acc": v.get("aggregate_acc"),
        "llm_calls": float(np.mean([r.llm_calls for r in ok])) if ok else None,
        "node_llm_calls": float(np.mean([r.extra.get("node_llm_calls", 0) for r in ok])) if ok else None,
        "guard_fallbacks": sum(t["guard_fallbacks"] for t in trust) if trust else None,
        "rejected_messages": sum(t["messages_rejected"] for t in trust) if trust else None,
        "violations": sum(len(t["violations"]) for t in trust) if trust else None,
        "ci_covers_truth": float(np.mean([iv["covers_truth"] for iv in ivs])) if ivs else None,
    }
    if mode == "program" and ok_d:
        gt_re = [relative_error(d["paired_gt_dsl"]["estimate"], d["truth"], n) for d in ok_d]
        diffs = [a - b for a, b in zip(re_, gt_re)]
        exact = [abs(d["estimate"] - d["paired_gt_dsl"]["estimate"]) <= EXACT_TOL * max(1.0, abs(d["truth"])) for d in ok_d]
        design = next((d["extra"]["trust"].get("design") for d in ok_d if d["extra"]["trust"].get("design")), None)
        row.update(
            gt_dsl_relative_error=float(np.mean(gt_re)), design_error=float(np.mean(diffs)),
            design_error_se=float(np.std(diffs, ddof=1) / math.sqrt(len(diffs))) if len(diffs) > 1 else None,
            design_exact=float(np.mean(exact)), gs_ratio=finite_mean(d.get("design_gs_ratio") for d in ok_d),
            split_match=float(np.mean([list(d["split"]) == list(d["paired_gt_dsl"]["split"]) for d in ok_d])),
            program=(design or {}).get("program", "").replace("\n", " ; ") if design else "(library)",
            design_iterations=(design or {}).get("iterations"),
        )
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", default="CU")
    ap.add_argument("--tasks", default="degree,3-star,triangle,4-star")
    ap.add_argument("--modes", default=DEFAULT_MODES, help=f"comma separated subset of {','.join(ALL_MODES)}")
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--gt-runs", type=int, default=None,
                    help="runs of the code-only modes (gt-*), default --runs; e.g. 1000 as in the paper")
    ap.add_argument("--eps", type=float, default=2.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--data", default=str(DATA_DIR))
    ap.add_argument("--provider", default="mock", choices=PROVIDERS)
    ap.add_argument("--profile", default=None)
    ap.add_argument("--config", default=None)
    ap.add_argument("--node-model", default=None)
    ap.add_argument("--curator-model", default=None)
    ap.add_argument("--mock-error-rate", type=float, default=0.0)
    ap.add_argument("--dry-run", action="store_true", help="print the planned model calls and exit")
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    if args.provider == "mock":
        cfg = ModelConfig(mock_error_rate=args.mock_error_rate)
    else:
        cfg = ModelConfig.from_env(provider=args.provider, config_path=args.config, profile=args.profile,
                                   node_model=args.node_model, curator_model=args.curator_model)
    datasets, tasks, modes = args.datasets.split(","), args.tasks.split(","), args.modes.split(",")
    unknown = [m for m in modes if m not in ALL_MODES]
    if unknown:
        ap.error(f"unknown mode(s) {unknown}; choose from {', '.join(ALL_MODES)}")
    loaded = {ds: load_dataset(args.data, ds) for ds in datasets}
    cells = [(ds, t, m) for ds in datasets for t in tasks for m in modes if supported(m, t)]
    planned = sum(planned_calls(m, t, loaded[ds]["degree"].vertex_num, args.runs) for ds, t, m in cells)
    print(f"{len(cells)} cells x {args.runs} runs, at most {planned} model calls ({args.provider})")
    if args.dry_run:
        return

    gt_runs = args.gt_runs if args.gt_runs is not None else args.runs
    out = out_dir("execution", args.tag, "execution")
    write_manifest(out, {**vars(args), "planned_calls": planned})

    async def run_all() -> list[dict]:
        rows = []
        with llm_progress(planned) as bar:
            for c, (ds, task, mode) in enumerate(cells, 1):
                rec = task_record(loaded[ds], ds, task)
                fw = None if mode in CODE_MODES else make_framework(mode, cfg)
                method = CODE_MODES.get(mode) or ("DSL" if mode == "program" else fw.name)
                results: list[RunResult] = []
                dicts: list[dict] = []
                n_runs = gt_runs if fw is None else args.runs
                t0 = time.perf_counter()
                for i in range(n_runs):
                    bar.set_description(f"cell {c}/{len(cells)} {ds} {task} {method} run {i + 1}/{n_runs}", refresh=False)
                    if fw is None:
                        res = run_code(mode, rec, args.eps, run_rng(args.seed, i))
                    else:
                        res = await fw.run(rec, args.eps, rng=run_rng(args.seed, i))
                    d = res.to_dict()
                    d["mode"], d["run"] = mode, i
                    if mode == "program":
                        gt = gt_dsl(rec.graph(), task, args.eps, run_rng(args.seed, i), mechanism=DEFAULT_MECHANISM)
                        d["paired_gt_dsl"] = gt.to_dict()
                        d["design_gs_ratio"] = None if res.extra.get("rejected") else gs_ratio(res.sensitivity, gt.gs)
                    results.append(res)
                    dicts.append(d)
                    append_jsonl(d, out / "runs.jsonl")
                row = summarize(ds, task, mode, method, rec, results, dicts)
                rows.append(row)
                extra = f", design_error {row['design_error']:.4f}" if row.get("design_error") is not None else ""
                bar.write(f"[{c}/{len(cells)}] {ds} {task} {method}: RE {row['relative_error']:.4f} over {row['runs']} runs"
                          f" ({row['rejected']} rejected){extra}, {time.perf_counter() - t0:.1f}s", file=bar.fp)
        return rows

    rows = asyncio.run(run_all())
    write_json({"settings": vars(args), "rows": rows}, out / "summary.json")
    cmp_cols = ["dataset", "task", "method", "runs", "relative_error", "rule_relative_error", "llm_error", "llm_calls", "node_llm_calls"]
    dsl_cols = ["dataset", "task", "runs", "rejected", "relative_error", "gt_dsl_relative_error", "design_error",
                "design_error_se", "design_exact", "gs_ratio", "split_match", "design_iterations", "program"]
    detail_cols = ["dataset", "task", "mode", "runs", "relative_error", "rule_relative_error", "exec_exact", "node_e2e_acc",
                   "aggregate_acc", "llm_calls", "node_llm_calls", "guard_fallbacks", "rejected_messages", "violations",
                   "ci_covers_truth"]
    dsl_rows = [r for r in rows if r["mode"] == "program"]
    md = [
        "# P4 methods and execution modes on identical noise", "",
        f"provider = {cfg.provider}, node = {cfg.node_model}, curator = {cfg.curator_model}, mock error rate = {args.mock_error_rate}, "
        f"ε = {args.eps}, {args.runs} runs (noise of run i: seed [{args.seed}, i]). Out-of-library tasks: {', '.join(OUT_OF_LIBRARY)}.", "",
        "## Goal 1: methods", "",
        "`rule_relative_error`: the paired code value on the same noise (GT-Naive for Naive, GT-PSC for PSC, the program "
        "itself for DSL); `llm_error` = relative_error − rule_relative_error (execution error added by the LLM). "
        f"GT-* rows are the code-only references over {gt_runs} runs; GT-Naive / GT-PSC draw the RR noise in another "
        "order than the agents (equal in distribution, not run by run), GT-DSL in the same order as `program`.", "",
        markdown_table(rows, cmp_cols), "",
    ]
    if dsl_rows:
        md += [
            "## Goal 2: error added by the DSL designer (paired with GT-DSL on the same noise)", "",
            "`design_error` = relative_error − gt_dsl_relative_error; `design_exact`: share of runs whose estimate equals "
            "GT-DSL; `gs_ratio`: GS of the designed program / GS of the reference program at the run's d̂max.", "",
            markdown_table(dsl_rows, dsl_cols), "",
        ]
    md += ["## Details", "", markdown_table(rows, detail_cols), ""]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    print(f"results in {out}")


if __name__ == "__main__":
    main()
