"""Degree violation probe (route B): does a local node model break the ε3 claim
of the PSC degree step?  See :mod:`certicount.probe` for the setting and the
statistics, :mod:`certicount.probe_client` for the model calls.

Every model gets its own run directory; the plan (inputs and pairs) is fixed by
``init`` and copied unchanged to the runs of the other models (``--plan-from``).

Commands (all resumable: a rerun only makes the missing calls)::

    init     plan + settings of one run directory (no model call)
    pilot    ~300 calls over the degree bins: error / parse / length / jitter / throughput, time forecast
    screen   few calls on every planned pair; writes the ranked candidates
    rank     recompute the screen tables (no model call)
    confirm  fresh evaluation trials of a fixed pair set; Clopper–Pearson + Bonferroni
    report   tables across run directories (no model call)

Examples (from ``certicount/``)::

    # offline negative controls (mock: exact / bias / edge-correlated error)
    P=../.venv/bin/python
    $P scripts/run_degree_probe.py init --out results/audit/sensitivity/_probe_mock_exact --provider mock \\
        --mock-mode exact --hub-flips 40 --mid-nodes 6 --low-nodes 4
    $P scripts/run_degree_probe.py screen  --out results/audit/sensitivity/_probe_mock_exact
    $P scripts/run_degree_probe.py confirm --out results/audit/sensitivity/_probe_mock_exact --name main --pairs top:40

    # Qwen3-1.7B on a local vLLM server (no thinking, temperature 0, max_tokens 4096 from the config)
    $P scripts/run_degree_probe.py init --out results/audit/sensitivity/probe_pm_degree_qwen3-1.7b \\
        --provider vllm --config ../psc/config.vllm-1.7b.toml --node-model Qwen3-1.7B \\
        --base-url http://127.0.0.1:8001/v1 --concurrency 128
    $P scripts/run_degree_probe.py pilot   --out results/audit/sensitivity/probe_pm_degree_qwen3-1.7b
    $P scripts/run_degree_probe.py screen  --out results/audit/sensitivity/probe_pm_degree_qwen3-1.7b
    $P scripts/run_degree_probe.py confirm --out results/audit/sensitivity/probe_pm_degree_qwen3-1.7b --name main --pairs top:40
    $P scripts/run_degree_probe.py confirm --out results/audit/sensitivity/probe_pm_degree_qwen3-1.7b --name random \\
        --pairs random --select 20

    # Qwen3-8B: same plan; transfer of the 1.7B violations, same random pairs, independent screen
    $P scripts/run_degree_probe.py init --out results/audit/sensitivity/probe_pm_degree_qwen3-8b \\
        --plan-from results/audit/sensitivity/probe_pm_degree_qwen3-1.7b \\
        --provider vllm --config ../psc/config.vllm.toml --node-model Qwen3-8B --base-url http://127.0.0.1:8003/v1
    $P scripts/run_degree_probe.py confirm --out results/audit/sensitivity/probe_pm_degree_qwen3-8b --name transfer \\
        --pairs confirmed:results/audit/sensitivity/probe_pm_degree_qwen3-1.7b/confirm_main --select 30

Outputs of a run directory: ``plan.json`` (true neighbour lists: trusted storage
only), ``settings.json``, ``manifest.json``, ``server.jsonl``; per stage
``samples.jsonl`` (one trial per line), ``replies.jsonl`` (wrong or non-JSON
replies), ``errors.jsonl`` (API failures, retried by a rerun), ``summary.json``
and ``table.md``; ``screen/candidates.jsonl``; ``confirm_<name>/design.json``,
``pairs.jsonl`` and ``confirmed.jsonl``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401  (puts ../psc on sys.path)
from certicount.probe import (  # noqa: E402
    DEGREE_BINS,
    GS,
    analyze,
    as_trials,
    build_plan,
    check_plan,
    degree_bin,
    family_recompute,
    load_graph,
    node_level_pairs,
    node_table,
    plan_hash,
    plan_inputs,
    rank_candidates,
    screen_pair,
    summary_tables,
    top_pairs,
    violation_rate_upper,
)
from certicount.probe_client import load_jsonl, make_client, missing_jobs, run_jobs  # noqa: E402
from psc.prompts import strip_structured  # noqa: E402

DEFAULT_ROOT = ROOT / "results" / "audit" / "sensitivity"


# ---------------------------------------------------------------------------
# Run directory helpers
# ---------------------------------------------------------------------------


def out_dir(value: str) -> Path:
    p = Path(value)
    if not p.is_absolute() and len(p.parts) == 1:
        p = DEFAULT_ROOT / p
    return p.resolve()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False, default=_jsonable), encoding="utf-8")
    tmp.replace(path)


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, default=_jsonable) + "\n")


def _jsonable(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (set, tuple)):
        return list(o)
    raise TypeError(type(o).__name__)


def _git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:  # noqa: BLE001
        return None


def load_run(d: Path) -> tuple[dict, dict]:
    if not (d / "settings.json").exists():
        sys.exit(f"{d}: no settings.json (run `init` first)")
    settings = read_json(d / "settings.json")
    plan = read_json(d / "plan.json")
    if plan_hash(plan) != plan.get("plan_hash"):
        sys.exit(f"{d}/plan.json was modified (hash mismatch)")
    if settings.get("base_url"):
        os.environ["VLLM_NODE_BASE_URL"] = settings["base_url"]
        os.environ.setdefault("OPENAI_BASE_URL", settings["base_url"])
    return settings, plan


async def record_server(d: Path, client, stage: str) -> None:
    """Log the server's models / version; stop at once when it is unreachable or
    does not serve the configured model (instead of retrying every call)."""
    info = await client.server_info()
    from psc.artifacts import append_run

    append_run(d / "server.jsonl", {"stage": stage, "t": time.time(), **info})
    if "models_error" in info:
        raise SystemExit(f"node server {info.get('base_url')} unreachable: {info['models_error']}")
    names = [m.get("id") for m in info.get("models", [])] if "models" in info else None
    if names is not None and getattr(client, "model", None) not in names:
        raise SystemExit(f"server serves {names}, not {client.model!r} (--served-model-name / --node-model)")


def run_stage(d: Path, settings: dict, plan: dict, stage_dir: Path, jobs, desc: str, concurrency: int | None,
              save_all_replies: bool = False) -> dict:
    stage_dir.mkdir(parents=True, exist_ok=True)
    have = load_jsonl(stage_dir / "samples.jsonl")
    todo = missing_jobs(jobs, have)
    print(f"[{desc}] {len(jobs)} trials planned, {len(jobs) - len(todo)} done, {len(todo)} to run")
    stats: dict = {"jobs": 0}
    if todo:
        client = make_client(settings)
        inputs = plan_inputs(plan)

        async def main():
            await record_server(d, client, desc)
            return await run_jobs(client, inputs, todo, stage_dir, concurrency=concurrency or settings["concurrency"],
                                  seed=settings["seed"], desc=desc, save_all_replies=save_all_replies)

        stats = asyncio.run(main())
        from psc.artifacts import append_run

        append_run(stage_dir / "runs.jsonl", {"t": time.time(), "model": settings.get("node_model"), **stats})
        print(f"[{desc}] {stats}")
    left = missing_jobs(jobs, load_jsonl(stage_dir / "samples.jsonl"))
    if left:
        print(f"[{desc}] WARNING: {len(left)} trials missing (API errors, see errors.jsonl); rerun the command")
    return {"missing": len(left), **stats}


def samples_by_key(path: Path, phase: str | None = None) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    seen = set()
    for s in load_jsonl(path):
        if phase is not None and s["phase"] != phase:
            continue
        k = (s["key"], s["phase"], int(s["rep"]))
        if k in seen:
            continue
        seen.add(k)
        out[s["key"]].append(s)
    return out


def _fmt(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.3g}"
    return str(v)


def md_table(rows, cols) -> str:
    if not rows:
        return "(none)\n"
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    return head + "".join("| " + " | ".join(_fmt(r.get(c)) for c in cols) + " |\n" for r in rows)


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------


def design_probe_program(a, plan: dict) -> dict:
    """CertiCount node for the probe: the curator designs the program once from public
    information (``--program-source design``, the analyst prompt of the dataset) or the
    library program is used; the system derives and certifies GS in code. The probe's
    test calibrates the noise with the plan's GS, so the certified GS must equal it."""
    import asyncio

    from certicount.dsl.designer import design_reference_params, design_with_restarts
    from certicount.dsl.library import PROGRAMS
    from certicount.dsl.sensitivity import SensitivityError, certify, verify_certificate
    from psc.graph import load_dataset
    from psc.models import ModelConfig, create_formatter, create_model

    rec = load_dataset(str(Path(certicount.DATA_DIR)), plan["dataset"])[plan["task"]]
    n = rec.vertex_num
    params = design_reference_params(n)
    info: dict = {"source": a.program_source, "n": n, "task": plan["task"]}
    if a.program_source == "library":
        program = PROGRAMS[plan["task"]].parse()
        info.update(designer=None, llm_calls=0, history=[])
    else:
        if not a.config or not a.designer_model:
            sys.exit("--program-source design needs --config and --designer-model (the curator)")
        cfg = ModelConfig.from_env(a.designer_provider, config_path=a.config, profile=a.profile,
                                   curator_model=a.designer_model)
        model, fmt = create_model(cfg, "curator"), create_formatter(cfg)
        res = asyncio.run(design_with_restarts(model, fmt, rec.input_prompt, n, params, task=plan["task"],
                                               max_iterations=a.design_iterations, restarts=a.design_restarts))
        info.update(designer=a.designer_model, llm_calls=res.llm_calls, iterations=res.iterations,
                    restarts=res.restarts, history=res.history, attempts=res.attempts)
        if not res.accepted or res.program is None:
            sys.exit(f"the designer produced no certified program in {res.llm_calls} call(s): {res.history}")
        program = res.program
    if program.uses_rows or program.needs_degree_bound:
        sys.exit(f"program needs public rows / a degree bound, which the probe input lacks:\n{program.text()}")
    try:
        cert = certify(program, params)
    except SensitivityError as exc:
        sys.exit(f"certification failed: {exc}")
    ok, msg = verify_certificate(cert, program, params)
    if not ok:
        sys.exit(f"node-side certificate check failed: {msg}")
    if abs(cert.gs - float(plan["gs"])) > 1e-9:
        sys.exit(f"certified GS {cert.gs:g} differs from the probe's GS {plan['gs']:g}: the test would be miscalibrated")
    info.update(text=program.text(), digest=program.digest, gs=cert.gs, certificate_trace=list(cert.trace),
                certificate_check=msg)
    print(f"[program] {a.program_source}: certified GS = {cert.gs:g} ({msg})\n{program.text()}")
    return info


