"""Experiment helpers: paper reference numbers, table formatting, runners."""

from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Awaitable, Callable, Sequence

import numpy as np

from .framework import NaiveFramework, PSCFramework, RunResult
from .graph import TASKS, TaskRecord, load_dataset
from .ground_truth import average_relative_error, gt_naive, gt_psc, relative_error
from .models import ModelConfig

DATASETS: tuple[str, ...] = ("CU", "Do", "ML", "CS", "EE", "PM")

# Table 2 of the paper (average relative error, eps = 2)
PAPER_TABLE2: dict[str, dict[str, list[float]]] = {
    "triangle": {
        "GT-Naive": [1.4545, 1.8761, 0.5655, 7.0165, 1.9941, 12.0592],
        "Naive": [9.1228, 12.9684, 7.4197, 51.1905, 11.4162, 32.7652],
        "GT-PSC": [0.9612, 0.8162, 0.3877, 1.7108, 0.2803, 1.0863],
        "PSC": [0.7939, 0.8628, 0.3240, 2.9922, 0.2914, 0.4786],
    },
    "degree": {
        "GT-Naive": [1.0707, 1.1791, 1.1351, 3.2757, 1.7026, 5.7853],
        "Naive": [1.1020, 1.3935, 1.8939, 4.1415, 2.5564, 5.3465],
        "GT-PSC": [0.0187, 0.0143, 0.0098, 0.0202, 0.0052, 0.0030],
        "PSC": [0.0174, 0.0162, 0.0110, 0.0259, 0.0070, 0.0666],
    },
    "2-star": {
        "GT-Naive": [3.6030, 3.1858, 1.9165, 13.0441, 4.4800, 9.9490],
        "Naive": [10.4517, 7.9931, 7.0450, 48.4216, 24.5390, 14.3962],
        "GT-PSC": [0.1062, 0.0585, 0.0444, 0.1210, 0.0295, 0.0284],
        "PSC": [0.0929, 0.0679, 0.0563, 0.0800, 0.0349, 0.3508],
    },
    "3-star": {
        "GT-Naive": [10.1186, 6.7480, 2.0073, 29.8754, 7.4755, 5.0099],
        "Naive": [109.3320, 46.9049, 9.4129, 159.4328, 3.1083, 33.7694],
        "GT-PSC": [0.8035, 0.3434, 0.2077, 0.5410, 0.1647, 0.1290],
        "PSC": [0.7325, 0.3816, 0.1703, 0.4711, 0.2445, 0.6904],
    },
}

# Table 3 of the paper: (GT-PSC, PSC, GT-PSC-B, PSC-B)
PAPER_TABLE3: dict[tuple[str, str], tuple[float, float, float, float]] = {
    ("triangle", "CU"): (0.9612, 0.7939, 1.4714, 1.8654),
    ("triangle", "Do"): (0.8162, 0.8628, 1.2985, 2.4463),
    ("2-star", "CU"): (0.1062, 0.0929, 0.4487, 0.4390),
    ("2-star", "Do"): (0.0585, 0.0679, 0.2580, 0.2167),
    ("3-star", "CU"): (0.8035, 0.7325, 4.6370, 4.6034),
    ("3-star", "Do"): (0.3434, 0.3816, 2.4373, 2.2909),
}


# Table 4 of the paper (Exp5, no DP): RAW / REFINED / PSC without noise
PAPER_TABLE4: dict[str, dict[str, list[float]]] = {
    "triangle": {
        "RAW": [0.2667, 0.6316, 3.6304, 0.2762, 2.2499, 2.5283],
        "REFINED": [0.2683, 0.3193, 0.6820, 0.3929, 0.8121, 0.8503],
        "PSC-noDP": [0.0035, 0.0063, 0.0128, 0.0048, 0.0003, 0.0094],
    },
    "degree": {
        "RAW": [0.0056, 0.0101, 0.1559, 0.0685, 0.2560, 0.2391],
        "REFINED": [0.0117, 0.0094, 0.0177, 0.0040, 0.1056, 1.6781],
        "PSC-noDP": [0.0011, 0.0075, 0.0144, 0.0013, 0.0031, 0.0599],
    },
    "2-star": {
        "RAW": [0.0931, 0.2414, 1.2063, 0.2570, 0.5427, 0.9519],
        "REFINED": [0.0000, 0.0026, 0.0014, 0.0059, 0.0941, 0.4254],
        "PSC-noDP": [0.0000, 0.0000, 0.0000, 0.0013, 0.0173, 0.3136],
    },
    "3-star": {
        "RAW": [0.3518, 0.4480, 1.1728, 0.3513, 1.0313, 1.2114],
        "REFINED": [0.0000, 0.0099, 1.6500, 0.0000, 0.0445, 0.5276],
        "PSC-noDP": [0.0000, 0.0000, 0.0000, 0.0000, 0.0013, 0.6838],
    },
}

