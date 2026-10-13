"""Prompt templates shared by the agents.

Every prompt is built with a natural-language description **and** a
machine-readable copy of the inputs inside ``<structured_input>`` tags.  The
block is only needed by the offline :class:`~psc.mock_model.MockChatModel`;
:func:`psc.models.chat` strips it before calling a real LLM (see
``ModelConfig.structured_input``) so that real models see the paper's
natural-language prompts only.
"""

from __future__ import annotations

import json
import re
from typing import Any

STRUCT_OPEN = "<structured_input>"
STRUCT_CLOSE = "</structured_input>"

ANSWER_INSTRUCTION = (
    "Think step by step if needed, then finish your reply with a single JSON "
    "object inside a ```json code block with exactly the requested keys."
)


def structured_block(payload: dict[str, Any]) -> str:
    return f"{STRUCT_OPEN}\n{json.dumps(payload, ensure_ascii=False)}\n{STRUCT_CLOSE}"


def extract_structured(text: str) -> dict[str, Any] | None:
    m = re.search(re.escape(STRUCT_OPEN) + r"\s*(\{.*?\})\s*" + re.escape(STRUCT_CLOSE), text, re.S)
    if not m:
        return None
    return json.loads(m.group(1))


_STRUCT_BLOCK = re.compile(r"\s*" + re.escape(STRUCT_OPEN) + r".*?" + re.escape(STRUCT_CLOSE), re.S)


def strip_structured(text: str) -> str:
    """Remove the ``<structured_input>`` block, leaving the natural-language prompt."""
    return _STRUCT_BLOCK.sub("", text).rstrip()


def extract_json(text: str) -> dict[str, Any] | None:
    """Return the last JSON object found in an LLM reply (fenced or bare)."""
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidates = fenced[::-1] + re.findall(r"\{[^{}]*\}", text)[::-1]
    for cand in candidates:
        try:
            obj = json.loads(cand)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


# "12,300,000" is one number, but "(44,341)" and "114,115,119," are lists of node ids
_NUMBER = re.compile(
    r"(?<![\d,(])-?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\d,)])"
    r"|-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?",
)
_FRAC = re.compile(r"\\[dt]?frac\{\s*(-?[\d.,]+)\s*\}\{\s*(-?[\d.,]+)\s*\}|(-?[\d.]+)\s*/\s*(-?[\d.]+)")
# the "3" of "3-stars", the "1" of "1-hop"
_TERM_SUFFIX = re.compile(r"\s*-\s*(?:stars?|hop)", re.I)


def _to_float(token: str) -> float:
    return float(token.replace(",", ""))


