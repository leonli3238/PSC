"""Model / formatter factory for AgentScope 1.0 chat models.

Supported providers::

    openai     OpenAIChatModel   (also any OpenAI-compatible endpoint via
                                  OPENAI_BASE_URL, e.g. DeepSeek, vLLM ...)
    vllm       OpenAIChatModel   (self-hosted vLLM servers, one per role:
                                  VLLM_NODE_BASE_URL / VLLM_CURATOR_BASE_URL)
    dashscope  DashScopeChatModel (Qwen family)
    ollama     OllamaChatModel   (local models)
    mock       MockChatModel     (offline, rule-following reasoner)

The paper uses GPT-4.1-mini for node agents and GPT-4.1 for the curator agent
with temperature 0.
"""

from __future__ import annotations

import asyncio
import os
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from agentscope.formatter import (
    DashScopeChatFormatter,
    FormatterBase,
    OllamaChatFormatter,
    OpenAIChatFormatter,
)
from agentscope.message import Msg
from agentscope.model import ChatModelBase, ChatResponse
from dotenv import load_dotenv

from .events import record_error
from .mock_model import MockChatModel
from .progress import note_llm_call
from .prompts import strip_structured

PROVIDERS = ("openai", "vllm", "dashscope", "ollama", "mock")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config.toml"
DEFAULT_ENV = PROJECT_ROOT / ".env"


@dataclass
class ModelConfig:
    provider: str = "mock"
    node_model: str = "gpt-4.1-mini"
    curator_model: str = "gpt-4.1"
    api_key: str | None = None
    base_url: str | None = None
    # Per-role endpoints (e.g. two vLLM servers); None -> base_url
    node_base_url: str | None = None
    curator_base_url: str | None = None
    temperature: float = 0.0
    max_concurrency: int = 8
    # Runs (of all dataset / task / method cells) executed concurrently
    parallel_runs: int = 1
    mock_error_rate: float = 0.0
    # Send the <structured_input> block to the model; None -> only for "mock"
    structured_input: bool | None = None
    # Streaming chat requests (some OpenAI-compatible gateways reject non-stream calls)
    stream: bool = False
    # Retries per model call on rate limits / 5xx / connection errors / empty
    # replies, waiting retry_backoff * 2^attempt seconds (or the server's Retry-After)
    max_retries: int = 4
    retry_backoff: float = 5.0
    extra: dict = field(default_factory=dict)
    # Per-role overrides merged over ``extra`` (top-level keys replace, e.g. extra_body)
    node_extra: dict = field(default_factory=dict)
    curator_extra: dict = field(default_factory=dict)

    def role_extra(self, role: str) -> dict:
        return {**self.extra, **(self.node_extra if role == "node" else self.curator_extra)}

    @property
    def use_structured_input(self) -> bool:
        if self.structured_input is None:
            return self.provider == "mock"
        return self.structured_input

    def endpoint(self, role: str) -> str | None:
        """Base URL used by ``role in {"node", "curator"}``."""
        url = self.node_base_url if role == "node" else self.curator_base_url
        return url or self.base_url

    @classmethod
    def from_env(
        cls,
        provider: str | None = None,
        config_path: str | Path | None = None,
        env_path: str | Path | None = DEFAULT_ENV,
        **overrides,
    ) -> "ModelConfig":
        """Build the config from ``.env`` (keys / URLs) and ``config.toml`` (models).

        Precedence: ``overrides`` (CLI flags) > environment variables
        (``PSC_PROVIDER``, ``OLLAMA_MODEL``) > config file > built-in defaults.
        Variables already set in the environment win over ``.env``.
        """
        if env_path is not None:
            load_dotenv(env_path, override=False)
        path = Path(config_path or os.getenv("PSC_CONFIG") or DEFAULT_CONFIG)
        file_cfg = load_config_file(path)

        provider = provider or os.getenv("PSC_PROVIDER") or file_cfg.get("provider") or "mock"
        if provider not in PROVIDERS:
            raise ValueError(f"unknown provider {provider!r}; choose from {PROVIDERS}")
        cfg = cls(provider=provider)
        if provider == "openai":
            cfg.api_key = os.getenv("OPENAI_API_KEY") or None
            cfg.base_url = os.getenv("OPENAI_BASE_URL") or None
        elif provider == "vllm":
            # vLLM ignores the key unless the server was started with --api-key
            cfg.api_key = os.getenv("VLLM_API_KEY") or "EMPTY"
            cfg.base_url = os.getenv("VLLM_BASE_URL") or None
            cfg.node_base_url = os.getenv("VLLM_NODE_BASE_URL") or None
            cfg.curator_base_url = os.getenv("VLLM_CURATOR_BASE_URL") or None
        elif provider == "dashscope":
            cfg.api_key = os.getenv("DASHSCOPE_API_KEY") or None
            cfg.node_model, cfg.curator_model = "qwen3-8b", "qwen-plus"
        elif provider == "ollama":
            cfg.base_url = os.getenv("OLLAMA_HOST") or None
            cfg.node_model = cfg.curator_model = "qwen3:8b"

        shared = {k: v for k, v in file_cfg.items() if k != "provider" and not isinstance(v, dict)}
        for values in (shared, file_cfg.get(provider, {})):
            for k, v in values.items():
                setattr(cfg, k, v)

        if provider == "ollama" and os.getenv("OLLAMA_MODEL"):
            cfg.node_model = cfg.curator_model = os.environ["OLLAMA_MODEL"]
        for k, v in overrides.items():
            if v is not None:
                setattr(cfg, k, v)
        return cfg


