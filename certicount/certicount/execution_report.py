"""Summaries and tables of ``scripts/run_execution_compare.py`` (shared with the rebuild script).

Metric conventions (fixed 2026-11):

* ``llm_error`` = ``relative_error − rule_relative_error`` where the rule value is
  the paired code execution of the *same* algorithm on the same noise. For DSL
  runs that is the program itself (no LLM executes anything), so it is 0; a
  design that differs from the library algorithm is measured by ``design_error``
  against GT-DSL, not as an execution error.
* ``noise_ratio`` = final noise scale ``|c| · GS / ε3`` of the design over the
  reference's (``c``: slope of the aggregate in ``total``); ``gs_ratio`` ignores
  ``c`` and ``ε3`` and is kept for the record only.
* ``design_exact`` counts runs whose estimate equals GT-DSL, excluding runs where
  both are clamped to 0 (``both_zero``) -- those say nothing about the design.
"""

from __future__ import annotations

import math
from typing import Mapping, Sequence

import numpy as np

from psc.experiments import validation_summary
from psc.framework import RunResult
from psc.ground_truth import relative_error

from .artifacts import markdown_table
from .dsl.quality import finite_mean
from .evaluation import report_interval

EXACT_TOL = 1e-9
CODE_METHODS = ("GT-Naive", "GT-PSC", "GT-DSL", "GT-Tuned")


def _se(values: Sequence[float]) -> float | None:
    return float(np.std(values, ddof=1) / math.sqrt(len(values))) if len(values) > 1 else None


def _ok(d: Mapping) -> bool:
    return not d["extra"].get("rejected") and d.get("estimate") is not None


def summarize(ds: str, task: str, mode: str, method: str, n: int, eps: float, results: Sequence[RunResult],
              dicts: Sequence[dict], code: bool) -> dict:
    ok = [r for r, d in zip(results, dicts) if _ok(d)]
    ok_d = [d for d in dicts if _ok(d)]
    re_ = [relative_error(r.estimate, r.truth, n) for r in ok]
    v = validation_summary(ok, n) if ok and not code else {}
    trust = [r.extra["trust"] for r in ok if "trust" in r.extra]
    ivs = [iv for iv in (report_interval(r.to_dict()) for r in ok) if iv]
    row = {
        "dataset": ds, "task": task, "eps": eps, "mode": mode, "method": method, "runs": len(ok),
        "rejected": len(results) - len(ok),
        "relative_error": float(np.mean(re_)) if re_ else math.nan, "se": _se(re_),
        "median_relative_error": float(np.median(re_)) if re_ else math.nan,
        "rule_relative_error": v.get("rule_relative_error"), "llm_error": v.get("delta_signed"),
        "exec_exact": v.get("exec_exact"), "node_e2e_acc": v.get("node_e2e_acc"), "aggregate_acc": v.get("aggregate_acc"),
        "llm_calls": float(np.mean([r.llm_calls for r in results])) if results else None,
        "llm_calls_total": int(sum(r.llm_calls for r in results)),
        "node_llm_calls": float(np.mean([r.extra.get("node_llm_calls", 0) for r in ok])) if ok else None,
        "rejected_messages": sum(t["messages_rejected"] for t in trust) if trust else None,
        "violations": sum(len(t["violations"]) for t in trust) if trust else None,
        "ci_covers_truth": float(np.mean([iv["covers_truth"] for iv in ivs])) if ivs else None,
    }
    if mode == "program":
        design = next((d["extra"].get("trust", {}).get("design") for d in dicts
                       if d["extra"].get("trust", {}).get("design")), None) or {}
        row.update(
            design_mode=design.get("mode", "exact"), design_restarts=design.get("restarts", 1),
            design_iterations=design.get("iterations"),
            program=(design.get("program") or "-").replace("\n", " ; ") if design else "(library)",
            search_score=(design.get("score") or {}).get("score"),
        )
    if mode == "program" and ok_d:
        gt_re = [relative_error(d["paired_gt_dsl"]["estimate"], d["truth"], n) for d in ok_d]
        diffs = [a - b for a, b in zip(re_, gt_re)]
        both_zero = [d["estimate"] == 0 and d["paired_gt_dsl"]["estimate"] == 0 for d in ok_d]
        exact = [abs(d["estimate"] - d["paired_gt_dsl"]["estimate"]) <= EXACT_TOL * max(1.0, abs(d["truth"]))
                 for d, z in zip(ok_d, both_zero) if not z]
        row.update(
            gt_dsl_relative_error=float(np.mean(gt_re)), design_error=float(np.mean(diffs)), design_error_se=_se(diffs),
            design_exact=float(np.mean(exact)) if exact else None, both_zero=float(np.mean(both_zero)),
            noise_ratio=finite_mean(d.get("design_noise_ratio") for d in ok_d),
            gs_ratio=finite_mean(d.get("design_gs_ratio") for d in ok_d),
            split_match=float(np.mean([list(d["split"]) == list(d["paired_gt_dsl"]["split"]) for d in ok_d])),
        )
    return row


