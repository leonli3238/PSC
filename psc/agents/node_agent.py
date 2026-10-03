"""Node agent ``N_i``: manages the neighborhood information of node ``v_i``.

Two kinds of memory are kept, mirroring Section 3 ("Distributed Execution"):

* ``_real_neighbors`` -- the true neighbor set ``N_G(v_i)``.  It is *never*
  sent to anybody in the clear.  It is only read by the **update** step
  (whose result is later protected by the Laplace mechanism) and by the
  local randomized-response / noisy-degree routines, which are executed as
  code on the node's trusted local server.
* ``noisy_neighbors`` -- the node's neighbors in the noisy graph ``G'``.
  Only this list is accessed by the **send** step.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Iterable

import numpy as np
from agentscope.agent import AgentBase
from agentscope.formatter import FormatterBase
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.model import ChatModelBase

from .. import rules
from ..dp import laplace_mechanism, node_noisy_lower_row, project_neighbor_list
from ..events import record_error
from ..models import chat
from ..prompts import NODE_SYSTEM, extract_json, extract_number, node_send_prompt, node_update_prompt


class NodeAgent(AgentBase):
    """A node agent driven by an LLM that follows the curator's rules."""

    # Class-level limiter so that hundreds of node agents do not flood the API
    _semaphore: asyncio.Semaphore | None = None

    @classmethod
    def set_max_concurrency(cls, k: int) -> None:
        cls._semaphore = asyncio.Semaphore(max(1, k))

    def __init__(
        self,
        node_id: int,
        neighbors: Iterable[int],
        model: ChatModelBase,
        formatter: FormatterBase,
    ) -> None:
        super().__init__()
        self.name = f"Node-{node_id}"
        self.node_id = int(node_id)
        self.model = model
        self.formatter = formatter
        self.memory = InMemoryMemory()

        # private memory
        self._real_neighbors: list[int] = sorted(int(x) for x in neighbors)
        self._update_neighbors: list[int] = list(self._real_neighbors)
        # noisy edge memory (set by the privacy controller)
        self.noisy_neighbors: list[int] = []

        # algorithm state
        self.count: float = 0.0
        self.inbox: list[dict] = []
        self.sent_payload: dict | None = None

        # bookkeeping
        self.llm_calls = 0
        self.parse_failures = 0

    # ------------------------------------------------------------------
    # Local DP routines (code, executed on the trusted local server)
    # ------------------------------------------------------------------
    @property
    def degree(self) -> int:
        return len(self._real_neighbors)

    def release_noisy_edges(self, eps1: float, rng: np.random.Generator) -> list[tuple[int, int]]:
        """Algorithm 1, lines 2-4: RR on entries ``a_{i,j}, j < i``."""
        noisy_lower = node_noisy_lower_row(self.node_id, self._real_neighbors, eps1, rng)
        return [(self.node_id, j) for j in noisy_lower]

    def report_noisy_degree(self, eps2: float, rng: np.random.Generator) -> float:
        """Algorithm 2, line 2: ``deg + Lap(1/eps2)``."""
        return laplace_mechanism(self.degree, 1.0, eps2, rng)

    def set_noisy_neighbors(self, neighbors: Iterable[int]) -> None:
        self.noisy_neighbors = sorted(int(x) for x in neighbors)

    def bound_degree(self, d_max: int, rng: np.random.Generator) -> None:
        """Project the neighbor list used in the update step to ``d_max``
        neighbors (tasks without a noisy graph, see ``GSOptimize``)."""
        self._update_neighbors = project_neighbor_list(self._real_neighbors, d_max, rng)

    def protected_count(self, sensitivity: float, eps3: float, rng: np.random.Generator) -> float:
        """Algorithm 3, line 13: ``count + Lap(GS_f / eps3)``."""
        return laplace_mechanism(self.count, sensitivity, eps3, rng)

    def reference_count(self, task: str, messages: list[dict]) -> float:
        """The update rule executed in code on ``messages`` (validation only;
        the result never leaves the trusted local server)."""
        return rules.update(task, self._update_neighbors, messages)

    def reset(self) -> None:
        self.count = 0.0
        self.inbox.clear()
        self.sent_payload = None

    # ------------------------------------------------------------------
    # AgentScope API
    # ------------------------------------------------------------------
    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        """Receive messages from other node agents (Algorithm 3, line 10)."""
        if msg is None:
            return
        for m in msg if isinstance(msg, list) else [msg]:
            meta = m.metadata or {}
            if meta.get("kind") == "node_message":
                self.inbox.append(meta["payload"])
            await self.memory.add(m)

    async def reply(self, msg: Msg | None = None, **kwargs) -> Msg:  # type: ignore[override]
        """Execute the phase requested by the curator (``send`` or ``update``)."""
        if msg is None:
            raise ValueError("NodeAgent.reply expects an instruction message")
        meta = msg.metadata or {}
        phase = meta.get("phase")
        rule = msg.get_text_content() or ""
        if phase == "send":
            return await self._send(rule)
        if phase == "update":
            return await self._update(meta["task"], rule)
        raise ValueError(f"unknown phase {phase!r}")

    # ------------------------------------------------------------------
    async def _llm(self, user_prompt: str) -> str:
        system = NODE_SYSTEM.format(node_id=self.node_id)
        self.llm_calls += 1
        if NodeAgent._semaphore is None:
            return await chat(self.model, self.formatter, system, user_prompt)
        async with NodeAgent._semaphore:
            return await chat(self.model, self.formatter, system, user_prompt)

    async def _send(self, rule: str) -> Msg:
        """Send rule: reads only the noisy edge memory.

        An unparseable reply is counted as a failure and nothing is sent, so
        LLM mistakes propagate exactly as they would in the paper's setting.
        """
        text = await self._llm(node_send_prompt(self.node_id, self.noisy_neighbors, rule, self.count))
        self.sent_payload = _parse_send_payload(extract_json(text))
        if self.sent_payload is None:
            self.parse_failures += 1
            record_error(
                "parse_failure", f"Node {self.node_id}: could not parse send message, nothing is sent",
                reply=text, agent=self.name, phase="send",
            )
        return Msg(
            name=self.name,
            content=json.dumps(self.sent_payload),
            role="assistant",
            metadata={
                "kind": "node_message",
                "sender": self.node_id,
                "recipients": list(self.noisy_neighbors) if self.sent_payload is not None else [],
                "payload": self.sent_payload,
            },
        )

    async def _update(self, task: str, rule: str) -> Msg:
        """Update rule: loads the (possibly degree-bounded) real neighbor list."""
        text = await self._llm(
            node_update_prompt(task, self.node_id, self._update_neighbors, self.inbox, rule, self.count),
        )
        payload = extract_json(text)
        value = None
        if payload and "count" in payload:
            try:
                value = float(payload["count"])
            except (TypeError, ValueError):
                value = None
        if value is None:
            value = extract_number(text)
        if value is None:
            self.parse_failures += 1
            record_error(
                "parse_failure", f"Node {self.node_id}: could not parse count, keeping {self.count}",
                reply=text, agent=self.name, phase="update",
            )
            value = self.count
        self.count = value
        return Msg(
            name=self.name,
            content=f"count={self.count}",
            role="assistant",
            metadata={"kind": "node_state", "node_id": self.node_id, "count": self.count},
        )


_NODE_REF = re.compile(r"\s*(?:node\s*)?(\d+)\s*", re.IGNORECASE)


def _node_id(x) -> int:
    """Accept ``12``, ``"12"`` and ``"Node 12"``: the send prompt lists the
    neighbors as ``Node 12`` (Appendix E format) and models echo that form."""
    if isinstance(x, bool):
        raise TypeError(f"not a node id: {x!r}")
    if isinstance(x, int):
        return x
    if isinstance(x, float) and x.is_integer():
        return int(x)
    m = _NODE_REF.fullmatch(x) if isinstance(x, str) else None
    if m is None:
        raise ValueError(f"not a node id: {x!r}")
    return int(m.group(1))


def _parse_send_payload(payload: dict | None) -> dict | None:
    if not payload or "Sender_ID" not in payload or "Sender_Neighbors" not in payload:
        return None
    neighbors = payload["Sender_Neighbors"]
    if not isinstance(neighbors, list):
        return None
    try:
        return {
            "Sender_ID": _node_id(payload["Sender_ID"]),
            "Sender_Neighbors": sorted(_node_id(x) for x in neighbors),
        }
    except (TypeError, ValueError):
        return None