_CONFIG_KEYS = frozenset(
    {
        "node_model", "curator_model", "temperature", "max_concurrency", "structured_input", "stream",
        "max_retries", "retry_backoff", "parallel_runs",
    },
)
# Only allowed inside a provider section: extra request parameters merged into
# every chat call, e.g. [openai.extra] extra_body = {...}, and per-role
# overrides [openai.node_extra] / [openai.curator_extra]
_SECTION_ONLY_KEYS = frozenset({"extra", "node_extra", "curator_extra"})


def load_config_file(path: str | Path) -> dict:
    """Read ``config.toml``; a missing file means "use the defaults"."""
    path = Path(path)
    if not path.exists():
        return {}
    with path.open("rb") as f:
        data = tomllib.load(f)
    for key, value in data.items():
        if key == "provider":
            continue
        if isinstance(value, dict):
            if key not in PROVIDERS:
                raise ValueError(f"{path}: unknown provider section [{key}]; choose from {PROVIDERS}")
            bad = set(value) - _CONFIG_KEYS - _SECTION_ONLY_KEYS
            for table in _SECTION_ONLY_KEYS & set(value):
                if not isinstance(value[table], dict):
                    raise ValueError(f"{path}: [{key}.{table}] must be a table")
        else:
            bad = {key} - _CONFIG_KEYS
        if bad:
            raise ValueError(f"{path}: unknown key(s) {sorted(bad)}; allowed: {sorted(_CONFIG_KEYS | _SECTION_ONLY_KEYS)}")
    return data


def create_model(cfg: ModelConfig, role: str) -> ChatModelBase:
    """Instantiate the chat model for ``role in {"node", "curator"}``."""
    model = _create_model(cfg, role)
    model.psc_structured_input = cfg.use_structured_input
    model.psc_max_retries = cfg.max_retries
    model.psc_retry_backoff = cfg.retry_backoff
    return model


def _create_model(cfg: ModelConfig, role: str) -> ChatModelBase:
    name = cfg.node_model if role == "node" else cfg.curator_model
    extra = cfg.role_extra(role)
    if cfg.provider == "mock":
        return MockChatModel(error_rate=cfg.mock_error_rate if role == "node" else 0.0)
    if cfg.provider in ("openai", "vllm"):
        from agentscope.model import OpenAIChatModel

        if not cfg.api_key:
            raise RuntimeError(f"OPENAI_API_KEY is not set (fill it in {DEFAULT_ENV})")
        url = cfg.endpoint(role)
        if cfg.provider == "vllm" and not url:
            raise RuntimeError(f"VLLM_{role.upper()}_BASE_URL (or VLLM_BASE_URL) is not set (fill it in {DEFAULT_ENV})")
        # retries are done (and recorded) by ``chat``, not silently by the client
        client_kwargs = {"max_retries": 0, **({"base_url": url} if url else {})}
        return OpenAIChatModel(
            model_name=name,
            api_key=cfg.api_key,
            stream=cfg.stream,
            client_kwargs=client_kwargs,
            generate_kwargs={"temperature": cfg.temperature, **extra},
        )
    if cfg.provider == "dashscope":
        from agentscope.model import DashScopeChatModel

        if not cfg.api_key:
            raise RuntimeError(f"DASHSCOPE_API_KEY is not set (fill it in {DEFAULT_ENV})")
        return DashScopeChatModel(
            model_name=name,
            api_key=cfg.api_key,
            stream=cfg.stream,
            enable_thinking=False,
            generate_kwargs={"temperature": cfg.temperature, **extra},
        )
    if cfg.provider == "ollama":
        from agentscope.model import OllamaChatModel

        return OllamaChatModel(
            model_name=name,
            stream=cfg.stream,
            host=cfg.base_url,
            options={"temperature": cfg.temperature, **extra},
        )
    raise ValueError(cfg.provider)


