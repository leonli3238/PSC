"""Cost accounting of the execution modes (research content 5).

* :func:`transcript_costs` -- calls, input / output tokens and wall time per
  agent role and phase, from a run directory's ``transcripts.jsonl``;
* :func:`calls_per_run` -- LLM calls of one run for each execution mode.

Every optimisation must state its DP effect. Allowed here: generating the
send message in code (the message is the node's public noisy row), aggregating
in code and caching designs that depend on public data only (all
post-processing). Not allowed: batching several nodes into one prompt (the
nodes' data would interact in a way the GS does not cover) and routing nodes to
models by private information (the choice, its latency and token counts are
visible to the curator or the model provider: a side channel).
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

FORBIDDEN_OPTIMISATIONS = (
    "batch several nodes into one prompt",
    "choose the model / route a node by private information (degree, neighbour list)",
)


def role(agent: str) -> str:
    return "node" if agent.startswith("Node-") else agent.lower()


def transcript_costs(path: str | Path) -> dict:
    p = Path(path)
    if p.is_dir():
        p = p / "transcripts.jsonl"
    cells: dict[tuple, dict] = defaultdict(lambda: {"calls": 0, "input_tokens": 0, "output_tokens": 0, "elapsed": 0.0,
                                                     "user_chars": 0, "reply_chars": 0, "usage_missing": 0})
    runs: set = set()
    with p.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            key = (r.get("dataset"), r.get("task"), r.get("method"), role(r.get("agent", "")), r.get("phase"))
            runs.add((r.get("dataset"), r.get("task"), r.get("method"), r.get("run")))
            c = cells[key]
            c["calls"] += 1
            c["elapsed"] += float(r.get("elapsed") or 0.0)
            c["user_chars"] += len(r.get("user") or "")
            c["reply_chars"] += len(r.get("reply") or "")
            usage = r.get("usage") or {}
            if usage:
                c["input_tokens"] += int(usage.get("input_tokens") or 0)
                c["output_tokens"] += int(usage.get("output_tokens") or 0)
            else:
                c["usage_missing"] += 1
    rows = [dict(zip(("dataset", "task", "method", "role", "phase"), k), **v) for k, v in sorted(cells.items(), key=lambda kv: str(kv[0]))]
    out_total = sum(r["output_tokens"] for r in rows)
    for r in rows:
        r["output_share"] = r["output_tokens"] / out_total if out_total else None
    return {"runs": len(runs), "rows": rows}


def calls_per_run(task_needs_messages: bool, n: int, execution: str = "llm", send_by_code: bool = False,
                  aggregate_by_code: bool = False, design_calls: int = 1) -> dict:
    """LLM calls of one run; ``design_calls`` is the program design loop length
    (0 once cached: the design depends on public data only)."""
    if execution == "program":
        return {"select": 0, "design": design_calls, "send": 0, "update": 0, "aggregate": 0, "total": design_calls, "node": 0}
    send = n if task_needs_messages and not send_by_code else 0
    agg = 0 if aggregate_by_code else 1
    total = 1 + 1 + send + n + agg
    return {"select": 1, "design": 1, "send": send, "update": n, "aggregate": agg, "total": total, "node": send + n}
