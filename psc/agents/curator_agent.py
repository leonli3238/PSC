"""Curator agent: the (untrusted) LLM that receives ``(V(G), Q)``.

Responsibilities (Section 3):

* **Algorithm Establishment** -- look up the distributed algorithm library
  and specify the send / update / aggregate rules for the task.
* **Result Aggregation** -- combine the noisy reports of the node agents into
  the final answer following the aggregate rule.
* For the **Naive** baseline it directly answers the question from the noisy
  edge list appended to the prompt (Section 2.4).
"""

from __future__ import annotations

from agentscope.agent import AgentBase
from agentscope.formatter import FormatterBase
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.model import ChatModelBase

from ..events import record_error
from ..graph import TASKS, infer_task_from_prompt
from ..library import AlgorithmSpec, algorithm_library_summary, get_algorithm
from ..models import chat
from ..prompts import (
    CURATOR_SYSTEM,
    PAPER_NAIVE_PROMPTS,
    curator_aggregate_prompt,
    extract_json,
    extract_number,
    naive_answer_prompt,
    task_selection_prompt,
)


class CuratorAgent(AgentBase):
    def __init__(self, model: ChatModelBase, formatter: FormatterBase, name: str = "Curator") -> None:
        super().__init__()
        self.name = name
        self.model = model
        self.formatter = formatter
        self.memory = InMemoryMemory()
        self.llm_calls = 0
        self.parse_failures = 0
        self.last_reply = ""

    async def _llm(self, user_prompt: str, system: str | None = CURATOR_SYSTEM) -> str:
        self.llm_calls += 1
        self.last_reply = await chat(self.model, self.formatter, system, user_prompt, agent=self.name)
        return self.last_reply

    # ------------------------------------------------------------------
    # Algorithm establishment (Algorithm 3, line 9)
    # ------------------------------------------------------------------
    async def design_algorithm(self, input_prompt: str) -> AlgorithmSpec:
        text = await self._llm(
            task_selection_prompt("curator agent", input_prompt, algorithm_library_summary(), list(TASKS)),
        )
        payload = extract_json(text) or {}
        task = str(payload.get("task", "")).strip().lower()
        if task not in TASKS:
            self.parse_failures += 1
            task = infer_task_from_prompt(input_prompt)
            record_error(
                "parse_failure", f"Curator: invalid task, falling back to rule-based inference ({task})",
                reply=text, agent=self.name, phase="design",
            )
        return get_algorithm(task)

    # ------------------------------------------------------------------
    # Result aggregation (Algorithm 3, line 14)
    # ------------------------------------------------------------------
    async def aggregate(self, algo: AlgorithmSpec, input_prompt: str, counts: list[float], n: int) -> float:
        text = await self._llm(curator_aggregate_prompt(algo.task, input_prompt, algo.aggregate, counts, n))
        return self._parse_result(text, "aggregate")

    # ------------------------------------------------------------------
    # Naive baseline (Section 2.4)
    # ------------------------------------------------------------------
    async def answer_with_noisy_graph(
        self,
        task: str,
        input_prompt: str,
        n: int,
        noisy_edges: list[tuple[int, int]],
        style: str = "default",
    ) -> float:
        """The paper styles send no curator system prompt, see :data:`psc.prompts.NAIVE_PROMPTS`."""
        text = await self._llm(
            naive_answer_prompt(task, input_prompt, n, noisy_edges, style),
            system=None if style in PAPER_NAIVE_PROMPTS else CURATOR_SYSTEM,
        )
        return self._parse_result(text, "answer")

    async def answer_prompt(self, prompt: str) -> float:
        """Answer an arbitrary counting prompt (RAW / REFINED baselines)."""
        return self._parse_result(await self._llm(prompt), "answer")

    def _parse_result(self, text: str, phase: str) -> float:
        payload = extract_json(text)
        if payload and "result" in payload:
            try:
                return float(payload["result"])
            except (TypeError, ValueError):
                pass
        value = extract_number(text)
        if value is None:
            self.parse_failures += 1
            record_error(
                "parse_failure", "Curator: could not parse a numeric result, using 0.0",
                reply=text, agent=self.name, phase=phase,
            )
            return 0.0
        return value

    # ------------------------------------------------------------------
    # AgentScope API
    # ------------------------------------------------------------------
    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        if msg is not None:
            await self.memory.add(msg)

    async def reply(self, msg: Msg | None = None, **kwargs) -> Msg:  # type: ignore[override]
        """Given the analyst prompt, return the designed distributed algorithm."""
        if msg is None:
            raise ValueError("CuratorAgent.reply expects the input prompt message")
        algo = await self.design_algorithm(msg.get_text_content() or "")
        return Msg(name=self.name, content=algo.describe(), role="assistant", metadata={"task": algo.task})