def create_formatter(cfg: ModelConfig) -> FormatterBase:
    if cfg.provider == "dashscope":
        return DashScopeChatFormatter()
    if cfg.provider == "ollama":
        return OllamaChatFormatter()
    return OpenAIChatFormatter()


def response_text(res: ChatResponse) -> str:
    """Concatenate the text blocks of a ``ChatResponse``."""
    parts = []
    for block in res.content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(parts)


_RETRYABLE_STATUS = frozenset({408, 409, 429})
# Exceptions without an HTTP status: openai connection / timeout / mid-stream
# errors and the underlying httpx transport errors
_RETRYABLE_NAMES = frozenset({"APIConnectionError", "APITimeoutError", "APIError", "TransportError", "TimeoutException"})


def _is_retryable(exc: BaseException) -> bool:
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status in _RETRYABLE_STATUS or status >= 500
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    return any(c.__name__ in _RETRYABLE_NAMES for c in type(exc).__mro__)


def _retry_after(exc: BaseException) -> float | None:
    response = getattr(exc, "response", None)
    value = getattr(response, "headers", {}).get("retry-after") if response is not None else None
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


async def _call_once(model: ChatModelBase, prompt) -> tuple[str, list[str]]:
    """Return the reply text and the types of all content blocks."""
    res = await model(prompt)
    if not isinstance(res, ChatResponse):
        # streaming: every chunk carries the accumulated content, keep the last
        last = None
        async for chunk in res:
            last = chunk
        if last is None:
            return "", []
        res = last
    types = [b.get("type", "?") if isinstance(b, dict) else type(b).__name__ for b in res.content]
    return response_text(res), types


async def chat(model: ChatModelBase, formatter: FormatterBase, system: str, user: str) -> str:
    """One-shot system+user call returning the reply text.

    Retryable API errors and empty replies are recorded and retried with
    exponential backoff; ``""`` is returned when every attempt failed, so the
    caller's parser records a failure instead of the experiment crashing.
    Non-retryable errors (bad request, authentication, ...) are raised.
    """
    if not getattr(model, "psc_structured_input", True):
        user = strip_structured(user)
    msgs = [Msg("system", system, "system"), Msg("user", user, "user")]
    prompt = await formatter.format(msgs)
    retries = max(0, int(getattr(model, "psc_max_retries", 0)))
    backoff = float(getattr(model, "psc_retry_backoff", 0.0))
    model_name = getattr(model, "model_name", type(model).__name__)
    for attempt in range(1, retries + 2):
        t0 = time.perf_counter()
        wait = backoff * 2 ** (attempt - 1)
        try:
            text, block_types = await _call_once(model, prompt)
        except Exception as exc:  # noqa: BLE001 - classified below
            if not _is_retryable(exc):
                raise
            wait = max(wait, _retry_after(exc) or 0.0)
            record_error(
                "api_error", f"{type(exc).__name__}: {exc}",
                model=model_name, attempt=attempt, elapsed=round(time.perf_counter() - t0, 2),
                status=getattr(exc, "status_code", None),
            )
        else:
            if text.strip():
                note_llm_call()
                return text
            record_error(
                "empty_reply", f"no text in reply (content blocks: {block_types})",
                model=model_name, attempt=attempt, elapsed=round(time.perf_counter() - t0, 2),
            )
        if attempt <= retries:
            await asyncio.sleep(wait)
    note_llm_call()
    record_error("call_failed", f"no usable reply after {retries + 1} attempts", model=model_name)
    return ""
