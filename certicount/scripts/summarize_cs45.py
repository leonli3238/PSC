"""One-page summary of the CS4 (online check of the design-loop fixes) and CS5 (prompt evolution,
held-out evaluation) runs of ``scripts/run_cscwd.sh cs45-all``. Reads result directories only.

    ../.venv/bin/python scripts/summarize_cs45.py --out results/reports/cs45_summary.md

Per design run: accept rate, qualified rate (accepted and within the noise-free bias of the
reference: ``noise_free_pass``), median / mean relative error of the accepted designs vs the
reference program (GT-DSL), model calls per design, repairs (designs whose last rejected draft was
followed by an accepted one, by rejection stage), and the certification ablation (drafts that
would violate ε without certification, unsound certificates).
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DSL = ROOT / "results" / "dsl_eval"
EVO = ROOT / "results" / "evolve"

RUNS = [
    ("CS2 (old checks)", "cs2_pm_psc-arch_d10"),
    ("CS4 online, PSC arch", "cs4_online_psc-arch_d10"),
    ("CS3 (old checks)", "cs3_pm_node-arch_d10_a5.0"),
    ("CS4 online, per-node arch", "cs4_online_node-arch_d10_a5.0"),
    *((f"CS5 held-out, {arch}, {arm}", f"cs5_eval_{arch}_{arm}")
      for arch in ("psc", "node") for arm in ("v0", "evolved", "v0-r2")),
]


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def fmt(x, nd=3) -> str:
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.{nd}g}" if abs(x) < 1e-2 or abs(x) >= 1e3 else f"{x:.{nd}f}"
    return str(x)


def table(rows: list[list], head: list[str]) -> str:
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(fmt(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def run_rows(label: str, d: Path) -> list[list]:
    designs = jl(d / "designs.jsonl")
    cert = json.loads((d / "certification_ablation" / "summary.json").read_text())["table"] \
        if (d / "certification_ablation" / "summary.json").exists() else []
    cert_by = {r["task"]: r for r in cert}
    rows = []
    for task in sorted({x["task"] for x in designs}, key=lambda t: [x["task"] for x in designs].index(t)):
        ds = [x for x in designs if x["task"] == task]
        acc = [x for x in ds if x["accepted"]]
        qual = [x for x in acc if x.get("noise_free_pass", True)]
        repairs = Counter(x["stages"][-2] for x in acc if len(x.get("stages") or []) > 1)
        c = cert_by.get(task, {})
        rows.append([
            label, task, len(ds), len(acc) / len(ds), len(qual) / len(ds),
            statistics.median(x["relative_error"] for x in acc) if acc else None,
            statistics.mean(x["relative_error"] for x in acc) if acc else None,
            statistics.mean(x["gt_dsl_relative_error"] for x in acc) if acc else None,
            statistics.mean(x["llm_calls"] for x in ds),
            ", ".join(f"{k}:{v}" for k, v in sorted(repairs.items())) or "-",
            c.get("uncertified_violations"), c.get("certificate_unsound"),
        ])
    return rows


def evo_section(tag: str) -> list[str]:
    d = EVO / tag
    lineage = jl(d / "lineage.jsonl")
    if not lineage:
        return [f"### {tag}: not run", ""]
    rows, refuted = [], 0
    for r in lineage:
        if "evaluation" in r:
            e = r["evaluation"]
            refuted += e["stages"].get("refuted", 0)
            patch = (r.get("reflection") or {}).get("patch")
            rows.append([r["generation"], r["kind"], r["name"], e["score"], r["mean_score"], e["qualified_rate"],
                         e["accept_rate"], e["mean_calls"],
                         (json.dumps(patch, ensure_ascii=False)[:120] if patch else "-").replace("|", "/")])
    best = json.loads((d / "best_prompt.json").read_text()) if (d / "best_prompt.json").exists() else {}
    out = [f"### {tag}", "", f"Best prompt: {best.get('name')} ({best.get('digest')}); falsifier refutations during "
           f"evolution: {refuted} (must be 0).", "",
           table(rows, ["gen", "kind", "name", "score", "mean score", "qualified", "accepted", "calls/design", "patch"]),
           "", "Best prompt modules:", "", "```json",
           json.dumps({k: best.get(k) for k in ("rules", "examples", "repair_hints")}, indent=2, ensure_ascii=False),
           "```", ""]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "results" / "reports" / "cs45_summary.md"))
    a = ap.parse_args()
    rows = []
    for label, tag in RUNS:
        if (DSL / tag / "designs.jsonl").exists():
            rows += run_rows(label, DSL / tag)
    md = ["# CS4 + CS5 summary (PM, ε = 2, Qwen3-8B thinking curator)", "",
          "qualified = accepted and noise-free bias within the gate (old-check runs: recorded only where available); "
          "RE over 100 paired code runs per accepted design; repairs = rejection stage of the draft before the accepted "
          "one; uncertified = drafts that would violate ε without certification; unsound = certificates refuted "
          "(must be 0).", "",
          "## Design runs", "",
          table(rows, ["run", "task", "designs", "accept", "qualified", "median RE", "mean RE", "reference RE",
                       "calls/design", "repairs", "uncertified", "unsound"]), "",
          "## Prompt evolution", ""]
    md += evo_section("cs5_evolve_psc") + evo_section("cs5_evolve_node")
    replay = DSL / "cs4_step1a_replay" / "table.md"
    md += ["## Offline replay", "", f"See {replay.relative_to(ROOT)}" if replay.exists() else "not run", ""]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
