"""Empirical sensitivity audit of LLM node agents (ε3 step of PSC).

For logged PSC runs, the node update prompts are rebuilt from
``transcripts.jsonl``, one bit of each node's private neighbour list is
flipped (strategies S1–S4, see :mod:`certicount.audit`), and the node model answers
both prompts ``--repeats`` times with the same system prompt and parser as
:class:`psc.agents.node_agent.NodeAgent`.  The privacy loss of
``L(x) + Lap(GS/ε3)`` against ``L(x') + Lap(GS/ε3)`` is compared with ε3:

* robust violation: every repeat of x and of x' gives the same value and
  ``|L(x) - L(x')| > GS``; then ``ε_emp = ε3 |L(x) - L(x')| / GS``;
* suspect: the repeats differ and the mixture privacy loss exceeds ε3.

Pairs whose loss exceeds ε3 get ``--followup`` extra samples per side, on
which a Clopper–Pearson lower bound ``ε_lb`` is computed (event chosen on the
first samples).  Only ``ε_lb > ε3`` counts as a confirmed violation.

Examples::

    # offline check of the pipeline (mock = exact rule execution; no violation expected)
    .venv/bin/python scripts/run_sensitivity_audit.py --provider mock \\
        --source ../psc-reproduction/results/exp1/gpt-4.1-mini-node_gpt-4.1-curator/gpt41mini-node_gpt41-curator_exp1_CU_degree_r10_PSC --tag _mock_check

    # P1 pilot: CU, gpt-4.1-mini nodes, 2 runs per task, 4 pairs per node, 3 repeats
    .venv/bin/python scripts/run_sensitivity_audit.py --provider openai --profile gpt41 --node-model gpt-4.1-mini \\
        --source ../psc-reproduction/results/exp1/gpt-4.1-mini-node_gpt-4.1-curator/gpt41mini-node_gpt41-curator_exp1_CU_degree_r10_PSC \\
        --source ../psc-reproduction/results/exp1/gpt-4.1-mini-node_gpt-4.1-curator/gpt41mini-node_gpt41-curator_exp1_CU_3-star_r10_PSC \\
        --source ../psc-reproduction/results/exp1/gpt-4.1-mini-node_gpt-4.1-curator/gpt41mini-node_gpt41-curator_exp1_CU_triangle_r10_PSC \\
        --runs 2 --pairs 4 --repeats 3 --tag p1_cu_gpt41mini

    # recompute the tables of an existing audit (no model calls)
    .venv/bin/python scripts/run_sensitivity_audit.py --analyze results/audit/sensitivity/p1_cu_gpt41mini

Outputs in ``results/audit/sensitivity/<tag>/``: ``plan.json`` (node inputs and
pairs), ``samples.jsonl`` (one parsed reply per line, written as calls finish),
``pairs.jsonl`` (per-pair metrics), ``summary.json``, ``table.md``,
``transcripts.jsonl``, ``errors.jsonl`` and ``manifest.json``.  The plan holds
true neighbour lists: keep the directory in trusted storage.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from certicount import DATA_DIR, REPRO_ROOT  # noqa: E402  (puts ../psc-reproduction on sys.path)

from psc.agents.node_agent import parse_update_reply  # noqa: E402
from psc.artifacts import append_run, new_run_directory, write_manifest  # noqa: E402
from certicount.audit import (  # noqa: E402
    VALUE_TOL,
    NodeInput,
    PairSpec,
    analyze_pair,
    parse_update_prompt,
    projection_bound,
    rule_delta,
    select_flips,
    summarize,
)
from psc.events import collect_errors, set_error_sink, set_transcript_sink  # noqa: E402
from psc.graph import load_dataset  # noqa: E402
from psc.models import PROVIDERS, ModelConfig, chat, create_formatter, create_model  # noqa: E402
from psc.prompts import NODE_SYSTEM, strip_structured  # noqa: E402

OUT_BASE = ROOT / "results" / "audit" / "sensitivity"


def resolve_source(src: str | Path) -> Path:
    """A PSC result directory; relative paths are tried from the current
    directory first, then from the reproduction directory ``REPRO_ROOT`` (where the runs live)."""
    p = Path(src)
    if p.is_absolute() or p.exists():
        return p.resolve()
    return (REPRO_ROOT / p).resolve()


# ---------------------------------------------------------------------------
# Plan: node inputs and neighbouring pairs
# ---------------------------------------------------------------------------


def _input_key(inp: NodeInput) -> str:
    return hashlib.sha1(inp.prompt().encode("utf-8")).hexdigest()[:16]


def _input_dict(inp: NodeInput) -> dict:
    return {
        "task": inp.task, "node_id": inp.node_id, "neighbors": list(inp.neighbors),
        "messages": [[s, list(nb)] for s, nb in inp.messages],
        "rule": inp.rule, "state_var": inp.state_var, "state": inp.state,
    }


def _input_from_dict(d: dict) -> NodeInput:
    return NodeInput(
        d["task"], d["node_id"], tuple(d["neighbors"]), tuple((s, tuple(nb)) for s, nb in d["messages"]),
        d["rule"], d["state_var"], d["state"],
    )


def _run_meta(runs: list[dict]) -> dict[tuple, dict]:
    meta = {}
    for r in runs:
        if r.get("method") != "PSC":
            continue
        trace = r["extra"].get("mechanism_trace", {})
        meta[(r["dataset"], r["task"], int(r["extra"]["run"]))] = {
            "gs": float(r["sensitivity"]),
            "eps": tuple(float(e) for e in r["split"]),
            "d_hat_max": r.get("d_hat_max"),
            "node_bounds": trace.get("node_projection_degrees"),
            "node_gs": trace.get("node_sensitivities"),
            "mechanism": r["extra"].get("mechanism"),
        }
    return meta


def _stratified(nodes: list[NodeInput], k: int | None) -> list[NodeInput]:
    """``k`` nodes evenly spread over the degree order (all when ``k`` is None)."""
    if k is None or k >= len(nodes):
        return nodes
    order = sorted(nodes, key=lambda i: (len(i.neighbors), i.node_id))
    idx = sorted({int(round(x)) for x in np.linspace(0, len(order) - 1, k)})
    return [order[i] for i in idx]


def build_plan(args, rng: np.random.Generator) -> dict:
    inputs: dict[str, dict] = {}
    pairs: list[dict] = []
    checks = Counter()
    for src in args.source:
        src = resolve_source(src)
        meta = _run_meta(json.loads((src / "runs.json").read_text()))
        logged: dict[tuple, dict] = {}
        with (src / "transcripts.jsonl").open(encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                if rec.get("phase") != "update" or rec.get("method") != "PSC" or not str(rec.get("agent", "")).startswith("Node-"):
                    continue
                if args.datasets and rec["dataset"] not in args.datasets:
                    continue
                if args.tasks and rec["task"] not in args.tasks:
                    continue
                logged.setdefault((rec["dataset"], rec["task"], int(rec["run"]), rec["agent"]), rec)
        cells = sorted({(d, t) for d, t, _, _ in logged})
        for dataset, task in cells:
            graph = load_dataset(args.data, dataset)[task].graph()
            run_ids = sorted({r for d, t, r, _ in logged if (d, t) == (dataset, task)})[: args.runs]
            for run in run_ids:
                m = meta[(dataset, task, run)]
                recs = [rec for (d, t, r, _), rec in logged.items() if (d, t, r) == (dataset, task, run)]
                parsed = []
                for rec in recs:
                    inp = parse_update_prompt(task, rec["user"])  # raises if the prompt does not round-trip
                    checks["roundtrip_ok"] += 1
                    real = graph.neighbors(inp.node_id)
                    bound = projection_bound(task, m["node_bounds"][inp.node_id] if m["node_bounds"] else m["d_hat_max"])
                    if bound is None:
                        assert list(inp.neighbors) == sorted(real), f"{dataset} {task} run {run} node {inp.node_id}: neighbours differ from the dataset"
                    else:
                        assert set(inp.neighbors) <= set(real) and len(inp.neighbors) == min(len(real), bound), \
                            f"{dataset} {task} run {run} node {inp.node_id}: not a projection of the real list"
                    checks["neighbors_ok"] += 1
                    parsed.append((inp, rec))
                chosen = {i.node_id for i in _stratified([p[0] for p in parsed], args.nodes)}
                for inp, rec in parsed:
                    if inp.node_id not in chosen:
                        continue
                    bound = projection_bound(task, m["node_bounds"][inp.node_id] if m["node_bounds"] else m["d_hat_max"])
                    gs = float(m["node_gs"][inp.node_id]) if m["node_gs"] else m["gs"]
                    x_key = _input_key(inp)
                    inputs[x_key] = _input_dict(inp)
                    logged_value, logged_status = parse_update_reply(rec.get("reply") or "", inp.state_var)
                    for j, flip in enumerate(select_flips(inp, graph.n, bound, args.pairs, rng)):
                        inp2 = inp.with_neighbors(flip.apply(inp.neighbors))
                        x2_key = _input_key(inp2)
                        inputs[x2_key] = _input_dict(inp2)
                        d_rule = rule_delta(inp, flip)
                        if abs(d_rule) > gs + 1e-9:
                            checks["rule_exceeds_gs"] += 1
                        spec = PairSpec(
                            pair_id=f"{src.name}|{dataset}|{task}|r{run}|n{inp.node_id}|p{j}",
                            source=src.name, dataset=dataset, task=task, run=run, node_id=inp.node_id,
                            x_key=x_key, x2_key=x2_key,
                            flip={"op": flip.op, "vertex": flip.vertex, "removed": flip.removed, "note": flip.note},
                            strategy=flip.strategy, gs=gs, eps=m["eps"], bound=bound,
                            degree=len(inp.neighbors), degree2=len(inp2.neighbors), messages=len(inp.messages),
                            valid_messages=inp.valid_messages, valid_messages2=inp2.valid_messages,
                            f_x=inp.rule_value(), f_x2=inp2.rule_value(),
                            prompt_chars=len(strip_structured(inp.prompt())),
                            extra={
                                "logged_model": rec.get("model"), "logged_value": logged_value,
                                "logged_status": logged_status, "mechanism": m["mechanism"],
                            },
                        )
                        pairs.append(spec.to_dict())
    return {"inputs": inputs, "pairs": pairs, "checks": dict(checks)}


# ---------------------------------------------------------------------------
# Model calls
# ---------------------------------------------------------------------------


def _load_samples(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


async def sample_inputs(cfg: ModelConfig, plan: dict, jobs: list[tuple[str, int, str]], out: Path, desc: str) -> None:
    """Ask the node model each ``(input key, repeat, phase)`` of ``jobs``; one line per reply in samples.jsonl."""
    if not jobs:
        return
    model = create_model(cfg, "node")
    formatter = create_formatter(cfg)
    sem = asyncio.Semaphore(max(1, cfg.max_concurrency))
    bar = tqdm(total=len(jobs), desc=desc, unit="call")
    tag = {p["x_key"]: p for p in plan["pairs"]} | {p["x2_key"]: p for p in plan["pairs"]}

    async def one(key: str, rep: int, phase: str) -> None:
        inp = _input_from_dict(plan["inputs"][key])
        p = tag[key]
        async with sem:
            with collect_errors(dataset=p["dataset"], task=p["task"], run=p["run"], node=inp.node_id,
                                input=key, rep=rep, audit_phase=phase):
                text = await chat(model, formatter, NODE_SYSTEM.format(node_id=inp.node_id), inp.prompt(),
                                  agent=f"Node-{inp.node_id}")
        value, status = parse_update_reply(text, inp.state_var)
        append_run(out / "samples.jsonl", {
            "key": key, "rep": rep, "phase": phase, "status": status,
            # a failed parse keeps the node's previous count, as NodeAgent._update does
            "value": inp.state if value is None else value,
            "reply_chars": len(text), "model": cfg.node_model,
        })
        bar.update()

    await asyncio.gather(*(one(*job) for job in jobs))
    bar.close()


def _missing(jobs: list[tuple[str, int, str]], done: list[dict]) -> list[tuple[str, int, str]]:
    have = {(s["key"], s["rep"], s["phase"]) for s in done}
    return [j for j in jobs if j not in have]


# ---------------------------------------------------------------------------
# Analysis and report
# ---------------------------------------------------------------------------


def analyze(plan: dict, samples: list[dict], model: str, alpha: float) -> list[dict]:
    by_key: dict[str, list[dict]] = {}
    for s in samples:
        by_key.setdefault(s["key"], []).append(s)
    rows = []
    for p in plan["pairs"]:
        spec = PairSpec.from_dict(p)
        if spec.x_key not in by_key or spec.x2_key not in by_key:
            continue
        row = analyze_pair(spec, by_key[spec.x_key], by_key[spec.x2_key], alpha)
        row["group"] = "random" if spec.strategy == "S1" else "targeted"
        row["model"] = model
        rows.append(row)
    return rows


def followup_jobs(rows: list[dict], n: int, max_pairs: int) -> list[tuple[str, int, str]]:
    """Pairs whose point loss exceeds ε3, largest first."""
    over = sorted((r for r in rows if r["eps_point"] > r["eps"][2] + VALUE_TOL), key=lambda r: -r["eps_point"])[:max_pairs]
    keys = list(dict.fromkeys(k for r in over for k in (r["x_key"], r["x2_key"])))
    return [(k, rep, "followup") for k in keys for rep in range(n)]


def _fmt(v, digits: int = 3) -> str:
    if v is None:
        return "-"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def markdown(rows: list[dict], summary: list[dict], by_strategy: list[dict], plan: dict, settings: dict) -> str:
    lines = [
        "# LLM node sensitivity audit",
        "",
        f"- model: `{settings['node_model']}` ({settings['provider']}), temperature {settings['temperature']}, "
        f"{settings['repeats']} repeats per input, follow-up {settings['followup']} samples on at most "
        f"{settings['followup_pairs']} pairs, α = {settings['alpha']}",
        f"- sources: {', '.join(f'`{s}`' for s in settings['source_names'])}",
        f"- plan checks: {plan['checks']}",
        "- robust violation: all repeats agree on both inputs and |L(x) − L(x')| > GS; "
        "ε_emp = ε3·|L(x) − L(x')|/GS (else the mixture loss of the repeats); "
        "confirmed: Clopper–Pearson ε_lb > ε3 on the follow-up samples",
        "",
        "## Summary by task (random = S1, targeted = S2–S4)",
        "",
        "| dataset | task | group | pairs | nodes | GS | ε3 | robust viol. | rate (95% CI) | suspect | confirmed / followed | "
        "max ε_emp/ε3 | P95 ε_emp/ε3 | exec err x / x' | jitter x / x' | parse fail x / x' |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in summary:
        gs = _fmt(s["gs_min"], 0) if s["gs_min"] == s["gs_max"] else f"{s['gs_min']:.0f}–{s['gs_max']:.0f}"
        lo, hi = s["violation_ci"]
        lines.append(
            f"| {s['dataset']} | {s['task']} | {s['group']} | {s['pairs']} | {s['nodes']} | {gs} | {s['eps3']:g} | "
            f"{s['robust_violations']} | {s['violation_rate']:.3f} ({lo:.3f}–{hi:.3f}) | {s['suspect']} | "
            f"{s['confirmed']} / {s['followed_up']} | {s['eps_emp_max'] / s['eps3']:.3f} | {s['eps_emp_p95'] / s['eps3']:.3f} | "
            f"{s['exec_error_rate_x']:.3f} / {s['exec_error_rate_x2']:.3f} | {s['jitter_rate_x']:.3f} / {s['jitter_rate_x2']:.3f} | "
            f"{s['failure_rate_x']:.3f} / {s['failure_rate_x2']:.3f} |",
        )
    lines += [
        "",
        "## By strategy",
        "",
        "| dataset | task | strategy | pairs | robust viol. | suspect | max ε_emp/ε3 | mean |Δf|/GS | exec err x' |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for s in by_strategy:
        rs = [r for r in rows if (r["dataset"], r["task"], r["strategy"]) == (s["dataset"], s["task"], s["strategy"])]
        mean_rule = float(np.mean([r["delta_rule"] / r["gs"] for r in rs]))
        lines.append(
            f"| {s['dataset']} | {s['task']} | {s['strategy']} | {s['pairs']} | {s['robust_violations']} | {s['suspect']} | "
            f"{s['eps_emp_max'] / s['eps3']:.3f} | {mean_rule:.3f} | {s['exec_error_rate_x2']:.3f} |",
        )
    top = sorted(rows, key=lambda r: -r["eps_emp"] / r["eps"][2])[:15]
    lines += [
        "",
        "## Largest ε_emp / ε3",
        "",
        "| task | run | node | strategy | flip | |P| → |P'| | GS | f(x) → f(x') | L(x) | L(x') | ε_emp/ε3 | ε_lb | robust |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in top:
        flip = r["flip"]
        what = f"{flip['op']} {flip['vertex']}" + (f" (−{flip['removed']})" if flip["removed"] is not None else "")
        lines.append(
            f"| {r['task']} | {r['run']} | {r['node_id']} | {r['strategy']} | {what} | {r['degree']} → {r['degree2']} | "
            f"{r['gs']:g} | {r['f_x']:g} → {r['f_x2']:g} | {', '.join(f'{v:g}' for v in r['values'])} | "
            f"{', '.join(f'{v:g}' for v in r['values2'])} | {r['eps_emp'] / r['eps'][2]:.3f} | {_fmt(r['eps_lb'])} | "
            f"{_fmt(r['robust_violation'])} |",
        )
    errs = [r for r in rows if r["exec_error"] > 0 or r["exec_error2"] > 0]
    lines += ["", f"## Pairs with an execution error ({len(errs)})", ""]
    if errs:
        lines += [
            "| task | run | node | strategy | flip | f(x) → f(x') | L(x) | L(x') | |Δ_LLM| − |Δf| |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for r in sorted(errs, key=lambda r: (r["task"], r["run"], r["node_id"]))[:60]:
            flip = r["flip"]
            lines.append(
                f"| {r['task']} | {r['run']} | {r['node_id']} | {r['strategy']} | {flip['op']} {flip['vertex']} | "
                f"{r['f_x']:g} → {r['f_x2']:g} | {', '.join(f'{v:g}' for v in r['values'])} | "
                f"{', '.join(f'{v:g}' for v in r['values2'])} | {r['excess']:g} |",
            )
    return "\n".join(lines) + "\n"


def write_report(out: Path, plan: dict, settings: dict) -> list[dict]:
    rows = analyze(plan, _load_samples(out / "samples.jsonl"), settings["node_model"], settings["alpha"])
    (out / "pairs.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    summary = summarize(rows, ("dataset", "task", "group")) + summarize(rows, ("dataset", "task")) if rows else []
    for s in summary:
        s.setdefault("group", "all")
    summary.sort(key=lambda s: (s["dataset"], s["task"], {"random": 0, "targeted": 1, "all": 2}[s["group"]]))
    by_strategy = summarize(rows, ("dataset", "task", "strategy")) if rows else []
    (out / "summary.json").write_text(
        json.dumps({"settings": settings, "checks": plan["checks"], "summary": summary, "by_strategy": by_strategy},
                   indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out / "table.md").write_text(markdown(rows, summary, by_strategy, plan, settings), encoding="utf-8")
    return rows


# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", action="append", default=[], help="PSC result directory with transcripts.jsonl and runs.json (repeatable)")
    ap.add_argument("--analyze", default=None, help="recompute pairs/summary/table of an existing audit directory")
    ap.add_argument("--resume", default=None, help="continue an interrupted audit directory (same settings)")
    ap.add_argument("--data", default=str(DATA_DIR))
    ap.add_argument("--datasets", default=None, help="comma separated subset")
    ap.add_argument("--tasks", default=None, help="comma separated subset")
    ap.add_argument("--runs", type=int, default=2, help="first N logged runs per dataset/task")
    ap.add_argument("--nodes", type=int, default=None, help="nodes per run, spread over the degree order (default: all)")
    ap.add_argument("--pairs", type=int, default=4, help="neighbouring pairs per node")
    ap.add_argument("--repeats", type=int, default=3, help="model calls per input")
    ap.add_argument("--followup", type=int, default=50, help="extra samples per side for pairs whose loss exceeds ε3 (0: none)")
    ap.add_argument("--followup-pairs", type=int, default=20)
    ap.add_argument("--alpha", type=float, default=0.05, help="1 - confidence of ε_lb")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--config", default=None)
    ap.add_argument("--profile", default=None)
    ap.add_argument("--provider", default=None, choices=PROVIDERS)
    ap.add_argument("--node-model", default=None)
    ap.add_argument("--concurrency", type=int, default=None)
    ap.add_argument("--mock-error-rate", type=float, default=0.0)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--out", default=str(OUT_BASE))
    ap.add_argument("--dry-run", action="store_true", help="build the plan and print the call count only")
    ap.add_argument("--log-level", default="ERROR")
    args = ap.parse_args()
    logging.basicConfig(level=args.log_level)

    if args.analyze:
        out = Path(args.analyze)
        plan = json.loads((out / "plan.json").read_text())
        settings = json.loads((out / "settings.json").read_text())
        write_report(out, plan, settings)
        print((out / "table.md").read_text())
        return

    if args.resume:
        out = Path(args.resume)
        plan = json.loads((out / "plan.json").read_text())
        settings = json.loads((out / "settings.json").read_text())
        cfg = ModelConfig.from_env(settings["provider"], config_path=settings["config"], profile=settings["profile"],
                                   node_model=settings["node_model"], max_concurrency=args.concurrency,
                                   mock_error_rate=settings["mock_error_rate"])
    else:
        if not args.source:
            ap.error("--source is required")
        args.datasets = args.datasets.split(",") if args.datasets else None
        args.tasks = args.tasks.split(",") if args.tasks else None
        cfg = ModelConfig.from_env(args.provider, config_path=args.config, profile=args.profile,
                                   node_model=args.node_model, max_concurrency=args.concurrency,
                                   mock_error_rate=args.mock_error_rate)
        plan = build_plan(args, np.random.default_rng(args.seed))
        n_calls = len(plan["inputs"]) * args.repeats
        chars = sum(len(strip_structured(_input_from_dict(d).prompt())) for d in plan["inputs"].values()) * args.repeats
        print(f"plan: {len(plan['pairs'])} pairs, {len(plan['inputs'])} distinct inputs, {n_calls} calls "
              f"(~{chars / 4 / 1e6:.2f}M prompt tokens) + follow-up up to "
              f"{2 * args.followup * args.followup_pairs} calls; checks {plan['checks']}")
        print("pairs per task/strategy:", dict(Counter((p["task"], p["strategy"]) for p in plan["pairs"])))
        if args.dry_run:
            return
        out = new_run_directory(args.out, args.tag, cfg.node_model.replace("/", "_"))
        settings = {
            "provider": cfg.provider, "profile": cfg.profile, "config": args.config, "node_model": cfg.node_model,
            "temperature": cfg.temperature, "node_base_url": cfg.endpoint("node"), "repeats": args.repeats,
            "pairs_per_node": args.pairs, "runs": args.runs, "nodes": args.nodes, "followup": args.followup,
            "followup_pairs": args.followup_pairs, "alpha": args.alpha, "seed": args.seed,
            "mock_error_rate": args.mock_error_rate, "source_names": [Path(s).name for s in args.source],
            "sources": [str(resolve_source(s)) for s in args.source],
        }
        (out / "settings.json").write_text(json.dumps(settings, indent=2) + "\n")
        (out / "plan.json").write_text(json.dumps(plan, ensure_ascii=False) + "\n")
        datasets = sorted({p["dataset"] for p in plan["pairs"]})
        mechanisms = {p["extra"]["mechanism"] for p in plan["pairs"]}
        write_manifest(out, mechanisms.pop() if len(mechanisms) == 1 else "floor_tight", args.data, datasets, settings)

    # a resumed audit keeps what was logged before the interruption
    set_error_sink(out / "errors.jsonl", keep=bool(args.resume))
    set_transcript_sink(out / "transcripts.jsonl", keep=bool(args.resume))

    main_jobs = [(k, rep, "main") for k in plan["inputs"] for rep in range(settings["repeats"])]
    asyncio.run(sample_inputs(cfg, plan, _missing(main_jobs, _load_samples(out / "samples.jsonl")), out, "main"))
    rows = write_report(out, plan, settings)
    if settings["followup"] > 0:
        jobs = followup_jobs(rows, settings["followup"], settings["followup_pairs"])
        asyncio.run(sample_inputs(cfg, plan, _missing(jobs, _load_samples(out / "samples.jsonl")), out, "follow-up"))
        write_report(out, plan, settings)
    print((out / "table.md").read_text())
    print(f"results in {out}")


if __name__ == "__main__":
    main()