def _boxed_contents(text: str) -> list[str]:
    """Contents of every ``\\boxed{...}``, with nested braces."""
    out = []
    for m in re.finditer(r"\\boxed\{", text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        if depth == 0:
            out.append(text[m.end():i - 1])
    return out


def _numbers(text: str) -> list[str]:
    return [m.group() for m in _NUMBER.finditer(text) if not _TERM_SUFFIX.match(text, m.end())]


_PLAIN_FRAC = re.compile(r"(-?\d+(?:\.\d+)?)\s*/\s*(-?\d+(?:\.\d+)?)")


def _last_number(text: str) -> float | None:
    """The last number, or ``a/b`` when that number is the denominator of a bare fraction."""
    matches = [m for m in _NUMBER.finditer(text) if not _TERM_SUFFIX.match(text, m.end())]
    if not matches:
        return None
    last = matches[-1]
    for frac in _PLAIN_FRAC.finditer(text):
        if frac.end() == last.end() and frac.start(2) == last.start():
            b = float(frac.group(2))
            return float(frac.group(1)) / b if b else None
    return _to_float(last.group())


def _boxed_value(content: str) -> float | None:
    frac = _FRAC.search(content)
    if frac:
        a, b = (frac.group(1), frac.group(2)) if frac.group(1) is not None else (frac.group(3), frac.group(4))
        return _to_float(a) / _to_float(b) if _to_float(b) else None
    nums = _numbers(content)
    return _to_float(nums[-1]) if nums else None


def extract_number(text: str) -> float | None:
    """Fallback when the reply has no JSON answer: the last ``\\boxed{...}``
    (a number or ``\\frac{a}{b}``), else the last ``###421``, else the last
    number (or bare ``a/b``) that is not part of a ``k-star`` / ``k-hop`` term."""
    for content in reversed(_boxed_contents(text)):
        value = _boxed_value(content)
        if value is not None:
            return value
    marked = re.findall(r"###\s*(" + _NUMBER.pattern + ")", text)
    if marked:
        return _to_float(marked[-1])
    return _last_number(text)


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

CURATOR_SYSTEM = (
    "You are the curator agent of a multi-agent system that solves substructure "
    "counting problems on a graph under edge local differential privacy. You "
    "never see the true edges of the graph. You (1) design a distributed "
    "algorithm for the node agents using the algorithm library, and (2) "
    "aggregate the noisy reports from node agents into the final answer. Be "
    "precise with arithmetic."
)

PRIVACY_CONTROLLER_SYSTEM = (
    "You are the privacy controller of a multi-agent system. Given a graph "
    "reasoning task you look up the DP framework library and decide which DP "
    "framework applies. You must answer strictly with the requested JSON."
)

NODE_SYSTEM = (
    "You are node agent {node_id} in a distributed graph algorithm. You manage "
    "the neighborhood information of node {node_id} only. Follow the rules given "
    "to you exactly, be careful with arithmetic, and reply with the requested "
    "JSON at the end."
)


# ---------------------------------------------------------------------------
# Task-level prompts
# ---------------------------------------------------------------------------


def task_selection_prompt(role: str, input_prompt: str, library_summary: str, options: list[str]) -> str:
    payload = {"phase": "select_task", "input_prompt": input_prompt, "options": options}
    return (
        f"{library_summary}\n\n"
        f"The input prompt from the analyst is:\n\"\"\"\n{input_prompt}\n\"\"\"\n\n"
        f"As the {role}, identify which entry of the library matches the task in the "
        f"input prompt. The valid answers are: {', '.join(options)}.\n"
        f"{ANSWER_INSTRUCTION} Required key: \"task\".\n\n{structured_block(payload)}"
    )


def node_send_prompt(node_id: int, noisy_neighbors: list[int], send_rule: str, value: float, state_var: str) -> str:
    """``state_var`` is the task's state variable (:attr:`psc.library.AlgorithmSpec.state_var`)."""
    payload = {
        "phase": "node_send",
        "node_id": node_id,
        "neighbors": noisy_neighbors,
        "state": {state_var: value},
    }
    nb = ", ".join(f"Node {x}" for x in noisy_neighbors) if noisy_neighbors else "(none)"
    return (
        f"Send rule:\n{send_rule}\n\n"
        f"Node ID: {node_id}\nState: 1. `{state_var}`: {value}\n"
        f"Neighbor Information:\nConnected to:\n{nb}\n\n"
        "Construct the message that this node sends to each of its neighbors. "
        f"{ANSWER_INSTRUCTION} Required keys: \"Sender_ID\", \"Sender_Neighbors\".\n\n"
        f"{structured_block(payload)}"
    )


def node_update_prompt(
    task: str,
    node_id: int,
    real_neighbors: list[int],
    received: list[dict],
    update_rule: str,
    value: float,
    state_var: str,
) -> str:
    """The State line, the requested value and the JSON key all use ``state_var``,
    the variable the update rule sets."""
    payload = {
        "phase": "node_update",
        "task": task,
        "node_id": node_id,
        "neighbors": real_neighbors,
        "messages": received,
        "state_var": state_var,
        "state": {state_var: value},
    }
    nb = ", ".join(str(x) for x in real_neighbors) if real_neighbors else "(none)"
    if received:
        msg_lines = "\n".join(
            f"Message: 1. `Sender_ID`: {m['Sender_ID']}; 2. `Sender_Neighbors`: {m['Sender_Neighbors']}"
            for m in received
        )
    else:
        msg_lines = "(no messages received)"
    return (
        f"Update rule:\n{update_rule}\n\n"
        f"Node ID: {node_id}\nState: 1. `{state_var}`: {value}\n"
        f"Neighbor Information:\nConnected to:\n{nb}\n"
        f"Received Messages:\n{msg_lines}\n\n"
        f"Apply the update rule and report the updated `{state_var}` of this node. "
        f"{ANSWER_INSTRUCTION} Required key: \"{state_var}\" (a number).\n\n"
        f"{structured_block(payload)}"
    )


def curator_aggregate_prompt(task: str, input_prompt: str, aggregate_rule: str, counts: list[float], n: int) -> str:
    payload = {
        "phase": "curator_aggregate",
        "task": task,
        "n": n,
        "counts": counts,
    }
    listed = ", ".join(f"{c:.4f}" for c in counts)
    return (
        f"The analyst asked:\n\"\"\"\n{input_prompt}\n\"\"\"\n\n"
        f"The graph has {n} nodes. The node agents have finished the distributed "
        f"execution and reported the following noisy counts (one per node):\n[{listed}]\n\n"
        f"Aggregation rule:\n{aggregate_rule}\n\n"
        f"{ANSWER_INSTRUCTION} Required key: \"result\" (a number).\n\n"
        f"{structured_block(payload)}"
    )


_NODES_SENTENCE = re.compile(r"(Q:\s*The nodes are numbered from \d+ to \d+\.)")


def edge_list_string(edges: list[tuple[int, int]]) -> str:
    """RAW-style edge list: ``(0, 1), (0, 2), ...`` (Appendix B)."""
    return ", ".join(f"({u}, {v})" for u, v in edges)


def insert_edges_into_prompt(input_prompt: str, edges: list[tuple[int, int]]) -> str:
    """Encode ``edges`` into the ``(V(G), Q)`` prompt following the RAW format
    of Appendix B: ``Q: The nodes are numbered from 0 to n-1. The edges are:
    (0, 1), ... What is ...?``  Falls back to appending when the node sentence
    cannot be located."""
    sentence = f" The edges are: {edge_list_string(edges)}."
    new_prompt, k = _NODES_SENTENCE.subn(lambda m: m.group(1) + sentence, input_prompt, count=1)
    if k == 0:
        new_prompt = f"{input_prompt}{sentence}"
    return new_prompt


# "paper" (default): only the RAW-style (V(G), Q) + edge list that the paper
# shows, no system prompt and no answer-format instruction;
# "paper-direct": "paper" followed by NO_REASONING_INSTRUCTION;
# "cot": curator system prompt + ANSWER_INSTRUCTION (step by step, then JSON);
# the default before 2026-10-13, recorded as "default" in older manifests.
NAIVE_PROMPTS: tuple[str, ...] = ("paper", "paper-direct", "cot")
DEFAULT_NAIVE_PROMPT = "paper"
PAPER_NAIVE_PROMPTS: frozenset[str] = frozenset({"paper", "paper-direct"})
NO_REASONING_INSTRUCTION = (
    "Answer directly with the final number only. Do not reason step by step, do not list "
    "nodes, neighbors or degrees, and do not show any intermediate calculation."
)


def naive_answer_prompt(
    task: str, input_prompt: str, n: int, noisy_edges: list[tuple[int, int]], style: str = DEFAULT_NAIVE_PROMPT,
) -> str:
    """Section 2.4: the curator encodes the noisy edges of ``G'`` as an edge
    list string and appends it to the original prompt ``(V(G), Q)``."""
    if style not in NAIVE_PROMPTS:
        raise ValueError(f"unknown naive prompt {style!r}, expected one of {NAIVE_PROMPTS}")
    payload = {
        "phase": "naive_answer",
        "task": task,
        "n": n,
        "edges": [list(e) for e in noisy_edges],
    }
    if style == "paper":
        instruction = ""
    elif style == "paper-direct":
        instruction = f"{NO_REASONING_INSTRUCTION}\n\n"
    else:
        instruction = f"{ANSWER_INSTRUCTION} Required key: \"result\" (a number).\n\n"
    return (
        f"{insert_edges_into_prompt(input_prompt, noisy_edges)}\n\n"
        f"{instruction}"
        f"{structured_block(payload)}"
    )


# ---------------------------------------------------------------------------
# Appendix B: single-LLM prompting baselines (RAW / REFINED)
# ---------------------------------------------------------------------------

_DEFINITIONS = {
    "degree": (
        "The degree of a node is the number of edges connected to it. The "
        "average degree of a graph is the sum of all node degrees divided by "
        "the number of nodes."
    ),
    "2-star": (
        "A 2-star graph consists of a central node, called the center, which is "
        "connected to exactly two other nodes by edges."
    ),
    "3-star": (
        "A 3-star graph consists of a central node, called the center, which is "
        "connected to exactly three other nodes by edges."
    ),
    "triangle": (
        "A triangle consists of three nodes where each pair of nodes is "
        "connected by an edge."
    ),
}

_COT = {
    "degree": (
        "1. List all edges and identify each node's neighbors.\n"
        "2. For each node, calculate its degree (number of neighbors).\n"
        "3. Sum all degrees and divide by the number of nodes to get the average degree."
    ),
    "2-star": (
        "1. List all edges and identify each node's neighbors.\n"
        "2. For each node, calculate its degree (number of neighbors).\n"
        "3. For nodes with degree >= 2, calculate combinations C(degree, 2).\n"
        "4. Sum all combinations to get the total 2-stars."
    ),
    "3-star": (
        "1. List all edges and identify each node's neighbors.\n"
        "2. For each node, calculate its degree (number of neighbors).\n"
        "3. For nodes with degree >= 3, calculate combinations C(degree, 3).\n"
        "4. Sum all combinations to get the total 3-stars."
    ),
    "triangle": (
        "1. List all edges and identify each node's neighbors.\n"
        "2. For each edge (u, v), find the common neighbors of u and v.\n"
        "3. Sum the number of common neighbors over all edges.\n"
        "4. Divide the sum by 3 to get the total number of triangles, because "
        "each triangle is counted once per edge."
    ),
}

_QUESTION = {
    "degree": "What is the average degree of the following graph?",
    "2-star": "What is the total number of 2-stars in the following graph?",
    "3-star": "What is the total number of 3-stars in the following graph?",
    "triangle": "What is the total number of triangles in the following graph?",
}


def raw_prompt(task: str, n: int, edges: list[tuple[int, int]]) -> str:
    """RAW (zero-shot) prompt of Appendix B -- definition + task with node and
    edge string, no LDP notice."""
    from .graph import task_prompt  # local import to avoid a cycle

    payload = {"phase": "single_llm", "task": task, "n": n, "edges": [list(e) for e in edges]}
    base = task_prompt(task, n, ldp=False)
    return (
        f"{insert_edges_into_prompt(base, edges)}\n\n"
        f"{ANSWER_INSTRUCTION} Required key: \"result\" (a number).\n\n"
        f"{structured_block(payload)}"
    )


def refined_prompt(task: str, n: int, edges: list[tuple[int, int]], neighbors: list[list[int]], example: str) -> str:
    """REFINED prompt (Nguyen and Yan, 2024): FS + Least-to-Most + 1-hop.

    Sections follow Appendix B: definition, COT instruction, a worked example
    on a 10-node graph, the task, and the 1-hop neighbor sets of every node.
    """
    payload = {"phase": "single_llm", "task": task, "n": n, "edges": [list(e) for e in edges]}
    hop = "\n".join(
        f"1-hop neighbor set of node {i} is {', '.join(map(str, nb)) if nb else '(empty)'}"
        for i, nb in enumerate(neighbors)
    )
    return (
        f"# The definition of {task}\n{_DEFINITIONS[task]}\n\n"
        f"# The COT instruction\n{_COT[task]}\n\n"
        f"# The example with 10 nodes\n{example}\n\n"
        f"# The substructure counting task\nFollow the given example, you need to answer:\n"
        f"{_QUESTION[task]} The edges of this graph are: {edge_list_string(edges)}. "
        f"The nodes are numbered from 0 to {n - 1}.\n\n"
        f"# The 1-hop neighbor of the given graph\n"
        f"The one-hop neighboring information of the graph in the problem is:\n{hop}\n\n"
        f"{ANSWER_INSTRUCTION} Required key: \"result\" (a number).\n\n"
        f"{structured_block(payload)}"
    )