def pivot(rows: Sequence[dict]) -> tuple[list[dict], list[str]]:
    """One line per (dataset, task, ε), one column per method: mean relative error."""
    methods: list[str] = []
    for r in rows:
        if r["method"] not in methods:
            methods.append(r["method"])
    out: dict[tuple, dict] = {}
    for r in rows:
        key = (r["dataset"], r["task"], r["eps"])
        line = out.setdefault(key, {"dataset": key[0], "task": key[1], "eps": key[2]})
        line[r["method"]] = r["relative_error"] if r["runs"] else None
    return list(out.values()), ["dataset", "task", "eps", *methods]


def markdown(rows: Sequence[dict], header: str, gt_runs: int | None) -> str:
    cmp_cols = ["dataset", "task", "eps", "method", "runs", "rejected", "relative_error", "se", "median_relative_error",
                "rule_relative_error", "llm_error", "llm_calls", "node_llm_calls"]
    dsl_cols = ["dataset", "task", "eps", "runs", "rejected", "relative_error", "gt_dsl_relative_error", "design_error",
                "design_error_se", "design_exact", "both_zero", "noise_ratio", "split_match", "design_mode",
                "design_restarts", "design_iterations", "llm_calls_total", "search_score", "program"]
    detail_cols = ["dataset", "task", "eps", "mode", "runs", "relative_error", "rule_relative_error", "exec_exact",
                   "node_e2e_acc", "aggregate_acc", "llm_calls", "node_llm_calls",
                   "rejected_messages", "violations", "ci_covers_truth"]
    dsl_rows = [r for r in rows if r["mode"] == "program"]
    piv, piv_cols = pivot(rows)
    md = [
        "# P4 methods and execution modes on identical noise", "", header, "",
        "## Mean relative error by method", "",
        "Lower is better (|estimate − truth| / truth, averaged over runs).", "",
        markdown_table(piv, piv_cols), "",
        "## Goal 1: methods", "",
        "`rule_relative_error`: the paired code value on the same noise (GT-Naive for Naive, GT-PSC for PSC, the program "
        "itself for DSL); `llm_error` = relative_error − rule_relative_error (execution error added by the LLM; 0 for DSL "
        "by construction). `se`: standard error of the mean. "
        f"GT-* rows are code-only references over {gt_runs if gt_runs is not None else 'the same number of'} runs; "
        "GT-Naive / GT-PSC draw the RR noise in another order than the agents (equal in distribution, not run by run), "
        "GT-DSL / GT-Tuned in the same order as `program`. GT-Tuned: the library algorithm with its threshold factor "
        "and budget split grid-tuned on public synthetic graphs (same scorer as the DSL search).", "",
        markdown_table(rows, cmp_cols), "",
    ]
    if dsl_rows:
        md += [
            "## Goal 2: the DSL design (paired with GT-DSL on the same noise)", "",
            "`design_error` = relative_error − gt_dsl_relative_error (negative: better than the library algorithm); "
            "`design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs (both clamped to 0); "
            "`noise_ratio`: final noise |c|·GS/ε3 of the design over the reference (c: aggregate slope); "
            "`search_score`: simulated error on public synthetic graphs (search mode).", "",
            markdown_table(dsl_rows, dsl_cols), "",
        ]
    md += ["## Details", "", markdown_table(rows, detail_cols), ""]
    return "\n".join(md)
