"""Result directories and manifests of certicount experiments."""

from __future__ import annotations

import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from psc.artifacts import new_run_directory

from . import REPRO_ROOT, RESULTS_DIR, ROOT


def out_dir(kind: str, tag: str | None, prefix: str) -> Path:
    """``results/<kind>/<tag>/``; an existing tag is refused (no overwrite)."""
    return new_run_directory(RESULTS_DIR / kind, tag, prefix)


def _clean(obj):
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, set):
        return sorted(_clean(v) for v in obj)
    return obj


def write_json(obj, path: Path) -> None:
    path.write_text(json.dumps(_clean(obj), indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def append_jsonl(row: dict, path: Path) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(_clean(row), ensure_ascii=False, default=str) + "\n")


def write_manifest(out: Path, settings: dict) -> None:
    paths = sorted((ROOT / "certicount").rglob("*.py")) + sorted((ROOT / "scripts").glob("*.py"))
    paths += sorted((REPRO_ROOT / "psc").rglob("*.py"))
    write_json({
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "settings": settings,
        "sha256": {str(p.relative_to(ROOT.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    }, out / "manifest.json")


def markdown_table(rows: Sequence[dict], columns: Sequence[str], digits: int = 4) -> str:
    out = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for r in rows:
        cells = []
        for c in columns:
            v = r.get(c)
            if isinstance(v, bool) or v is None:
                cells.append("-" if v is None else str(v))
            elif isinstance(v, float):
                cells.append(f"{v:.{digits}g}" if abs(v) >= 1e4 or (v != 0 and abs(v) < 1e-3) else f"{v:.{digits}f}")
            elif isinstance(v, dict):
                cells.append(", ".join(f"{k}={x}" for k, x in v.items()) or "-")
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)
