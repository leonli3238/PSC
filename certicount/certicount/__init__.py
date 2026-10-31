"""CertiCount (formerly ``psc-trust`` / ``psctrust``): execution trustworthiness of LLM multi-agent substructure counting under edge LDP.

Research code of the thesis proposal (``docs/OPENING_REPORT_FINAL_2026-10-18.md``):
sensitivity audit of LLM node agents, node-side binding and message validation,
guarded and programmatic (DSL) execution, cost and composite-query accounting.

The paper reproduction (sibling directory ``../psc``, formerly
``../psc-reproduction``) is a frozen dependency: its ``psc`` package provides
the DP primitives, the agents, the datasets and the model configuration
(``config.toml`` / ``.env``), and is never modified by this project. When
``psc`` is not installed, the reproduction directory is put on ``sys.path``;
``PSC_REPRO_ROOT`` overrides where it is looked for.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _repro_root() -> Path:
    """The reproduction directory: ``$PSC_REPRO_ROOT``, else ``../psc``, else ``../psc-reproduction``."""
    env = os.getenv("PSC_REPRO_ROOT")
    candidates = [Path(env)] if env else [ROOT.parent / "psc", ROOT.parent / "psc-reproduction"]
    for c in candidates:
        if (c / "psc" / "__init__.py").exists():
            return c.resolve()
    return candidates[0]


REPRO_ROOT = _repro_root()
DATA_DIR = REPRO_ROOT / "data"
RESULTS_DIR = ROOT / "results"

try:
    import psc  # noqa: F401
except ImportError:  # pragma: no cover - depends on the environment
    sys.path.insert(0, str(REPRO_ROOT))
    import psc  # noqa: F401

__version__ = "0.1.0"
