"""Integration test of the real-LLM code path (``provider="openai"``).

A tiny local server speaks the OpenAI ``/v1/chat/completions`` protocol and
answers with the rule-following mock, so we can verify that
``OpenAIChatModel`` + ``OpenAIChatFormatter`` + response parsing work end to
end without an API key.
"""

from __future__ import annotations

import asyncio
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from psc.framework import NaiveFramework, PSCFramework  # noqa: E402
from psc.graph import Graph, TaskRecord, task_prompt  # noqa: E402
from psc.mock_model import MockChatModel  # noqa: E402
from psc.models import ModelConfig  # noqa: E402


class _Handler(BaseHTTPRequestHandler):
    mock = MockChatModel()
    stream_only = False  # mimic gateways that reject non-stream requests

    def log_message(self, *args):  # silence
        pass

    def _send(self, status: int, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        if self.stream_only and not body.get("stream"):
            err = {"code": 11101, "msg": "Non-stream chat request is currently not supported"}
            self._send(400, json.dumps(err).encode(), "application/json")
            return
        res = asyncio.run(self.mock(body["messages"]))
        text = "".join(b["text"] for b in res.content if b.get("type") == "text")
        if body.get("stream"):
            self._send(200, _sse(text, body.get("model", "stub")), "text/event-stream")
            return
        payload = {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 0,
            "model": body.get("model", "stub"),
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        self._send(200, json.dumps(payload).encode(), "application/json")


def _sse(text: str, model: str) -> bytes:
    """OpenAI streaming format: content deltas, a usage-only chunk, [DONE]."""
    half = len(text) // 2
    base = {"id": "chatcmpl-test", "object": "chat.completion.chunk", "created": 0, "model": model}
    chunks = [
        {**base, "choices": [{"index": 0, "delta": {"role": "assistant", "content": piece}, "finish_reason": None}]}
        for piece in (text[:half], text[half:])
    ]
    chunks.append({**base, "choices": [], "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}})
    return "".join(f"data: {json.dumps(c)}\n\n" for c in chunks).encode() + b"data: [DONE]\n\n"


def _serve(stream_only: bool = False) -> tuple[HTTPServer, str]:
    handler = type("_H", (_Handler,), {"stream_only": stream_only})
    server = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/v1"


def test_openai_provider_end_to_end():
    server, base_url = _serve()
    try:
        # the stub answers with the mock, which needs the <structured_input> block
        cfg = ModelConfig(
            provider="openai", api_key="sk-test", base_url=base_url, node_model="stub-mini",
            curator_model="stub", structured_input=True,
        )
        g = Graph.from_edges(6, [(0, 1), (0, 2), (1, 2), (2, 3), (2, 4), (3, 4), (4, 5)])
        rec = TaskRecord(1, task_prompt("triangle", g.n), g.edge_string(), g.n, g.m, g.ground_truth("triangle"), "triangle", "toy")
        res = asyncio.run(PSCFramework(cfg, seed=0).run(rec, eps=1e6))
        assert res.parse_failures == 0
        assert abs(res.estimate - 2.0) < 1e-3  # only Lap(GS/eps3) noise remains
        assert res.llm_calls == 2 * g.n + 3
        nv = asyncio.run(NaiveFramework(cfg, seed=0).run(rec, eps=1e6))
        assert abs(nv.estimate - 2.0) < 1e-3
    finally:
        server.shutdown()


def test_openai_provider_streaming_gateway():
    """A gateway that only accepts streaming requests works with ``stream=True``."""
    import openai
    import pytest

    server, base_url = _serve(stream_only=True)
    try:
        g = Graph.from_edges(6, [(0, 1), (0, 2), (1, 2), (2, 3), (2, 4), (3, 4), (4, 5)])
        rec = TaskRecord(1, task_prompt("triangle", g.n), g.edge_string(), g.n, g.m, g.ground_truth("triangle"), "triangle", "toy")
        common = dict(provider="openai", api_key="sk-test", base_url=base_url, structured_input=True)

        with pytest.raises(openai.BadRequestError, match="Non-stream"):
            asyncio.run(PSCFramework(ModelConfig(**common), seed=0).run(rec, eps=1e6))

        res = asyncio.run(PSCFramework(ModelConfig(**common, stream=True), seed=0).run(rec, eps=1e6))
        assert res.parse_failures == 0 and res.extra["validation"]["e2e_exact"] == g.n
        assert abs(res.estimate - 2.0) < 1e-3
    finally:
        server.shutdown()


if __name__ == "__main__":
    test_openai_provider_end_to_end()
    print("test_openai_provider_end_to_end: ok")
    test_openai_provider_streaming_gateway()
    print("test_openai_provider_streaming_gateway: ok")
