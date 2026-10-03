"""Per-run error records: API errors, retries, empty and unparseable replies.

Model calls and reply parsers report problems through :func:`record_error`.
The experiment runner wraps every run in :func:`collect_errors`, which tags
the records with the run (dataset / task / method / run number) and returns
them for ``RunResult.extra["errors"]``. Each record is also appended to the
file set by :func:`set_error_sink` as soon as it happens, so the log survives
a crashed experiment, and is emitted as a logging warning.
"""

from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger("psc.errors")

# Replies are stored with up to this many characters (head and tail kept);
# the JSON answer usually sits at the end of a reply, so the tail matters.
MAX_RECORDED_CHARS = 20000
# Characters of the reply shown in the warning line on the console / run.log
MAX_LOGGED_CHARS = 4000

_records: ContextVar[list[dict] | None] = ContextVar("psc_error_records", default=None)
_context: ContextVar[dict[str, Any]] = ContextVar("psc_error_context", default={})
_sink: Path | None = None


def clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    half = limit // 2
    return f"{text[:half]}\n...[{len(text) - 2 * half} chars omitted]...\n{text[-half:]}"


def set_error_sink(path: str | Path | None) -> None:
    """Append every record as one JSON line to ``path`` (``None`` disables)."""
    global _sink
    _sink = Path(path) if path is not None else None
    if _sink is not None:
        _sink.parent.mkdir(parents=True, exist_ok=True)
        _sink.write_text("", encoding="utf-8")


@contextmanager
def collect_errors(**context: Any) -> Iterator[list[dict]]:
    """Collect the records of one run; child asyncio tasks inherit the collector."""
    records: list[dict] = []
    rec_token = _records.set(records)
    ctx_token = _context.set(context)
    try:
        yield records
    finally:
        _records.reset(rec_token)
        _context.reset(ctx_token)


def record_error(kind: str, message: str, *, reply: str | None = None, **fields: Any) -> None:
    """Record one problem.

    ``kind`` is one of ``api_error`` (retryable exception, will retry),
    ``empty_reply`` (will retry), ``call_failed`` (no usable reply after all
    retries) or ``parse_failure`` (reply received but not understood).
    """
    rec: dict[str, Any] = {
        "time": datetime.now().isoformat(timespec="milliseconds"),
        "kind": kind,
        **_context.get(),
        **fields,
        "message": message,
    }
    if reply is not None:
        rec["reply_chars"] = len(reply)
        rec["reply"] = clip(reply, MAX_RECORDED_CHARS)
    records = _records.get()
    if records is not None:
        records.append(rec)
    if _sink is not None:
        with _sink.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    where = " ".join(f"{k}={v}" for k, v in _context.get().items())
    shown = f" | reply ({len(reply)} chars): {clip(reply, MAX_LOGGED_CHARS)!r}" if reply is not None else ""
    logger.warning("[%s]%s %s%s", kind, f" {where}" if where else "", message, shown)


def count_errors(records: list[dict], *kinds: str) -> int:
    return sum(r["kind"] in kinds for r in records)
