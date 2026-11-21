"""GT-Select: the release choice of CertiCount with the reference programs, in code (no model call).

CertiCount (``run_dsl_design_eval.py --node-bounds --select simulated``) lets the curator
write one program per release (rows ``N`` / matrix ``A``) and the system picks among the
certified candidates by simulation (:mod:`certicount.dsl.selection`). For triangles this
choice, not the program text, decides the error. GT-Select runs the same two-step choice
with the hand-written reference programs of both releases, so

    CertiCount - GT-Select  = what the LLM designer adds on top of the selection, and
    GT-Select - GT-DSL-node = what the selection adds on top of the reference program.

Methods (run ``i`` uses the noise of ``[seed, i]``, as every other runner):

* ``GT-Naive``         the whole budget on the RR noisy graph, exact count on it
                       (:func:`certicount.dsl.ground_truth.gt_naive`; any task with a counter)
* ``GT-Rows``          the rows program alone (RR of the full lists, then projection; biased);
                       tasks with a rows / matrix pair only (``library.RELEASE_PAIRS``)
* ``GT-DSL-node``      the per-node reference program (``library.NODE_PROGRAMS``: the matrix
                       program of a pair; = GT-DSL-node of ``run_execution_compare.py``)
* ``GT-Select-design`` design-time choice only (public Holme-Kim graphs, :func:`select_program`)
* ``GT-Select``        design-time choice + run-time choice from the published noisy degrees
                       (:func:`execute_selected`, the CertiCount procedure); runs 0..99 are
                       paired with the CertiCount runs of the same index

A task without a pair has one candidate, the per-node reference program: GT-Select is then
GT-DSL-node, or no release at all when the simulated choice refuses the program (score >= the
``--sim-useless`` threshold; ``design_choice = refused``), as CertiCount would refuse it.

``--certicount-tags``: dsl_eval tags whose runs are compared with GT-Select and GT-Naive (same
dataset / task / run index). Tags of one prompt core only: the runs of all tags are pooled.

    OMP_NUM_THREADS=1 ../.venv/bin/python scripts/run_gt_select.py --runs 1000 --workers 48 --tag cs8_gt_select_r1000 \\
        --certicount-tags cs7_node_v1alt_sim,cs7_node_v1alt_sim_cudo,cs8_node_v1alt_sim_mlcsee
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from psc.experiments import run_rng  # noqa: E402
from psc.graph import load_dataset  # noqa: E402
from psc.ground_truth import relative_error  # noqa: E402
from psc.mechanism import DEFAULT_MECHANISM, MECHANISMS  # noqa: E402
from certicount import DATA_DIR  # noqa: E402
from certicount.artifacts import append_jsonl, markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.dsl.ground_truth import dp_execute, gt_naive  # noqa: E402
from certicount.dsl.library import NODE_PROGRAMS, RELEASE_PAIRS  # noqa: E402
from certicount.dsl.quality import task_record  # noqa: E402
from certicount.dsl.selection import Selection, SimOptions, execute_selected, select_program  # noqa: E402
from certicount.dsl.utility import reference_counter  # noqa: E402

RESULTS = ROOT / "results"
METHODS = ("GT-Naive", "GT-Rows", "GT-DSL-node", "GT-Select-design", "GT-Select")


def candidates(task: str) -> dict:
    """Release name -> expert program: the rows / matrix pair (``library.RELEASE_PAIRS``; rows
    triangle = the projected list against the noisy rows, as the curator writes it under
    --own-row-check), otherwise the per-node reference program alone."""
    if task in RELEASE_PAIRS:
        assert RELEASE_PAIRS[task]["matrix"] == NODE_PROGRAMS[task]
        return dict(RELEASE_PAIRS[task])
    return {"node": NODE_PROGRAMS[task]}


_CTX: dict = {}


def _context(data: str, ds: str, task: str) -> tuple:
    key = (ds, task)
    if key not in _CTX:
        rec = task_record(load_dataset(data, ds), ds, task)
        cand = candidates(task)
        _CTX[key] = (rec.graph(), rec.vertex_num, rec.answer, tuple(cand), [p.parse() for p in cand.values()])
    return _CTX[key]


def _entry(estimate: float, truth: float, n: int, gs: float | None = None, split: list | None = None) -> dict:
    return {"estimate": estimate, "relative_error": relative_error(estimate, truth, n), "gs": gs, "split": split}


def run_chunk(data: str, ds: str, task: str, opts: SimOptions, sel: Selection, seed: int,
              indices: list[int]) -> list[dict]:
    g, n, truth, names, progs = _context(data, ds, task)
    out = []
    for i in indices:
        traces = [dp_execute(g, p, opts.eps, run_rng(seed, i), task, opts.mechanism, opts.r1, opts.r2,
                             opts.node_bounds, opts.alpha) for p in progs]
        entries = [_entry(tr.estimate, truth, n, tr.gs, list(tr.split)) for tr in traces]
        row = {"dataset": ds, "task": task, "run": i, "truth": truth, "n": n,
               "GT-Naive": _entry(gt_naive(g, task, opts.eps, run_rng(seed, i)), truth, n),
               "GT-Rows": entries[0] if "rows" in names else None,
               "GT-DSL-node": entries[names.index("matrix") if "matrix" in names else 0],
               "GT-Select-design": None, "GT-Select": None,
               "select_read": None, "runtime_scores": None,
               "design_read": None if sel.chosen is None else names[sel.chosen]}
        if sel.chosen is not None:
            # one candidate in the run-time set: execute_selected runs that program on the same noise
            row["GT-Select-design"] = entries[sel.chosen]
            if len(sel.runtime) < 2:
                row["GT-Select"], row["select_read"] = entries[sel.chosen], names[sel.chosen]
            else:
                tr, idx, scores = execute_selected(g, progs, sel, task, opts, run_rng(seed, i))
                row["GT-Select"] = _entry(tr.estimate, truth, n, tr.gs, list(tr.split))
                row["select_read"], row["runtime_scores"] = names[idx], scores
        out.append(row)
    return out


def _stats(est: list[float], truth: float, n: int) -> dict:
    re_ = np.array([relative_error(e, truth, n) for e in est])
    scale = max(truth, 0.001 * n)
    signed = (np.array(est) - truth) / scale
    k = len(re_)
    return {"runs": k, "relative_error": float(re_.mean()),
            "se": float(re_.std(ddof=1) / math.sqrt(k)) if k > 1 else None,
            "median": float(np.median(re_)), "p90": float(np.percentile(re_, 90)),
            "bias": float(signed.mean()), "rmse": float(math.sqrt(np.mean(signed ** 2))),
            "zero_share": float(np.mean(np.array(est) == 0))}


def _paired(diff: list[float]) -> tuple[float | None, float | None]:
    if not diff:
        return None, None
    d = np.array(diff)
    return float(d.mean()), (float(d.std(ddof=1) / math.sqrt(len(d))) if len(d) > 1 else None)


def load_certicount(tags: list[str], tasks: list[str]) -> dict[tuple, list[dict]]:
    """(dataset, task) -> run rows of the accepted CertiCount designs."""
    out: dict[tuple, list[dict]] = defaultdict(list)
    for tag in tags:
        path = RESULTS / "dsl_eval" / tag / "runs.jsonl"
        with path.open(encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r["task"] in tasks:
                    out[(r["dataset"], r["task"])].append({**r, "source": tag})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", default="PM,CU,Do,ML,CS,EE")
    ap.add_argument("--tasks", default="triangle")
    ap.add_argument("--runs", type=int, default=1000)
    ap.add_argument("--eps", type=float, default=2.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--mechanism", default=DEFAULT_MECHANISM, choices=MECHANISMS)
    ap.add_argument("--clip-alpha", type=float, default=5.0)
    ap.add_argument("--sim-reps", type=int, default=8)
    ap.add_argument("--sim-degrees", default="4,8,16")
    ap.add_argument("--sim-useless", type=float, default=1.0)
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--chunk", type=int, default=10)
    ap.add_argument("--certicount-tags", default="", help="dsl_eval tags paired with GT-Select by run index")
    ap.add_argument("--data", default=str(DATA_DIR))
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    datasets, tasks = args.datasets.split(","), args.tasks.split(",")
    bad = []
    for t in tasks:
        try:
            reference_counter(t)
        except ValueError:
            bad.append(t)
    bad += [t for t in tasks if t not in NODE_PROGRAMS and t not in bad]
    if bad:
        ap.error(f"no per-node reference program or counter for {bad}; known: {', '.join(NODE_PROGRAMS)}")
    tags = [t for t in args.certicount_tags.split(",") if t]
    for t in tags:
        if not (RESULTS / "dsl_eval" / t / "runs.jsonl").exists():
            ap.error(f"no results/dsl_eval/{t}/runs.jsonl")
    out = out_dir("execution", args.tag, "gt_select")
    write_manifest(out, vars(args))

    cells: dict[tuple, dict] = {}
    for ds in datasets:
        for task in tasks:
            g, n, truth, names, progs = _context(args.data, ds, task)
            opts = SimOptions(n, args.eps, True, args.clip_alpha, args.mechanism,
                              avg_degrees=tuple(float(x) for x in args.sim_degrees.split(",")), reps=args.sim_reps,
                              useless=args.sim_useless if args.sim_useless > 0 else None)
            t0 = time.perf_counter()
            sel = select_program(progs, task, opts)
            cells[(ds, task)] = {"opts": opts, "sel": sel, "n": n, "truth": truth, "names": names}
            choice = "refused" if sel.chosen is None else names[sel.chosen]
            print(f"{ds} {task}: design-time choice {choice} scores {[round(r['score'], 4) for r in sel.rows]} "
                  f"runtime {sel.runtime} ({time.perf_counter() - t0:.1f}s)", flush=True)
            append_jsonl({"dataset": ds, "task": task, "releases": list(names), "selection": sel.to_dict(),
                          "sim_options": opts.to_dict()}, out / "selections.jsonl")

    rows: list[dict] = []
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(run_chunk, args.data, ds, task, c["opts"], c["sel"], args.seed,
                            list(range(s, min(s + args.chunk, args.runs))))
                for (ds, task), c in cells.items() for s in range(0, args.runs, args.chunk)]
        for k, fut in enumerate(as_completed(futs), 1):
            for r in fut.result():
                append_jsonl(r, out / "runs.jsonl")
                rows.append(r)
            if k % 20 == 0 or k == len(futs):
                print(f"[{k}/{len(futs)} chunks] {time.perf_counter() - t0:.0f}s", flush=True)

    by_cell: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        by_cell[(r["dataset"], r["task"])].append(r)
    cc = load_certicount(tags, tasks) if tags else {}

    summary, main_rows, paired_rows = [], [], []
    for (ds, task), c in cells.items():
        rs = sorted(by_cell[(ds, task)], key=lambda r: r["run"])
        n, truth, names, sel = c["n"], c["truth"], c["names"], c["sel"]
        line = {"dataset": ds, "task": task, "truth": truth, "n": n, "runs": len(rs), "releases": "/".join(names),
                "design_choice": "refused" if sel.chosen is None else names[sel.chosen]}
        for m in METHODS:
            est = [r[m]["estimate"] for r in rs if r[m] is not None]
            line[m] = None
            if est:
                s = _stats(est, truth, n)
                summary.append({"dataset": ds, "task": task, "method": m, **s})
                line[m] = s["relative_error"]
        line["GT-Oracle"] = min(line["GT-Rows"], line["GT-DSL-node"]) if line["GT-Rows"] is not None else None
        line["select_rows_share"] = (float(np.mean([r["select_read"] == "rows" for r in rs]))
                                     if "rows" in names and sel.chosen is not None else None)
        runs_cc = cc.get((ds, task), [])
        if runs_cc:
            s = _stats([r["estimate"] for r in runs_cc], truth, n)
            summary.append({"dataset": ds, "task": task, "method": "CertiCount", **s,
                            "designs": len({(r["source"], r["design"]) for r in runs_cc})})
            line["CertiCount"] = s["relative_error"]
            line["cc_rows_share"] = float(np.mean([r.get("program_read") == "rows" for r in runs_cc]))
            by_run = {r["run"]: r for r in rs}
            pairs = [(r, by_run[r["run"]]) for r in runs_cc if r["run"] in by_run]
            if pairs:
                sub = [b for b in rs if b["run"] < 1 + max(a["run"] for a, _ in pairs)]
                d_sel, se_sel = _paired([a["relative_error"] - b["GT-Select"]["relative_error"] for a, b in pairs
                                         if b["GT-Select"] is not None])
                d_naive, se_naive = _paired([a["relative_error"] - b["GT-Naive"]["relative_error"] for a, b in pairs])
                same = [abs(a["estimate"] - b["GT-Select"]["estimate"]) <= 1e-9 * max(1.0, truth)
                        for a, b in pairs if b["GT-Select"] is not None]

                def mean_of(m: str) -> float | None:
                    v = [b[m]["relative_error"] for b in sub if b[m] is not None]
                    return float(np.mean(v)) if v else None

                paired_rows.append({
                    "dataset": ds, "task": task, "pairs": len(pairs),
                    "designs": len({(a["source"], a["design"]) for a, _ in pairs}),
                    "CertiCount": float(np.mean([a["relative_error"] for a, _ in pairs])),
                    "GT-Select (same runs)": mean_of("GT-Select"),
                    "GT-DSL-node (same runs)": mean_of("GT-DSL-node"),
                    "GT-Naive (same runs)": mean_of("GT-Naive"),
                    "cc_minus_select": d_sel, "se": se_sel,
                    "cc_minus_naive": d_naive, "se_naive": se_naive,
                    "identical_estimate": float(np.mean(same)) if same else None,
                })
        main_rows.append(line)

    write_json({"settings": vars(args), "main": main_rows, "summary": summary, "paired": paired_rows},
               out / "summary.json")
    main_cols = ["dataset", "task", "n", "truth", "runs", "releases", "GT-Naive", "GT-Rows", "GT-DSL-node", "GT-Oracle",
                 "GT-Select-design", "GT-Select", "select_rows_share", "design_choice"]
    if tags:
        main_cols += ["CertiCount", "cc_rows_share"]
    md = [
        "# GT-Select: the release choice with reference programs (code only)", "",
        f"ε = {args.eps}, α = {args.clip_alpha}, {args.mechanism}, seed {args.seed}, {args.runs} runs per method "
        f"(run i: noise [seed, i]). Mean relative error, lower is better.", "",
        "* `GT-Naive`: the whole budget on the RR noisy graph, exact count on it (no correction).",
        "* `GT-Rows` / `GT-DSL-node`: rows program / per-node reference program (the matrix program of a pair) alone; "
        "`GT-Oracle`: the better of the two per dataset in hindsight (not a method).",
        "* `GT-Select-design`: design-time choice on public Holme-Kim graphs only; `GT-Select`: + run-time choice from "
        "the published noisy degrees (the CertiCount procedure). `select_rows_share`: runs of GT-Select that ran rows. "
        "`design_choice = refused`: the simulated choice releases nothing (no GT-Select value).",
        "* `CertiCount`: all runs of the accepted LLM designs (" + (", ".join(tags) or "-") + "); `cc_rows_share`: "
        "their runs that read the rows.", "",
        markdown_table(main_rows, main_cols), "",
    ]
    if paired_rows:
        md += ["## CertiCount against GT-Select and GT-Naive on the same runs", "",
               "`cc_minus_select` / `cc_minus_naive`: mean over all (design, run) pairs of RE(CertiCount) − RE(GT-Select) / "
               "RE(GT-Naive) on run index i (negative: the LLM design is better); `identical_estimate`: share of pairs "
               "with the same estimate as GT-Select (the design behaves as the reference pair).", "",
               markdown_table(paired_rows, ["dataset", "task", "designs", "pairs", "CertiCount", "GT-Select (same runs)",
                                            "GT-DSL-node (same runs)", "GT-Naive (same runs)", "cc_minus_select", "se",
                                            "cc_minus_naive", "se_naive", "identical_estimate"]),
               ""]
    md += ["## Details", "", "`bias`: mean signed error / truth; `rmse`: of the signed relative error; `zero_share`: "
           "estimates clamped to 0.", "",
           markdown_table(summary, ["dataset", "task", "method", "runs", "relative_error", "se", "median", "p90", "bias",
                                    "rmse", "zero_share"]), ""]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {out}", flush=True)


if __name__ == "__main__":
    main()