def cmd_init(a) -> None:
    d = out_dir(a.out)
    if (d / "settings.json").exists() and not a.force:
        sys.exit(f"{d} already initialised (use --force to overwrite settings; the plan is kept)")
    d.mkdir(parents=True, exist_ok=True)
    if a.plan_from:
        src = out_dir(a.plan_from) / "plan.json"
        plan = read_json(src)
        if plan_hash(plan) != plan.get("plan_hash"):
            sys.exit(f"{src} was modified (hash mismatch)")
        if not (d / "plan.json").exists():
            shutil.copyfile(src, d / "plan.json")
    elif (d / "plan.json").exists():
        plan = read_json(d / "plan.json")
    else:
        hub_flips = None if a.hub_flips == "all" else int(a.hub_flips)
        graph = load_graph(a.dataset)
        plan = build_plan(graph, a.dataset, seed=a.seed, mid_nodes=a.mid_nodes, low_nodes=a.low_nodes,
                          hub_flips=hub_flips, constructed=not a.no_constructed, random_per_node=a.random_per_node)
        write_json(d / "plan.json", plan)
    check_plan(plan)
    if a.provider not in ("mock", "program") and not a.node_model:
        sys.exit("--node-model is required for a real model (the --served-model-name of the vLLM server)")
    program = design_probe_program(a, plan) if a.provider == "program" else None
    default_name = "certicount-program" if program else f"mock-{a.mock_mode}"
    settings = {
        "provider": a.provider,
        "config": str(Path(a.config).resolve()) if a.config else None,
        "profile": a.profile,
        "node_model": a.node_model or default_name,
        "base_url": a.base_url,
        "concurrency": a.concurrency,
        "seed": a.seed,
        "guided_json": a.guided_json,
        "mock": {"mode": a.mock_mode, "rate": a.mock_rate, "trigger": a.mock_trigger} if a.provider == "mock" else None,
        "plan_hash": plan["plan_hash"],
        "plan_from": str(out_dir(a.plan_from)) if a.plan_from else None,
    }
    if program is not None:
        settings["program"] = program
    if a.provider not in ("mock", "program"):
        from psc.models import ModelConfig

        if a.base_url:
            os.environ["VLLM_NODE_BASE_URL"] = a.base_url
        cfg = ModelConfig.from_env(a.provider, config_path=settings["config"], profile=a.profile, node_model=a.node_model)
        settings["decoding"] = {
            "temperature": cfg.temperature, "extra": cfg.role_extra("node"), "stream": cfg.stream,
            "structured_input": cfg.use_structured_input, "max_retries": cfg.max_retries,
        }
        if cfg.temperature != 0:
            print(f"WARNING: temperature = {cfg.temperature} (PSC runs at 0)")
        if cfg.use_structured_input:
            sys.exit("structured_input must be off for a real model (PSC strips the block)")
    write_json(d / "settings.json", settings)
    write_json(d / "manifest.json", {
        "argv": sys.argv, "created": time.strftime("%Y-%m-%d %H:%M:%S"), "python": platform.python_version(),
        "host": platform.node(), "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain", "--", ".")),
    })
    counts = Counter((p["kind"], p["tier"], p["family"]) for p in plan["pairs"])
    print(f"{d}\n  inputs {len(plan['inputs'])}, pairs {len(plan['pairs'])}, "
          f"random_ref {sum(p['random_ref'] for p in plan['pairs'])}, plan_hash {plan['plan_hash']}")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")


