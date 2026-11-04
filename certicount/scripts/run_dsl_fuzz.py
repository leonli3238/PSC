"""Differential test of the sensitivity deriver on random DSL programs (offline, no model calls).

Every program's GS is derived at small public parameters and compared with the
largest change the falsifier finds with the same parameters (node 0, every
``P`` and every flip; on every symmetric graph or on random ones). A refutation
is a bug of the deriver or the interpreter, never of the program, so a campaign
must report 0 refuted and 0 interpreter errors. ``gs / max`` > 1 only means the
bound may be loose (the falsifier's maximum is a lower bound of the true GS).

    ../.venv/bin/python scripts/run_dsl_fuzz.py --count 10000 --workers 8 --tag dsl_fuzz
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from certicount.artifacts import append_jsonl, markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.dsl.fuzz import Setting, run_case, sources, summarize  # noqa: E402


def parse_checks(text: str) -> list[Setting]:
    """``"5x3,7x4:200"`` -> ``[(5, 3, None), (7, 4, 200)]`` (``:k`` = k random graphs)."""
    out: list[Setting] = []
    for part in text.split(","):
        size, _, samples = part.strip().partition(":")
        n, dmax = (int(x) for x in size.split("x"))
        out.append((n, dmax, int(samples) if samples else None))
    return out


def _run(args: tuple) -> object:
    return run_case(*args)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--count", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--depth", type=int, default=3, help="expression depth of the generator")
    ap.add_argument("--focus", type=float, default=0.5, help="share of programs built around a sum of rows")
    ap.add_argument("--checks", default="5x3,7x4:200", help="n x dmax, ':k' for k random symmetric graphs")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()

    settings = parse_checks(args.checks)
    out = out_dir("dsl", args.tag, "dsl_fuzz")
    jobs = [(i, src, settings, args.seed) for i, src in enumerate(sources(args.count, args.seed, args.depth, args.focus))]
    t0 = time.perf_counter()
    cases = []
    if args.workers > 1:
        with ProcessPoolExecutor(args.workers) as pool:
            for case in pool.map(_run, jobs, chunksize=25):
                cases.append(case)
                if len(cases) % 1000 == 0:
                    print(f"{len(cases)}/{args.count} programs, {time.perf_counter() - t0:.0f}s", flush=True)
    else:
        for job in jobs:
            cases.append(_run(job))
            if len(cases) % 1000 == 0:
                print(f"{len(cases)}/{args.count} programs, {time.perf_counter() - t0:.0f}s", flush=True)
    elapsed = time.perf_counter() - t0

    failures = [c for c in cases if c.refuted or c.failed]
    for c in failures:
        append_jsonl(c.to_dict(), out / "failures.jsonl")
    rows = summarize(cases, settings)
    # loosest bounds on the first setting: candidates for a more precise rule
    first = [c for c in cases if c.checks[0].witness is not None and c.checks[0].witness.max_delta > 0]
    loose = sorted(first, key=lambda c: c.checks[0].gs / c.checks[0].witness.max_delta, reverse=True)[:10]
    loose_rows = [{"index": c.index, "gs": c.checks[0].gs, "max_delta": c.checks[0].witness.max_delta,
                   "gs_over_max": c.checks[0].gs / c.checks[0].witness.max_delta,
                   "program": c.source.replace("\n", " ; ")} for c in loose]
    write_json({"settings": [list(s) for s in settings], "count": args.count, "elapsed_seconds": elapsed,
                "summary": rows, "failures": len(failures), "loosest": loose_rows}, out / "summary.json")
    md = [
        "# Deriver fuzz", "",
        f"{args.count} random programs (seed {args.seed}, depth {args.depth}, focus {args.focus}); GS derived at "
        "`PublicParams(n, D = dmax, dmax)` vs the falsifier's largest change on the same parameters "
        f"(node 0, every P, every flip); {elapsed:.0f}s with {args.workers} worker(s).", "",
        "`refuted`: falsifier change > derived GS (a deriver bug, must be 0); `tight`: equal; "
        "`median_gs_over_max` / `max_gs_over_max` over programs with a nonzero change (> 1: possibly loose).", "",
        markdown_table(rows, ["n", "dmax", "graphs", "programs", "derived", "rejected_by_deriver", "interpreter_errors",
                              "falsified", "refuted", "tight", "zero_change", "median_gs_over_max", "max_gs_over_max"]), "",
        f"## Refuted or failing programs: {len(failures)}", "",
    ]
    if failures:
        md += [markdown_table([{"index": c.index, "program": c.source.replace("\n", " ; "),
                                "checks": "; ".join(f"n={k.n} dmax={k.dmax}: gs={k.gs} max="
                                                    f"{k.witness.max_delta if k.witness else None} {k.error or ''}"
                                                    for k in c.checks)} for c in failures[:20]],
                              ["index", "program", "checks"]), "", "Details in `failures.jsonl`.", ""]
    md += [f"## Loosest bounds (n = {settings[0][0]}, dmax = {settings[0][1]})", "",
           markdown_table(loose_rows, ["index", "gs", "max_delta", "gs_over_max", "program"]), ""]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")
    write_manifest(out, vars(args))
    print(f"results in {out}; {len(failures)} refuted or failing program(s) out of {args.count}")


if __name__ == "__main__":
    main()
