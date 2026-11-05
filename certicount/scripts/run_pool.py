"""LLM-designed program pools with degree-first adaptive selection (research content 4, LLM back in the loop).

Phase 1, design (the only phase that may call a model): for every task a pool per designer
  ``hand``    the library program only (no design)
  ``llm``     :func:`certicount.dsl.pool.design_pool` with the curator model (``--provider mock`` offline);
              the model only sees the task, the language and scores on public synthetic graphs
  ``random``  :func:`certicount.dsl.pool.random_design`: random programs of the language through the
              same gates (non-LLM baseline)
Every request to the model, retries included, counts against ``--max-requests``. The pools go to
``pools.json`` (reuse them with ``--pools`` to evaluate again without any model call), every draft with
its gates and scores to ``designs.jsonl``, every model call to ``transcripts.jsonl``.

Phase 2, evaluation (code only): for every dataset x task and run i, with the common random numbers of
``[seed, i]`` (:func:`certicount.dsl.adaptive.run_streams`):
  ``default``         the PSC setting: the library program, bound D, eps1 = r1 eps
  ``<designer>``      the adaptive selection over that designer's pool, from public values only
  ``oracle-<designer>`` the best candidate of the pool on the real graph in that run (ceiling, not private)
  ``GT-TriTR``        reference (alpha = 0, the PSC split, its own streams)
All pools are selected with one scoring of the union of their candidates (a candidate's score does not
depend on the other candidates), so every difference between pools is paired.

    ../.venv/bin/python scripts/run_pool.py --tasks 2-star,3-star,triangle --runs 200 --workers 8 --tag pool_mock
    ../.venv/bin/python scripts/run_pool.py --provider openai --profile glm --curator-model glm-5.2 \\
        --max-requests 20 --tasks 3-star --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import math
import statistics as st
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from psc.events import set_error_sink, set_transcript_sink  # noqa: E402
from psc.experiments import run_rng  # noqa: E402
from psc.dp import split_budget  # noqa: E402
from psc.graph import TASKS, kstar_k, load_dataset  # noqa: E402
from psc.ground_truth import gt_tritr, relative_error  # noqa: E402
from psc.models import PROVIDERS, ModelConfig, create_formatter, create_model  # noqa: E402
from certicount import DATA_DIR  # noqa: E402
from certicount.artifacts import append_jsonl, markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.dsl.adaptive import (  # noqa: E402
    SelectOptions, choose, default_index, execute, pool_space, release_degrees, run_streams, select,
)
from certicount.dsl.lang import parse_program_text  # noqa: E402
from certicount.dsl.library import PROGRAMS  # noqa: E402
from certicount.dsl.pool import (  # noqa: E402
    BudgetedModel, MockPoolModel, PoolOptions, Scorer, design_pool, random_design, task_setting,
)
from certicount.dsl.quality import task_record  # noqa: E402

DESIGNERS = ("llm", "random")


# ---------------------------------------------------------------------------
# Phase 1: design
# ---------------------------------------------------------------------------


def make_model(args):
    if args.provider == "mock":
        return MockPoolModel(), ModelConfig()
    overrides = {k: v for k, v in (("curator_model", args.curator_model), ("temperature", args.temperature),
                                   ("max_retries", args.max_retries)) if v is not None}
    cfg = ModelConfig.from_env(provider=args.provider, config_path=args.config, profile=args.profile, **overrides)
    return create_model(cfg, "curator"), cfg


def design(args, tasks: list[str], opts: PoolOptions, out: Path) -> dict:
    pools: dict[str, dict[str, list[str]]] = {"hand": {t: [PROGRAMS[t].parse().text()] for t in tasks}}
    designers = [d for d in args.designers.split(",") if d]
    summaries = []
    model = fmt = None
    if "llm" in designers:
        inner, cfg = make_model(args)
        model, fmt = BudgetedModel(inner, args.max_requests), create_formatter(cfg)
        set_error_sink(out / "errors.jsonl")
        set_transcript_sink(out / "transcripts.jsonl")
    for task in tasks:
        scorer = Scorer(task, opts)
        for name in designers:
            if name == "llm":
                res = asyncio.run(design_pool(model, fmt, task, opts, scorer))
            elif name == "random":
                res = random_design(task, args.random_programs, args.seed, opts, scorer)
            else:
                raise ValueError(f"unknown designer {name!r}; choose from {DESIGNERS}")
            pools.setdefault(name, {})[task] = [p.text() for p in res.programs]
            d = res.to_dict()
            append_jsonl({"designer": name, **d}, out / "designs.jsonl")
            summaries.append({k: v for k, v in d.items() if k not in ("drafts", "hand_errors", "pool_errors")}
                             | {"designer": name})
            print(f"[design] {task} {name}: proposed {d['proposed']}, certified {d['certified']}, deployed "
                  f"{d['deployed']}; public score {d['hand_score']:.4f} -> {d['pool_score']:.4f} "
                  f"({res.seconds:.0f}s, requests so far {getattr(model, 'requests', 0)})", flush=True)
    return {"pools": pools, "designs": summaries, "requests": getattr(model, "requests", 0) if model else 0}


# ---------------------------------------------------------------------------
# Phase 2: evaluation
# ---------------------------------------------------------------------------


def tritr_reference(g, task: str, eps: float, rng: np.random.Generator) -> float:
    """GT-TriTR (alpha = 0, PSC split); for an out-of-library k-star task the k-star branch of
    :func:`psc.ground_truth.gt_tritr` with the k-star split (per-node bound floor(max(y_i, 0)),
    C(min(d_i, D_i), k) + Lap(C(D_i - 1, k - 1) / eps3)); NaN for other tasks."""
    if task in TASKS:
        return gt_tritr(g, task, eps, rng)
    try:
        k = kstar_k(task)
    except ValueError:
        return math.nan
    split = split_budget(eps, False, True)
    deg = np.array(g.degrees(), dtype=float)
    limits = np.floor(np.maximum(deg + rng.laplace(0.0, 1.0 / split.eps2, size=g.n), 0.0)).astype(int)
    counts = sum(math.comb(min(int(d), int(t)), k) for d, t in zip(deg, limits))
    sens = np.array([math.comb(t - 1, k - 1) if t >= 1 else 0 for t in limits], dtype=float)
    return max(0.0, counts + rng.laplace(0.0, sens / split.eps3).sum())


def run_chunk(job: dict) -> list[dict]:
    rec = task_record(load_dataset(job["data"], job["dataset"]), job["dataset"], job["task"])  # out-of-library: brute force
    g, n, truth, task, eps, seed = rec.graph(), rec.vertex_num, rec.answer, job["task"], job["eps"], job["seed"]
    setting = task_setting(task, eps)
    pools = {name: [parse_program_text(t) for t in texts] for name, texts in job["pools"].items()}
    union, owner = [], {}  # distinct programs over the pools, and the pools of every program
    for name, progs in pools.items():
        for p in progs:
            if p.digest not in owner:
                owner[p.digest] = set()
                union.append(p)
            owner[p.digest].add(name)
    opts = SelectOptions(**job["select"])
    rows = any(p.uses_rows for p in union)
    out = []
    for i in job["runs"]:
        streams = run_streams(n, seed, i, rows)
        rel = release_degrees(g, setting.eps2, streams, setting.degree_class)
        cands = pool_space(union, rel.D, eps, setting.eps2)
        d = default_index(cands, rel.D, setting.eps1_default)
        sel = select(rel, n, eps, cands, union[0], np.random.default_rng([seed, i, 2]), opts, default=d)
        cache: dict = {}
        real = [relative_error(execute(g, c, eps, rel, streams, cache), truth, n) for c in cands]
        row = {"dataset": job["dataset"], "task": task, "run": i, "D": rel.D, "default": real[d],
               "GT-TriTR": relative_error(tritr_reference(g, task, eps, run_rng(seed, i)), truth, n)}
        for name in pools:
            subset = [k for k, c in enumerate(cands) if name in owner[c.program.digest]]
            chosen, best = choose(sel.scores, subset, d, opts.margin)
            c = cands[chosen]
            row[name] = real[chosen]
            row[f"oracle-{name}"] = min(real[k] for k in subset)
            row[f"{name}_program"] = [p.digest for p in pools[name]].index(c.program.digest)
            row[f"{name}_bound_ratio"] = c.bound / max(1, rel.D)
            row[f"{name}_eps1"] = c.eps1
        out.append(row)
    return out


def _se(x) -> float:
    return float(np.std(x, ddof=1) / math.sqrt(len(x))) if len(x) > 1 else float("nan")


def summarize_cell(rows: list[dict], names: list[str]) -> dict:
    out = {"runs": len(rows)}
    for m in ["default", *names, *(f"oracle-{x}" for x in names), "GT-TriTR"]:
        v = [r[m] for r in rows]
        out[m], out[f"{m}_se"] = float(np.mean(v)), _se(v)
    for x in names:
        diff = [r[x] - r["default"] for r in rows]
        out[f"{x}_diff"], out[f"{x}_diff_se"] = float(np.mean(diff)), _se(diff)
        out[f"{x}_change"] = out[x] / out["default"] - 1.0
        out[f"{x}_new_program"] = float(np.mean([r[f"{x}_program"] > 0 for r in rows]))
        if x != "hand":
            diff = [r[x] - r["hand"] for r in rows]
            out[f"{x}_vs_hand"], out[f"{x}_vs_hand_se"] = float(np.mean(diff)), _se(diff)
    return out


def _z(mean: float, se: float) -> float:
    return mean / se if se and se > 0 else 0.0


def report(args, tasks, datasets, pools, rows, design_info, elapsed, out: Path) -> None:
    names = list(pools)
    cells = []
    for ds in datasets:
        for task in tasks:
            sel = sorted((r for r in rows if r["dataset"] == ds and r["task"] == task), key=lambda r: r["run"])
            if sel:
                cells.append({"dataset": ds, "task": task, **summarize_cell(sel, names)})
    averages = []
    for task in tasks:
        cs = [c for c in cells if c["task"] == task]
        avg = {"task": task, **{m: st.mean(c[m] for c in cs) for m in ["default", *names, *(f"oracle-{x}" for x in names), "GT-TriTR"]}}
        for x in names:
            avg[f"{x}_vs_default"] = f"{100 * (avg[x] / avg['default'] - 1):+.1f}%"
            avg[f"{x}_better/worse"] = (f"{sum(_z(c[f'{x}_diff'], c[f'{x}_diff_se']) < -1.96 for c in cs)}/"
                                        f"{sum(_z(c[f'{x}_diff'], c[f'{x}_diff_se']) > 1.96 for c in cs)}")
            if x != "hand":
                avg[f"{x}_vs_hand"] = f"{100 * (avg[x] / avg['hand'] - 1):+.1f}%"
                avg[f"{x}_vs_hand_better/worse"] = (
                    f"{sum(_z(c[f'{x}_vs_hand'], c[f'{x}_vs_hand_se']) < -1.96 for c in cs)}/"
                    f"{sum(_z(c[f'{x}_vs_hand'], c[f'{x}_vs_hand_se']) > 1.96 for c in cs)}")
        averages.append(avg)
    write_json({"settings": vars(args), "elapsed_seconds": elapsed, "pools": pools, "designs": design_info.get("designs"),
                "requests": design_info.get("requests"), "cells": cells, "averages": averages}, out / "summary.json")

    others = [x for x in names if x != "hand"]
    avg_cols = ["task", "default", *names, *(f"oracle-{x}" for x in names), "GT-TriTR",
                *(f"{x}_vs_default" for x in names), *(f"{x}_better/worse" for x in names),
                *(f"{x}_vs_hand" for x in others), *(f"{x}_vs_hand_better/worse" for x in others)]
    cell_rows = []
    for c in cells:
        r = {"dataset": c["dataset"], "task": c["task"], "default": c["default"],
             **{x: c[x] for x in names}, **{f"oracle-{x}": c[f"oracle-{x}"] for x in names}, "GT-TriTR": c["GT-TriTR"]}
        for x in others:
            r[f"{x}_vs_hand"] = f"{c[f'{x}_vs_hand']:+.4f} ± {1.96 * c[f'{x}_vs_hand_se']:.4f}"
            r[f"{x}_new_program"] = c[f"{x}_new_program"]
        cell_rows.append(r)
    cell_cols = ["dataset", "task", "default", *names, *(f"oracle-{x}" for x in names), "GT-TriTR",
                 *(f"{x}_vs_hand" for x in others), *(f"{x}_new_program" for x in others)]
    md = [
        "# LLM-designed program pools + degree-first adaptive selection", "",
        f"eps = {args.eps:g}, {args.runs} runs per cell (seed {args.seed}); selector: {args.samples} posterior samples "
        f"(k-star), {args.sims} simulations x 3 families (triangle), margin {args.margin:g}. Mean relative error "
        "(lower is better). `default` = PSC (library program, bound D, eps1 = r1 eps); every pool column is the "
        "adaptive selection over that pool on the same noise; `oracle-*` picks the best candidate of the pool on "
        "the real graph (not private).", "",
    ]
    if design_info.get("designs"):
        md += ["## Pool design", "",
               f"Model requests (retries included): {design_info.get('requests')}"
               + (f", made by the design run of `{design_info['source']}`; this evaluation made none" if design_info.get("source") else "")
               + ". Public score: geometric mean over the public synthetic graphs of the best pool program on each.", "",
               markdown_table(design_info["designs"], ["task", "designer", "calls", "requests", "proposed", "certified",
                                                        "deployed", "rejections", "hand_score", "pool_score", "stopped"]), ""]
    md += ["## Deployed pools", ""]
    for x in names:
        for t in tasks:
            md.append(f"- **{x} / {t}**: " + " · ".join(f"`{p.replace(chr(10), ' ; ')}`" for p in pools[x][t]))
    md += ["", "## Averages over the datasets", "",
           "`better/worse`: datasets with a significant paired difference (|z| > 1.96).", "",
           markdown_table(averages, avg_cols), "", "## Cells", "",
           "`*_vs_hand`: paired mean difference to the hand pool ± 95% CI; `*_new_program`: share of runs in which "
           "the selector picked a program that is not the library program.", "",
           markdown_table(cell_rows, cell_cols), ""]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", default="2-star,3-star,triangle")
    ap.add_argument("--datasets", default="CU,Do,ML,CS,EE,PM")
    ap.add_argument("--designers", default="llm,random", help="pools to design besides hand (llm, random)")
    ap.add_argument("--pools", default=None, help="pools.json of an earlier run: skip the design (no model call)")
    ap.add_argument("--rounds", type=int, default=3, help="model calls per task")
    ap.add_argument("--per-call", type=int, default=4, help="programs asked for per model call")
    ap.add_argument("--max-pool", type=int, default=4)
    ap.add_argument("--min-gain", type=float, default=0.03)
    ap.add_argument("--random-programs", type=int, default=2000)
    ap.add_argument("--max-requests", type=int, default=20, help="hard cap on model requests, retries included")
    ap.add_argument("--runs", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--eps", type=float, default=2.0)
    ap.add_argument("--samples", type=int, default=1000, help="selector: posterior degree sequences (k-star)")
    ap.add_argument("--sims", type=int, default=4, help="selector: simulations per synthetic graph (triangle)")
    ap.add_argument("--margin", type=float, default=0.1)
    ap.add_argument("--chunk", type=int, default=20)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--data", default=str(DATA_DIR))
    ap.add_argument("--provider", default="mock", choices=PROVIDERS)
    ap.add_argument("--profile", default=None)
    ap.add_argument("--config", default=None)
    ap.add_argument("--curator-model", default=None)
    ap.add_argument("--temperature", type=float, default=None)
    ap.add_argument("--max-retries", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true", help="print the planned model calls and exit")
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    tasks, datasets = args.tasks.split(","), args.datasets.split(",")
    unknown = [t for t in tasks if t not in PROGRAMS or not PROGRAMS[t].parse().needs_degree_bound]
    if unknown:
        ap.error(f"tasks without a degree bound or a reference program: {unknown}")
    designers = [d for d in args.designers.split(",") if d]
    llm_calls = len(tasks) * args.rounds if "llm" in designers and args.pools is None else 0
    print(f"design: {len(tasks)} task(s) x {args.rounds} round(s) = {llm_calls} model call(s) ({args.provider}), at most "
          f"{min(args.max_requests, llm_calls * (args.max_retries + 1)) if llm_calls else 0} request(s) with retries; "
          f"evaluation: {len(datasets)} dataset(s) x {len(tasks)} task(s) x {args.runs} run(s), code only")
    if args.dry_run:
        return

    out = out_dir("pool", args.tag, "pool")
    write_manifest(out, vars(args))
    opts = PoolOptions(rounds=args.rounds, per_call=args.per_call, max_pool=args.max_pool, min_gain=args.min_gain,
                       eps=args.eps)
    t0 = time.perf_counter()
    if args.pools:
        data = json.loads(Path(args.pools).read_text(encoding="utf-8"))
        info = {"pools": {k: {t: v[t] for t in tasks} for k, v in data["pools"].items()},
                "designs": [x for x in data.get("designs") or [] if x["task"] in tasks],
                "requests": sum(x.get("requests") or 0 for x in data.get("designs") or [] if x["task"] in tasks),
                "source": str(args.pools)}
    else:
        info = design(args, tasks, opts, out)
        write_json({"pools": info["pools"], "designs": info["designs"], "requests": info["requests"],
                    "pool_options": dataclasses.asdict(opts)}, out / "pools.json")
    pools = info["pools"]

    select_opts = {"samples": args.samples, "sims": args.sims, "margin": args.margin}
    jobs = []
    for ds in datasets:
        for task in tasks:
            for start in range(0, args.runs, args.chunk):
                jobs.append({"dataset": ds, "task": task, "runs": list(range(start, min(args.runs, start + args.chunk))),
                             "seed": args.seed, "eps": args.eps, "data": args.data, "select": select_opts,
                             "pools": {name: pools[name][task] for name in pools}})
    sizes = {ds: next(iter(load_dataset(args.data, ds).values())).vertex_num for ds in datasets}
    jobs.sort(key=lambda j: (not PROGRAMS[j["task"]].parse().uses_rows, -sizes[j["dataset"]]))
    rows, t1 = [], time.perf_counter()

    def keep(k: int, chunk: list[dict]) -> None:  # written as it comes: a crash keeps the finished chunks
        rows.extend(chunk)
        for r in chunk:
            append_jsonl(r, out / "runs.jsonl")
        if k % 10 == 0 or k == len(jobs):
            print(f"[eval] {k}/{len(jobs)} chunks, {time.perf_counter() - t1:.0f}s", flush=True)

    if args.workers > 1:
        with ProcessPoolExecutor(args.workers) as pool:
            for k, chunk in enumerate(pool.map(run_chunk, jobs), 1):
                keep(k, chunk)
    else:
        for k, job in enumerate(jobs, 1):
            keep(k, run_chunk(job))
    report(args, tasks, datasets, pools, rows, info, time.perf_counter() - t0, out)
    print(f"results in {out}")


if __name__ == "__main__":
    main()