# ---------------------------------------------------------------------------
# pilot
# ---------------------------------------------------------------------------


def screen_jobs(plan: dict, x_reps: int, x2_reps: int, pairs=None) -> list[tuple[str, str, int]]:
    reps: dict[str, int] = {}
    for p in pairs if pairs is not None else plan["pairs"]:
        reps[p["x_key"]] = max(reps.get(p["x_key"], 0), x_reps)
        reps[p["x2_key"]] = max(reps.get(p["x2_key"], 0), x2_reps)
    return [(k, "screen", r) for k, n in sorted(reps.items()) for r in range(n)]


def _q(vals, q):
    return float(np.quantile(vals, q)) if vals else None


def stage_stats(samples: list[dict], plan: dict) -> list[dict]:
    """Per degree bin: execution error, parse source, length, truncation, jitter."""
    by_bin: dict[str, list[dict]] = defaultdict(list)
    for s in samples:
        by_bin[degree_bin(s["degree"])].append(s)
    rows = []
    order = [degree_bin(lo) for lo, _ in DEGREE_BINS]
    for b in sorted(by_bin, key=lambda x: order.index(x) if x in order else 99):
        ss = by_bin[b]
        toks = [s["completion_tokens"] for s in ss if s.get("completion_tokens") is not None]
        per_key: dict[str, set] = defaultdict(set)
        n_key: Counter = Counter()
        for s in ss:
            per_key[s["key"]].add(round(s["value"], 6))
            n_key[s["key"]] += 1
        multi = [k for k in per_key if n_key[k] > 1]
        st = Counter(s["status"] for s in ss)
        rows.append({
            "bin": b, "trials": len(ss), "inputs": len(per_key),
            "exec_error": sum(not s["correct"] for s in ss) / len(ss),
            "abs_err_mean": float(np.mean([abs(s["value"] - s["rule"]) for s in ss])),
            "json": st["json"] / len(ss), "number": st["number"] / len(ss), "failed": st["failed"] / len(ss),
            "length_cut": sum(s.get("finish_reason") == "length" for s in ss) / len(ss),
            "tok_mean": float(np.mean(toks)) if toks else None, "tok_p50": _q(toks, 0.5), "tok_p95": _q(toks, 0.95),
            "tok_max": max(toks) if toks else None,
            "jitter_inputs": (sum(len(per_key[k]) > 1 for k in multi) / len(multi)) if multi else None,
        })
    return rows


