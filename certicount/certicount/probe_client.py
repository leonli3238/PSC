"""Model clients and the sampling loop of the degree violation probe (:mod:`certicount.probe`).

The probe calls the node model exactly as :class:`psc.agents.node_agent.NodeAgent`
does: same system prompt, same update prompt (``<structured_input>`` stripped
for real models), same AgentScope formatter and request parameters
(``temperature`` and the ``extra`` table of the config, e.g. ``max_tokens`` and
``extra_body``), and the reply text is ``message.content`` as in
:func:`psc.models.response_text`.  It talks to the OpenAI-compatible endpoint
directly so that every trial also records ``finish_reason``, token usage,
latency and the request id, which :func:`psc.models.chat` drops.

Retries follow :func:`psc.models.chat`: retryable API errors and empty replies
are retried with exponential backoff; an empty reply after every attempt is the
model's answer (the parser records a failure and the node keeps its count, as
in PSC).  A call whose attempts all ended in API errors is an infrastructure
failure: it is logged in ``errors.jsonl`` and **not** written as a trial, so a
rerun of the stage retries it.

:class:`MockProbeClient` is the offline stand-in used by the negative controls:
``exact`` (rule value), ``bias`` (always one less), ``random`` (input-independent
±1 with probability ``rate``) and ``edge`` (``+2`` whenever the list contains the
``trigger`` vertex: an error correlated with one bit of the private list).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from agentscope.message import Msg
from tqdm import tqdm

from psc import rules
from psc.agents.node_agent import parse_update_reply
from psc.artifacts import append_run
from psc.models import ModelConfig, _is_retryable, _retry_after, create_formatter
from psc.prompts import NODE_SYSTEM, extract_structured, strip_structured

from .audit import NodeInput

VALUE_TOL = 1e-6
MOCK_MODES = ("exact", "bias", "random", "edge")


class InfraError(RuntimeError):
    """Every attempt of a call ended in an API error (no model answer)."""


@dataclass
class Reply:
    text: str
    finish_reason: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    latency: float
    attempts: int
    request_id: str | None = None
    has_reasoning: bool = False


async def format_messages(formatter, system: str | None, user: str) -> list[dict]:
    """The request messages of :func:`psc.models.chat`."""
    msgs = ([Msg("system", system, "system")] if system is not None else []) + [Msg("user", user, "user")]
    return await formatter.format(msgs)


class OpenAIProbeClient:
    """Node model behind an OpenAI-compatible endpoint (local vLLM for the probe)."""

    def __init__(self, cfg: ModelConfig, extra_override: Mapping[str, Any] | None = None, timeout: float = 900.0) -> None:
        from openai import AsyncOpenAI

        if cfg.provider not in ("vllm", "openai"):
            raise ValueError(f"OpenAIProbeClient needs provider vllm / openai, got {cfg.provider!r}")
        url = cfg.endpoint("node")
        if cfg.provider == "vllm" and not url:
            raise RuntimeError("VLLM_NODE_BASE_URL (or VLLM_BASE_URL) is not set (environment or ../psc/.env)")
        self.client = AsyncOpenAI(api_key=cfg.api_key or "EMPTY", base_url=url, max_retries=0, timeout=timeout)
        self.base_url = url
        self.model = cfg.node_model
        extra = dict(cfg.role_extra("node"))
        for k, v in (extra_override or {}).items():
            if k == "extra_body" and isinstance(v, dict):
                extra["extra_body"] = {**extra.get("extra_body", {}), **v}
            else:
                extra[k] = v
        self.kwargs = {"temperature": cfg.temperature, **extra}
        self.formatter = create_formatter(cfg)
        self.structured = cfg.use_structured_input
        self.retries = max(0, int(cfg.max_retries))
        self.backoff = float(cfg.retry_backoff)

    async def complete(self, system: str, user: str, ident: str) -> Reply:
        if not self.structured:
            user = strip_structured(user)
        messages = await format_messages(self.formatter, system, user)
        started = time.perf_counter()
        last_exc: BaseException | None = None
        last_reply: Reply | None = None
        for attempt in range(1, self.retries + 2):
            wait = self.backoff * 2 ** (attempt - 1)
            try:
                res = await self.client.chat.completions.create(
                    model=self.model, messages=messages, stream=False, **self.kwargs,
                )
            except Exception as exc:  # noqa: BLE001 - classified like psc.models.chat
                if not _is_retryable(exc):
                    raise
                last_exc, last_reply = exc, None
                wait = max(wait, _retry_after(exc) or 0.0)
            else:
                choice = res.choices[0] if res.choices else None
                message = choice.message if choice is not None else None
                text = (message.content or "") if message is not None else ""
                reasoning = None
                if message is not None:
                    reasoning = getattr(message, "reasoning_content", None) or getattr(message, "reasoning", None)
                usage = res.usage
                last_reply = Reply(
                    text=text,
                    finish_reason=choice.finish_reason if choice is not None else None,
                    prompt_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
                    completion_tokens=getattr(usage, "completion_tokens", None) if usage else None,
                    latency=round(time.perf_counter() - started, 3),
                    attempts=attempt,
                    request_id=getattr(res, "id", None),
                    has_reasoning=bool(reasoning),
                )
                last_exc = None
                if text.strip():
                    return last_reply
            if attempt <= self.retries:
                await asyncio.sleep(wait)
        if last_reply is not None:
            return last_reply  # empty after every attempt: a model answer, parsed as a failure
        raise InfraError(f"{type(last_exc).__name__}: {last_exc}")

    async def server_info(self) -> dict:
        info: dict[str, Any] = {"base_url": self.base_url}
        try:
            models = await self.client.models.list()
            info["models"] = [
                {k: getattr(m, k, None) for k in ("id", "root", "max_model_len", "owned_by")} for m in models.data
            ]
        except Exception as exc:  # noqa: BLE001 - informational only
            info["models_error"] = f"{type(exc).__name__}: {exc}"
        try:
            import httpx

            root = str(self.base_url or "").rstrip("/")
            root = root[: -len("/v1")] if root.endswith("/v1") else root
            async with httpx.AsyncClient(timeout=10) as h:
                r = await h.get(f"{root}/version")
                if r.status_code == 200:
                    info["server_version"] = r.json()
        except Exception as exc:  # noqa: BLE001
            info["version_error"] = f"{type(exc).__name__}: {exc}"
        return info


class MockProbeClient:
    """Offline node model for the negative controls (needs the structured block)."""

    def __init__(self, mode: str = "exact", rate: float = 0.05, trigger: int = 7, seed: int = 0) -> None:
        if mode not in MOCK_MODES:
            raise ValueError(f"mock mode must be one of {MOCK_MODES}")
        self.mode, self.rate, self.trigger, self.seed = mode, float(rate), int(trigger), int(seed)
        self.model = f"mock-{mode}"

    def _rng(self, ident: str) -> random.Random:
        h = hashlib.sha256(f"{self.seed}|mock|{ident}".encode()).digest()
        return random.Random(int.from_bytes(h[:8], "little"))

    async def complete(self, system: str, user: str, ident: str) -> Reply:
        await asyncio.sleep(0)
        p = extract_structured(user)
        if p is None or p.get("phase") != "node_update":
            raise ValueError("MockProbeClient needs the <structured_input> block of a node update prompt")
        value = float(rules.update(p["task"], p["neighbors"], p.get("messages")))
        if self.mode == "bias":
            value -= 1
        elif self.mode == "random":
            r = self._rng(ident)
            if r.random() < self.rate:
                value += r.choice((-1.0, 1.0))
        elif self.mode == "edge" and self.trigger in p["neighbors"]:
            value += 2
        text = f"Counting the distinct neighbours.\n```json\n{json.dumps({p['state_var']: value})}\n```"
        return Reply(text, "stop", None, max(1, len(text) // 4), 0.0, 1)

    async def server_info(self) -> dict:
        return {"mock": {"mode": self.mode, "rate": self.rate, "trigger": self.trigger, "seed": self.seed}}


def make_client(settings: Mapping[str, Any]):
    """The client of a probe directory (``settings.json``)."""
    if settings["provider"] == "mock":
        m = settings.get("mock") or {}
        return MockProbeClient(m.get("mode", "exact"), m.get("rate", 0.05), m.get("trigger", 7), settings.get("seed", 0))
    cfg = ModelConfig.from_env(
        settings["provider"], config_path=settings.get("config"), profile=settings.get("profile"),
        node_model=settings["node_model"],
    )
    override = {}
    if settings.get("guided_json"):
        override = {"extra_body": {"guided_json": guided_json_schema()}}
    return OpenAIProbeClient(cfg, override)


def guided_json_schema(state_var: str = "Degree") -> dict:
    """Ablation only: force the reply to be ``{"Degree": <number>}`` (vLLM ``guided_json``)."""
    return {
        "type": "object",
        "properties": {state_var: {"type": "number"}},
        "required": [state_var],
        "additionalProperties": False,
    }


# ---------------------------------------------------------------------------
# Sampling loop
# ---------------------------------------------------------------------------


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # a line cut by an interruption; the trial is redone
    return out


def terminate_last_line(path: Path) -> None:
    """End a log cut mid-line by an interruption with a newline, so the next
    appended trial is not glued to the broken line (which is then skipped)."""
    if not path.exists() or path.stat().st_size == 0:
        return
    with path.open("rb") as f:
        f.seek(-1, 2)
        last = f.read(1)
    if last != b"\n":
        with path.open("a", encoding="utf-8") as f:
            f.write("\n")


def missing_jobs(jobs: Sequence[tuple[str, str, int]], samples: Sequence[Mapping]) -> list[tuple[str, str, int]]:
    have = {(s["key"], s["phase"], int(s["rep"])) for s in samples}
    seen: set[tuple[str, str, int]] = set()
    out = []
    for j in jobs:
        if j not in have and j not in seen:
            seen.add(j)
            out.append(j)
    return out


async def run_jobs(
    client,
    inputs: Mapping[str, NodeInput],
    jobs: Sequence[tuple[str, str, int]],
    out: Path,
    *,
    concurrency: int,
    seed: int,
    desc: str,
    save_all_replies: bool = False,
) -> dict:
    """Run ``(input key, phase, rep)`` jobs in a seeded random order (x and x' of
    a pair interleaved, fixed concurrency); one line per trial in ``samples.jsonl``.
    Replies that are wrong or not parsed from JSON go to ``replies.jsonl``."""
    out.mkdir(parents=True, exist_ok=True)
    for name in ("samples.jsonl", "replies.jsonl", "errors.jsonl"):
        terminate_last_line(out / name)
    order = list(jobs)
    random.Random(f"{seed}|{desc}|{len(order)}").shuffle(order)
    sem = asyncio.Semaphore(max(1, int(concurrency)))
    stats = {"calls": 0, "infra_errors": 0, "prompt_tokens": 0, "completion_tokens": 0}
    bar = tqdm(total=len(order), desc=desc, unit="call", mininterval=5.0)
    model = getattr(client, "model", None)
    started = time.perf_counter()

    async def one(key: str, phase: str, rep: int) -> None:
        inp = inputs[key]
        ident = f"{key}|{phase}|{rep}"
        async with sem:
            try:
                reply = await client.complete(NODE_SYSTEM.format(node_id=inp.node_id), inp.prompt(), ident)
            except InfraError as exc:
                stats["infra_errors"] += 1
                append_run(out / "errors.jsonl", {"kind": "infra", "key": key, "phase": phase, "rep": rep,
                                                  "message": str(exc)[:2000], "t": time.time()})
                bar.update()
                return
        value, status = parse_update_reply(reply.text, inp.state_var)
        rule = float(inp.rule_value())
        reported = inp.state if value is None else float(value)  # a failed parse keeps the previous count
        row = {
            "key": key, "phase": phase, "rep": rep, "status": status, "value": reported, "parsed": value,
            "rule": rule, "correct": abs(reported - rule) <= VALUE_TOL, "degree": len(inp.neighbors),
            "finish_reason": reply.finish_reason, "prompt_tokens": reply.prompt_tokens,
            "completion_tokens": reply.completion_tokens, "reply_chars": len(reply.text), "latency": reply.latency,
            "attempts": reply.attempts, "request_id": reply.request_id, "has_reasoning": reply.has_reasoning,
            "model": model, "t": time.time(),
        }
        append_run(out / "samples.jsonl", row)
        if save_all_replies or status != "json" or not row["correct"]:
            append_run(out / "replies.jsonl", {"key": key, "phase": phase, "rep": rep, "reply": reply.text})
        stats["calls"] += 1
        stats["prompt_tokens"] += reply.prompt_tokens or 0
        stats["completion_tokens"] += reply.completion_tokens or 0
        bar.update()

    await asyncio.gather(*(one(*j) for j in order))
    bar.close()
    stats["wall_seconds"] = round(time.perf_counter() - started, 2)
    stats["jobs"] = len(order)
    return stats


__all__ = [
    "InfraError", "MOCK_MODES", "MockProbeClient", "OpenAIProbeClient", "Reply", "format_messages",
    "guided_json_schema", "load_jsonl", "make_client", "missing_jobs", "run_jobs",
]
