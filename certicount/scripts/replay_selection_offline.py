"""CS7 offline: the per-node design runs of CS4/CS5 replayed through the CS7 design checks (no model call).

CS7 changes the design side of the per-node architecture in three ways:

    own_row    a draft that reads this node's own release entries (N(self), A(self, .)) is rejected
               (certicount.dsl.designer.OWN_ROW_FEEDBACK); they are noisy copies of P;
    no gate    the noise-free gate is off (the simulated choice replaces it);
    choice     candidates from independent design loops are compared by simulating the whole release
               on public graphs (certicount.dsl.selection), with a run-time choice between candidates
               of the same budget split from the run's published noisy degrees.

The recorded drafts were written against the old feedback, so the replay is an approximation: a
design is accepted at its first recorded draft that passes the new checks, and fails if none does
(later drafts would have been written after the new feedback). Pairs of recorded designs of one
run stand in for the two design rounds of ``design_candidates`` (the recorded rounds were not
restricted to one release).

For every task the table gives, on the run's dataset with the run's ε and α (``--runs`` paired
code runs per program):

    recorded      the program the run accepted (old checks, gate on);
    single        one loop under the new checks;
    pair+choice   two loops under the new checks and the simulated choice;
    reference     GT-DSL-node.

and the agreement of the design-time simulated score with the real error over the distinct
programs (``rank_agreement``: share of program pairs ordered the same way).

    ../.venv/bin/python scripts/replay_selection_offline.py results/dsl_eval/cs5_eval_node_v0 \\
        results/dsl_eval/cs5_eval_node_evolved results/dsl_eval/cs5_eval_node_v0-r2 --tag cs7_offline_replay
"""

from __future__ import annotations

import argparse
import itertools
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from psc.experiments import run_rng  # noqa: E402
from psc.graph import load_dataset  # noqa: E402
from psc.ground_truth import relative_error  # noqa: E402
from certicount import DATA_DIR  # noqa: E402
from certicount.artifacts import markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.dsl.designer import (OWN_ROW_FEEDBACK, check_draft, design_reference_params,  # noqa: E402
                                     reads_own_row)
from certicount.dsl.ground_truth import dp_execute, gt_dsl  # noqa: E402
from certicount.dsl.lang import DSLError, Program, parse_program_text  # noqa: E402
from certicount.dsl.quality import task_record  # noqa: E402
from certicount.dsl.selection import SimOptions, execute_selected, select_program  # noqa: E402


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.mean(xs) if xs else None


def run_settings(d: Path) -> dict:
    m = json.loads((d / "manifest.json").read_text())
    a = m.get("settings", m)
    return {"eps": a.get("eps", 2.0), "alpha": a.get("clip_alpha", 0.0), "node_bounds": a.get("node_bounds", False),
            "seed": a.get("seed", 0)}