def cmd_pilot(a) -> None:
    d = out_dir(a.out)
    settings, plan = load_run(d)
    rng = np.random.default_rng(settings["seed"] + 17)
    real = {}
    for p in plan["pairs"]:
        if p["kind"] == "real":
            real[p["x_key"]] = p["degree"]
    by_bin: dict[str, list[str]] = defaultdict(list)
    for k, deg in sorted(real.items()):
        by_bin[degree_bin(deg)].append(k)
    keys = []
    for b, ks in sorted(by_bin.items()):
        keys += rng.choice(ks, size=min(a.per_bin, len(ks)), replace=False).tolist()
    keys += [k for k, v in plan["inputs"].items() if v["kind"] == "constructed" and len(v["neighbors"]) >= 350][:2]
    jobs = [(k, "pilot", r) for k in sorted(keys) for r in range(a.reps)]
    stage = d / "pilot"
    t0 = time.time()
    stats = run_stage(d, settings, plan, stage, jobs, "pilot", a.concurrency, save_all_replies=True)
    samples = [s for s in load_jsonl(stage / "samples.jsonl") if s["phase"] == "pilot"]
    rows = stage_stats(samples, plan)
    runs = load_jsonl(stage / "runs.jsonl")
    wall = sum(r.get("wall_seconds", 0) for r in runs) or (time.time() - t0)
    ctoks = sum(r.get("completion_tokens", 0) for r in runs)
    calls = sum(r.get("calls", 0) for r in runs)
    tput = ctoks / wall if wall > 0 else None
    # forecast: screen jobs weighted by the mean length of their degree bin
    tok_by_bin = {r["bin"]: r["tok_mean"] for r in rows if r["tok_mean"] is not None}
    fallback = float(np.mean(list(tok_by_bin.values()))) if tok_by_bin else None
    deg_of = {k: len(v["neighbors"]) for k, v in plan["inputs"].items()}

    def forecast(js):
        if not tput or fallback is None:
            return None
        toks = sum(tok_by_bin.get(degree_bin(deg_of[k]), fallback) for k, _, _ in js)
        return {"calls": len(js), "completion_tokens": round(toks), "hours": round(toks / tput / 3600, 2)}

    sj = screen_jobs(plan, a.x_reps, a.x2_reps)
    hub_keys = [k for k, v in plan["inputs"].items() if len(v["neighbors"]) > 30]
    confirm_like = [(k, "eval", r) for k in hub_keys[: 2 * a.top] for r in range(a.eval)][: 2 * a.top * a.eval]
    summary = {
        "model": settings["node_model"], "calls": calls, "wall_seconds": round(wall, 1),
        "completion_tokens": ctoks, "throughput_tok_s": round(tput, 1) if tput else None,
        "note": "pilot throughput at this small load can underestimate the steady state; refine after the first screen hour",
        "by_bin": rows,
        "forecast_screen": forecast(sj),
        "forecast_confirm_upper": forecast(confirm_like),
        "json_rate": (sum(s["status"] == "json" for s in samples) / len(samples)) if samples else None,
        "stats": stats,
    }
    if summary["json_rate"] is not None and summary["json_rate"] < 0.7:
        summary["advice"] = ("JSON rate < 70%: keep the PSC setting for the main run and add a guided_json "
                             "ablation run (init --guided-json) to separate format failures from count errors")
    write_json(stage / "summary.json", summary)
    md = (f"# Pilot: {settings['node_model']}\n\ncalls {calls}, wall {wall:.0f}s, completion tokens {ctoks}, "
          f"throughput {summary['throughput_tok_s']} tok/s, JSON rate {_fmt(summary['json_rate'])}\n\n"
          + md_table(rows, ["bin", "trials", "inputs", "exec_error", "abs_err_mean", "json", "number", "failed",
                            "length_cut", "tok_mean", "tok_p95", "tok_max", "jitter_inputs"])
          + f"\nforecast screen: {summary['forecast_screen']}\n\nforecast confirm (upper): {summary['forecast_confirm_upper']}\n")
    (stage / "table.md").write_text(md, encoding="utf-8")
    print(md)


# ---------------------------------------------------------------------------
# screen / rank
# ---------------------------------------------------------------------------


def _filter_pairs(plan: dict, only: str | None, max_per_node: int | None = None, seed: int = 0) -> list[dict]:
    """Pairs in scope: ``only`` keeps kinds / tiers / families; ``max_per_node``
    keeps at most that many pairs per input ``x`` (the random reference pairs
    first, then a seeded uniform sample) — a subsample, never 'exhaustive'."""
    pairs = plan["pairs"]
    if only:
        want = set(only.split(","))
        pairs = [p for p in pairs if p["kind"] in want or p["tier"] in want or p["family"] in want]
    if max_per_node:
        rng = np.random.default_rng(seed + 29)
        by_x: dict[str, list[dict]] = defaultdict(list)
        for p in pairs:
            by_x[p["x_key"]].append(p)
        kept = []
        for k in sorted(by_x):
            ps = by_x[k]
            ref = [p for p in ps if p.get("random_ref")]
            rest = [p for p in ps if not p.get("random_ref")]
            take = max(0, max_per_node - len(ref))
            idx = sorted(rng.choice(len(rest), size=min(take, len(rest)), replace=False).tolist()) if rest else []
            kept += ref + [rest[i] for i in idx]
        pairs = kept
    return pairs


def cmd_screen(a) -> None:
    d = out_dir(a.out)
    settings, plan = load_run(d)
    pairs = _filter_pairs(plan, a.only, a.max_per_node, settings["seed"])
    from psc.artifacts import append_run

    (d / "screen").mkdir(parents=True, exist_ok=True)
    in_scope = {p["pair_id"] for p in pairs}
    append_run(d / "screen" / "scope.jsonl", {
        "t": time.time(), "only": a.only, "max_per_node": a.max_per_node, "pairs": len(pairs),
        "x_reps": a.x_reps, "x2_reps": a.x2_reps,
        "exhaustive_hubs": all(p["pair_id"] in in_scope for p in plan["pairs"] if p["family"] == "E"),
    })
    jobs = screen_jobs(plan, a.x_reps, a.x2_reps, pairs)
    run_stage(d, settings, plan, d / "screen", jobs, "screen", a.concurrency)
    cmd_rank(a)


