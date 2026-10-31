"""Content 6: composite queries with one budget ledger and reuse of published releases.

Code-only execution (no model calls unless ``--planner llm``): each plan's
subqueries share the RR graph and the noisy degrees; the ledger must sum to ε.

    ../.venv/bin/python scripts/run_composite.py --datasets CU,EE --runs 100 --tag composite_r100
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from psc.experiments import run_rng  # noqa: E402
from psc.graph import load_dataset  # noqa: E402
from psc.models import PROVIDERS, ModelConfig, create_formatter, create_model  # noqa: E402
from certicount import DATA_DIR  # noqa: E402
from certicount.artifacts import markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.composite import PLANS, plan_from_keywords, plan_with_llm, run_composite, truth  # noqa: E402


def rel(est: float, true: float) -> float:
    return abs(est - true) / max(abs(true), 1e-3)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", default="CU,EE")
    ap.add_argument("--plans", default=",".join(PLANS))
    ap.add_argument("--question", default=None, help="plan this question instead of --plans")
    ap.add_argument("--planner", default="keywords", choices=("keywords", "llm"))
    ap.add_argument("--provider", default=None, choices=PROVIDERS)
    ap.add_argument("--profile", default=None)
    ap.add_argument("--runs", type=int, default=100)
    ap.add_argument("--eps", type=float, default=2.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--data", default=str(DATA_DIR))
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    if args.question:
        if args.planner == "llm":
            cfg = ModelConfig.from_env(provider=args.provider, profile=args.profile)
            plan = asyncio.run(plan_with_llm(create_model(cfg, "curator"), create_formatter(cfg), args.question))
        else:
            plan = plan_from_keywords(args.question)
        plans = [plan]
    else:
        plans = [PLANS[p] for p in args.plans.split(",")]

    rows, ledgers = [], {}
    for ds in args.datasets.split(","):
        g = load_dataset(args.data, ds)["degree"].graph()
        for plan in plans:
            t = truth(g, plan)
            errs: dict[str, list[float]] = {}
            for i in range(args.runs):
                r = run_composite(g, plan, args.eps, run_rng(args.seed, i))
                assert abs(r["spent"] - args.eps) < 1e-9, r["ledger"]
                ledgers.setdefault(plan.name, r["ledger"])
                for alias in r["estimates"]:
                    errs.setdefault(alias, []).append(rel(r["estimates"][alias], t[alias]))
                errs.setdefault("combined", []).append(rel(r["combined"], t["combined"]))
            for alias, e in errs.items():
                task = dict(plan.subqueries).get(alias, plan.combine)
                e = np.array(e, dtype=float)
                ok = e[np.isfinite(e)]  # a ratio is undefined when its noisy denominator was clamped to 0
                rows.append({"dataset": ds, "plan": plan.name, "part": alias, "task": task, "truth": t[alias],
                             "undefined_runs": int(len(e) - len(ok)),
                             "mean_relative_error": float(ok.mean()) if len(ok) else None,
                             "median_relative_error": float(np.median(ok)) if len(ok) else None})
    out = out_dir("composite", args.tag, "composite")
    write_json({"settings": vars(args), "rows": rows, "ledgers": ledgers}, out / "summary.json")
    md = ["# Composite queries", "", f"ε = {args.eps}, {args.runs} runs; relative error |est - truth| / max(|truth|, 1e-3).", "",
          markdown_table(rows, ["dataset", "plan", "part", "task", "truth", "undefined_runs", "mean_relative_error", "median_relative_error"]), "",
          "## Ledgers", ""]
    for name, ledger in ledgers.items():
        md += [f"### {name}", "", markdown_table(ledger, ["release", "eps", "note"]), ""]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")
    write_manifest(out, vars(args))
    print("\n".join(md))
    print(f"results in {out}")


if __name__ == "__main__":
    main()
