"""Degree-first adaptive selection vs PSC on identical noise (code only, no model calls).

For every dataset x task and run i (common random numbers of ``[seed, i]``,
:func:`certicount.dsl.adaptive.run_streams`):

  ``default``    the PSC setting (bound D, eps1 = r1 eps) through the same executor
  ``adaptive``   the candidate chosen from public values (:func:`certicount.dsl.adaptive.select`);
                 ``adaptive-best`` ignores the margin (always the best score), ``adaptive`` keeps
                 the default unless the best candidate is predicted ``--margin`` better
  ``tuned``      GT-Tuned: the library program with threshold factor / budget split tuned on
                 public synthetic graphs of size n only (:func:`certicount.dsl.search.tune_reference`)
  ``static``     the best fixed candidate (factor of D, eps1) of the dataset, chosen on the real
                 graph: an oracle reference, not a private method
  ``per-run``    the best candidate of every run on the real graph: the ceiling of selection

``default`` equals GT-PSC in distribution; GT-PSC and GT-TriTR (alpha = 0, PSC split) are
also run with their own streams (:func:`psc.experiments.run_rng`) as references.

    ../.venv/bin/python scripts/run_adaptive.py --runs 1000 --workers 8 --tag adaptive_r1000
"""

from __future__ import annotations

import argparse
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
from psc.dp import split_budget  # noqa: E402
from psc.experiments import run_rng  # noqa: E402
from psc.graph import load_dataset  # noqa: E402
from psc.ground_truth import gt_psc, gt_tritr, relative_error  # noqa: E402
from psc.mechanism import DEFAULT_MECHANISM  # noqa: E402
from certicount import DATA_DIR  # noqa: E402
from certicount.artifacts import append_jsonl, markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.dsl.adaptive import (  # noqa: E402
    Candidate, SelectOptions, bound_space, default_index, execute, factor_space, release_degrees, row_space,
    run_streams, select,
)
from certicount.dsl.lang import parse_program  # noqa: E402
from certicount.dsl.library import PROGRAMS  # noqa: E402
from certicount.dsl.search import SearchOptions, tune_reference  # noqa: E402

R1, R2 = 0.5, 0.2  # the paper's split


def _key(c: Candidate) -> str:
    return ",".join(f"{x:g}" if isinstance(x, float) else str(x) for x in c.key)


def run_chunk(job: dict) -> list[dict]:
    rec = load_dataset(job["data"], job["dataset"])[job["task"]]
    g, n, truth, task, eps, seed = rec.graph(), rec.vertex_num, rec.answer, job["task"], job["eps"], job["seed"]
    prog = PROGRAMS[task].parse()
    rows = prog.uses_rows
    split = split_budget(eps, rows, True, R1, R2)
    opts = SelectOptions(**job["select"])
    tuned = parse_program(job["tuned"]["local"], job["tuned"]["aggregate"], budget=job["tuned"]["budget"]) if job["tuned"] else None
    out = []
    for i in job["runs"]:
        streams = run_streams(n, seed, i, rows)
        rel = release_degrees(g, split.eps2, streams, task)
        cands = row_space(prog, rel.D, eps, split.eps2) if rows else bound_space(prog, rel.D)
        d = default_index(cands, rel.D, split.eps1)
        sel = select(rel, n, eps, cands, prog, np.random.default_rng([seed, i, 2]), opts, default=d)
        cache: dict = {}
        res = [relative_error(execute(g, c, eps, rel, streams, cache), truth, n) for c in cands]
        static = cands if rows else factor_space(prog, rel.D)
        static_re = res if rows else [relative_error(execute(g, c, eps, rel, streams), truth, n) for c in static]
        row = {
            "dataset": job["dataset"], "task": task, "run": i, "D": rel.D,
            "default": res[d], "adaptive": res[sel.index], "adaptive-best": res[sel.best], "per-run": min(res),
            "chosen": _key(cands[sel.index]), "best": _key(cands[sel.best]), "kept_default": sel.index == d,
            "chosen_bound_ratio": cands[sel.index].bound / max(1, rel.D), "chosen_eps1": cands[sel.index].eps1,
            "score_ratio": float(sel.scores[sel.best] / sel.scores[d]) if sel.scores[d] > 0 else None,
            "static": {_key(c): r for c, r in zip(static, static_re)},
            "GT-PSC": relative_error(gt_psc(g, task, eps, run_rng(seed, i), mechanism=DEFAULT_MECHANISM), truth, n),
            "GT-TriTR": relative_error(gt_tritr(g, task, eps, run_rng(seed, i)), truth, n),
        }
        if tuned is not None:
            r1, r2 = tuned.budget_fractions(R1, R2)
            t_split = split_budget(eps, rows, True, r1, r2)
            t_rel = release_degrees(g, t_split.eps2, streams, task)
            row["tuned"] = relative_error(execute(g, Candidate(tuned, t_rel.D, t_split.eps1), eps, t_rel, streams), truth, n)
        out.append(row)
    return out