def cmd_rank(a) -> None:
    d = out_dir(a.out)
    _, plan = load_run(d)
    by_key = samples_by_key(d / "screen" / "samples.jsonl", "screen")
    rows = [screen_pair(p, by_key.get(p["x_key"], []), by_key.get(p["x2_key"], [])) for p in plan["pairs"]]
    rows = [r for r in rows if r["complete"]]
    cands = rank_candidates(rows)
    write_jsonl(d / "screen" / "pairs.jsonl", rows)
    write_jsonl(d / "screen" / "candidates.jsonl", cands)
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        groups[(r["kind"], r["bin"], r["family"])].append(r)
        for t in r["tags"]:
            groups[(r["kind"], r["bin"], "tag:" + t)].append(r)
    table = []
    for (kind, b, fam), rs in sorted(groups.items()):
        st = Counter()
        for r in rs:
            st.update(r["statuses"])
        tot = sum(st.values()) or 1
        table.append({
            "kind": kind, "bin": b, "family": fam, "pairs": len(rs),
            "candidates": sum(r["candidate"] for r in rs),
            "cand_rate": sum(r["candidate"] for r in rs) / len(rs),
            "delta_max": max(r["delta_max"] for r in rs),
            "exec_error_x": float(np.mean([r["exec_error"] for r in rs])),
            "exec_error_x2": float(np.mean([r["exec_error2"] for r in rs])),
            "jitter": float(np.mean([r["jitter"] for r in rs])),
            "json": st["json"] / tot, "number": st["number"] / tot, "failed": st["failed"] / tot,
        })
    screen_samples = [s for ss in by_key.values() for s in ss]
    summary = {
        "pairs_screened": len(rows), "pairs_planned": len(plan["pairs"]), "candidates": len(cands),
        "by_group": table, "by_bin": stage_stats(screen_samples, plan),
        "top": [{k: c[k] for k in ("pair_id", "kind", "bin", "family", "delta_max", "frac_far", "values", "values2")}
                for c in cands[:a.top]],
    }
    write_json(d / "screen" / "summary.json", summary)
    md = (f"# Screen\n\npairs screened {len(rows)} / {len(plan['pairs'])}, candidates (observed |Δ| > GS) {len(cands)}"
          " — descriptive, no statistical claim\n\n## Per degree bin (all screen trials)\n\n"
          + md_table(summary["by_bin"], ["bin", "trials", "inputs", "exec_error", "abs_err_mean", "json", "number",
                                         "failed", "length_cut", "tok_mean", "tok_p95", "jitter_inputs"])
          + "\n## Per kind × bin × family / tag\n\n"
          + md_table(table, ["kind", "bin", "family", "pairs", "candidates", "cand_rate", "delta_max",
                             "exec_error_x", "exec_error_x2", "jitter", "json", "number", "failed"])
          + f"\n## Top {a.top} candidates\n\n"
          + md_table(summary["top"], ["pair_id", "kind", "bin", "family", "delta_max", "frac_far"]))
    (d / "screen" / "table.md").write_text(md, encoding="utf-8")
    print(f"[rank] screened {len(rows)} pairs, {len(cands)} candidates -> {d / 'screen'}")


# ---------------------------------------------------------------------------
# confirm
# ---------------------------------------------------------------------------


def locate(path: str | Path, hint: Path | None = None) -> Path:
    """A path recorded in a design (absolute, possibly on another machine):
    as is, else ``<run>/<confirm set>/<file>`` under the result root or next to
    ``hint``'s run directory.  Exits when nothing is found (never a silent 0)."""
    p = Path(path)
    if p.exists():
        return p
    tail = p.parts[-3:]
    roots = [DEFAULT_ROOT] + ([hint.parent] if hint is not None else [])
    for root in roots:
        q = root.joinpath(*tail)
        if q.exists():
            return q
    sys.exit(f"cannot find {p} (also tried {', '.join(str(r.joinpath(*tail)) for r in roots)})")


def resolve_pairs(d: Path, plan: dict, spec: str, per_node: int | None = None) -> tuple[list[str], dict]:
    by_id = {p["pair_id"] for p in plan["pairs"]}
    if spec.startswith("top:"):
        m = int(spec[4:])
        path = d / "screen" / "candidates.jsonl"
        if not path.exists():
            sys.exit("no screen/candidates.jsonl: run `screen` first")
        ids = top_pairs(load_jsonl(path), m, per_node)
        return ids, {"source": "screen_top", "top": m, "per_node": per_node}
    if spec == "nodes":
        path = d / "screen" / "pairs.jsonl"
        if not path.exists():
            sys.exit("no screen/pairs.jsonl: run `screen` first (the node-level design needs this model's screen)")
        ids, universe = node_level_pairs(plan, load_jsonl(path))
        return ids, {"source": "nodes", "universe": universe}
    if spec == "random":
        return [p["pair_id"] for p in plan["pairs"] if p.get("random_ref")], {"source": "random_ref"}
    if spec.startswith("confirmed:") or spec.startswith("file:"):
        path = out_dir(spec.split(":", 1)[1])
        if path.is_dir():
            design = read_json(path / "design.json")
            if design["plan_hash"] != plan["plan_hash"]:
                sys.exit(f"{path}: other plan ({design['plan_hash']} vs {plan['plan_hash']})")
            path = path / ("confirmed.jsonl" if spec.startswith("confirmed:") else "pairs.jsonl")
        rows = load_jsonl(path) if path.suffix == ".jsonl" else read_json(path)
        ids = [r["pair_id"] if isinstance(r, dict) else str(r) for r in rows]
        bad = [i for i in ids if i not in by_id]
        if bad:
            sys.exit(f"{len(bad)} pair ids are not in this plan, e.g. {bad[0]}")
        return ids, {"source": spec.split(":", 1)[0], "path": str(path)}
    sys.exit(f"unknown --pairs {spec!r} (top:N [--per-node K] | nodes | random | confirmed:DIR | file:PATH)")


