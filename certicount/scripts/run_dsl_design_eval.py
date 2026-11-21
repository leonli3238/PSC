"""Goal 2: how much error does the LLM designer add to the DSL method? (research content 4)

For every task the curator model designs the program ``--designs`` times
independently (no cache). Each design is scored from public information only
(:func:`certicount.dsl.quality.design_quality`) and every accepted program is run
``--runs`` times in code (:func:`certicount.dsl.ground_truth.dp_execute`, the same
DP steps and random-number order as the ``program`` mode of the framework),
paired run by run with GT-DSL -- the reference program of the task on the same
noise. Since the node executes the program exactly, the paired difference

    design_error = RE(designed program) - RE(GT-DSL)

is the error added by the LLM designer alone (local function, GS, budget split).

Design metrics per task: acceptance rate, first-try rate, iterations and model
calls, share of programs identical to the reference, budget split equal to the
reference, GS ratio (derived GS / reference GS at the design-time bound and at
``--bounds``), independent semantic test (``--utility-graphs`` random graphs of
up to ``--utility-max-n`` nodes, another seed than the design loop) and the
falsifier's soundness check.

Offline with the mock designer (it writes the reference program; ``--flawed-first``
makes its first k-star draft unprojected). A real provider calls a paid /
remote model: check ``--dry-run`` first; use ``--temperature`` > 0 to sample
different designs.

    ../.venv/bin/python scripts/run_dsl_design_eval.py --datasets CU --designs 3 --runs 10 --flawed-first --tag dsl_eval_mock
    ../.venv/bin/python scripts/run_dsl_design_eval.py --datasets CU --designs 10 --runs 10 \\
        --provider openai --profile <profile> --temperature 0.7 --tag dsl_eval_real
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
from psc.events import collect_errors, set_error_sink, set_transcript_sink  # noqa: E402
from psc.experiments import run_rng  # noqa: E402
from psc.graph import load_dataset  # noqa: E402
from psc.ground_truth import relative_error  # noqa: E402
from psc.mechanism import DEFAULT_MECHANISM, MECHANISMS  # noqa: E402
from psc.models import PROVIDERS, ModelConfig, create_formatter, create_model  # noqa: E402
from certicount import DATA_DIR  # noqa: E402
from certicount.artifacts import append_jsonl, markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.dsl.designer import (RELEASES, DesignOptions, MockDesignerModel, design_candidates,  # noqa: E402
                                     design_reference_params, design_with_restarts, draft_stage)
from certicount.dsl.evolve import wilson_interval  # noqa: E402
from certicount.dsl.noisy_gate import NoisyGate, noise_free_check  # noqa: E402
from certicount.dsl.prompt_spec import core_leak_check, load_spec  # noqa: E402
from certicount.dsl.ground_truth import dp_execute, gs_ratio, gt_dsl, noise_ratio  # noqa: E402
from certicount.dsl.library import PROGRAMS  # noqa: E402
from certicount.dsl.quality import design_quality, finite_mean, task_record  # noqa: E402
from certicount.dsl.search import SearchOptions, search_program  # noqa: E402
from certicount.dsl.selection import SimOptions, execute_selected  # noqa: E402

EXACT_TOL = 1e-9


def _rate(values) -> float | None:
    vals = [bool(v) for v in values if v is not None]
    return float(np.mean(vals)) if vals else None


def _se(values: list[float]) -> float | None:
    return float(np.std(values, ddof=1) / math.sqrt(len(values))) if len(values) > 1 else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", default="CU")
    ap.add_argument("--tasks", default="degree,3-star,triangle,4-star,5-star,degree-moment2")
    ap.add_argument("--designs", type=int, default=5, help="independent designs per task (success rate)")
    ap.add_argument("--max-iterations", type=int, default=3, help="exact mode: drafts per design loop")
    ap.add_argument("--restarts", type=int, default=1, help="exact mode: fresh-history loops per design until accepted")
    ap.add_argument("--design-mode", default="exact", choices=("exact", "search"))
    ap.add_argument("--search-rounds", type=int, default=4)
    ap.add_argument("--search-proposals", type=int, default=3)
    ap.add_argument("--search-sims", type=int, default=50)
    ap.add_argument("--runs", type=int, default=10, help="DP runs per accepted design (paired with GT-DSL)")
    ap.add_argument("--eps", type=float, default=2.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--mechanism", default=DEFAULT_MECHANISM, choices=MECHANISMS)
    ap.add_argument("--bounds", default="5,10,20", help="public bounds D = dmax of the GS-ratio check")
    ap.add_argument("--utility-graphs", type=int, default=100)
    ap.add_argument("--utility-max-n", type=int, default=16)
    ap.add_argument("--no-falsify", action="store_true", help="skip the falsifier soundness check")
    ap.add_argument("--node-bounds", action="store_true",
                    help="per-node architecture: edge clipping + NAM-DPRD unbiased matrix A (the curator's prompt "
                         "documents A; designs are paired with GT-DSL-node)")
    ap.add_argument("--clip-alpha", type=float, default=0.0, help="--node-bounds: public margin α of the clipping bound")
    ap.add_argument("--noisy-gate", action="store_true",
                    help="design loop: noise-free check of each draft through the real release on public graphs "
                         "(certicount.dsl.noisy_gate); its statistic is recorded for every accepted design anyway")
    ap.add_argument("--noisy-tau", type=float, default=2.0, help="gate threshold on the median noise-free relative error")
    ap.add_argument("--noisy-reps", type=int, default=8, help="releases per public test graph")
    ap.add_argument("--prompt", default="v0",
                    help="design instructions: v0 / v1 (empty modules, prompt core v1), legacy (the CS2-CS5 prompt byte "
                         "for byte), v1-repeat3 (v1, prohibitions stated three times), v1-alt (v1 + rewrites of "
                         "Python constructs + closing checklist + rewrite hints; its pair rewrites contain the rows "
                         "triangle and open-wedge programs), generic (v1 + rewrites of single constructs over "
                         "placeholders, leak-checked, + checklist) or a spec JSON, e.g. "
                         "results/evolve/<tag>/best_prompt.json (a spec without a 'core' field was evolved on the "
                         "legacy core and keeps it)")
    ap.add_argument("--select", default="first", choices=("first", "min_gs", "simulated"),
                    help="exact mode with --restarts > 1: first accepted program, or the smallest derived GS among "
                         "--min-accepted behaviourally different accepted programs. simulated (--node-bounds only): "
                         "one design loop per release of --releases, choice by simulating the release on public graphs "
                         "(certicount.dsl.selection; replaces the noise-free gate, --noisy-gate is ignored) and, between "
                         "candidates with the same budget split, again in every run from its published noisy degrees")
    ap.add_argument("--releases", default=",".join(RELEASES), help="--select simulated: design rounds (rows, matrix)")
    ap.add_argument("--own-row-check", action="store_true",
                    help="reject drafts that read this node's own release entries N(self) / A(self, .) (per-node)")
    ap.add_argument("--sim-reps", type=int, default=8, help="--select simulated: releases per public graph")
    ap.add_argument("--sim-degrees", default="4,8,16", help="--select simulated: average degrees of the public graphs")
    ap.add_argument("--sim-useless", type=float, default=1.0,
                    help="--select simulated: candidates with a simulated score at or above this are never chosen "
                         "(<= 0: no threshold)")
    ap.add_argument("--min-accepted", type=int, default=1, help="--select min_gs: accepted programs to collect")
    ap.add_argument("--early-stop", default="", help="comma-separated stages (e.g. noisy,gs_loose): two rejections in a "
                                                     "row at one of them end the design loop")
    ap.add_argument("--tighten", type=int, default=0,
                    help="extra calls after an acceptance whose derived GS is loose on the falsifier's graphs")
    ap.add_argument("--slack-tol", type=float, default=1.2, help="--tighten: derived GS / observed change that triggers it")
    ap.add_argument("--no-normalize", action="store_true",
                    help="no format-only repairs of the curator's replies (tag lines, aggregate inside the block, //)")
    ap.add_argument("--design-concurrency", type=int, default=1,
                    help="designs of a task run concurrently (transcripts carry dataset/task/design)")
    ap.add_argument("--data", default=str(DATA_DIR))
    ap.add_argument("--provider", default="mock", choices=PROVIDERS)
    ap.add_argument("--profile", default=None)
    ap.add_argument("--config", default=None)
    ap.add_argument("--curator-model", default=None)
    ap.add_argument("--temperature", type=float, default=None, help="designer sampling temperature (config default: 0)")
    ap.add_argument("--flawed-first", action="store_true", help="mock designer: unprojected first draft for k-star tasks")
    ap.add_argument("--dry-run", action="store_true", help="print the planned model calls and exit")
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    datasets, tasks = args.datasets.split(","), args.tasks.split(",")
    unknown = [t for t in tasks if t not in PROGRAMS]
    if unknown:
        ap.error(f"no reference program for {unknown}; known: {', '.join(PROGRAMS)}")
    bounds = tuple(int(x) for x in args.bounds.split(","))
    simulated = args.select == "simulated"
    releases = tuple(r for r in args.releases.split(",") if r)
    if simulated and not args.node_bounds:
        ap.error("--select simulated chooses between the releases of the per-node architecture: add --node-bounds")
    if simulated and (args.design_mode != "exact" or any(r not in RELEASES for r in releases) or not releases):
        ap.error(f"--select simulated needs --design-mode exact and --releases from {RELEASES}")
    if simulated and args.noisy_gate:
        print("--select simulated: the noise-free gate is replaced by the simulated choice (--noisy-gate ignored)")
        args.noisy_gate = False
    options = DesignOptions(normalize=not args.no_normalize, tighten=args.tighten, slack_tol=args.slack_tol,
                            early_stop=tuple(s for s in args.early_stop.split(",") if s),
                            select="first" if simulated else args.select, min_accepted=args.min_accepted,
                            own_row=args.own_row_check)
    per_design = (args.search_rounds * args.search_proposals if args.design_mode == "search"
                  else (args.max_iterations + args.tighten) * args.restarts * (len(releases) if simulated else 1))
    planned = len(datasets) * len(tasks) * args.designs * per_design
    print(f"{len(datasets)} dataset(s) x {len(tasks)} task(s) x {args.designs} design(s): at most {planned} model calls "
          f"({args.provider}); {args.runs} code runs per accepted design")
    if args.dry_run:
        return

    if args.provider == "mock":
        cfg = ModelConfig()
        model = MockDesignerModel(flawed_first=args.flawed_first)
    else:
        overrides = {k: v for k, v in (("curator_model", args.curator_model), ("temperature", args.temperature)) if v is not None}
        cfg = ModelConfig.from_env(provider=args.provider, config_path=args.config, profile=args.profile, **overrides)
        model = create_model(cfg, "curator")
    fmt = create_formatter(cfg)
    spec = load_spec(args.prompt)
    leaks = core_leak_check(spec.core)
    leaked = sorted({lk["task"] for lk in leaks})
    if leaked:
        print(f"WARNING: prompt core {spec.core!r} shows programs of {', '.join(leaked)} "
              f"(prompt_spec.core_leak_check); results on these tasks are not out-of-prompt")
    out = out_dir("dsl_eval", args.tag, "dsl_eval")
    write_manifest(out, {**vars(args), "planned_calls": planned, "designer": getattr(cfg, "curator_model", None),
                         "prompt_spec": spec.to_dict(), "design_options": options.to_dict(),
                         "core_leaks": list(leaks), "core_leaked_tasks": leaked})
    set_error_sink(out / "errors.jsonl")
    set_transcript_sink(out / "transcripts.jsonl")

    async def evaluate() -> tuple[list[dict], list[dict]]:
        summaries, designs = [], []
        sem = asyncio.Semaphore(max(1, args.design_concurrency))
        for ds in datasets:
            recs = load_dataset(args.data, ds)
            for task in tasks:
                rec = task_record(recs, ds, task)
                g, n, truth = rec.graph(), rec.vertex_num, rec.answer
                ref_params = design_reference_params(n)
                gt = [gt_dsl(g, task, args.eps, run_rng(args.seed, i), mechanism=args.mechanism,
                             node_bounds=args.node_bounds, alpha=args.clip_alpha) for i in range(args.runs)]
                gt_re = [relative_error(t.estimate, truth, n) for t in gt]
                sim = (SimOptions(n, args.eps, True, args.clip_alpha, args.mechanism,
                                  avg_degrees=tuple(float(x) for x in args.sim_degrees.split(",")), reps=args.sim_reps,
                                  useless=args.sim_useless if args.sim_useless > 0 else None) if simulated else None)
                noisy = (NoisyGate(n, args.eps, args.node_bounds, args.clip_alpha, args.mechanism,
                                   tau=args.noisy_tau, reps=args.noisy_reps) if args.noisy_gate else None)

                async def one(k: int) -> tuple[dict, list[dict]]:
                    """Design k, then its paired code runs; the transcript lines carry dataset/task/design."""
                    async with sem:
                        with collect_errors(dataset=ds, task=task, design=k):
                            t0 = time.perf_counter()
                            if args.design_mode == "search":
                                opts = SearchOptions(rounds=args.search_rounds, proposals=args.search_proposals,
                                                     sims=args.search_sims, eps=args.eps, mechanism=args.mechanism)
                                res = await search_program(model, fmt, rec.input_prompt, n, task, opts)
                            elif simulated:
                                res, cands, sel = await design_candidates(
                                    model, fmt, rec.input_prompt, n, ref_params, task, sim,
                                    max_iterations=args.max_iterations, restarts=args.restarts, spec=spec,
                                    options=options, releases=releases)
                            else:
                                res = await design_with_restarts(model, fmt, rec.input_prompt, n, ref_params, task=task,
                                                                 max_iterations=args.max_iterations,
                                                                 restarts=args.restarts, matrix=args.node_bounds,
                                                                 noisy=noisy, spec=spec, options=options)
                    run_rows: list[dict] = []
                    loops = res.attempts or [{"history": res.history}]
                    row = {
                        "dataset": ds, "task": task, "design": k, "accepted": res.accepted, "iterations": res.iterations,
                        "restarts": res.restarts, "first_loop_accepted": (res.accepted and res.restarts == 1) if simulated
                        else bool(res.attempts and res.attempts[0]["accepted"]) if res.mode == "exact" else res.accepted,
                        "llm_calls": res.llm_calls, "design_seconds": round(time.perf_counter() - t0, 3),
                        "program": res.program.text() if res.program else None,
                        "search_score": (res.score or {}).get("score"),
                        "feedback": [h["feedback"] for h in res.history],
                        "stages": [draft_stage(h["feedback"]) for a in loops for h in a["history"]],
                        "normalized_drafts": sum(bool(h.get("normalized")) for a in loops for h in a["history"]),
                        "selection": res.selection,
                    }
                    if res.program is not None:
                        q = design_quality(res.program, task, n, int(ref_params.D), bounds, args.utility_graphs,
                                           utility_n=(5, args.utility_max_n), falsify_program=not args.no_falsify,
                                           truncate=args.design_mode == "exact", node_bounds=args.node_bounds)
                        row.update(q.to_dict())
                        re_, diffs, exact, ratios, nratios, zeros, picked = [], [], [], [], [], [], []
                        for i in range(args.runs):
                            if simulated:
                                tr, idx, _ = execute_selected(g, cands, sel, task, sim, run_rng(args.seed, i))
                                picked.append("matrix" if cands[idx].uses_matrix else
                                              "rows" if cands[idx].uses_rows else "private")
                            else:
                                tr = dp_execute(g, res.program, args.eps, run_rng(args.seed, i), task, args.mechanism,
                                                node_bounds=args.node_bounds, alpha=args.clip_alpha)
                            e = relative_error(tr.estimate, truth, n)
                            re_.append(e)
                            diffs.append(e - gt_re[i])
                            both_zero = tr.estimate == 0 and gt[i].estimate == 0
                            zeros.append(both_zero)
                            if not both_zero:
                                exact.append(abs(tr.estimate - gt[i].estimate) <= EXACT_TOL * max(1.0, abs(truth)))
                            ratios.append(gs_ratio(tr.gs, gt[i].gs))
                            nratios.append(noise_ratio(tr.final_noise_scale, gt[i].final_noise_scale))
                            run_rows.append({
                                "dataset": ds, "task": task, "design": k, "run": i, "truth": truth,
                                "estimate": tr.estimate, "gt_dsl_estimate": gt[i].estimate,
                                "relative_error": e, "gt_dsl_relative_error": gt_re[i], "design_error": e - gt_re[i],
                                "gs": tr.gs, "gt_dsl_gs": gt[i].gs, "split": tr.split, "gt_dsl_split": gt[i].split,
                                "d_hat_max": tr.d_hat_max, "gt_dsl_d_hat_max": gt[i].d_hat_max,
                                "final_noise_scale": tr.final_noise_scale, "gt_dsl_final_noise_scale": gt[i].final_noise_scale,
                                **({"program_read": picked[-1]} if picked else {}),
                            })
                        # diagnostic for every accepted design (also without the gate): the gate's statistic
                        nrep = noise_free_check(res.program, task, noisy or diag_gate)
                        row.update(
                            relative_error=float(np.mean(re_)), gt_dsl_relative_error=float(np.mean(gt_re)),
                            design_error=float(np.mean(diffs)), design_error_se=_se(diffs),
                            design_exact=float(np.mean(exact)) if exact else None, both_zero=float(np.mean(zeros)),
                            run_gs_ratio=finite_mean(ratios), noise_ratio=finite_mean(nratios),
                            noise_free_bias=max((r["bias"] for r in nrep.rows), default=None),
                            noise_free_pass=nrep.passed,
                        )
                        if simulated:
                            row.update(candidates=len(cands), runtime_alternatives=len(sel.runtime),
                                       runs_matrix=float(np.mean([p == "matrix" for p in picked])),
                                       runs_rows=float(np.mean([p == "rows" for p in picked])))
                    elif simulated:
                        row.update(candidates=len((res.selection or {}).get("candidates") or []))
                    return row, run_rows

                diag_gate = NoisyGate(n, args.eps, args.node_bounds, args.clip_alpha, args.mechanism,
                                      tau=args.noisy_tau, reps=args.noisy_reps)
                rows: list[dict] = []
                for row, run_rows in await asyncio.gather(*(one(k) for k in range(args.designs))):
                    for rr in run_rows:
                        append_jsonl(rr, out / "runs.jsonl")
                    append_jsonl(row, out / "designs.jsonl")
                    rows.append(row)
                    designs.append(row)
                acc = [r for r in rows if r["accepted"]]
                diffs_all = [r["design_error"] for r in acc]
                lo, hi = wilson_interval(len(acc), len(rows))
                summaries.append({
                    "dataset": ds, "task": task, "designs": len(rows),
                    "accept_rate": _rate(r["accepted"] for r in rows),
                    "accept_ci95": f"[{lo:.2f}, {hi:.2f}]",
                    "first_loop_rate": _rate(r["first_loop_accepted"] for r in rows),
                    "first_try_rate": _rate(r["accepted"] and r["iterations"] == 1 and r["restarts"] == 1 for r in rows),
                    "mean_iterations": finite_mean(r["iterations"] for r in acc),
                    "mean_restarts": finite_mean(r["restarts"] for r in rows),
                    "mean_llm_calls": finite_mean(r["llm_calls"] for r in rows),
                    "distinct_programs": len({r["program"] for r in acc}),
                    "same_as_reference": _rate(r.get("same_as_reference") for r in acc),
                    "split_match": _rate(r.get("split_match") for r in acc),
                    "semantic_pass": _rate(r.get("semantic_pass") for r in acc),
                    "sound": _rate(r.get("sound") for r in acc),
                    "gs_ratio": finite_mean(r.get("gs_ratio") for r in acc),
                    "gs_ratio_max": max((r["gs_ratio"] for r in acc if r.get("gs_ratio") is not None), default=None),
                    "noise_ratio": finite_mean(r.get("noise_ratio") for r in acc),
                    "relative_error": finite_mean(r.get("relative_error") for r in acc),
                    "gt_dsl_relative_error": float(np.mean(gt_re)) if gt_re else None,
                    "design_error": finite_mean(diffs_all),
                    "design_error_max": max(diffs_all, default=None),
                    "design_exact": finite_mean(r.get("design_exact") for r in acc),
                    "both_zero": finite_mean(r.get("both_zero") for r in acc),
                    "noise_free_pass": _rate(r.get("noise_free_pass") for r in acc),
                    "median_relative_error": float(np.median([r["relative_error"] for r in acc])) if acc else None,
                    "mean_candidates": finite_mean(r.get("candidates") for r in rows),
                    "runs_matrix": finite_mean(r.get("runs_matrix") for r in acc),
                    "runs_rows": finite_mean(r.get("runs_rows") for r in acc),
                })
        return summaries, designs

    summaries, designs = asyncio.run(evaluate())
    write_json({"settings": vars(args), "summary": summaries, "designs": designs}, out / "summary.json")
    sum_cols = ["dataset", "task", "designs", "accept_rate", "accept_ci95", "first_loop_rate", "first_try_rate",
                "mean_iterations", "mean_restarts", "mean_llm_calls", "distinct_programs", "same_as_reference",
                "split_match", "semantic_pass", "sound", "noise_free_pass", "gs_ratio", "gs_ratio_max", "noise_ratio"]
    if simulated:
        sum_cols += ["mean_candidates", "runs_matrix", "runs_rows"]
    err_cols = ["dataset", "task", "relative_error", "median_relative_error", "gt_dsl_relative_error", "design_error",
                "design_error_max", "design_exact", "both_zero"]
    design_cols = ["dataset", "task", "design", "accepted", "restarts", "iterations", "same_as_reference", "split_match",
                   "noise_ratio", "semantic_pass", "sound", "noise_free_bias", "search_score", "relative_error",
                   "design_error", "program"]
    shown = [{**d, "program": (d["program"] or "-").replace("\n", " ; ")} for d in designs]
    sim_note = (f" (public Holme-Kim graphs, average degrees {args.sim_degrees}, {args.sim_reps} releases each, "
                f"never chosen at a score >= {args.sim_useless:g}; run-time choice on Chung-Lu graphs of the published "
                "noisy degrees)")
    loop = (f"search: {args.search_rounds} round(s) x {args.search_proposals} proposal(s)" if args.design_mode == "search"
            else f"{args.max_iterations} draft(s) x up to {args.restarts} restart(s)"
                 f"{' per release (' + ', '.join(releases) + ')' if simulated else ''}, selection {args.select}"
                 f"{sim_note if simulated else ''}, own-row check {'on' if args.own_row_check else 'off'}"
                 f"{' of %d' % args.min_accepted if args.select == 'min_gs' else ''}, tighten {args.tighten}, "
                 f"early stop {args.early_stop or 'off'}, normalisation {'off' if args.no_normalize else 'on'}, "
                 f"prompt {spec.name} (core {spec.core}, {spec.digest})")
    md = [
        "# DSL design evaluation (goal 2: error added by the LLM designer)", "",
        f"designer = {args.provider}{' / ' + str(cfg.curator_model) if args.provider != 'mock' else ''}"
        f"{' (flawed first draft)' if args.flawed_first and args.provider == 'mock' else ''}, temperature = "
        f"{args.temperature if args.temperature is not None else cfg.temperature}, {args.designs} independent design(s), "
        f"{loop}, ε = {args.eps}, {args.runs} runs per design (noise of run i: seed [{args.seed}, i]), "
        f"mechanism = {args.mechanism}, architecture = "
        f"{'per-node (edge clipping + unbiased matrix A, α = %g)' % args.clip_alpha if args.node_bounds else 'PSC'}, "
        f"noise-aware gate {'on (τ = %g, %d releases per graph)' % (args.noisy_tau, args.noisy_reps) if args.noisy_gate else 'off'}.", "",
        "`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of "
        "the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; "
        "certicount.dsl.noisy_gate), recorded with the gate off too.", "",
        "## Design quality", "",
        "`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; "
        "`first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound "
        "D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); "
        "`noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; "
        "`semantic_pass`: independent utility test; `sound`: no falsifier counterexample.", "",
        markdown_table(summaries, sum_cols), "",
        "## Accuracy (accepted designs, paired with GT-DSL on the same noise)", "",
        "`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library "
        "algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.", "",
        markdown_table(summaries, err_cols), "",
        "## Designs", "", markdown_table(shown, design_cols), "",
    ]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    print(f"results in {out}")


if __name__ == "__main__":
    main()
