"""Strict validation of the messages a node receives (research content 3.2).

The triangle GS ``dmax - 1`` assumes that every noisy neighbour sends exactly
one message, that the sender identity is genuine and that the list equals the
sender's row of the public projected noisy graph ``G'``. PSC checks none of
these (an attacker can repeat a sender id, claim someone else's id, or attach
free text). Before any message reaches the update step, the node's local
server applies, using public information and channel metadata only:

1. the sender (taken from the channel, never from the message body) is in ``N'(i)``;
2. at most one message per sender;
3. the payload's sender id equals the channel identity (strict mode; loose mode
   overwrites it with the channel identity);
4. the neighbour list equals the sender's public row ``G'(sender)``;
5. the payload has exactly the two integer fields; anything else is dropped,
   so no free text reaches a prompt that also holds private data.

Accepted messages are re-serialised from the validated integers. The checks
cost no privacy budget, and every message of an honest run passes them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

ALLOWED_KEYS = frozenset({"Sender_ID", "Sender_Neighbors"})


@dataclass(frozen=True)
class ChannelMessage:
    """A payload together with the sender identity the transport observed."""

    channel_sender: int
    payload: object


@dataclass
class ValidationResult:
    accepted: list[dict] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.rejected:
            out[r["reason"]] = out.get(r["reason"], 0) + 1
        return out


def _int_list(x) -> list[int] | None:
    if not isinstance(x, list):
        return None
    out = []
    for v in x:
        if isinstance(v, bool) or not isinstance(v, int):
            return None
        out.append(int(v))
    return out


def validate_messages(
    node_id: int,
    noisy_neighbors: Iterable[int],
    public_rows: Mapping[int, Iterable[int]],
    inbox: Sequence[ChannelMessage],
    strict: bool = True,
) -> ValidationResult:
    expected = set(int(x) for x in noisy_neighbors)
    seen: set[int] = set()
    res = ValidationResult()

    def reject(msg: ChannelMessage, reason: str) -> None:
        res.rejected.append({"channel_sender": msg.channel_sender, "reason": reason})

    for msg in inbox:
        s = msg.channel_sender
        p = msg.payload
        if s not in expected or s == node_id:
            reject(msg, "sender_not_noisy_neighbor")
            continue
        if s in seen:
            reject(msg, "duplicate_sender")
            continue
        if not isinstance(p, Mapping) or set(p) != ALLOWED_KEYS:
            reject(msg, "malformed_payload")
            continue
        claimed = p["Sender_ID"]
        lst = _int_list(p["Sender_Neighbors"])
        if isinstance(claimed, bool) or not isinstance(claimed, int) or lst is None:
            reject(msg, "malformed_payload")
            continue
        if claimed != s and strict:
            reject(msg, "spoofed_sender_id")
            continue
        if sorted(set(lst)) != sorted(set(int(x) for x in public_rows.get(s, ()))) or len(lst) != len(set(lst)):
            reject(msg, "list_differs_from_public_row")
            continue
        seen.add(s)
        res.accepted.append({"Sender_ID": s, "Sender_Neighbors": sorted(lst)})
    return res


def honest_inbox(node_id: int, noisy_neighbors: Iterable[int], public_rows: Mapping[int, Iterable[int]]) -> list[ChannelMessage]:
    """What every noisy neighbour sends in an honest run (also what a node can
    rebuild from the public ``G'`` without any message)."""
    return [
        ChannelMessage(j, {"Sender_ID": j, "Sender_Neighbors": sorted(int(x) for x in public_rows.get(j, ()))})
        for j in sorted(int(x) for x in noisy_neighbors)
    ]