def cmd_confirm(a) -> None:
    d = out_dir(a.out)
    settings, plan = load_run(d)
    cdir = d / f"confirm_{a.name}"
    pairs_by_id = {p["pair_id"]: p for p in plan["pairs"]}
    screen = samples_by_key(d / "screen" / "samples.jsonl", "screen")
    if (cdir / "design.json").exists():
        design = read_json(cdir / "design.json")
        for k, v in (("eval", a.eval), ("eval_jitter", a.eval_jitter), ("select", a.select), ("alpha", a.alpha),
                     ("pairs_spec", a.pairs)):
            if design[k] != v:
                sys.exit(f"{cdir}: design has {k}={design[k]}, got {v} (use another --name for a new design)")
        if design["pair_source"].get("per_node") != a.per_node and design["pair_source"]["source"] == "screen_top":
            sys.exit(f"{cdir}: design has per_node={design['pair_source'].get('per_node')}, got {a.per_node}")
        ids = design["pair_ids"]
    else:
        ids, src = resolve_pairs(d, plan, a.pairs, a.per_node)
        ids = list(dict.fromkeys(ids))
        if not ids:
            if src.get("universe") is not None:
                write_json(cdir / "nodes_universe.json", src["universe"])
            sys.exit("no pairs to confirm (zero screen candidates or empty list): report the screen result")
        jittery = []
        for i in ids:
            p = pairs_by_id[i]
            vals = {round(s["value"], 6) for s in screen.get(p["x_key"], [])}
            vals2 = {round(s["value"], 6) for s in screen.get(p["x2_key"], [])}
            if len(vals) > 1 or len(vals2) > 1:
                jittery.append(i)
        design = {
            "name": a.name, "pairs_spec": a.pairs, "pair_source": src, "pair_ids": ids, "m": len(ids),
            "alpha": a.alpha, "alpha_pair": a.alpha / len(ids), "eval": a.eval, "eval_jitter": a.eval_jitter,
            "jitter_pairs": jittery, "select": a.select, "plan_hash": plan["plan_hash"],
            # Laplace draws are a hash of (salt, input, phase, rep): a salt per model and design keeps the
            # noise of different confirmation sets / models independent
            "noise_salt": f"{settings['seed']}|{settings['node_model']}|{a.name}",
            "model": settings["node_model"], "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "note": "fixed before any evaluation trial; Bonferroni over the m pairs of this design",
        }
        write_json(cdir / "design.json", design)
    pairs = [pairs_by_id[i] for i in ids]
    jittery = set(design["jitter_pairs"])
    n_eval: dict[str, int] = {}
    n_sel: dict[str, int] = {}
    for p in pairs:
        n = design["eval_jitter"] if p["pair_id"] in jittery else design["eval"]
        for k in (p["x_key"], p["x2_key"]):
            n_eval[k] = max(n_eval.get(k, 0), n)
            n_sel[k] = design["select"]
    jobs = [(k, "eval", r) for k, n in sorted(n_eval.items()) for r in range(n)]
    jobs += [(k, "select", r) for k, n in sorted(n_sel.items()) for r in range(n)]
    missing_sel = [k for k in n_sel if not screen.get(k) and design["select"] == 0]
    if missing_sel:
        sys.exit(f"{len(missing_sel)} inputs have no screen trials in this run: set --select (e.g. 30) "
                 "for fresh selection trials (another model's screen cannot select the test)")
    st = run_stage(d, settings, plan, cdir, jobs, f"confirm_{a.name}", a.concurrency)
    if st["missing"] and not a.allow_incomplete:
        sys.exit("trials missing: rerun (or --allow-incomplete to analyse what is there)")
    analyze_confirm(d, settings, plan, cdir, design, pairs, screen)


