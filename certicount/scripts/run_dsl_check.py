"""Check the DSL programs: derived GS vs hand derivation, falsifier, utility test, design loop.

Offline, no model calls (the design loop uses the mock designer unless
``--provider`` is given). Acceptance criteria of the proposal (Table 13): the
derived GS equals ``1``, ``C(D-1, 2)`` and ``dmax - 1`` for the three library
tasks, and at least two out-of-library tasks are designed and verified.

    ../.venv/bin/python scripts/run_dsl_check.py --tag dsl_check
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from psc.models import PROVIDERS, ModelConfig, create_formatter, create_model  # noqa: E402
from certicount.artifacts import markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.dsl import HAND_GS, OUT_OF_LIBRARY, PROGRAMS, Facts, PublicParams, analyst_prompt, derive  # noqa: E402
from certicount.dsl.designer import MockDesignerModel, design_program  # noqa: E402
from certicount.dsl.falsifier import falsify  # noqa: E402
from certicount.dsl.utility import utility_test  # noqa: E402

FACT_ABLATIONS = {
    "all facts": Facts(),
    "no symmetry": Facts(symmetric_rows=False),
    "no self-not-in-P": Facts(self_not_in_private=False),
    "neither": Facts(symmetric_rows=False, self_not_in_private=False),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--n", type=int, default=49, help="n of the GS table (CU has 49 nodes)")
    ap.add_argument("--bounds", default="2,5,8,16,36", help="D = dmax values of the GS table")
    ap.add_argument("--falsify-n", type=int, default=5)
    ap.add_argument("--falsify-dmax", type=int, default=3)
    ap.add_argument("--utility-graphs", type=int, default=30)
    ap.add_argument("--provider", default="mock", choices=PROVIDERS, help="designer model; non-mock calls a real LLM")
    ap.add_argument("--profile", default=None)
    ap.add_argument("--curator-model", default=None)
    ap.add_argument("--flawed-first", action="store_true", help="mock designer: unprojected first draft for k-star tasks")
    args = ap.parse_args()

    out = out_dir("dsl", args.tag, "dsl_check")
    bounds = [int(x) for x in args.bounds.split(",")]
    rows, ablation, fals, util = [], [], [], []
    for task, src in PROGRAMS.items():
        prog = src.parse()
        for b in bounds:
            p = PublicParams(args.n, D=b, dmax=b)
            der = derive(prog, p)
            hand = HAND_GS[task](p)
            rows.append({"task": task, "library": task not in OUT_OF_LIBRARY, "D=dmax": b, "derived_gs": der.gs,
                         "hand_gs": hand, "equal": abs(der.gs - hand) < 1e-9, "facts_used": ",".join(sorted(der.facts_used))})
        t0 = time.perf_counter()
        gs_small = derive(prog, PublicParams(args.falsify_n, args.falsify_dmax, args.falsify_dmax)).gs
        refuted, ce = falsify(prog, gs_small, n=args.falsify_n, dmax=args.falsify_dmax)
        fals.append({"task": task, "graph": "symmetric (exhaustive)", "derived_gs": gs_small, "max_delta": ce.max_delta,
                     "refuted": refuted, "tight": abs(ce.max_delta - gs_small) < 1e-9, "checked": ce.checked,
                     "seconds": round(time.perf_counter() - t0, 2)})
        if prog.uses_rows:
            for name, facts in FACT_ABLATIONS.items():
                for b in bounds:
                    ablation.append({"task": task, "facts": name, "D=dmax": b,
                                     "derived_gs": derive(prog, PublicParams(args.n, b, b), facts).gs})
            _, ce2 = falsify(prog, gs_small, n=args.falsify_n, dmax=args.falsify_dmax, symmetric=False)
            fals.append({"task": task, "graph": "asymmetric rows (sampled)", "derived_gs": gs_small, "max_delta": ce2.max_delta,
                         "refuted": ce2.max_delta > gs_small + 1e-9, "tight": None, "checked": ce2.checked, "seconds": None})
        rep = utility_test(prog, task, count=args.utility_graphs)
        util.append({"task": task, "graphs": rep.graphs, "passed": rep.passed})

    if args.provider == "mock":
        cfg = ModelConfig()
        model = MockDesignerModel(flawed_first=args.flawed_first)
    else:
        cfg = ModelConfig.from_env(provider=args.provider, profile=args.profile, curator_model=args.curator_model)
        model = create_model(cfg, "curator")
    fmt = create_formatter(cfg)
    designs = []
    for task in PROGRAMS:
        res = asyncio.run(design_program(model, fmt, analyst_prompt(task, args.n), args.n,
                                         PublicParams(args.n, D=10, dmax=10), task=task))
        designs.append({"task": task, "accepted": res.accepted, "iterations": res.iterations,
                        "program": res.program.text().replace("\n", " ; ") if res.program else None,
                        "feedback": " | ".join(h["feedback"][:90] for h in res.history)})

    write_json({"gs": rows, "fact_ablation": ablation, "falsifier": fals, "utility": util, "design": designs}, out / "summary.json")
    md = [
        "# DSL check", "",
        f"n = {args.n}; falsifier on n = {args.falsify_n}, dmax = {args.falsify_dmax}; designer = {args.provider}"
        f"{' (flawed first draft)' if args.flawed_first else ''}", "",
        "## Derived vs hand GS", "", markdown_table(rows, ["task", "library", "D=dmax", "derived_gs", "hand_gs", "equal", "facts_used"]), "",
        "## Public facts used by the triangle derivation", "", markdown_table(ablation, ["task", "facts", "D=dmax", "derived_gs"]), "",
        "## Falsifier (node 0, every P, every flip)", "",
        markdown_table(fals, ["task", "graph", "derived_gs", "max_delta", "refuted", "tight", "checked", "seconds"]), "",
        "## Utility test (no noise, no truncation, random public graphs)", "", markdown_table(util, ["task", "graphs", "passed"]), "",
        "## Design loop", "", markdown_table(designs, ["task", "accepted", "iterations", "program", "feedback"]), "",
    ]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")
    write_manifest(out, vars(args))
    ok = all(r["equal"] for r in rows) and not any(f["refuted"] for f in fals if f["graph"].startswith("symmetric"))
    print(f"results in {out}; derived GS = hand GS and no symmetric counterexample: {ok}")


if __name__ == "__main__":
    main()
