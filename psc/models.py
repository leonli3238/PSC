"""Model / formatter factory for AgentScope 1.0 chat models.

Supported providers::

    openai     OpenAIChatModel   (also any OpenAI-compatible endpoint via
                                  OPENAI_BASE_URL, e.g. DeepSeek, vLLM ...)
    dashscope  DashScopeChatModel (Qwen family)
    ollama     OllamaChatModel   (local models)
    mock       MockChatModel     (offline, rule-following reasoner)

The paper uses GPT-4.1-mini for node agents and GPT-4.1 for the curator agent
with temperature 0.
"""

from __future__ import annotations

import os
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

from .mock_model import MockChatModel
from .prompts import strip_structured

PROVIDERS = ("openai", "dashscope", "ollama", "mock")
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
    temperature: float = 0.0
    max_concurrency: int = 8
    mock_error_rate: float = 0.0
    # Send the <structured_input> block to the model; None -> only for "mock"
    structured_input: bool | None = None
    # Streaming chat requests (some OpenAI-compatible gateways reject non-stream calls)
    stream: bool = False
    extra: dict = field(default_factory=dict)

    @property
    def use_structured_input(self) -> bool:
        if self.structured_input is None:
            return self.provider == "mock"
        return self.structured_input

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
    {"node_model", "curator_model", "temperature", "max_concurrency", "structured_input", "stream"},
)


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
            bad = set(value) - _CONFIG_KEYS
        else:
            bad = {key} - _CONFIG_KEYS
        if bad:
            raise ValueError(f"{path}: unknown key(s) {sorted(bad)}; allowed: {sorted(_CONFIG_KEYS)}")
    return data


def create_model(cfg: ModelConfig, role: str) -> ChatModelBase:
    """Instantiate the chat model for ``role in {"node", "curator"}``."""
    model = _create_model(cfg, role)
    model.psc_structured_input = cfg.use_structured_input
    return model


def _create_model(cfg: ModelConfig, role: str) -> ChatModelBase:
    name = cfg.node_model if role == "node" else cfg.curator_model
    if cfg.provider == "mock":
        return MockChatModel(error_rate=cfg.mock_error_rate if role == "node" else 0.0)
    if cfg.provider == "openai":
        from agentscope.model import OpenAIChatModel

        if not cfg.api_key:
            raise RuntimeError(f"OPENAI_API_KEY is not set (fill it in {DEFAULT_ENV})")
        client_kwargs = {"base_url": cfg.base_url} if cfg.base_url else None
        return OpenAIChatModel(
            model_name=name,
            api_key=cfg.api_key,
            stream=cfg.stream,
            client_kwargs=client_kwargs,
            generate_kwargs={"temperature": cfg.temperature, **cfg.extra},
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
            generate_kwargs={"temperature": cfg.temperature, **cfg.extra},
        )
    if cfg.provider == "ollama":
        from agentscope.model import OllamaChatModel

        return OllamaChatModel(
            model_name=name,
            stream=cfg.stream,
            host=cfg.base_url,
            options={"temperature": cfg.temperature, **cfg.extra},
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


async def chat(model: ChatModelBase, formatter: FormatterBase, system: str, user: str) -> str:
    """One-shot system+user call returning the reply text."""
    if not getattr(model, "psc_structured_input", True):
        user = strip_structured(user)
    msgs = [Msg("system", system, "system"), Msg("user", user, "user")]
    prompt = await formatter.format(msgs)
    res = await model(prompt)
    if not isinstance(res, ChatResponse):
        # streaming: every chunk carries the accumulated content, keep the last
        last = None
        async for chunk in res:
            last = chunk
        if last is None:
            return ""
        res = last
    return response_text(res)
