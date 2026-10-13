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

from psc.events import clip, collect_errors, set_error_sink  # noqa: E402
from psc.framework import NaiveFramework, PSCFramework  # noqa: E402
from psc.graph import Graph, TaskRecord, task_prompt  # noqa: E402
from psc.mock_model import MockChatModel  # noqa: E402
from psc.models import ModelConfig  # noqa: E402
from psc.prompts import NO_REASONING_INSTRUCTION  # noqa: E402


GARBAGE = "gateway busy, please retry later. " * 200  # an unparseable reply longer than any short log cut


class _Handler(BaseHTTPRequestHandler):
    mock = MockChatModel()
    stream_only = False  # mimic gateways that reject non-stream requests
    fail_plan: list[str] = []  # per request, in order: "429", "empty" or "garbage"; then normal answers

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
        mode = self.fail_plan.pop(0) if self.fail_plan else None
        if mode == "429":
            err = {"error": {"message": "Rate limit reached for requests", "type": "requests", "code": "rate_limit_exceeded"}}
            self._send(429, json.dumps(err).encode(), "application/json")
            return
        if mode in ("empty", "garbage"):
            text = "" if mode == "empty" else GARBAGE
        else:
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


def _serve(stream_only: bool = False, fail_plan: list[str] | None = None) -> tuple[HTTPServer, str]:
    handler = type("_H", (_Handler,), {"stream_only": stream_only, "fail_plan": list(fail_plan or [])})
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

        # Exercise the new k-star profile through the same streaming adapter.
        star = TaskRecord(1, task_prompt("3-star", g.n), g.edge_string(), g.n, g.m,
                          g.ground_truth("3-star"), "3-star", "toy")
        result = asyncio.run(PSCFramework(ModelConfig(**common, stream=True), seed=0,
                                         mechanism="floor_tight").run(star, eps=2))
        assert result.extra["mechanism"] == "floor_tight"
        assert result.extra["validation"]["e2e_exact"] == g.n
        assert result.extra["validation"]["aggregate_exact"]
    finally:
        server.shutdown()


def _toy_record() -> TaskRecord:
    g = Graph.from_edges(6, [(0, 1), (0, 2), (1, 2), (2, 3), (2, 4), (3, 4), (4, 5)])
    return TaskRecord(1, task_prompt("triangle", g.n), g.edge_string(), g.n, g.m, g.ground_truth("triangle"), "triangle", "toy")


def _stub_cfg(base_url: str, **kw) -> ModelConfig:
    return ModelConfig(provider="openai", api_key="sk-test", base_url=base_url, structured_input=True, retry_backoff=0.0, **kw)


def test_rate_limit_and_empty_reply_are_retried_and_recorded():
    server, base_url = _serve(fail_plan=["429", "empty"])
    try:
        with collect_errors(method="Naive", run=1) as errors:
            nv = asyncio.run(NaiveFramework(_stub_cfg(base_url), seed=0).run(_toy_record(), eps=1e6))
        assert abs(nv.estimate - 2.0) < 1e-3 and nv.parse_failures == 0
        assert [e["kind"] for e in errors] == ["api_error", "empty_reply"]
        assert errors[0]["status"] == 429 and errors[0]["method"] == "Naive" and errors[0]["attempt"] == 1
        assert errors[1]["attempt"] == 2
    finally:
        server.shutdown()


def test_exhausted_retries_and_parse_failures_keep_full_reply(tmp_path):
    sink = tmp_path / "errors.jsonl"
    set_error_sink(sink)
    server, base_url = _serve(fail_plan=["429", "429", "garbage"])
    try:
        with collect_errors(method="Naive", run=1) as errors:
            nv = asyncio.run(NaiveFramework(_stub_cfg(base_url, max_retries=1), seed=0).run(_toy_record(), eps=1e6))
        # select: 429 twice -> call_failed -> "" unparseable; answer: garbage unparseable -> 0.0
        assert [e["kind"] for e in errors] == ["api_error", "api_error", "call_failed", "parse_failure", "parse_failure"]
        assert nv.estimate == 0.0 and nv.parse_failures == 2
        garbage = errors[-1]
        assert garbage["phase"] == "answer" and garbage["reply"] == GARBAGE and garbage["reply_chars"] == len(GARBAGE)
        lines = [json.loads(x) for x in sink.read_text(encoding="utf-8").splitlines()]
        assert [x["kind"] for x in lines] == [e["kind"] for e in errors]
    finally:
        set_error_sink(None)
        server.shutdown()


