"""P5: attack cases with and without node-side binding and message validation.

Offline (code only; the undefended node is an obedient executor, the defended
node runs certicount's checks). Per dataset, run and attack the success rate,
false-positive rate and membership advantage are reported, plus the realised ε3
of task mismatch and the defence cost on honest runs.

    ../.venv/bin/python scripts/run_attacks.py --datasets CU,EE --runs 10 --tag p5_cu_ee
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from psc.graph import load_dataset  # noqa: E402
from certicount import DATA_DIR  # noqa: E402
from certicount.artifacts import markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.attacks import ATTACK_FUNCS, ATTACKS, AttackOutcome, honest_cost, prepare_setting  # noqa: E402

TASK_OF = {"malicious_rule": ("triangle", "degree"), "task_mismatch": ("triangle",),
           "text_injection": ("triangle",), "forged_messages": ("triangle",)}


def merge(outcomes: list[AttackOutcome]) -> dict:
    tot = AttackOutcome(outcomes[0].attack, outcomes[0].defended, eps3_claimed=outcomes[0].eps3_claimed)
    for o in outcomes:
        for k in ("probed_edges", "recovered_edges", "probed_non_edges", "false_positives", "nodes"):
            setattr(tot, k, getattr(tot, k) + getattr(o, k))
        tot.eps3_actual += o.eps3_actual
        tot.add_rejections(o.rejections)
    return tot.summary()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", default="CU,EE")
    ap.add_argument("--attacks", default=",".join(ATTACKS))
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--eps", type=float, default=2.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--data", default=str(DATA_DIR))
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    out = out_dir("attacks", args.tag, "attacks")
    rows, costs = [], []
    for ds in args.datasets.split(","):
        recs = load_dataset(args.data, ds)
        for attack in args.attacks.split(","):
            for task in TASK_OF[attack]:
                g = recs[task].graph()
                by: dict[bool, list[AttackOutcome]] = defaultdict(list)
                for run in range(args.runs):
                    for defended in (False, True):
                        # same public setting (same noise) for both arms
                        s = prepare_setting(g, task, args.eps, np.random.default_rng([args.seed, run]))
                        by[defended].append(ATTACK_FUNCS[attack](s, np.random.default_rng([args.seed, run, 1]), defended))
                for defended in (False, True):
                    rows.append({"dataset": ds, "task": task, **merge(by[defended])})
        for run in range(args.runs):
            s = prepare_setting(recs["triangle"].graph(), "triangle", args.eps, np.random.default_rng([args.seed, run]))
            costs.append({"dataset": ds, "run": run, **honest_cost(s)})

    agg_cost = []
    for ds in args.datasets.split(","):
        cs = [c for c in costs if c["dataset"] == ds]
        msgs, rej = sum(c["messages"] for c in cs), sum(c["rejected"] for c in cs)
        agg_cost.append({"dataset": ds, "honest_messages": msgs, "rejected": rej, "pass_rate": 1 - rej / msgs if msgs else None,
                         "max_count_change": max(c["max_count_change"] for c in cs)})
    write_json({"settings": vars(args), "rows": rows, "honest_cost": agg_cost}, out / "summary.json")
    cols = ["dataset", "task", "attack", "defended", "nodes", "probed_edges", "success_rate", "false_positive_rate",
            "advantage", "eps3_claimed", "eps3_actual_max", "eps3_actual_median", "frac_nodes_over_claim", "rejections"]
    md = [
        "# P5 attack cases", "",
        f"ε = {args.eps}, {args.runs} runs per dataset (run i uses the noise of seed [{args.seed}, i]); undefended = obedient node, "
        "defended = binding + strict message validation.", "",
        markdown_table(rows, cols), "",
        "## Defence cost on honest runs", "",
        markdown_table(agg_cost, ["dataset", "honest_messages", "rejected", "pass_rate", "max_count_change"]), "",
    ]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")
    write_manifest(out, vars(args))
    print("\n".join(md))
    print(f"results in {out}")


if __name__ == "__main__":
    main()
