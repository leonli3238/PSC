"""One-page summary of the CS6 runs of ``scripts/run_cscwd.sh`` (reads result directories only).

    CS6a  prompt-core comparison on the held-out tasks: A = v1, B = v1-repeat3 (the prohibition
          paragraph stated three times), C = v1-alt (rewrites of the Python constructs, closing
          checklist, rewrite hints); one loop per design, format repairs on, no selection
    CS6b  offline: replay of the recorded runs (``replay_fixes_offline.py``) and deriver fuzzing
    CS6c  the four fixes online: legacy (CS5 prompt, no format repairs; current deriver), v1,
          more restarts without / with selection (min_gs + tighten + early stop), the evolution with
          the new rules (``cs6c_evolve_psc``) and its prompt with and without selection

    ../.venv/bin/python scripts/summarize_cs6.py --out results/reports/cs6_summary.md

Per run and task: accept and qualified rates (Wilson 95 % interval of the accept rate), drafts,
parse failures per draft and per first draft of a loop, model calls per design, GS ratio to the
reference (``loose``: > 1.05), noise ratio, mean / median relative error of the accepted designs and
of the reference program (100 paired code runs). Parse failures are re-read from the transcripts
with the run's prompt core and format setting and sorted by :func:`parse_category`.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DSL = ROOT / "results" / "dsl_eval"
EVO = ROOT / "results" / "evolve"
LOOSE = 1.05

CS6A = [("A v1", "cs6a_psc_v1"), ("B v1-repeat3", "cs6a_psc_v1-repeat3"), ("C v1-alt", "cs6a_psc_v1-alt")]
CS6C = [("CS5 v0 (recorded, old deriver)", "cs5_eval_psc_v0"),
        ("CS5 v0-r2 (recorded, old deriver)", "cs5_eval_psc_v0-r2"),
        ("CS5 evolved (recorded, old deriver)", "cs5_eval_psc_evolved"),
        ("legacy", "cs6c_psc_legacy"), ("v1 (= CS6a A)", "cs6a_psc_v1"),
        ("v1, 4 restarts, first", "cs6c_psc_v1-r4-first"), ("v1, 4 restarts, min_gs", "cs6c_psc_v1-r4-mings"),
        ("evolved", "cs6c_psc_evolved"), ("evolved, 4 restarts, min_gs", "cs6c_psc_evolved-r4-mings")]


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def parse_category(entry: dict) -> str:
    """Category of a parse failure from its history entry (feedback, program, aggregate)."""
    f = entry.get("feedback") or ""
    prog = entry.get("program") or ""
    agg = entry.get("aggregate") or ""
    if "no code block" in f:
        return "no_code_block"
    if re.search(r"^\s*</?[A-Za-z][A-Za-z _-]*>\s*$", prog, re.M):
        return "tag_line"
    if "without conditions" in f:
        return "condition_in_sum"
    if re.search(r"expects \(num|expects \(set, num\), got \(num|not defined for set", f):
        return "set_as_number" if "project expects" not in f else "project_args"
    if "project expects" in f:
        return "project_args"
    if "unknown name" in f:
        return "unknown_node_name"
    if "unsupported syntax BinOp" in f:
        if "//" in agg:
            return "floor_div_in_aggregate"
        if "**" in prog:
            return "power_operator"
        if "//" in prog or "%" in prog:
            return "floor_div_or_mod"
        return "binop_other"
    if re.search(r"only 'name = <expr>' lines|must end with 'return", f):
        return "procedural_loop" if re.search(r"^\s*for |\+=|^\s*if ", prog, re.M) else "missing_return"
    if "already defined" in f:
        return "name_reassigned"
    if re.search(r"unsupported syntax (Set|List|Tuple|Dict|Subscript)", f):
        return "literal_or_index"
    if "second argument of comb" in f:
        return "comb_nonconstant_k"
    if "unknown function" in f:
        return "unknown_function"
    return "other"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p, den = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / den, z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / den
    return max(0.0, c - h), min(1.0, c + h)


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


def mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.mean(xs) if xs else None


def run_setting(d: Path) -> tuple[str, bool]:
    """Prompt core and format-repair setting of a run (runs before cores: legacy, no repairs)."""
    s = json.loads((d / "manifest.json").read_text())["settings"]
    core = (s.get("prompt_spec") or {}).get("core", "legacy")
    return core, bool((s.get("design_options") or {}).get("normalize", False))


def draft_rows(d: Path) -> list[dict]:
    sys.path.insert(0, str(ROOT))
    import certicount  # noqa: F401
    from certicount.dsl.designer import read_draft
    core, norm = run_setting(d)
    out = []
    for c in jl(d / "transcripts.jsonl"):
        if c.get("agent") not in (None, "Curator"):
            continue
        p, e = read_draft(c["reply"], normalize=norm, core=core)
        out.append({"task": c.get("task"), "fresh": "previous attempts" not in c["user"],
                    "truncated": bool(e.get("truncated")),
                    "category": None if p is not None or e.get("truncated") else parse_category(e)})
    return out


def run_rows(label: str, d: Path) -> tuple[list[list], Counter]:
    designs, drafts = jl(d / "designs.jsonl"), draft_rows(d)
    rows, cats = [], Counter(r["category"] for r in drafts if r["category"])
    for task in dict.fromkeys(x["task"] for x in designs):
        ds = [x for x in designs if x["task"] == task]
        acc = [x for x in ds if x["accepted"]]
        qual = [x for x in acc if x.get("noise_free_pass", True)]
        dr = [x for x in drafts if x["task"] == task]
        fresh = [x for x in dr if x["fresh"]]
        lo, hi = wilson(len(acc), len(ds))
        ratios = [x.get("gs_ratio") for x in acc if x.get("gs_ratio") is not None]
        rows.append([
            label, task, len(ds), len(acc) / len(ds), f"[{lo:.2f}, {hi:.2f}]", len(qual) / len(ds),
            len(dr), sum(bool(x["category"]) for x in dr) / len(dr) if dr else None,
            sum(bool(x["category"]) for x in fresh) / len(fresh) if fresh else None,
            mean(x["llm_calls"] for x in ds), mean(ratios), sum(r > LOOSE for r in ratios),
            mean(x.get("noise_ratio") for x in acc),
            mean(x["relative_error"] for x in acc),
            statistics.median(x["relative_error"] for x in acc) if acc else None,
            mean(x["gt_dsl_relative_error"] for x in acc),
        ])
    return rows, cats


HEAD = ["run", "task", "designs", "accept", "accept 95% CI", "qualified", "drafts", "parse/draft",
        "parse/fresh draft", "calls/design", "gs_ratio", "loose", "noise_ratio", "mean RE", "median RE", "reference RE"]


def section(title: str, runs: list[tuple[str, str]]) -> list[str]:
    rows, cat_rows = [], []
    for label, tag in runs:
        d = DSL / tag
        if not (d / "designs.jsonl").exists():
            rows.append([label, "not run"] + [None] * (len(HEAD) - 2))
            continue
        r, cats = run_rows(label, d)
        rows += r
        cat_rows.append([label, sum(cats.values()), ", ".join(f"{k}:{v}" for k, v in cats.most_common()) or "-"])
    return [f"## {title}", "", table(rows, HEAD), "", "Parse failures by category:", "",
            table(cat_rows, ["run", "parse failures", "categories"]), ""]


def evo_section(tag: str) -> list[str]:
    d = EVO / tag
    lineage = jl(d / "lineage.jsonl")
    if not lineage:
        return [f"### {tag}: not run", ""]
    rows, gens, refuted = [], [], 0
    for r in lineage:
        if "evaluation" in r:
            e = r["evaluation"]
            refuted += e["stages"].get("refuted", 0)
            ci = e.get("qualified_ci95")
            patch = (r.get("reflection") or {}).get("patch")
            rows.append([r["generation"], r["kind"], r["name"], r["mean_score"], r.get("se"), r.get("evaluations"),
                         e["qualified_rate"], f"[{ci[0]:.2f}, {ci[1]:.2f}]" if ci else "-", e["accept_rate"],
                         e["mean_calls"], (json.dumps(patch, ensure_ascii=False)[:100] if patch else "-").replace("|", "/")])
        elif r.get("kind") == "generation":
            gens.append([r["generation"], r["parent"], r.get("parent_mean"), r.get("parent_se"), r.get("improved"),
                         ", ".join(r.get("front") or [])])
    best = json.loads((d / "best_prompt.json").read_text()) if (d / "best_prompt.json").exists() else {}
    return [f"### {tag}", "", f"Best prompt: {best.get('name')} ({best.get('digest')}, core {best.get('core')}); "
            f"falsifier refutations during the evolution: {refuted} (must be 0).", "",
            table(rows, ["gen", "kind", "name", "mean score", "se", "evals", "qualified", "qualified 95% CI",
                         "accepted", "calls/design", "patch"]), "",
            table(gens, ["gen", "incumbent", "mean", "se", "improved", "Pareto front"]), "",
            "Best prompt modules:", "", "```json",
            json.dumps({k: best.get(k) for k in ("rules", "examples", "repair_hints")}, indent=2, ensure_ascii=False),
            "```", ""]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "results" / "reports" / "cs6_summary.md"))
    a = ap.parse_args()
    md = ["# CS6 summary (PM, ε = 2, Qwen3-8B thinking curator, held-out tasks)", "",
          "parse/draft: drafts that could not be parsed (after the run's format repairs) / all drafts; "
          "parse/fresh draft: the same over the first draft of every loop (no feedback yet). qualified: accepted "
          "and within the noise-free gate. RE: mean relative error over 100 paired code runs per accepted design.", ""]
    md += section("CS6a: prompt cores A / B / C", CS6A)
    md += section("CS6c: the four fixes online", CS6C)
    md += ["## CS6c: prompt evolution", ""] + evo_section("cs6c_evolve_psc")
    off = DSL / "cs6b_offline_replay" / "table.md"
    md += ["## CS6b: offline replay and fuzzing", "",
           f"See {off.relative_to(ROOT)}" if off.exists() else "offline replay not run"]
    for t in ("cs6b_fuzz_shapes", "cs6b_fuzz_mixed"):
        s = ROOT / "results" / "dsl" / t / "summary.json"
        if s.exists():
            j = json.loads(s.read_text())
            md.append(f"- {t}: {json.dumps({k: j[k] for k in j if k in ('programs', 'count', 'refuted', 'failures')})}")
    md.append("")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