# Table 5 of the paper (Exp6): Naive + REFINED prompt on the noisy graph
PAPER_TABLE5_REFINED: dict[str, list[float]] = {
    "triangle": [21.4772, 13.0442, 27.9884, 172.3929, 90.0144, 119.3614],
    "degree": [1.3645, 1.6490, 1.9101, 4.2875, 1.7669, 1.8404],
    "2-star": [4.3050, 5.7166, 7.7655, 20.7292, 10.9272, 23.6128],
    "3-star": [13.5125, 7.7468, 15.8053, 63.4106, 10.2418, 0.6741],
}

NON_DP_METHODS: tuple[str, ...] = ("RAW", "REFINED", "PSC-noDP")
ALL_METHODS: tuple[str, ...] = ("Naive", "Naive+REFINED", "PSC", "PSC-B") + NON_DP_METHODS


def paper_value(task: str, method: str, dataset: str) -> float | None:
    try:
        i = DATASETS.index(dataset)
        if method in PAPER_TABLE2.get(task, {}):
            return PAPER_TABLE2[task][method][i]
        if method in PAPER_TABLE4.get(task, {}):
            return PAPER_TABLE4[task][method][i]
        if method == "Naive+REFINED":
            return PAPER_TABLE5_REFINED[task][i]
    except (KeyError, ValueError, IndexError):
        pass
    return None


def make_framework(method: str, cfg: ModelConfig, seed: int, r1: float = 0.5, r2: float = 0.2):
    """Instantiate the agent-based method by its paper name."""
    if method == "Naive":
        return NaiveFramework(cfg, seed=seed)
    if method == "Naive+REFINED":
        return NaiveFramework(cfg, seed=seed, prompt_style="refined")
    if method == "PSC":
        return PSCFramework(cfg, seed=seed, gs_optimization=True, r1=r1, r2=r2)
    if method == "PSC-B":
        return PSCFramework(cfg, seed=seed, gs_optimization=False, r1=r1, r2=r2)
    if method == "PSC-noDP":
        return PSCFramework(cfg, seed=seed, dp=False)
    if method in ("RAW", "REFINED"):
        from .baselines import SingleLLMBaseline

        return SingleLLMBaseline(cfg, style=method.lower(), seed=seed)
    raise ValueError(f"unknown method {method!r}; choose from {ALL_METHODS}")


# ---------------------------------------------------------------------------
# Ground truth runner
# ---------------------------------------------------------------------------


def run_ground_truth(
    data_dir: str | Path,
    datasets: Sequence[str],
    tasks: Sequence[str],
    eps_values: Sequence[float],
    runs: int,
    seed: int = 0,
    methods: Sequence[str] = ("GT-Naive", "GT-PSC", "GT-PSC-B"),
    r1: float = 0.5,
    r2: float = 0.2,
    log: Callable[[str], None] = print,
) -> list[dict]:
    rows: list[dict] = []
    for ds in datasets:
        recs = load_dataset(data_dir, ds)
        for task in tasks:
            g = recs[task].graph()
            for eps in eps_values:
                t0 = time.perf_counter()
                for method in methods:
                    if method == "GT-Naive":
                        re, ests = average_relative_error(gt_naive, g, task, eps, runs, seed)
                    elif method == "GT-PSC":
                        re, ests = average_relative_error(gt_psc, g, task, eps, runs, seed, r1=r1, r2=r2)
                    elif method == "GT-PSC-B":
                        re, ests = average_relative_error(
                            gt_psc, g, task, eps, runs, seed, gs_optimization=False, r1=r1, r2=r2,
                        )
                    else:
                        raise ValueError(method)
                    rows.append(
                        {
                            "method": method,
                            "dataset": ds,
                            "task": task,
                            "eps": eps,
                            "runs": runs,
                            "truth": g.ground_truth(task),
                            "mean_estimate": float(np.mean(ests)),
                            "std_estimate": float(np.std(ests)),
                            "avg_relative_error": re,
                            "paper": paper_value(task, method, ds) if eps == 2.0 else None,
                            "r1": r1,
                            "r2": r2,
                        },
                    )
                log(f"[GT] {ds:>3} {task:<9} eps={eps:<4} " + "  ".join(
                    f"{r['method']}={r['avg_relative_error']:.4f}" for r in rows[-len(methods):]
                ) + f"  ({time.perf_counter() - t0:.1f}s)")
    return rows