def _se(x) -> float:
    return float(np.std(x, ddof=1) / math.sqrt(len(x))) if len(x) > 1 else float("nan")


def summarize(rows: list[dict]) -> dict:
    out = {"runs": len(rows)}
    for m in ("GT-PSC", "default", "tuned", "adaptive", "adaptive-best", "per-run", "GT-TriTR"):
        if m in rows[0]:
            v = [r[m] for r in rows]
            out[m] = float(np.mean(v))
            out[f"{m}_se"] = _se(v)
    keys = list(rows[0]["static"])
    means = {k: float(np.mean([r["static"][k] for r in rows])) for k in keys}
    out["static_key"] = min(means, key=means.get)
    out["static"] = means[out["static_key"]]
    for m in ("adaptive", "adaptive-best", "tuned"):
        if m in rows[0]:
            diff = [r[m] - r["default"] for r in rows]
            out[f"{m}_diff"] = float(np.mean(diff))
            out[f"{m}_diff_se"] = _se(diff)
            out[f"{m}_change"] = out[m] / out["default"] - 1.0
    out["kept_default"] = float(np.mean([r["kept_default"] for r in rows]))
    out["chosen_bound_ratio"] = float(np.mean([r["chosen_bound_ratio"] for r in rows]))
    eps1 = [r["chosen_eps1"] for r in rows]
    out["chosen_eps1"] = {f"{e:g}": eps1.count(e) for e in sorted(set(eps1))}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", default="CU,Do,ML,CS,EE,PM")
    ap.add_argument("--tasks", default="2-star,3-star,triangle")
    ap.add_argument("--runs", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--eps", type=float, default=2.0)
    ap.add_argument("--samples", type=int, default=1000, help="posterior degree sequences (k-star)")
    ap.add_argument("--sims", type=int, default=8, help="DP simulations per synthetic graph (triangle)")
    ap.add_argument("--graphs", type=int, default=1, help="synthetic graphs per family (triangle)")
    ap.add_argument("--margin", type=float, default=0.1, help="keep the default unless the best is this much better")
    ap.add_argument("--no-tuned", action="store_true", help="skip GT-Tuned")
    ap.add_argument("--chunk", type=int, default=20)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--data", default=str(DATA_DIR))
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    out = out_dir("adaptive", args.tag, "adaptive")
    datasets, tasks = args.datasets.split(","), args.tasks.split(",")
    select_opts = {"samples": args.samples, "sims": args.sims, "graphs": args.graphs, "margin": args.margin}
    jobs = []
    for ds in datasets:
        recs = load_dataset(args.data, ds)
        for task in tasks:
            tuned = None
            if not args.no_tuned:
                t = tune_reference(task, recs[task].vertex_num, SearchOptions(eps=args.eps)).program
                tuned = {"local": t.source, "aggregate": t.aggregate_source,
                         "budget": None if t.budget is None else f"r1={t.budget[0]:g}, r2={t.budget[1]:g}"}
            for start in range(0, args.runs, args.chunk):
                jobs.append({"dataset": ds, "task": task, "runs": list(range(start, min(args.runs, start + args.chunk))),
                             "seed": args.seed, "eps": args.eps, "data": args.data, "select": select_opts, "tuned": tuned})
    # heavy cells first, so that the pool stays busy
    jobs.sort(key=lambda j: (j["task"] != "triangle", -load_dataset(args.data, j["dataset"])[j["task"]].vertex_num))
    t0, rows = time.perf_counter(), []
    if args.workers > 1:
        with ProcessPoolExecutor(args.workers) as pool:
            for k, chunk in enumerate(pool.map(run_chunk, jobs), 1):
                rows += chunk
                if k % 20 == 0 or k == len(jobs):
                    print(f"{k}/{len(jobs)} chunks, {time.perf_counter() - t0:.0f}s", flush=True)
    else:
        for k, job in enumerate(jobs, 1):
            rows += run_chunk(job)
            print(f"{k}/{len(jobs)} chunks, {time.perf_counter() - t0:.0f}s", flush=True)
    for r in rows:
        append_jsonl(r, out / "runs.jsonl")

    cells = []
    for ds in datasets:
        for task in tasks:
            sel = sorted((r for r in rows if r["dataset"] == ds and r["task"] == task), key=lambda r: r["run"])
            cells.append({"dataset": ds, "task": task, **summarize(sel)})
    averages = []
    for task in tasks:
        cs = [c for c in cells if c["task"] == task]
        avg = {"task": task}
        for m in ("GT-PSC", "default", "tuned", "adaptive", "adaptive-best", "static", "per-run", "GT-TriTR"):
            if m in cs[0]:
                avg[m] = st.mean(c[m] for c in cs)
        for m in ("adaptive", "adaptive-best", "tuned"):
            if m in cs[0]:
                z = [c[f"{m}_diff"] / c[f"{m}_diff_se"] for c in cs if c[f"{m}_diff_se"] > 0]
                avg[f"{m}_better"] = sum(x < -1.96 for x in z)
                avg[f"{m}_worse"] = sum(x > 1.96 for x in z)
                avg[f"{m}_change"] = avg[m] / avg["default"] - 1.0
        averages.append(avg)
    write_json({"settings": vars(args), "elapsed_seconds": time.perf_counter() - t0, "cells": cells,
                "averages": averages}, out / "summary.json")

    def pct(x):
        return None if x is None else f"{100 * x:+.1f}%"

    main_rows = [{**c, "adaptive_vs_default": pct(c.get("adaptive_change")), "best_vs_default": pct(c.get("adaptive-best_change")),
                  "tuned_vs_default": pct(c.get("tuned_change")),
                  "adaptive_diff": f"{c['adaptive_diff']:+.4f} ± {1.96 * c['adaptive_diff_se']:.4f}"} for c in cells]
    avg_rows = [{**a, **{f"{m}_vs_default": pct(a.get(f"{m}_change")) for m in ("adaptive", "adaptive-best", "tuned")},
                 "adaptive_better/worse": f"{a.get('adaptive_better')}/{a.get('adaptive_worse')}",
                 "best_better/worse": f"{a.get('adaptive-best_better')}/{a.get('adaptive-best_worse')}",
                 "tuned_better/worse": f"{a.get('tuned_better')}/{a.get('tuned_worse')}"} for a in averages]
    md = [
        "# Degree-first adaptive selection", "",
        f"eps = {args.eps:g}, {args.runs} runs per cell (seed {args.seed}); selection: {args.samples} posterior samples "
        f"(k-star), {args.graphs} graph(s) x {args.sims} simulations per family (triangle), margin {args.margin:g}. "
        "Mean relative error (lower is better). `default`, `adaptive`, `adaptive-best`, `tuned`, `static` and `per-run` "
        "share the noise of every run; `static` and `per-run` choose on the real graph (oracle references); GT-PSC and "
        "GT-TriTR use their own streams.", "",
        "## Averages over the datasets", "",
        "`better/worse`: datasets where the paired difference to `default` is significant (|z| > 1.96).", "",
        markdown_table(avg_rows, ["task", "GT-PSC", "default", "tuned", "adaptive", "adaptive-best", "static", "per-run",
                                  "GT-TriTR", "adaptive_vs_default", "adaptive_better/worse", "adaptive-best_vs_default",
                                  "best_better/worse", "tuned_vs_default", "tuned_better/worse"]), "",
        "## Cells", "",
        markdown_table(main_rows, ["dataset", "task", "GT-PSC", "default", "tuned", "adaptive", "adaptive-best", "static",
                                   "static_key", "per-run", "GT-TriTR", "adaptive_vs_default", "adaptive_diff",
                                   "best_vs_default", "tuned_vs_default", "kept_default", "chosen_bound_ratio", "chosen_eps1"]), "",
    ]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")
    write_manifest(out, vars(args))
    print(f"results in {out}")


if __name__ == "__main__":
    main()
