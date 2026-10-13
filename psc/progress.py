"""Optional progress bar for experiment runs.

``chat`` ticks the bar after each model call. The experiment runner sets the
current cell label and pipeline phase. Both are no-ops when no bar is active,
so tests and one-off framework calls stay quiet.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Callable, Iterator

from tqdm import tqdm

_tick: ContextVar[Callable[[], None] | None] = ContextVar("psc_llm_tick", default=None)
_phase: ContextVar[Callable[[str], None] | None] = ContextVar("psc_phase", default=None)
_current_phase: ContextVar[str | None] = ContextVar("psc_current_phase", default=None)


def note_llm_call() -> None:
    """Count one finished model call. No-op outside :func:`llm_progress`."""
    fn = _tick.get()
    if fn is not None:
        fn()


def note_phase(phase: str) -> None:
    """Show the current pipeline step (``send``, ``update``, ...) on the bar.

    The step is also kept for the current run (child tasks started afterwards
    inherit it), see :func:`current_phase`."""
    _current_phase.set(phase)
    fn = _phase.get()
    if fn is not None:
        fn(phase)


def current_phase() -> str | None:
    return _current_phase.get()


@contextmanager
def llm_progress(total: int) -> Iterator[tqdm]:
    """A stderr bar over ``total`` model calls. Child tasks inherit the hooks."""
    bar = tqdm(total=total, unit="call", mininterval=0.2, miniters=1, dynamic_ncols=True, file=sys.stderr)
    tick_token = _tick.set(bar.update)
    phase_token = _phase.set(lambda phase: bar.set_postfix_str(phase, refresh=True))
    try:
        yield bar
    finally:
        _tick.reset(tick_token)
        _phase.reset(phase_token)
        bar.close()
