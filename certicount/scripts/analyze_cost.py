"""Content 5: token / call cost of the reproduction's LLM runs and of each execution mode.

Reads ``transcripts.jsonl`` of the given result directories (default: the
gpt-4.1-mini node + gpt-4.1 curator runs on CU) and tabulates calls and tokens
per role and phase, including the share of output tokens spent on the send
step that code generation removes. Also prints the per-run call model of every
execution mode for the five datasets. No model calls.

    ../.venv/bin/python scripts/analyze_cost.py --tag cost_cu_gpt41mini
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from psc.graph import load_dataset  # noqa: E402
from certicount import REPRO_ROOT  # noqa: E402
from certicount.artifacts import markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.cost import FORBIDDEN_OPTIMISATIONS, calls_per_run, transcript_costs  # noqa: E402

DEFAULT = REPRO_ROOT / "results" / "exp1" / "gpt-4.1-mini-node_gpt-4.1-curator"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="*")
    ap.add_argument("--datasets", default="CU,Do,ML,CS,EE")
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    dirs = [Path(d) for d in args.dirs] or sorted(p.parent for p in DEFAULT.rglob("transcripts.jsonl"))
    rows = []
    for d in dirs:
        c = transcript_costs(d)
        for r in c["rows"]:
            rows.append({"source": d.name, "runs": c["runs"], **r})
    model_rows = []
    for ds in args.datasets.split(","):
        n = load_dataset(REPRO_ROOT / "data", ds)["degree"].vertex_num
        for task, msgs in (("degree", False), ("3-star", False), ("triangle", True)):
            for label, kw in (
                ("baseline / bind / guard", {}),
                ("code send + code aggregate", {"send_by_code": True, "aggregate_by_code": True}),
                ("program (first run)", {"execution": "program", "design_calls": 1}),
                ("program (design cached)", {"execution": "program", "design_calls": 0}),
            ):
                per = calls_per_run(msgs, n, **kw)
                model_rows.append({"dataset": ds, "n": n, "task": task, "mode": label, **per})
    out = out_dir("cost", args.tag, "cost")
    write_json({"dirs": [str(d) for d in dirs], "transcripts": rows, "call_model": model_rows,
                "forbidden": list(FORBIDDEN_OPTIMISATIONS)}, out / "summary.json")
    md = [
        "# Cost", "",
        "## Measured (transcripts)", "",
        markdown_table(rows, ["source", "runs", "task", "method", "role", "phase", "calls", "input_tokens", "output_tokens",
                              "output_share", "elapsed", "usage_missing"]), "",
        "## LLM calls per run by execution mode", "",
        markdown_table(model_rows, ["dataset", "n", "task", "mode", "select", "design", "send", "update", "aggregate", "total", "node"]), "",
        "Forbidden optimisations (side channels or unaccounted interaction): " + "; ".join(FORBIDDEN_OPTIMISATIONS), "",
    ]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")
    write_manifest(out, vars(args))
    print(f"results in {out}")


if __name__ == "__main__":
    main()
