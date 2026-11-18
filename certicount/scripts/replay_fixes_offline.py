"""CS6b: offline replay of recorded design runs through the current code (no model call).

Two questions, answered on the drafts and the accepted programs that the runs recorded:

    format   how many parse failures of the run the format-only repairs (``normalize_source``)
             rescue, and the category of every parse failure left (problem 2; categories of
             :func:`summarize_cs6.parse_category`)
    gs       the GS of every accepted program under the current deriver against the GS the run
             recorded (``gs_ratio`` of ``designs.jsonl``, old deriver), and the mean relative error of
             the program re-executed with the current GS on the run's graph, seeds and ε against the
             error the run recorded (problem 1; same seeds, so the comparison is paired)

The privacy side of the tighter deriver is checked separately by ``run_dsl_fuzz.py`` (stage cs6b).

    ../.venv/bin/python scripts/replay_fixes_offline.py results/dsl_eval/cs2_pm_psc-arch_d10 \\
        results/dsl_eval/cs5_eval_psc_v0 --tag cs6b_offline_replay

Outputs in ``results/dsl_eval/<tag>/``: ``drafts.jsonl``, ``programs.jsonl``, ``summary.json``, ``table.md``.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import certicount  # noqa: E402,F401
from psc.experiments import run_rng  # noqa: E402
from psc.graph import load_dataset  # noqa: E402
from psc.ground_truth import relative_error  # noqa: E402
from psc.mechanism import DEFAULT_MECHANISM  # noqa: E402
from certicount import DATA_DIR  # noqa: E402
from certicount.artifacts import markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.dsl.designer import design_reference_params, read_draft  # noqa: E402
from certicount.dsl.ground_truth import dp_execute, gs_ratio, reference_program  # noqa: E402
from certicount.dsl.lang import parse_program_text  # noqa: E402
from certicount.dsl.matrix import REFERENCE_EPS1  # noqa: E402
from certicount.dsl.quality import task_record  # noqa: E402
from certicount.dsl.sensitivity import PublicParams, derive  # noqa: E402
from summarize_cs6 import jl, parse_category  # noqa: E402

LOOSE = 1.05  # a program is loose if its GS exceeds the reference GS by more than 5 %


def mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.mean(xs) if xs else None


def replay_format(d: Path) -> list[dict]:
    rows = []
    for c in jl(d / "transcripts.jsonl"):
        p0, e0 = read_draft(c["reply"])
        if p0 is not None or e0.get("truncated"):
            continue
        p1, e1 = read_draft(c["reply"], normalize=True)
        rows.append({"source": d.name, "task": c.get("task"), "design": c.get("design"),
                     "rescued": p1 is not None, "notes": e1.get("normalized"),
                     "category": None if p1 is not None else parse_category(e1),
                     "feedback": e1.get("feedback"), "program": e1.get("program")})
    return rows


def replay_gs(d: Path, runs: int | None) -> list[dict]:
    settings = json.loads((d / "manifest.json").read_text())["settings"]
    node_bounds = bool(settings.get("node_bounds"))
    eps, seed = float(settings.get("eps", 2.0)), int(settings.get("seed", 0))
    mech, alpha = settings.get("mechanism", DEFAULT_MECHANISM), float(settings.get("clip_alpha", 0.0))
    runs = runs or int(settings.get("runs", 100))
    rows, cache, recs = [], {}, {}
    for r in jl(d / "designs.jsonl"):
        if not r.get("accepted") or not r.get("program"):
            continue
        ds, task = r["dataset"], r["task"]
        recs.setdefault(ds, load_dataset(str(DATA_DIR), ds))
        rec = task_record(recs[ds], ds, task)
        key = (ds, task, r["program"])
        if key not in cache:
            prog = parse_program_text(r["program"])
            b = int(design_reference_params(rec.vertex_num).D)
            p = PublicParams(rec.vertex_num, D=b, dmax=b, eps1=REFERENCE_EPS1)
            ratio = gs_ratio(derive(prog, p).gs, derive(reference_program(task, node_bounds), p).gs)
            g = rec.graph()
            re_new = mean(relative_error(dp_execute(g, prog, eps, run_rng(seed, i), task, mech, node_bounds=node_bounds,
                                                    alpha=alpha).estimate, rec.answer, rec.vertex_num)
                          for i in range(runs))
            cache[key] = (ratio, re_new)
        ratio, re_new = cache[key]
        rows.append({"source": d.name, "dataset": ds, "task": task, "design": r["design"], "program": r["program"],
                     "gs_ratio_old": r.get("gs_ratio"), "gs_ratio_new": ratio,
                     "re_old": r.get("relative_error"), "re_new": re_new,
                     "re_reference": r.get("gt_dsl_relative_error")})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--runs", type=int, default=None, help="code runs per accepted program (default: the run's --runs)")
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()

    drafts, progs = [], []
    for d in map(Path, a.dirs):
        drafts += replay_format(d)
        progs += replay_gs(d, a.runs)

    fmt_rows = []
    for src in dict.fromkeys(r["source"] for r in drafts):
        rs = [r for r in drafts if r["source"] == src]
        fmt_rows.append({"source": src, "parse_failures": len(rs), "rescued": sum(r["rescued"] for r in rs),
                         "left": sum(not r["rescued"] for r in rs)})
    cats = Counter(r["category"] for r in drafts if not r["rescued"])
    examples = {}
    for r in drafts:
        if not r["rescued"] and r["category"] not in examples:
            examples[r["category"]] = r["program"]
    cat_rows = [{"category": c, "drafts": k, "example": (examples.get(c) or "").replace("\n", " ; ")[:140]}
                for c, k in cats.most_common()]

    by = defaultdict(list)
    for r in progs:
        by[(r["source"], r["task"])].append(r)
    gs_rows = []
    for (src, task), rs in by.items():
        gs_rows.append({
            "source": src, "task": task, "accepted": len(rs),
            "gs_ratio_old": mean(r["gs_ratio_old"] for r in rs), "gs_ratio_new": mean(r["gs_ratio_new"] for r in rs),
            "loose_old": sum((r["gs_ratio_old"] or 0) > LOOSE for r in rs),
            "loose_new": sum((r["gs_ratio_new"] or 0) > LOOSE for r in rs),
            "re_old": mean(r["re_old"] for r in rs), "re_new": mean(r["re_new"] for r in rs),
            "re_reference": mean(r["re_reference"] for r in rs),
        })

    out = out_dir("dsl_eval", a.tag, "offline_replay")
    for name, rows in (("drafts.jsonl", drafts), ("programs.jsonl", progs)):
        with (out / name).open("w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    total_fail, total_resc = sum(r["parse_failures"] for r in fmt_rows), sum(r["rescued"] for r in fmt_rows)
    write_json({"dirs": a.dirs, "format": fmt_rows, "categories": cat_rows, "gs": gs_rows,
                "parse_failures": total_fail, "rescued": total_resc}, out / "summary.json")
    md = ["# CS6b: offline replay of the recorded runs (no model call)", "",
          f"## Problem 2: format-only repairs ({total_resc} of {total_fail} parse failures rescued)", "",
          markdown_table(fmt_rows, ["source", "parse_failures", "rescued", "left"]), "",
          "Parse failures left, by category (example: the first draft of the category):", "",
          markdown_table(cat_rows, ["category", "drafts", "example"]), "",
          f"## Problem 1: GS of the accepted programs, recorded (old deriver) vs current deriver", "",
          f"`loose`: GS > {LOOSE} x reference GS at the design-time bound. `re_*`: mean relative error over the run's "
          "seeds (paired); `re_reference`: the reference program (GT-DSL) of the run.", "",
          markdown_table(gs_rows, ["source", "task", "accepted", "gs_ratio_old", "gs_ratio_new", "loose_old",
                                   "loose_new", "re_old", "re_new", "re_reference"]), ""]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")
    write_manifest(out, vars(a))
    print("\n".join(md))
    print(f"results in {out}")


if __name__ == "__main__":
    main()