def analyze_confirm(d: Path, settings: dict, plan: dict, cdir: Path, design: dict, pairs, screen) -> None:
    own = samples_by_key(cdir / "samples.jsonl")
    inputs = plan_inputs(plan)
    rows = []
    for p in pairs:
        def trials(key):
            ss = own.get(key, [])
            sel = as_trials(screen.get(key, []), "screen") + as_trials([s for s in ss if s["phase"] == "select"], "select")
            ev = as_trials([s for s in ss if s["phase"] == "eval"], "eval")
            return sel, ev

        sel, ev = trials(p["x_key"])
        sel2, ev2 = trials(p["x2_key"])
        if not ev or not ev2:
            continue
        row = analyze(plan, p, sel, sel2, ev, ev2, design["alpha_pair"], design["noise_salt"])
        row["prompt_chars"] = len(strip_structured(inputs[p["x_key"]].prompt()))
        row["model"] = settings["node_model"]
        rows.append(row)
    write_jsonl(cdir / "pairs.jsonl", rows)
    viol = [r for r in rows if r["violation"]]
    write_jsonl(cdir / "confirmed.jsonl", viol)
    tables = summary_tables(rows)
    tested = tables["overall"]["tested"]
    tables["overall"]["violation_share_upper95"] = violation_rate_upper(len(viol), tested)
    universe = design["pair_source"].get("universe")
    if universe is not None:
        tables["nodes"] = node_table(universe, rows)
    summary = {"design": {k: v for k, v in design.items() if k != "pair_ids"}, "model": settings["node_model"], **tables}
    write_json(cdir / "summary.json", summary)
    o = tables["overall"]
    node_md = ""
    if universe is not None:
        node_md = ("## Node level (one most suspicious pair per selected real node)\n\n"
                   "`confirmed_share` is a lower bound on the share of violating nodes among the selected nodes "
                   "of the bin (unconfirmed nodes may still violate; hub nodes are all PM nodes of degree > 30, "
                   "the other bins are samples).\n\n"
                   + md_table(tables["nodes"], ["bin", "nodes", "with_candidate", "tested", "confirmed",
                                                "confirmed_share"]) + "\n")
    md = (f"# Confirm `{design['name']}` — {settings['node_model']}\n\n"
          f"pairs {design['m']} ({design['pairs_spec']}"
          + (f", per node ≤ {design['pair_source']['per_node']}" if design["pair_source"].get("per_node") else "")
          + f"), family α = {design['alpha']}, per pair α/m = "
          f"{design['alpha_pair']:.2e}, eval trials per side {design['eval']} (jittery pairs {design['eval_jitter']}), "
          f"extra selection trials {design['select']}\n\n"
          f"**violations (ε_lb > ε3 = {plan['eps'][2]}): {o['violations']} / {o['tested']}**, of which real-node "
          f"count-error type {o['violations_real_count']}; ε_lb max {_fmt(o['eps_lb_max'])}, median "
          f"{_fmt(o['eps_lb_median'])}; max observed |Δ| {_fmt(o['max_delta_llm'])} (descriptive); "
          f"distinct inputs x among the pairs {len({r['x_key'] for r in rows})}, among the violations "
          f"{len({r['x_key'] for r in viol})}\n\n"
          "An audit only refutes: zero violations is no evidence of privacy.\n\n"
          + node_md +
          "## Violations by kind × bin × category\n\n"
          + md_table(tables["violations_by_category"], ["kind", "bin", "category", "violations"])
          + "\n## By kind × bin × family\n\n"
          + md_table(tables.get("by_kind_bin_family", []),
                     ["kind", "bin", "family", "pairs", "tested", "violations", "eps_lb_max", "eps_lb_median",
                      "max_delta_llm_over_gs", "exec_error_rate_x", "exec_error_rate_x2", "jitter_rate_x",
                      "failure_rate_x"])
          + "\n## Confirmed pairs\n\n"
          + md_table(sorted(viol, key=lambda r: -r["eps_lb"]),
                     ["pair_id", "kind", "bin", "family", "category", "eps_lb", "delta_llm_max", "exec_error",
                      "exec_error2"]))
    (cdir / "table.md").write_text(md, encoding="utf-8")
    print(md)


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


def cmd_report(a) -> None:
    runs = [out_dir(r) for r in a.runs]
    want = set(a.sets.split(",")) if a.sets else None
    rows, bins, transfer, nodes = [], [], [], []
    family_sets: dict[str, dict[str, list[dict]]] = defaultdict(dict)
    for d in runs:
        settings = read_json(d / "settings.json")
        model = settings["node_model"]
        ssum = d / "screen" / "summary.json"
        if ssum.exists():
            for b in read_json(ssum)["by_bin"]:
                bins.append({"model": model, **b})
        for cdir in sorted(d.glob("confirm_*")):
            if not (cdir / "summary.json").exists():
                continue
            s = read_json(cdir / "summary.json")
            o, des = s["overall"], s["design"]
            if want is not None and des["name"] not in want:
                continue
            rows.append({"model": model, "set": des["name"], "source": des["pair_source"]["source"], **o})
            pair_rows = load_jsonl(cdir / "pairs.jsonl")
            scope = "all" if a.family_scope == "all" else model
            family_sets[scope][f"{model}/{des['name']}"] = pair_rows
            ids = {r["pair_id"] for r in pair_rows if r.get("violation")}
            for n in s.get("nodes", []):
                nodes.append({"model": model, "set": des["name"], **n})
            src = des["pair_source"].get("path")
            if des["pair_source"]["source"] == "confirmed" and src:
                src_path = locate(src, d)
                src_rows = load_jsonl(src_path)
                src_ids = {r["pair_id"] for r in src_rows}
                cats = Counter(r["category"] for r in src_rows)
                transfer.append({"model": model, "set": des["name"], "from": src_path.parent.parent.name,
                                 "source_violations": len(src_ids), "retained": len(ids & src_ids),
                                 "retention": len(ids & src_ids) / len(src_ids) if src_ids else None,
                                 "source_categories": dict(cats)})
    family, family_totals = [], []
    for scope, sets in family_sets.items():
        fr, tot = family_recompute(sets, a.family_alpha)
        family += [{"scope": scope, **r} for r in fr]
        family_totals.append({"scope": scope, **tot})
    outd = out_dir(a.report_dir) if a.report_dir else (DEFAULT_ROOT / "probe_report")
    outd.mkdir(parents=True, exist_ok=True)
    write_json(outd / "report.json", {"runs": [str(r) for r in runs], "confirm": rows, "screen_bins": bins,
                                      "transfer": transfer, "nodes": nodes, "family": family,
                                      "family_totals": family_totals})
    md = ("# Degree probe report\n\n## Confirmation sets (each at its own family α)\n\n"
          + md_table(rows, ["model", "set", "source", "pairs", "tested", "violations", "violations_real_count",
                            "violation_share_upper95", "eps_lb_max", "eps_lb_median", "max_delta_llm"])
          + f"\n## Joint Bonferroni over the sets (family α = {a.family_alpha}, scope = {a.family_scope})\n\n"
          "Every tested pair of the scope is re-bounded at α/M from its stored evaluation counts (the test was "
          "chosen on selection trials only); these are the numbers for a single joint claim.\n\n"
          + md_table(family_totals, ["scope", "M", "alpha_pair", "violations_family", "violations_family_real_count"])
          + "\n" + md_table(family, ["scope", "set", "tested", "violations_design", "violations_family",
                                    "violations_family_real_count", "eps_lb_family_max"])
          + "\n## Node level\n\n"
          + md_table(nodes, ["model", "set", "bin", "nodes", "with_candidate", "tested", "confirmed",
                             "confirmed_share"])
          + "\n## Transfer of confirmed violations\n\n"
          + md_table(transfer, ["model", "set", "from", "source_violations", "retained", "retention"])
          + "\n## Screen: execution by model × degree bin\n\n"
          + md_table(bins, ["model", "bin", "trials", "exec_error", "abs_err_mean", "json", "number", "failed",
                            "length_cut", "tok_mean", "jitter_inputs"]))
    (outd / "report.md").write_text(md, encoding="utf-8")
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(11, 4))
        models = list(dict.fromkeys(r["model"] for r in rows))
        for name in sorted({r["set"] for r in rows}):
            ys = [next((r["violations"] / r["tested"] for r in rows if r["model"] == m and r["set"] == name
                        and r["tested"]), np.nan) for m in models]
            axes[0].plot(models, ys, marker="o", label=name)
        axes[0].set_ylabel("confirmed violations / tested pairs")
        axes[0].set_title("violations by model")
        axes[0].legend()
        for m in dict.fromkeys(b["model"] for b in bins):
            bb = [b for b in bins if b["model"] == m]
            axes[1].plot([b["bin"] for b in bb], [b["exec_error"] for b in bb], marker="o", label=m)
        axes[1].set_xlabel("degree bin")
        axes[1].set_ylabel("execution error rate (screen)")
        axes[1].legend()
        fig.tight_layout()
        fig.savefig(outd / "probe_models.png", dpi=150)
    except ImportError:
        print("matplotlib not installed: no figure")
    print(md)
    print(f"-> {outd}")


# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, needs_out=True):
        if needs_out:
            p.add_argument("--out", required=True, help="run directory (a bare name goes under results/audit/sensitivity)")
        p.add_argument("--concurrency", type=int, default=None, help="override the run's concurrency")
        p.add_argument("--top", type=int, default=40)

    p = sub.add_parser("init")
    common(p)
    p.add_argument("--provider", choices=("mock", "vllm", "openai", "program"), required=True,
                   help="program: CertiCount node (certified DSL program in the interpreter, no node model)")
    p.add_argument("--config", help="psc config (e.g. ../psc/config.vllm-1.7b.toml); with --provider program "
                                    "the curator config of the designer")
    p.add_argument("--program-source", choices=("design", "library"), default="design",
                   help="provider program: the curator LLM designs the program, or the library program")
    p.add_argument("--designer-provider", choices=("vllm", "openai"), default="vllm")
    p.add_argument("--designer-model", help="provider program: served curator model name")
    p.add_argument("--design-iterations", type=int, default=3)
    p.add_argument("--design-restarts", type=int, default=1)
    p.add_argument("--profile")
    p.add_argument("--node-model", help="served model name")
    p.add_argument("--base-url", help="node endpoint, e.g. http://127.0.0.1:8001/v1 (else VLLM_NODE_BASE_URL)")
    p.set_defaults(concurrency=128)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--guided-json", action="store_true", help="ablation: vLLM guided_json {Degree: number}")
    p.add_argument("--mock-mode", default="exact", choices=("exact", "bias", "random", "edge"))
    p.add_argument("--mock-rate", type=float, default=0.05)
    p.add_argument("--mock-trigger", type=int, default=7)
    p.add_argument("--plan-from", help="copy the plan of another run directory (cross-model comparison)")
    p.add_argument("--dataset", default="PM")
    p.add_argument("--mid-nodes", type=int, default=30)
    p.add_argument("--low-nodes", type=int, default=12)
    p.add_argument("--hub-flips", default="all", help="'all' (452 per hub) or a number of targeted flips per hub")
    p.add_argument("--random-per-node", type=int, default=1)
    p.add_argument("--no-constructed", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("pilot")
    common(p)
    p.add_argument("--per-bin", type=int, default=10)
    p.add_argument("--reps", type=int, default=5)
    p.add_argument("--x-reps", type=int, default=3)
    p.add_argument("--x2-reps", type=int, default=2)
    p.add_argument("--eval", type=int, default=300)
    p.set_defaults(fn=cmd_pilot)

    p = sub.add_parser("screen")
    common(p)
    p.add_argument("--x-reps", type=int, default=3)
    p.add_argument("--x2-reps", type=int, default=2)
    p.add_argument("--only", help="comma list of kinds / tiers / families to screen (e.g. hub or real or L,X)")
    p.add_argument("--max-per-node", type=int, default=None,
                   help="subsample: at most N pairs per input (random reference pairs kept); recorded in scope.jsonl")
    p.set_defaults(fn=cmd_screen)

    p = sub.add_parser("rank")
    common(p)
    p.set_defaults(fn=cmd_rank)

    p = sub.add_parser("confirm")
    common(p)
    p.add_argument("--name", required=True, help="confirmation set name (one design per name)")
    p.add_argument("--pairs", default="top:40", help="top:N | nodes | random | confirmed:DIR | file:PATH")
    p.add_argument("--per-node", type=int, default=None,
                   help="with top:N, at most K pairs per input x (one real node = one input)")
    p.add_argument("--eval", type=int, default=300)
    p.add_argument("--eval-jitter", type=int, default=500, help="eval trials for pairs that jittered in the screen")
    p.add_argument("--select", type=int, default=20,
                   help="extra fresh selection trials per input (added to the screen trials of this run)")
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--allow-incomplete", action="store_true")
    p.set_defaults(fn=cmd_confirm)

    p = sub.add_parser("report")
    common(p, needs_out=False)
    p.add_argument("--runs", nargs="+", required=True)
    p.add_argument("--report-dir")
    p.add_argument("--sets", help="comma list of confirmation set names to include (default: all)")
    p.add_argument("--family-alpha", type=float, default=0.05, help="family level of the joint Bonferroni")
    p.add_argument("--family-scope", choices=("all", "model"), default="all",
                   help="one joint family over every included set, or one family per model")
    p.set_defaults(fn=cmd_report)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
