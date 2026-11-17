"""Step 1a: replay recorded curator drafts through the old and the new design checks (no model call).

For every draft of the given design-evaluation directories (``run_dsl_design_eval.py``
output: ``designs.jsonl`` + ``transcripts.jsonl``) the reply is classified twice:

    old  the stage recorded by ``analyze_design_certification.py`` (certification_ablation/drafts.jsonl),
         i.e. the checks of the run
    new  the current reader (reasoning block skipped, truncation detected, several ``for``
         clauses read as nested sums) and checks with the noise-aware gate
         (:mod:`certicount.dsl.noisy_gate`), at the run's ε, architecture and α

and every accepted program is executed on the evaluation graph (``--runs`` paired code
runs, same seeds as the run) to show what the gate removed. The reference program of
every task and architecture is replayed too: the gate must never reject it.

What a replay cannot show: whether better feedback (hints, gate symptoms) makes the
*next* draft right -- that needs new model calls (step 2).

    ../.venv/bin/python scripts/replay_design_drafts.py results/dsl_eval/cs2_pm_psc-arch_d10 \\
        results/dsl_eval/cs3_pm_node-arch_d10_a5.0 --tag step1a_replay

Outputs in ``results/dsl_eval/<tag>/``: ``drafts.jsonl`` (one line per draft: old/new stage,
program, gate statistic, PM error), ``references.jsonl``, ``summary.json``, ``table.md``.
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

import certicount  # noqa: E402,F401
from psc.experiments import run_rng  # noqa: E402
from psc.graph import load_dataset  # noqa: E402
from psc.ground_truth import relative_error  # noqa: E402
from psc.mechanism import DEFAULT_MECHANISM  # noqa: E402
from certicount import DATA_DIR  # noqa: E402
from certicount.artifacts import markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.dsl.designer import check_draft, design_reference_params, draft_stage, read_draft  # noqa: E402
from certicount.dsl.ground_truth import dp_execute, reference_program  # noqa: E402
from certicount.dsl.noisy_gate import NoisyGate, noise_free_check  # noqa: E402
from certicount.dsl.quality import task_record  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from analyze_design_certification import calls_by_design, load_jsonl  # noqa: E402

STAGES = ("truncated", "parse", "duplicate", "gs_failed", "gs_loose", "semantic", "noisy", "refuted", "accepted")


def settings_of(d: Path) -> dict:
    return json.loads((d / "manifest.json").read_text()).get("settings", {})


def gate_for(settings: dict, n: int, tau: float, reps: int) -> NoisyGate:
    return NoisyGate(n, float(settings.get("eps", 2.0)), bool(settings.get("node_bounds")),
                     float(settings.get("clip_alpha", 0.0)), settings.get("mechanism", DEFAULT_MECHANISM),
                     tau=tau, reps=reps)


def pm_error(program, rec, settings: dict, runs: int) -> float:
    g, n, truth = rec.graph(), rec.vertex_num, rec.answer
    res = [relative_error(dp_execute(g, program, float(settings.get("eps", 2.0)), run_rng(int(settings.get("seed", 0)), i),
                                     rec.task, settings.get("mechanism", DEFAULT_MECHANISM),
                                     node_bounds=bool(settings.get("node_bounds")),
                                     alpha=float(settings.get("clip_alpha", 0.0))).estimate, truth, n)
           for i in range(runs)]
    return float(statistics.mean(res))


def replay_dir(d: Path, tau: float, reps: int, runs: int) -> tuple[list[dict], list[dict]]:
    settings = settings_of(d)
    designs, calls = load_jsonl(d / "designs.jsonl"), load_jsonl(d / "transcripts.jsonl")
    old = load_jsonl(d / "certification_ablation" / "drafts.jsonl")
    old_by = {(r["dataset"], r["task"], r["design"], r["iteration"]): r["stage"] for r in old}
    rows, gates, recs = [], {}, {}
    for r, design_calls in zip(designs, calls_by_design(designs, calls)):
        ds, task = r["dataset"], r["task"]
        if ds not in recs:
            recs[ds] = load_dataset(str(DATA_DIR), ds)
        rec = task_record(recs[ds], ds, task)
        n = rec.vertex_num
        gate = gates.setdefault((ds, n), gate_for(settings, n, tau, reps))
        params = design_reference_params(n)
        seen: set[str] = set()
        for it, call in enumerate(design_calls, 1):
            program, entry = read_draft(call["reply"])
            row = {"source": d.name, "dataset": ds, "task": task, "design": r["design"], "iteration": it,
                   "node_bounds": gate.node_bounds, "old_stage": old_by.get((ds, task, r["design"], it))}
            if program is None:
                row.update(new_stage=draft_stage(entry["feedback"]), program=entry.get("program"),
                           feedback=entry["feedback"])
            elif program.digest in seen:
                row.update(new_stage="duplicate", program=program.text())
            else:
                seen.add(program.digest)
                fb = check_draft(program, task, params, public_n=n, noisy=gate)
                nrep = noise_free_check(program, task, gate)
                row.update(new_stage=draft_stage(fb), program=program.text(), feedback=fb,
                           noise_free_bias=max((x["bias"] for x in nrep.rows), default=None))
            accepted_somewhere = "accepted" in (row["old_stage"], row["new_stage"])
            if accepted_somewhere and program is not None:
                row["pm_relative_error"] = pm_error(program, rec, settings, runs)
            rows.append(row)
    refs = []
    for (ds, n), gate in gates.items():
        for task in sorted({r["task"] for r in designs if r["dataset"] == ds}):
            prog = reference_program(task, gate.node_bounds)
            fb = check_draft(prog, task, design_reference_params(n), public_n=n, noisy=gate)
            nrep = noise_free_check(prog, task, gate)
            refs.append({"source": d.name, "dataset": ds, "task": task, "node_bounds": gate.node_bounds,
                         "program": prog.text(), "new_stage": draft_stage(fb), "feedback": fb,
                         "noise_free_bias": max(x["bias"] for x in nrep.rows), "rows": nrep.rows})
    return rows, refs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--tau", type=float, default=2.0)
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--runs", type=int, default=20, help="paired code runs on the evaluation graph per accepted draft")
    ap.add_argument("--catastrophe", type=float, default=10.0,
                    help="an accepted draft is catastrophic if its evaluation RE exceeds this many times the reference's")
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()

    rows, refs = [], []
    for d in map(Path, a.dirs):
        r, f = replay_dir(d, a.tau, a.reps, a.runs)
        rows += r
        refs += f
    ref_re = {}
    for f in refs:
        prog_rec = task_record(load_dataset(str(DATA_DIR), f["dataset"]), f["dataset"], f["task"])
        settings = settings_of(next(Path(x) for x in a.dirs if Path(x).name == f["source"]))
        f["pm_relative_error"] = pm_error(reference_program(f["task"], f["node_bounds"]), prog_rec, settings, a.runs)
        ref_re[(f["source"], f["task"])] = f["pm_relative_error"]
    for r in rows:
        if "pm_relative_error" in r:
            r["catastrophic"] = r["pm_relative_error"] > a.catastrophe * max(ref_re[(r["source"], r["task"])], 1e-9)

    out = out_dir("dsl_eval", a.tag, "replay")
    with (out / "drafts.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (out / "references.jsonl").open("w", encoding="utf-8") as fh:
        for r in refs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    table = []
    by = defaultdict(list)
    for r in rows:
        by[(r["source"], r["task"])].append(r)
    for (src, task), rs in sorted(by.items()):
        old_acc = [r for r in rs if r["old_stage"] == "accepted"]
        new_acc = [r for r in rs if r["new_stage"] == "accepted"]
        table.append({
            "source": src, "task": task, "drafts": len(rs),
            "old_accepted": len(old_acc), "old_catastrophic": sum(bool(r.get("catastrophic")) for r in old_acc),
            "new_accepted": len(new_acc), "new_catastrophic": sum(bool(r.get("catastrophic")) for r in new_acc),
            "rejected_by_gate": sum(r["new_stage"] == "noisy" for r in rs),
            "gate_rejected_catastrophic": sum(r["new_stage"] == "noisy" and bool(r.get("catastrophic")) for r in rs),
            "rescued_parse": sum(r["old_stage"] == "parse" and r["new_stage"] not in ("parse", "truncated") for r in rs),
            "truncated": sum(r["new_stage"] == "truncated" for r in rs),
            "old_median_re": statistics.median([r["pm_relative_error"] for r in old_acc]) if old_acc else None,
            "new_median_re": statistics.median([r["pm_relative_error"] for r in new_acc]) if new_acc else None,
            "old_mean_re": statistics.mean([r["pm_relative_error"] for r in old_acc]) if old_acc else None,
            "new_mean_re": statistics.mean([r["pm_relative_error"] for r in new_acc]) if new_acc else None,
            "reference_re": ref_re[(src, task)],
        })
    transitions = Counter((r["old_stage"], r["new_stage"]) for r in rows)
    ref_ok = all(f["new_stage"] == "accepted" for f in refs)
    summary = {"dirs": a.dirs, "tau": a.tau, "reps": a.reps, "runs": a.runs, "references_accepted": ref_ok,
               "table": table, "transitions": {f"{o} -> {n}": c for (o, n), c in sorted(transitions.items(), key=str)},
               "references": [{k: f[k] for k in ("source", "task", "new_stage", "noise_free_bias", "pm_relative_error")}
                              for f in refs]}
    write_json(summary, out / "summary.json")
    cols = ["source", "task", "drafts", "old_accepted", "old_catastrophic", "new_accepted", "new_catastrophic",
            "rejected_by_gate", "gate_rejected_catastrophic", "rescued_parse", "truncated",
            "old_median_re", "new_median_re", "old_mean_re", "new_mean_re", "reference_re"]
    tr_rows = [{"old_stage": o, "new_stage": n, "drafts": c} for (o, n), c in sorted(transitions.items(), key=str)]
    ref_rows = [{k: f[k] for k in ("source", "task", "new_stage", "noise_free_bias", "pm_relative_error", "program")}
                for f in refs]
    md = ["# Step 1a: replay of the recorded drafts (no model call)", "",
          f"Gate: τ = {a.tau}, {a.reps} releases per public Holme-Kim graph; evaluation error: mean RE over {a.runs} "
          f"paired code runs on the run's graph; catastrophic = RE > {a.catastrophe:g} x the reference program's.", "",
          "## Per task", "", markdown_table(table, cols), "",
          "## Stage transitions (old -> new)", "", markdown_table(tr_rows, ["old_stage", "new_stage", "drafts"]), "",
          f"## Reference programs (must be accepted: {'yes' if ref_ok else 'NO'})", "",
          markdown_table([{**r, "program": r["program"].replace(chr(10), " ; ")} for r in ref_rows],
                         ["source", "task", "new_stage", "noise_free_bias", "pm_relative_error", "program"]), ""]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")
    write_manifest(out, vars(a))
    print("\n".join(md))
    print(f"results in {out}")


if __name__ == "__main__":
    main()
