"""Run directories and trusted local audit artifacts; never serialize secrets."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
from typing import Iterable

from .mechanism import get_mechanism


def new_run_directory(base: str | Path, tag: str | None, default_prefix: str) -> Path:
    name = tag or f"{default_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    if Path(name).name != name or name in (".", ".."):
        raise ValueError("tag must be a single directory name")
    path = Path(base) / name
    path.mkdir(parents=True, exist_ok=False)
    return path


def append_run(path: str | Path, row: dict) -> None:
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")


def write_manifest(
    out: Path, mechanism: str, data: str | Path, datasets: Iterable[str], settings: dict,
) -> None:
    root = Path(__file__).resolve().parents[1]
    paths = sorted((root / "psc").rglob("*.py")) + sorted((root / "scripts").glob("*.py"))
    paths += [Path(data) / f"{dataset}.json" for dataset in datasets]
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "mechanism": get_mechanism(mechanism).to_dict(),
        "settings": settings,
        "sha256": {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "trace_note": "runs.jsonl includes local raw-count diagnostics; keep it in trusted storage.",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