# ---------------------------------------------------------------------------
# Agent runner
# ---------------------------------------------------------------------------


async def run_agent_method(
    framework,
    record: TaskRecord,
    eps: float,
    runs: int,
    log: Callable[[str], None] | None = None,
) -> tuple[float, list[RunResult]]:
    results: list[RunResult] = []
    for i in range(runs):
        res = await framework.run(record, eps)
        results.append(res)
        if log:
            v = res.extra.get("validation", {})
            node_acc = f" node_acc={v['e2e_exact']}/{v['nodes']}" if "nodes" in v else ""
            rule_est = f" rule_est={v['rule_estimate']:.4f}" if "rule_estimate" in v else ""
            log(
                f"    run {i + 1:>2}/{runs} {framework.name:<6} est={res.estimate:12.4f}{rule_est} "
                f"truth={res.truth:10.4f} RE={relative_error(res.estimate, res.truth, record.vertex_num):.4f} "
                f"calls={res.llm_calls} fail={res.parse_failures}{node_acc} {res.elapsed:.1f}s",
            )
    re = float(np.mean([relative_error(r.estimate, r.truth, record.vertex_num) for r in results]))
    return re, results


def validation_summary(results: Sequence[RunResult], n: int) -> dict:
    """Aggregate the per-run LLM-vs-rule checks of :func:`psc.framework._validate_psc`."""
    vals = [r.extra["validation"] for r in results if "validation" in r.extra]
    if not vals:
        return {}
    out: dict = {"task_acc": float(np.mean([v["task_correct"] for v in vals]))}
    rule_res = [relative_error(v["rule_estimate"], r.truth, n) for v, r in zip(vals, results)]
    llm_res = [relative_error(r.estimate, r.truth, n) for r in results]
    out["rule_relative_error"] = float(np.mean(rule_res))
    # Delta of Table 6: |RE_LLM - RE_GT|, here with GT paired on the same noise
    out["delta"] = abs(float(np.mean(llm_res)) - out["rule_relative_error"])
    if "nodes" in vals[0]:
        nodes = sum(v["nodes"] for v in vals)
        sent = sum(v["send_checked"] for v in vals)
        out["node_samples"] = nodes
        out["node_update_acc"] = sum(v["update_exact"] for v in vals) / nodes
        out["node_e2e_acc"] = sum(v["e2e_exact"] for v in vals) / nodes
        out["send_acc"] = sum(v["send_exact"] for v in vals) / sent if sent else None
        out["count_rel_diff"] = float(np.mean([v["count_rel_diff"] for v in vals]))
        out["aggregate_acc"] = float(np.mean([v["aggregate_exact"] for v in vals]))
    return out