def new_outcome(drafts: list[dict], task: str, n: int, own_row: bool) -> tuple[Program | None, str]:
    """First recorded draft that passes the CS7 checks (no gate), and why the others failed."""
    params = design_reference_params(n)
    why = []
    for dr in drafts:
        try:
            prog = parse_program_text(dr["program"]) if dr.get("program") else None
        except DSLError:
            prog = None
        if prog is None:
            why.append(dr["stage"])
            continue
        if own_row and reads_own_row(prog):
            why.append("own_row")
            continue
        fb = check_draft(prog, task, params, public_n=n)
        if fb is None:
            return prog, ",".join(why + ["accepted"])
        why.append(fb.split(":")[0][:30])
    return None, ",".join(why)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="per-node design runs (results/dsl_eval/<tag>)")
    ap.add_argument("--tasks", default="3-star,5-star,triangle,degree-moment2")
    ap.add_argument("--runs-per-program", type=int, default=50)
    ap.add_argument("--data", default=str(DATA_DIR))
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()
    tasks = args.tasks.split(",")
    out = out_dir("dsl_eval", args.tag, "cs7_offline_replay")

    # (run, dataset, task, design) -> drafts in order; recorded accepted program
    groups: dict[tuple, list[dict]] = defaultdict(list)
    recorded: dict[tuple, str | None] = {}
    settings = {}
    for r in args.runs:
        d = Path(r)
        settings[d.name] = run_settings(d)
        if not settings[d.name]["node_bounds"]:
            sys.exit(f"{d}: not a per-node run")
        for dr in jl(d / "certification_ablation" / "drafts.jsonl"):
            if dr["task"] in tasks:
                groups[(d.name, dr["dataset"], dr["task"], dr["design"])].append(dr)
        for row in jl(d / "designs.jsonl"):
            if row["task"] in tasks:
                recorded[(d.name, row["dataset"], row["task"], row["design"])] = row["program"] if row["accepted"] else None

    real_cache: dict[tuple, float] = {}
    graphs = {}

    def real_re(prog: Program, ds: str, task: str, st: dict) -> float:
        key = (prog.digest, ds, task, st["eps"], st["alpha"])
        if key not in real_cache:
            rec, g = graphs[(ds, task)]
            real_cache[key] = float(np.mean([relative_error(
                dp_execute(g, prog, st["eps"], run_rng(st["seed"], i), task, node_bounds=True, alpha=st["alpha"]).estimate,
                rec.answer, rec.vertex_num) for i in range(args.runs_per_program)]))
        return real_cache[key]

    pair_cache: dict[tuple, tuple[float, str]] = {}

    def pair_re(progs: list[Program], ds: str, task: str, st: dict) -> tuple[float | None, str]:
        key = (tuple(sorted(p.digest for p in progs)), ds, task, st["eps"], st["alpha"])
        if key not in pair_cache:
            rec, g = graphs[(ds, task)]
            sim = SimOptions(rec.vertex_num, st["eps"], True, st["alpha"])
            sel = select_program(progs, task, sim)
            if sel.chosen is None:
                pair_cache[key] = (None, "none usable")
            else:
                res, picks = [], []
                for i in range(args.runs_per_program):
                    tr, idx, _ = execute_selected(g, progs, sel, task, sim, run_rng(st["seed"], i))
                    res.append(relative_error(tr.estimate, rec.answer, rec.vertex_num))
                    picks.append("A" if progs[idx].uses_matrix else "N" if progs[idx].uses_rows else "P")
                pair_cache[key] = (float(np.mean(res)), "".join(sorted(set(picks))))
        return pair_cache[key]

    rows_design, table, ranks = [], [], []
    for task in tasks:
        keys = sorted(k for k in groups if k[2] == task)
        if not keys:
            continue
        per = defaultdict(list)
        single_progs: dict[tuple, Program | None] = {}
        for key in keys:
            run, ds, _, design = key
            st = settings[run]
            if (ds, task) not in graphs:
                rec = task_record(load_dataset(args.data, ds), ds, task)
                graphs[(ds, task)] = (rec, rec.graph())
            rec, _ = graphs[(ds, task)]
            drafts = sorted(groups[key], key=lambda d: d["iteration"])
            prog, why = new_outcome(drafts, task, rec.vertex_num, own_row=True)
            prog_ng, _ = new_outcome(drafts, task, rec.vertex_num, own_row=False)
            single_progs[key] = prog
            old = recorded.get(key)
            old_prog = parse_program_text(old) if old else None
            row = {"run": run, "dataset": ds, "task": task, "design": design,
                   "recorded_accepted": old_prog is not None,
                   "recorded_re": real_re(old_prog, ds, task, st) if old_prog else None,
                   "recorded_own_row": reads_own_row(old_prog) if old_prog else None,
                   "nogate_accepted": prog_ng is not None,
                   "single_accepted": prog is not None, "single_re": real_re(prog, ds, task, st) if prog else None,
                   "stages": why, "program": prog.text().replace("\n", " ; ") if prog else None}
            rows_design.append(row)
            per[(run, ds)].append((design, key))
        pairs = []
        for (run, ds), items in per.items():
            items.sort()
            for (_, a), (_, b) in zip(items[0::2], items[1::2]):
                cands, seen = [], set()
                for k in (a, b):
                    p = single_progs[k]
                    if p is not None and p.digest not in seen:
                        cands.append(p)
                        seen.add(p.digest)
                re_, picks = pair_re(cands, ds, task, settings[run]) if cands else (None, "-")
                first = next((single_progs[k] for k in (a, b) if single_progs[k] is not None), None)
                pairs.append({"accepted": re_ is not None, "re": re_, "picks": picks,
                              "first_re": real_re(first, ds, task, settings[run]) if first else None})
        # reference on the dataset of this task's runs
        ds0 = keys[0][1]
        st0 = settings[keys[0][0]]
        rec, g = graphs[(ds0, task)]
        ref = float(np.mean([relative_error(gt_dsl(g, task, st0["eps"], run_rng(st0["seed"], i), node_bounds=True,
                                                   alpha=st0["alpha"]).estimate, rec.answer, rec.vertex_num)
                             for i in range(args.runs_per_program)]))
        dr = [r for r in rows_design if r["task"] == task]
        table.append({
            "task": task, "designs": len(dr), "pairs": len(pairs), "reference_re": ref,
            "recorded_accept": mean([r["recorded_accepted"] for r in dr]),
            "recorded_re": mean([r["recorded_re"] for r in dr]),
            "recorded_own_row": sum(bool(r["recorded_own_row"]) for r in dr),
            "nogate_accept": mean([r["nogate_accepted"] for r in dr]),
            "single_accept": mean([r["single_accepted"] for r in dr]),
            "single_re": mean([r["single_re"] for r in dr]),
            "pair_accept": mean([p["accepted"] for p in pairs]),
            "pair_first_re": mean([p["first_re"] for p in pairs]),
            "pair_choice_re": mean([p["re"] for p in pairs]),
            "pair_reads": ",".join(sorted({p["picks"] for p in pairs if p["accepted"]})),
        })
        # rank agreement of the design-time score with the real error over distinct accepted programs
        progs = {}
        for key in keys:
            for p in (single_progs[key], parse_program_text(recorded[key]) if recorded.get(key) else None):
                if p is not None:
                    progs[p.digest] = (p, key)
        if len(progs) > 1:
            sim = SimOptions(rec.vertex_num, st0["eps"], True, st0["alpha"])
            pts = [(select_program([p], task, sim).rows[0]["score"], real_re(p, k[1], task, settings[k[0]]),
                    p.text().replace("\n", " ; ")) for p, k in progs.values()]
            agree = [((a[0] - b[0]) * (a[1] - b[1]) > 0) for a, b in itertools.combinations(pts, 2)
                     if abs(a[1] - b[1]) > 0.05 * max(a[1], b[1])]
            ranks.append({"task": task, "programs": len(pts), "pairs_compared": len(agree),
                          "rank_agreement": mean(agree) if agree else None})
            for s_, r_, txt in sorted(pts):
                ranks.append({"task": task, "programs": "", "sim_score": s_, "real_re": r_, "program": txt})
        print(json.dumps(table[-1]), flush=True)

    write_json({"runs": args.runs, "table": table, "ranks": ranks}, out / "summary.json")
    with (out / "designs.jsonl").open("w", encoding="utf-8") as f:
        for r in rows_design:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    md = ["# CS7 offline replay: own-row check, no gate, simulated choice (per-node architecture)", "",
          f"Runs: {', '.join(Path(r).name for r in args.runs)}; {args.runs_per_program} paired code runs per program "
          "(seed [run seed, i]). The replay accepts a design at its first recorded draft that passes the new checks; "
          "pairs of recorded designs of one run stand in for the two design rounds.", "",
          "`recorded_*`: the run's own outcome (old checks, gate on); `nogate_accept`: new checks without the own-row "
          "check; `single_*`: one loop with the own-row check, no gate; `pair_*`: two loops, `first_re` keeps the "
          "first accepted program, `choice_re` the simulated choice; `pair_reads`: what the chosen programs read "
          "(P only, N rows, A matrix; several letters: run-time choice).", "",
          markdown_table(table, ["task", "designs", "pairs", "reference_re", "recorded_accept", "recorded_re",
                                 "recorded_own_row", "nogate_accept", "single_accept", "single_re", "pair_accept",
                                 "pair_first_re", "pair_choice_re", "pair_reads"]), "",
          "## Design-time simulated score against the real error", "",
          markdown_table(ranks, ["task", "programs", "rank_agreement", "sim_score", "real_re", "program"]), "",
          f"Own-row rejection text: {OWN_ROW_FEEDBACK}", ""]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")
    write_manifest(out, vars(args))
    print("\n".join(md))
    print(f"results in {out}")


if __name__ == "__main__":
    main()
