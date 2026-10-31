"""Node agent with the trusted execution layer of certicount.

:class:`TrustedNodeAgent` extends the reproduction's
:class:`psc.agents.node_agent.NodeAgent` without changing its DP routines
(RR, noisy degree, projection and Laplace stay the reproduction's code):

* ``execution="llm"``     -- the node LLM applies the update rule (paper baseline);
* ``execution="guard"``   -- Improvement 1: non-neighbour messages are filtered
  out in code before the prompt, and the LLM's count is replaced by the code
  value of the bound function when they differ, so the perturbed value always
  has sensitivity ``GS`` (the fallback rate measures how often the LLM was wrong);
* ``execution="program"`` -- Improvement 2: the node's interpreter runs a
  verified DSL program on the private list; no LLM is involved.

With a binding the update task and rule text come from the node's binding
table instead of the curator's instruction; with validation, received messages
pass :func:`certicount.messages.validate_messages` before the update step.
"""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
from agentscope.message import Msg

from psc import rules
from psc.agents.node_agent import NodeAgent

from .binding import Binding
from .dsl.lang import Env, Interpreter, Program, smallest_projector
from .messages import ChannelMessage, validate_messages

EXECUTIONS = ("llm", "guard", "program")


class TrustedNodeAgent(NodeAgent):
    def __init__(self, *args, execution: str = "llm", validate: bool = True, strict: bool = True,
                 send_by_code: bool = False, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if execution not in EXECUTIONS:
            raise ValueError(f"unknown execution {execution!r}; choose from {EXECUTIONS}")
        self.execution = execution
        self.validate = validate
        self.strict = strict
        self.send_by_code = send_by_code
        self.binding: Binding | None = None
        self.program: Program | None = None
        self.params_D = 0
        self.params_dmax = 0
        self.n = 0
        self.public_rows: dict[int, frozenset] = {}
        self.raw_inbox: list[ChannelMessage] = []
        self.rejected: list[dict] = []
        self.guard_fallbacks = 0
        self.guard_deviation = 0.0
        self._projection_limit: int | None = None

    # -- set-up by the framework ------------------------------------------------
    def bound_degree(self, d_max: int, rng: np.random.Generator) -> None:
        super().bound_degree(d_max, rng)
        self._projection_limit = int(d_max)

    def configure(self, n: int, public_rows: dict[int, Iterable[int]] | None, D: int | None,
                  binding: Binding | None = None, program: Program | None = None) -> None:
        self.n = n
        self.public_rows = {int(k): frozenset(v) for k, v in (public_rows or {}).items()}
        self.params_D = self.params_dmax = int(D or 0)
        self.binding = binding
        self.program = program

    # -- messages ---------------------------------------------------------------
    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        if msg is None:
            return
        for m in msg if isinstance(msg, list) else [msg]:
            meta = m.metadata or {}
            if meta.get("kind") == "node_message":
                self.raw_inbox.append(ChannelMessage(int(meta["channel_sender"]), meta.get("payload")))
                if not self.validate:
                    self.inbox.append(meta["payload"])
            await self.memory.add(m)

    def prepare_update(self) -> None:
        if not self.validate:
            return
        res = validate_messages(self.node_id, self.noisy_neighbors, self.public_rows, self.raw_inbox, self.strict)
        self.inbox = res.accepted
        self.rejected = res.rejected

    async def _send(self, task: str, rule: str) -> Msg:
        if not self.send_by_code:
            return await super()._send(task, rule)
        # the message is the node's public noisy row: post-processing, no LLM call
        self.sent_payload = rules.send_message(self.node_id, self.noisy_neighbors)
        return Msg(
            name=self.name, content=str(self.sent_payload), role="assistant",
            metadata={"kind": "node_message", "sender": self.node_id, "recipients": list(self.noisy_neighbors),
                      "payload": self.sent_payload},
        )

    # -- update -----------------------------------------------------------------
    async def reply(self, msg: Msg | None = None, **kwargs) -> Msg:  # type: ignore[override]
        meta = (msg.metadata or {}) if msg is not None else {}
        if self.binding is not None and meta.get("phase") in ("send", "update"):
            # the bound task and rule replace whatever the curator sent
            rule = self.binding.algorithm.send if meta["phase"] == "send" else self.binding.algorithm.update
            msg = Msg(msg.name, rule, "assistant", metadata={**meta, "task": self.binding.task})
        return await super().reply(msg, **kwargs)

    async def _update(self, task: str, rule: str) -> Msg:
        if self.execution == "program":
            self.count = self.run_program()
            return Msg(self.name, f"count={self.count}", "assistant",
                       metadata={"kind": "node_state", "node_id": self.node_id, "count": self.count})
        if self.execution == "guard":
            senders = set(self._update_neighbors)
            self.inbox = [m for m in self.inbox if m.get("Sender_ID") in senders]
        out = await super()._update(task, rule)
        if self.execution == "guard":
            code = self.reference_count(task, self.inbox)
            if not math.isclose(self.count, code, abs_tol=1e-6):
                self.guard_fallbacks += 1
                self.guard_deviation += abs(self.count - code)
                self.count = code
        return out

    def run_program(self) -> float:
        if self.program is None:
            raise RuntimeError("program execution without a program")
        env = Env(
            frozenset(self._real_neighbors), self.node_id, self.public_rows, self.n,
            D=self.params_D, dmax=self.params_dmax, projector=self._projector,
        )
        return Interpreter(self.program).local(env)

    def _projector(self, s: frozenset, k: int) -> frozenset:
        """The projection drawn by the privacy controller for this run (so that
        program and LLM execution see the same projected list); other sets fall
        back to a deterministic projection."""
        if s == frozenset(self._real_neighbors) and k == self._projection_limit:
            return frozenset(self._update_neighbors)
        return smallest_projector(s, k)