async def run_agent_experiment(
    data_dir: str | Path,
    cfg: ModelConfig,
    datasets: Sequence[str],
    tasks: Sequence[str],
    eps_values: Sequence[float],
    runs: int,
    methods: Sequence[str] = ("Naive", "PSC"),
    seed: int = 0,
    r1: float = 0.5,
    r2: float = 0.2,
    log: Callable[[str], None] = print,
    verbose: bool = False,
) -> tuple[list[dict], list[dict]]:
    """Return ``(summary rows, per-run rows)``."""
    summary: list[dict] = []
    per_run: list[dict] = []
    for ds in datasets:
        recs = load_dataset(data_dir, ds)
        for task in tasks:
            rec = recs[task]
            for eps in eps_values:
                line = f"[Agents/{cfg.provider}] {ds:>3} {task:<9} eps={eps:<4}"
                for method in methods:
                    fw = make_framework(method, cfg, seed, r1, r2)
                    # non-DP methods are deterministic up to LLM behaviour
                    n_runs = runs if method not in NON_DP_METHODS or cfg.provider != "mock" else 1
                    re, results = await run_agent_method(fw, rec, eps, n_runs, log if verbose else None)
                    per_run.extend(r.to_dict() for r in results)
                    summary.append(
                        {
                            "method": method,
                            "dataset": ds,
                            "task": task,
                            "eps": eps if method not in NON_DP_METHODS else None,
                            "runs": n_runs,
                            "truth": rec.answer,
                            "mean_estimate": float(np.mean([r.estimate for r in results])),
                            "avg_relative_error": re,
                            "llm_calls_per_run": float(np.mean([r.llm_calls for r in results])),
                            "parse_failures": int(sum(r.parse_failures for r in results)),
                            "paper": paper_value(task, method, ds) if (eps == 2.0 or method in NON_DP_METHODS) else None,
                            "provider": cfg.provider,
                            "node_model": cfg.node_model,
                            "curator_model": cfg.curator_model,
                            "r1": r1,
                            "r2": r2,
                            **validation_summary(results, rec.vertex_num),
                        },
                    )
                    line += f"  {method}={re:.4f}"
                log(line)
    return summary, per_run


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------


def table2_markdown(rows: list[dict], datasets: Sequence[str], methods: Sequence[str], eps: float = 2.0) -> str:
    """Render a Table-2 style markdown table with the paper's numbers."""
    idx = {(r["method"], r["dataset"], r["task"], r["eps"]): r for r in rows}
    hdr = "| Task | Method | " + " | ".join(datasets) + " | Avg. |"
    sep = "|" + "---|" * (len(datasets) + 3)
    out = [hdr, sep]
    for task in TASKS:
        for method in methods:
            vals = []
            for ds in datasets:
                key_eps = None if method in NON_DP_METHODS else eps
                r = idx.get((method, ds, task, key_eps))
                vals.append(r["avg_relative_error"] if r else None)
            present = [v for v in vals if v is not None]
            if not present:
                continue
            avg = float(np.mean(present))
            out.append(
                f"| {task} | {method} | " + " | ".join("-" if v is None else f"{v:.4f}" for v in vals) + f" | {avg:.4f} |",
            )
            paper = [paper_value(task, method, ds) for ds in datasets]
            if any(p is not None for p in paper):
                pav = float(np.mean([p for p in paper if p is not None]))
                out.append(
                    f"| {task} | *{method} (paper)* | " + " | ".join("-" if p is None else f"*{p:.4f}*" for p in paper) + f" | *{pav:.4f}* |",
                )
    return "\n".join(out)


def generic_markdown(rows: list[dict], columns: Sequence[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for r in rows:
        cells = []
        for c in columns:
            v = r.get(c)
            cells.append(f"{v:.4f}" if isinstance(v, float) else ("-" if v is None else str(v)))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def default_tag(cfg: ModelConfig) -> str:
    """``mock`` or ``<provider>_<node model>[+<curator model>]``, safe as a directory name."""
    if cfg.provider == "mock":
        return "mock"
    models = cfg.node_model if cfg.node_model == cfg.curator_model else f"{cfg.node_model}+{cfg.curator_model}"
    return re.sub(r"[^\w.+-]", "-", f"{cfg.provider}_{models}")


def save_results(out_dir: str | Path, summary, per_run=None, markdown: str | None = None) -> Path:
    """Write ``summary.json`` / ``runs.json`` / ``table.md`` into ``out_dir``
    (``results/<experiment>/<tag>/``) and return the directory."""
    out_dir = Path(out_dir)
    save_json(summary, out_dir / "summary.json")
    if per_run is not None:
        save_json(per_run, out_dir / "runs.json")
    if markdown is not None:
        (out_dir / "table.md").write_text(markdown + "\n", encoding="utf-8")
    return out_dir


def save_json(obj, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=str)


def run_async(coro: Awaitable):
    return asyncio.run(coro)
