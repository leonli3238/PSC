"""Evaluation protocol that separates mechanism error from execution error (research content 1).

* **Mechanism error** -- the error of the algorithm executed exactly in code
  (GT-Naive / GT-PSC, model independent); per run it is the relative error of
  the paired rule value ``extra.validation.rule_estimate`` computed by the
  reproduction on the *same* noise as the LLM run.
* **Execution error** -- the difference between the LLM result and that paired
  rule value; split into the part that increases the error (``llm_harm``) and
  the part that lowers it by luck (``lucky_gain``), see
  :func:`psc.experiments.validation_summary`.

In addition the curator can attach a confidence interval to its estimate from
public values only (GS, ε3, n and the aggregation rule) -- post-processing that
costs no budget. An interval covering 0 flags an estimate that cannot be told
apart from 0. The interval covers the Laplace noise only: the bias of the RR
noisy graph and of the projection is not in it, so ``covers_truth`` is a
diagnostic, not a guarantee.
"""

from __future__ import annotations

import json
import math
from dataclasses import fields
from pathlib import Path
from statistics import NormalDist
from typing import Iterable, Mapping, Sequence

import numpy as np

from psc.experiments import validation_summary
from psc.framework import RunResult
from psc.ground_truth import relative_error

_RUN_FIELDS = {f.name for f in fields(RunResult)}


def load_runs(path: str | Path) -> list[dict]:
    """Rows of ``runs.jsonl`` (or a directory holding it)."""
    p = Path(path)
    if p.is_dir():
        p = p / "runs.jsonl"
    with p.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def as_run_result(row: Mapping) -> RunResult:
    return RunResult(**{k: row[k] for k in _RUN_FIELDS if k in row})


def failed(row: Mapping) -> bool:
    """Runs whose model calls ran out of retries (their estimate is a placeholder 0)."""
    return any(e.get("kind") == "call_failed" for e in row.get("extra", {}).get("errors", []))


def aggregation_factor(task: str, n: int) -> float:
    """``estimate = factor * sum(reports)`` before the clamp at 0."""
    if task == "degree":
        return 1.0 / n
    if task == "triangle":
        return 1.0 / 3.0
    return 1.0


def report_interval(row: Mapping, alpha: float = 0.05) -> dict | None:
    """Normal-approximation interval of a PSC estimate from public values.

    The noisy total is ``sum(c_i) + sum(Lap(b_i))`` with ``b_i = GS_i / ε3``;
    its noise variance is ``2 sum(b_i^2)``. Only the published reports, GS, ε3,
    n and the aggregation rule are used (no budget). ``None`` for Naive runs.
    """
    trace = row.get("extra", {}).get("mechanism_trace")
    eps3 = row["split"][2]
    if not trace or not eps3 or row.get("sensitivity") is None:
        return None
    reports = trace["noisy_counts"]
    n = len(reports)
    scales = trace.get("node_laplace_scales") or [s / eps3 for s in trace.get("node_sensitivities") or []]
    if not scales:
        scales = [row["sensitivity"] / eps3] * n
    sd = math.sqrt(2.0 * sum(b * b for b in scales))
    f = aggregation_factor(row["task"], n)
    centre = f * float(sum(reports))
    half = NormalDist().inv_cdf(1 - alpha / 2) * f * sd
    lo, hi = centre - half, centre + half
    truth = row["truth"]
    return {
        "centre": centre, "lo": lo, "hi": hi, "half_width": half,
        "covers_zero": lo <= 0 <= hi, "covers_truth": lo <= truth <= hi,
        "half_width_over_truth": half / max(abs(truth), 1e-12),
    }


def decompose(rows: Sequence[Mapping], n: int, drop_failed: bool = True) -> dict:
    """Mechanism / execution decomposition of one cell (dataset × task × method)."""
    use = [r for r in rows if not (drop_failed and failed(r))]
    if not use:
        return {}
    res = [as_run_result(r) for r in use]
    re_llm = np.array([relative_error(r.estimate, r.truth, n) for r in res])
    out = {
        "runs": len(use), "dropped_failed": len(rows) - len(use),
        "relative_error": float(re_llm.mean()),
        "se_relative_error": float(re_llm.std(ddof=1) / math.sqrt(len(re_llm))) if len(re_llm) > 1 else None,
        **validation_summary(res, n),
    }
    ivs = [iv for iv in (report_interval(r) for r in use) if iv is not None]
    if ivs:
        out.update(
            ci_covers_zero=float(np.mean([iv["covers_zero"] for iv in ivs])),
            ci_covers_truth=float(np.mean([iv["covers_truth"] for iv in ivs])),
            ci_half_width_over_truth=float(np.median([iv["half_width_over_truth"] for iv in ivs])),
        )
    return out


def cells(rows: Iterable[Mapping]) -> dict[tuple[str, str, str], list[dict]]:
    out: dict[tuple[str, str, str], list[dict]] = {}
    for r in rows:
        out.setdefault((r["dataset"], r["task"], r["method"]), []).append(dict(r))
    return out


def find_run_dirs(base: str | Path, include_archive: bool = False) -> list[Path]:
    dirs = sorted({p.parent for p in Path(base).rglob("runs.jsonl")})
    return [d for d in dirs if include_archive or "archive" not in d.parts and "_smoke" not in d.parts]
