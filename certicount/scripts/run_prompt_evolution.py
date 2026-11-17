"""Self-evolution of the curator's design instructions (:mod:`certicount.dsl.evolve`).

The curator designs the training tasks with the full design loop (checks, noise-aware gate,
feedback-driven rewrites); its rejected drafts are reflected on by the same model, which edits
one instruction module per child; children replace the parent only after a confirmed better
score. Only public information is used: the training tasks, a public number of nodes and
synthetic graphs -- never an evaluation graph, never a held-out task.

    # offline check (mock curator and a mock reflector)
    ../.venv/bin/python scripts/run_prompt_evolution.py --provider mock --generations 1 --tag _evolve_mock

    # Qwen3-8B (thinking) on a local vLLM server, PSC architecture
    VLLM_CURATOR_BASE_URL=http://127.0.0.1:8003/v1 ../.venv/bin/python scripts/run_prompt_evolution.py \\
        --provider vllm --config configs/vllm_qwen3-8b-think_design.toml --curator-model Qwen3-8B \\
        --temperature 0.6 --tag cs5_evolve_psc

Outputs in ``results/evolve/<tag>/``: ``lineage.jsonl`` (every candidate: spec, patch, evaluation,
designs), ``best_prompt.json`` (load with ``run_dsl_design_eval.py --prompt``), ``transcripts.jsonl``,
``table.md``, ``manifest.json``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from agentscope.model import ChatModelBase, ChatResponse  # noqa: E402
from psc.events import set_error_sink, set_transcript_sink  # noqa: E402
from psc.mechanism import DEFAULT_MECHANISM, MECHANISMS  # noqa: E402
from psc.models import PROVIDERS, ModelConfig, create_formatter, create_model  # noqa: E402
from certicount.artifacts import markdown_table, out_dir, write_manifest  # noqa: E402
from certicount.dsl.designer import MockDesignerModel, _text  # noqa: E402
from certicount.dsl.evolve import EvolveConfig, evolve  # noqa: E402
from certicount.dsl.library import PROGRAMS  # noqa: E402
from certicount.dsl.prompt_spec import load_spec  # noqa: E402

HELD_OUT = ("3-star", "5-star", "triangle", "degree-moment2")


class MockModel(ChatModelBase):
    """Offline: the reference curator for design prompts, a fixed guidance rule for reflections."""

    def __init__(self) -> None:
        super().__init__(model_name="mock", stream=False)
        self.designer = MockDesignerModel()

    async def __call__(self, messages: list[dict], **kwargs: Any) -> ChatResponse:  # type: ignore[override]
        system = next((m.get("content") for m in messages if m.get("role") == "system"), "") or ""
        if isinstance(system, list):
            system = " ".join(b.get("text", "") for b in system if isinstance(b, dict))
        if "maintain the instructions" in system:
            return _text(json.dumps({"module": "rules", "op": "add", "reason": "mock",
                                     "value": "Count with this node's own neighbors P; N(...) is a randomized copy."}))
        return await self.designer(messages, **kwargs)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default="v0", help="starting spec: v0 or a JSON file")
    ap.add_argument("--train-tasks", default="degree,2-star,4-star")
    ap.add_argument("--n", type=int, default=400, help="public number of nodes of the training setting")
    ap.add_argument("--node-bounds", action="store_true")
    ap.add_argument("--clip-alpha", type=float, default=0.0)
    ap.add_argument("--eps", type=float, default=2.0)
    ap.add_argument("--mechanism", default=DEFAULT_MECHANISM, choices=MECHANISMS)
    ap.add_argument("--designs", type=int, default=4, help="designs per task and evaluation")
    ap.add_argument("--max-iterations", type=int, default=3)
    ap.add_argument("--generations", type=int, default=5)
    ap.add_argument("--children", type=int, default=3)
    ap.add_argument("--patience", type=int, default=2)
    ap.add_argument("--design-concurrency", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--provider", default="mock", choices=PROVIDERS)
    ap.add_argument("--profile", default=None)
    ap.add_argument("--config", default=None)
    ap.add_argument("--curator-model", default=None)
    ap.add_argument("--temperature", type=float, default=None)
    ap.add_argument("--allow-held-out", action="store_true", help="permit held-out tasks among the training tasks")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()

    tasks = tuple(t for t in a.train_tasks.split(",") if t)
    unknown = [t for t in tasks if t not in PROGRAMS]
    if unknown:
        ap.error(f"no reference program for {unknown}")
    leaked = [t for t in tasks if t in HELD_OUT]
    if leaked and not a.allow_held_out:
        ap.error(f"held-out tasks {leaked} cannot be training tasks (--allow-held-out to override)")
    cfg = EvolveConfig(train_tasks=tasks, n=a.n, node_bounds=a.node_bounds, alpha=a.clip_alpha, eps=a.eps,
                       mechanism=a.mechanism, designs=a.designs, max_iterations=a.max_iterations,
                       concurrency=a.design_concurrency, generations=a.generations, children=a.children,
                       patience=a.patience, seed=a.seed)
    per_eval = len(tasks) * a.designs * a.max_iterations
    per_gen = (a.children + 2) * per_eval + 2 * a.children
    print(f"at most {per_eval} design calls per evaluation, {per_gen} per generation, "
          f"{per_eval + a.generations * per_gen} in total ({a.provider})")
    if a.dry_run:
        return
    start = load_spec(a.start)
    if a.provider == "mock":
        cfg_m = ModelConfig()
        model: ChatModelBase = MockModel()
    else:
        overrides = {k: v for k, v in (("curator_model", a.curator_model), ("temperature", a.temperature)) if v is not None}
        cfg_m = ModelConfig.from_env(provider=a.provider, config_path=a.config, profile=a.profile, **overrides)
        model = create_model(cfg_m, "curator")
    fmt = create_formatter(cfg_m)
    out = out_dir("evolve", a.tag, "evolve")
    write_manifest(out, {**vars(a), "config": cfg.to_dict(), "start_digest": start.digest,
                         "curator": getattr(cfg_m, "curator_model", None)})
    set_error_sink(out / "errors.jsonl")
    set_transcript_sink(out / "transcripts.jsonl")

    rows: list[dict] = []

    def log(rec: dict) -> None:
        with (out / "lineage.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        if "evaluation" in rec:
            e = rec["evaluation"]
            rows.append({"generation": rec["generation"], "kind": rec["kind"], "name": rec["name"],
                         "parent": rec["parent"], "score": e["score"], "mean_score": rec["mean_score"],
                         "qualified_rate": e["qualified_rate"], "accept_rate": e["accept_rate"],
                         "mean_calls": e["mean_calls"], "refuted": e["stages"].get("refuted", 0),
                         "patch": json.dumps((rec.get("reflection") or {}).get("patch"), ensure_ascii=False)[:160]})
            print(f"[gen {rec['generation']}] {rec['kind']:7s} {rec['name']:6s} score {e['score']:.3f} "
                  f"(mean {rec['mean_score']:.3f}) qualified {e['qualified_rate']:.2f} calls {e['mean_calls']:.2f}")
        elif rec["kind"] == "refused":
            print(f"[gen {rec['generation']}] refused {rec['name']}: {rec['attempts'][-1].get('problems')}")

    best, lineage = asyncio.run(evolve(start, model, fmt, cfg, log))
    best.save(out / "best_prompt.json")
    refuted = sum(r["refuted"] for r in rows)
    md = ["# Prompt self-evolution", "",
          f"start = {a.start} ({start.digest}), training tasks = {', '.join(tasks)}, n = {a.n}, architecture = "
          f"{'per-node (α = %g)' % a.clip_alpha if a.node_bounds else 'PSC'}, ε = {a.eps}, {a.designs} designs per task "
          f"and evaluation. Best: {best.name} ({best.digest}). Falsifier refutations during evolution: {refuted} "
          "(must be 0: privacy does not depend on the prompt).", "",
          markdown_table(rows, ["generation", "kind", "name", "parent", "score", "mean_score", "qualified_rate",
                                "accept_rate", "mean_calls", "refuted", "patch"]), "",
          "## Best prompt modules", "", "```json", json.dumps(best.to_dict(), indent=2, ensure_ascii=False), "```", ""]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")
    print(f"best {best.name} ({best.digest}); results in {out}")


if __name__ == "__main__":
    main()