class _RecordingHandler(BaseHTTPRequestHandler):
    """Records every request and answers with a fixed reply (real-model path, no structured block)."""
    requests: list[dict] = []
    reply = '```json\n{"task": "triangle"}\n```\nCounting the triangles gives a total of 2.'

    def log_message(self, *args):  # silence
        pass

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        self.requests.append(body)
        data = _sse(self.reply, body.get("model", "stub"))
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _text(content) -> str:
    return content if isinstance(content, str) else "".join(b.get("text", "") for b in content)


def test_paper_naive_prompt_sends_only_the_paper_prompt():
    for style in ("cot", "paper", "paper-direct"):
        handler = type("_R", (_RecordingHandler,), {"requests": []})
        server = HTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            cfg = ModelConfig(
                provider="openai", api_key="sk-test", base_url=f"http://127.0.0.1:{server.server_address[1]}/v1",
                stream=True, structured_input=False, retry_backoff=0.0,
            )
            rec = _toy_record()
            nv = asyncio.run(NaiveFramework(cfg, seed=0, naive_prompt=style).run(rec, eps=1e6))
            assert nv.estimate == 2.0 and nv.extra["reply"] == _RecordingHandler.reply
            answer = [r["messages"] for r in handler.requests if "The edges are:" in _text(r["messages"][-1]["content"])]
            assert len(answer) == 1
            roles = [m["role"] for m in answer[0]]
            user = _text(answer[0][-1]["content"])
            assert "<structured_input>" not in user
            if style != "cot":
                assert roles == ["user"]
                assert user.startswith(rec.input_prompt.split(" Q:")[0])
                tail = "" if style == "paper" else f"\n\n{NO_REASONING_INSTRUCTION}"
                assert user.endswith(f"What is the total number of triangles in the graph?{tail}")
            else:
                assert roles == ["system", "user"] and "Think step by step" in user
        finally:
            server.shutdown()


def test_transcripts_record_every_call_with_agent_and_phase(tmp_path):
    from psc.events import set_transcript_sink

    sink = tmp_path / "transcripts.jsonl"
    set_transcript_sink(sink)
    server, base_url = _serve()
    try:
        rec = _toy_record()
        with collect_errors(method="PSC", run=1):
            psc = asyncio.run(PSCFramework(_stub_cfg(base_url), seed=0).run(rec, eps=1e6))
        with collect_errors(method="Naive", run=1):
            nv = asyncio.run(NaiveFramework(_stub_cfg(base_url), seed=0).run(rec, eps=1e6))
        calls = [json.loads(x) for x in sink.read_text(encoding="utf-8").splitlines()]
        assert len(calls) == psc.llm_calls + nv.llm_calls
        psc_calls = [c for c in calls if c["method"] == "PSC"]
        phases = [(c["agent"], c["phase"]) for c in psc_calls]
        n = rec.vertex_num
        assert phases.count(("PrivacyController", "select")) == 1 and ("Curator", "design") in phases
        assert sum(p == "send" for _, p in phases) == n and sum(p == "update" for _, p in phases) == n
        assert ("Curator", "aggregate") in phases
        assert all(a.startswith("Node-") for a, p in phases if p in ("send", "update"))
        answer = [c for c in calls if c["method"] == "Naive" and c["phase"] == "answer"]
        assert len(answer) == 1 and answer[0]["reply"] == nv.extra["reply"] and "The edges are:" in answer[0]["user"]
        assert all(c["model"] and c["reply"] and c["attempts"] == 1 for c in calls)
        # the default (paper) Naive answer is sent without a system prompt
        assert not answer[0]["system"] and all(c["system"] for c in calls if c is not answer[0])
    finally:
        set_transcript_sink(None)
        server.shutdown()


def test_clip_keeps_head_and_tail():
    text = "A" * 100 + "B" * 100
    out = clip(text, 50)
    assert out.startswith("A" * 25) and out.endswith("B" * 25) and "150 chars omitted" in out
    assert clip("short", 50) == "short"


if __name__ == "__main__":
    test_openai_provider_end_to_end()
    print("test_openai_provider_end_to_end: ok")
    test_openai_provider_streaming_gateway()
    print("test_openai_provider_streaming_gateway: ok")
    test_rate_limit_and_empty_reply_are_retried_and_recorded()
    print("test_rate_limit_and_empty_reply_are_retried_and_recorded: ok")
