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
from psc.events import set_error_sink, set_transcript_sink  # noqa: E402
from psc.experiments import run_rng  # noqa: E402
from psc.graph import load_dataset  # noqa: E402
from psc.ground_truth import relative_error  # noqa: E402
from psc.mechanism import DEFAULT_MECHANISM, MECHANISMS  # noqa: E402
from psc.models import PROVIDERS, ModelConfig, create_formatter, create_model  # noqa: E402
from certicount import DATA_DIR  # noqa: E402
from certicount.artifacts import append_jsonl, markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.dsl.designer import MockDesignerModel, design_reference_params, design_with_restarts  # noqa: E402
from certicount.dsl.ground_truth import dp_execute, gs_ratio, gt_dsl, noise_ratio  # noqa: E402
from certicount.dsl.library import PROGRAMS  # noqa: E402
from certicount.dsl.quality import design_quality, finite_mean, task_record  # noqa: E402
from certicount.dsl.search import SearchOptions, search_program  # noqa: E402

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
    per_design = (args.search_rounds * args.search_proposals if args.design_mode == "search"
                  else args.max_iterations * args.restarts)
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
    out = out_dir("dsl_eval", args.tag, "dsl_eval")
    write_manifest(out, {**vars(args), "planned_calls": planned, "designer": getattr(cfg, "curator_model", None)})
    set_error_sink(out / "errors.jsonl")
    set_transcript_sink(out / "transcripts.jsonl")

    async def evaluate() -> tuple[list[dict], list[dict]]:
        summaries, designs = [], []
        for ds in datasets:
            recs = load_dataset(args.data, ds)
            for task in tasks:
                rec = task_record(recs, ds, task)
                g, n, truth = rec.graph(), rec.vertex_num, rec.answer
                ref_params = design_reference_params(n)
                gt = [gt_dsl(g, task, args.eps, run_rng(args.seed, i), mechanism=args.mechanism) for i in range(args.runs)]
                gt_re = [relative_error(t.estimate, truth, n) for t in gt]
                rows: list[dict] = []
                for k in range(args.designs):
                    t0 = time.perf_counter()
                    if args.design_mode == "search":
                        opts = SearchOptions(rounds=args.search_rounds, proposals=args.search_proposals,
                                             sims=args.search_sims, eps=args.eps, mechanism=args.mechanism)
                        res = await search_program(model, fmt, rec.input_prompt, n, task, opts)
                    else:
                        res = await design_with_restarts(model, fmt, rec.input_prompt, n, ref_params, task=task,
                                                         max_iterations=args.max_iterations, restarts=args.restarts)
                    row = {
                        "dataset": ds, "task": task, "design": k, "accepted": res.accepted, "iterations": res.iterations,
                        "restarts": res.restarts, "first_loop_accepted": bool(res.attempts and res.attempts[0]["accepted"])
                        if res.mode == "exact" else res.accepted,
                        "llm_calls": res.llm_calls, "design_seconds": round(time.perf_counter() - t0, 3),
                        "program": res.program.text() if res.program else None,
                        "search_score": (res.score or {}).get("score"),
                        "feedback": [h["feedback"] for h in res.history],
                    }
                    if res.program is not None:
                        q = design_quality(res.program, task, n, int(ref_params.D), bounds, args.utility_graphs,
                                           utility_n=(5, args.utility_max_n), falsify_program=not args.no_falsify,
                                           truncate=args.design_mode == "exact")
                        row.update(q.to_dict())
                        re_, diffs, exact, ratios, nratios, zeros = [], [], [], [], [], []
                        for i in range(args.runs):
                            tr = dp_execute(g, res.program, args.eps, run_rng(args.seed, i), task, args.mechanism)
                            e = relative_error(tr.estimate, truth, n)
                            re_.append(e)
                            diffs.append(e - gt_re[i])
                            both_zero = tr.estimate == 0 and gt[i].estimate == 0
                            zeros.append(both_zero)
                            if not both_zero:
                                exact.append(abs(tr.estimate - gt[i].estimate) <= EXACT_TOL * max(1.0, abs(truth)))
                            ratios.append(gs_ratio(tr.gs, gt[i].gs))
                            nratios.append(noise_ratio(tr.final_noise_scale, gt[i].final_noise_scale))
                            append_jsonl({
                                "dataset": ds, "task": task, "design": k, "run": i, "truth": truth,
                                "estimate": tr.estimate, "gt_dsl_estimate": gt[i].estimate,
                                "relative_error": e, "gt_dsl_relative_error": gt_re[i], "design_error": e - gt_re[i],
                                "gs": tr.gs, "gt_dsl_gs": gt[i].gs, "split": tr.split, "gt_dsl_split": gt[i].split,
                                "d_hat_max": tr.d_hat_max, "gt_dsl_d_hat_max": gt[i].d_hat_max,
                                "final_noise_scale": tr.final_noise_scale, "gt_dsl_final_noise_scale": gt[i].final_noise_scale,
                            }, out / "runs.jsonl")
                        row.update(
                            relative_error=float(np.mean(re_)), gt_dsl_relative_error=float(np.mean(gt_re)),
                            design_error=float(np.mean(diffs)), design_error_se=_se(diffs),
                            design_exact=float(np.mean(exact)) if exact else None, both_zero=float(np.mean(zeros)),
                            run_gs_ratio=finite_mean(ratios), noise_ratio=finite_mean(nratios),
                        )
                    append_jsonl(row, out / "designs.jsonl")
                    rows.append(row)
                    designs.append(row)
                acc = [r for r in rows if r["accepted"]]
                diffs_all = [r["design_error"] for r in acc]
                summaries.append({
                    "dataset": ds, "task": task, "designs": len(rows),
                    "accept_rate": _rate(r["accepted"] for r in rows),
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
                })
        return summaries, designs

    summaries, designs = asyncio.run(evaluate())
    write_json({"settings": vars(args), "summary": summaries, "designs": designs}, out / "summary.json")
    sum_cols = ["dataset", "task", "designs", "accept_rate", "first_loop_rate", "first_try_rate", "mean_iterations",
                "mean_restarts", "mean_llm_calls", "distinct_programs", "same_as_reference", "split_match", "semantic_pass",
                "sound", "gs_ratio", "gs_ratio_max", "noise_ratio"]
    err_cols = ["dataset", "task", "relative_error", "gt_dsl_relative_error", "design_error", "design_error_max",
                "design_exact", "both_zero"]
    design_cols = ["dataset", "task", "design", "accepted", "restarts", "iterations", "same_as_reference", "split_match",
                   "noise_ratio", "semantic_pass", "sound", "search_score", "relative_error", "design_error", "program"]
    shown = [{**d, "program": (d["program"] or "-").replace("\n", " ; ")} for d in designs]
    loop = (f"search: {args.search_rounds} round(s) x {args.search_proposals} proposal(s)" if args.design_mode == "search"
            else f"{args.max_iterations} draft(s) x up to {args.restarts} restart(s)")
    md = [
        "# DSL design evaluation (goal 2: error added by the LLM designer)", "",
        f"designer = {args.provider}{' / ' + str(cfg.curator_model) if args.provider != 'mock' else ''}"
        f"{' (flawed first draft)' if args.flawed_first and args.provider == 'mock' else ''}, temperature = "
        f"{args.temperature if args.temperature is not None else cfg.temperature}, {args.designs} independent design(s), "
        f"{loop}, ε = {args.eps}, {args.runs} runs per design (noise of run i: seed [{args.seed}, i]), "
        f"mechanism = {args.mechanism}.", "",
        "## Design quality", "",
        "`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; "
        "`first_try_rate`: accepted at the first draft. `gs_ratio`: derived GS / reference GS at the design-time bound "
        "D = min(n−1, 10); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; "
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
