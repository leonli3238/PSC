"""Summary of the CSCWD feedback ablation (scripts/run_cscwd_fb.sh).

Arms: ``full`` (the checker's diagnosis goes back to the curator), ``binary`` (only the verdict
"rejected") and ``none`` (independent resampling of the first prompt). Same checks, same budget
(3 drafts per release, rows and matrix), tighten 0. Reads result directories only; the directories
``fb_<arm>_<task><suffix>`` of every ``--suffixes`` entry are pooled (first batch: CU, ML, EE, all
arms; ``_ext``: PM, Do, CS, arms full and none).

Per (task, arm), over all its datasets:

* ``released``: designs whose chosen program is released (certified and usable in the simulated
  choice), Wilson 95% interval; ``loop_at_b``: share of design loops (one per release) accepted
  within ``b`` drafts; ``design_at_b``: share of designs with a loop accepted within ``b``;
* cost, draft outcomes, released programs (independent semantic test, falsifier, mean RE).

Comparisons between two arms use only the datasets both arms ran:

* released per design: Mantel-Haenszel risk difference over the (task, dataset) strata with a Wald
  95% interval, odds ratio and the continuity-corrected Cochran-Mantel-Haenszel test;
* repair: design loops whose first draft was rejected, accepted at a later draft. The first draft's
  prompt is the same in every arm (only redrafts see feedback), so this isolates the redraft step;
  95% percentile bootstrap over designs, resampled within each (task, dataset);
* calls per released design: ratio, same bootstrap.
``full - none`` is the primary comparison (matched-budget resampling); the others are secondary.

    ../.venv/bin/python scripts/summarize_fb_ablation.py --out results/reports/fb_ablation.md
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from certicount.artifacts import markdown_table, write_json  # noqa: E402
from certicount.dsl.evolve import wilson_interval  # noqa: E402

RES = ROOT / "results"
ARMS = ("full", "binary", "none")
TASKS = ("triangle", "triangle-edge")
BUDGETS = (1, 2, 3)
PAIRS = (("full", "none"), ("full", "binary"), ("binary", "none"))
PRIMARY = ("full", "none")
STAGE_ORDER = ("truncated", "parse", "duplicate", "release", "own_row", "gs_failed", "gs_loose", "semantic", "noisy",
               "refuted", "accepted")
TRANSITION_STAGES = ("parse", "own_row", "gs_loose", "semantic")
Z = 1.959964


def load_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def tag(arm: str, task: str, suffix: str = "") -> str:
    return f"fb_{arm}_{task.replace('-', '_')}{suffix}"


def output_tokens(t: dict) -> int | None:
    u = t.get("usage") or {}
    v = u.get("output_tokens") or u.get("completion_tokens")
    return int(v) if v else None


def loops(d: dict) -> list[tuple[str | None, list[str], int | None]]:
    """(release, stages of its drafts, draft of the first acceptance) of every design loop of a design."""
    stages = d.get("stages") or []
    out, i = [], 0
    for lp in d.get("first_accepted_draft") or []:
        n = int(lp["drafts"])
        out.append((lp.get("release"), stages[i:i + n], lp.get("first_accepted")))
        i += n
    if i != len(stages):
        raise ValueError(f"design {d.get('dataset')}/{d.get('task')}/{d.get('design')}: "
                         f"{len(stages)} stages but {i} drafts in its loops")
    return out


def first_accepts(d: dict) -> list[int | None]:
    return [f for _, _, f in loops(d)]


def load_arm(arm: str, task: str, suffixes: list[str]) -> tuple[list[dict], list[dict], list[dict]]:
    designs, trans, runs = [], [], []
    for s in suffixes:
        d = RES / "dsl_eval" / tag(arm, task, s)
        if not d.exists():
            continue
        rows = load_jsonl(d / "designs.jsonl")
        runs.append({"tag": d.name, "finished": (d / "table.md").exists(), "designs": len(rows),
                     "datasets": ",".join(sorted({r["dataset"] for r in rows})) or "-",
                     "api_errors": len(load_jsonl(d / "errors.jsonl"))})
        designs += rows
        trans += load_jsonl(d / "transcripts.jsonl")
    dup = sorted(k for k, v in Counter((r["dataset"], r["design"]) for r in designs).items() if v > 1)
    if dup:
        raise SystemExit(f"{arm}/{task}: designs {dup[:5]} appear in more than one directory (would count twice)")
    return designs, trans, runs


def arm_row(arm: str, task: str, designs: list[dict], transcripts: list[dict], dataset: str = "all") -> dict:
    n = len(designs)
    rel = [d for d in designs if d.get("accepted")]
    lps = [f for d in designs for f in first_accepts(d)]
    calls = sum(int(d.get("llm_calls") or 0) for d in designs)
    toks = [output_tokens(t) for t in transcripts]
    tok_known = [t for t in toks if t is not None]
    lo, hi = wilson_interval(len(rel), n) if n else (None, None)
    stages = Counter(s for d in designs for s in d.get("stages", []))
    drafts = sum(stages.values())
    return {
        "task": task, "arm": arm, "dataset": dataset, "datasets": ",".join(sorted({d["dataset"] for d in designs})),
        "designs": n, "released": len(rel), "released_rate": len(rel) / n if n else None,
        "released_ci95": f"[{lo:.2f}, {hi:.2f}]" if n else "-",
        "loops": len(lps),
        **{f"loop_at_{b}": (sum(1 for f in lps if f is not None and f <= b) / len(lps)) if lps else None
           for b in BUDGETS},
        **{f"design_at_{b}": (sum(1 for d in designs if any(f is not None and f <= b for f in first_accepts(d))) / n)
           if n else None for b in BUDGETS},
        "calls_per_design": calls / n if n else None,
        "calls_per_released": calls / len(rel) if rel else None,
        "out_tokens_per_design": (sum(tok_known) / n) if n and tok_known else None,
        "out_tokens_per_released": (sum(tok_known) / len(rel)) if rel and tok_known else None,
        "tokens_missing": sum(1 for t in toks if t is None),
        "drafts": drafts,
        "duplicate_share": stages.get("duplicate", 0) / drafts if drafts else None,
        "draft_stages": dict(stages.most_common(8)),
        "semantic_pass": float(np.mean([bool(d.get("semantic_pass")) for d in rel])) if rel else None,
        "sound": float(np.mean([bool(d.get("sound")) for d in rel])) if rel else None,
        "mean_RE": (float(np.mean([d["relative_error"] for d in rel if d.get("relative_error") is not None]))
                    if rel else None),
        "design_error_vs_GT_DSL": (float(np.mean([d["design_error"] for d in rel if d.get("design_error") is not None]))
                                   if rel else None),
        "distinct_programs": len({d.get("program") for d in rel}),
    }


# ---------------------------------------------------------------- statistics
def mantel_haenszel(strata: list[tuple[int, int, int, int]]) -> dict | None:
    """Strata ``(k1, n1, k0, n0)``: MH risk difference (weights n1·n0/N) with a Wald interval, MH odds
    ratio and the continuity-corrected CMH test (two-sided p from chi-square with 1 df)."""
    tabs = [(k1, n1 - k1, k0, n0 - k0) for k1, n1, k0, n0 in strata if n1 and n0]
    if not tabs:
        return None
    a_obs = e = v = or_num = or_den = w_sum = rd_num = rd_var = 0.0
    for a, b, c, d in tabs:
        n1, n0 = a + b, c + d
        big_n, m1, m0 = n1 + n0, a + c, b + d
        a_obs += a
        e += n1 * m1 / big_n
        if big_n > 1:
            v += n1 * n0 * m1 * m0 / (big_n * big_n * (big_n - 1))
        or_num += a * d / big_n
        or_den += b * c / big_n
        w = n1 * n0 / big_n
        p1, p0 = a / n1, c / n0
        w_sum += w
        rd_num += w * (p1 - p0)
        rd_var += w * w * (p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    rd, se = rd_num / w_sum, math.sqrt(rd_var) / w_sum
    chi = max(abs(a_obs - e) - 0.5, 0.0) ** 2 / v if v > 0 else None
    return {"rd": rd, "lo": rd - Z * se, "hi": rd + Z * se, "or": or_num / or_den if or_den > 0 else math.inf,
            "p": math.erfc(math.sqrt(chi / 2)) if chi is not None else None, "strata": len(tabs)}


def _resample(groups: list[np.ndarray], rng: np.random.Generator) -> np.ndarray:
    return sum(g[rng.integers(0, len(g), len(g))].sum(0) for g in groups)


def boot(groups1: list[np.ndarray], groups0: list[np.ndarray], stat, rng: np.random.Generator, reps: int):
    """Observed ``stat(sum1, sum0)`` and its 95% percentile interval, designs resampled within each group."""
    obs = stat(sum(g.sum(0) for g in groups1), sum(g.sum(0) for g in groups0))
    vals = []
    for _ in range(reps):
        v = stat(_resample(groups1, rng), _resample(groups0, rng))
        if v is not None and math.isfinite(v):
            vals.append(v)
    if obs is None or not vals:
        return obs, None, None
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return obs, float(lo), float(hi)


def repair_pair(d: dict) -> tuple[int, int]:
    """(loops accepted after a rejected first draft, loops with a rejected first draft) of a design."""
    k = n = 0
    for _, st, fa in loops(d):
        if st and st[0] != "accepted":
            n += 1
            k += fa is not None
    return k, n


def diff_of_ratios(s1: np.ndarray, s0: np.ndarray) -> float | None:
    return s1[0] / s1[1] - s0[0] / s0[1] if s1[1] and s0[1] else None


def ratio_of_ratios(s1: np.ndarray, s0: np.ndarray) -> float | None:
    return (s1[0] / s1[1]) / (s0[0] / s0[1]) if s1[1] and s0[1] and s0[0] else None


def groups_of(designs_by_stratum: dict, fn) -> list[np.ndarray]:
    return [np.array([fn(d) for d in ds], dtype=float).reshape(-1, 2) for _, ds in sorted(designs_by_stratum.items())
            if ds]


def fmt(v: float | None, lo: float | None = None, hi: float | None = None, signed: bool = True) -> str:
    if v is None:
        return "-"
    s = f"{v:+.3f}" if signed else f"{v:.2f}"
    if lo is None or hi is None:
        return s
    return f"{s} [{lo:+.3f}, {hi:+.3f}]" if signed else f"{s} [{lo:.2f}, {hi:.2f}]"


def compare(a1: str, a0: str, tasks: tuple[str, ...], data: dict, rng: np.random.Generator, reps: int) -> dict | None:
    strata1, strata0, mh = {}, {}, []
    for t in tasks:
        d1, d0 = data.get((a1, t), []), data.get((a0, t), [])
        for ds in sorted({d["dataset"] for d in d1} & {d["dataset"] for d in d0}):
            x = [d for d in d1 if d["dataset"] == ds]
            y = [d for d in d0 if d["dataset"] == ds]
            strata1[(t, ds)], strata0[(t, ds)] = x, y
            mh.append((sum(bool(d["accepted"]) for d in x), len(x), sum(bool(d["accepted"]) for d in y), len(y)))
    if not mh:
        return None
    m = mantel_haenszel(mh)
    r1, r0 = groups_of(strata1, repair_pair), groups_of(strata0, repair_pair)
    rep = boot(r1, r0, diff_of_ratios, rng, reps)
    cost = boot(groups_of(strata1, lambda d: (d["llm_calls"], int(bool(d["accepted"])))),
                groups_of(strata0, lambda d: (d["llm_calls"], int(bool(d["accepted"])))), ratio_of_ratios, rng, reps)
    k1, n1 = (sum(g.sum(0) for g in r1)).astype(int)
    k0, n0 = (sum(g.sum(0) for g in r0)).astype(int)
    rel1, des1 = sum(s[0] for s in mh), sum(s[1] for s in mh)
    rel0, des0 = sum(s[2] for s in mh), sum(s[3] for s in mh)
    return {
        "comparison": f"{a1} - {a0}" + (" (primary)" if (a1, a0) == PRIMARY else ""),
        "tasks": "+".join(tasks), "datasets": ",".join(sorted({ds for _, ds in strata1})), "strata": m["strata"],
        f"released_{a1}": f"{rel1}/{des1}", f"released_{a0}": f"{rel0}/{des0}",
        "released": f"{rel1}/{des1} vs {rel0}/{des0}",
        "released_diff_MH": fmt(m["rd"], m["lo"], m["hi"]), "odds_ratio_MH": round(m["or"], 2),
        "p_CMH": m["p"],
        "repair": f"{k1}/{n1} vs {k0}/{n0}", "repair_diff": fmt(*rep),
        "calls_per_released_ratio": fmt(*cost, signed=False),
    }


def transitions(arm: str, task: str, designs: list[dict]) -> list[dict]:
    rows = []
    for s in TRANSITION_STAGES:
        n = past = acc = same = dup = 0
        for d in designs:
            for _, st, _ in loops(d):
                for x, y in zip(st, st[1:]):
                    if x != s:
                        continue
                    n += 1
                    past += y != "duplicate" and STAGE_ORDER.index(y) > STAGE_ORDER.index(x)
                    acc += y == "accepted"
                    same += y == s
                    dup += y == "duplicate"
        rows.append({"task": task, "arm": arm, "rejected_at": s, "next_drafts": n,
                     "next_gets_past": past / n if n else None, "next_accepted": acc / n if n else None,
                     "next_same_stage": same / n if n else None, "next_duplicate": dup / n if n else None})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(RES / "reports" / "fb_ablation.md"))
    ap.add_argument("--suffixes", default=",_ext", help="directory suffixes pooled per (arm, task)")
    ap.add_argument("--boot", type=int, default=4000, help="bootstrap replicates")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    suffixes = a.suffixes.split(",")
    rng = np.random.default_rng(a.seed)

    data, trans, runs = {}, {}, []
    for task in TASKS:
        for arm in ARMS:
            designs, tr, rs = load_arm(arm, task, suffixes)
            runs += rs
            if designs:
                data[(arm, task)], trans[(arm, task)] = designs, tr

    pooled = [arm_row(arm, t, data[(arm, t)], trans[(arm, t)]) for t in TASKS for arm in ARMS if (arm, t) in data]
    per_ds = []
    for t in TASKS:
        for arm in ARMS:
            for ds in sorted({d["dataset"] for d in data.get((arm, t), [])}):
                per_ds.append(arm_row(arm, t, [d for d in data[(arm, t)] if d["dataset"] == ds],
                                      [x for x in trans[(arm, t)] if x.get("dataset") == ds], ds))
    comps = [c for a1, a0 in PAIRS for tasks in ((TASKS[0],), (TASKS[1],), TASKS)
             if (c := compare(a1, a0, tasks, data, rng, a.boot)) is not None]
    first = []
    for t in TASKS:
        for arm in ARMS:
            lps = [st for d in data.get((arm, t), []) for _, st, _ in loops(d) if st]
            if lps:
                k = sum(st[0] == "accepted" for st in lps)
                lo, hi = wilson_interval(k, len(lps))
                rk, rn = map(sum, zip(*(repair_pair(d) for d in data[(arm, t)])))
                first.append({"task": t, "arm": arm, "datasets": ",".join(sorted({d["dataset"] for d in data[(arm, t)]})),
                              "first_draft_accepted": f"{k}/{len(lps)}", "rate": k / len(lps),
                              "ci95": f"[{lo:.2f}, {hi:.2f}]",
                              "repaired_after_rejected_first": f"{rk}/{rn}", "repair_rate": rk / rn if rn else None})
    trans_rows = [r for t in TASKS for arm in ARMS if (arm, t) in data for r in transitions(arm, t, data[(arm, t)])]

    unfinished = [r["tag"] for r in runs if not r["finished"]]
    md = ["# Feedback ablation (CSCWD): does the checker's diagnosis help the curator?", "",
          "CS9 settings (Qwen3-8B thinking curator, temperature 0.6, generic prompt core, per-node architecture, "
          "simulated choice, own-row check, ε = 2), tighten 0, 3 drafts per release (rows, matrix); the arms differ only "
          "in what a redraft's prompt shows: `full` = the rejected drafts with the checker's diagnosis, `binary` = the "
          "rejected drafts with the bare verdict, `none` = nothing (independent resampling, the same number of calls). "
          "The first draft's prompt is identical in all arms.", ""]
    if unfinished:
        md += ["Not finished (partial results): " + ", ".join(unfinished), ""]
    md += ["## 1. Comparisons (only the datasets both arms ran)", "",
           "`released_diff_MH`: Mantel-Haenszel risk difference of the released share over the (task, dataset) strata, "
           "Wald 95% interval; `p_CMH`: continuity-corrected Cochran-Mantel-Haenszel test. `repair`: design loops whose "
           "first draft was rejected that were accepted at draft 2 or 3, difference with a 95% bootstrap interval "
           f"({a.boot} replicates, designs resampled within each stratum). `calls_per_released_ratio`: model calls per "
           "released design, first arm over second. `full - none` is the primary comparison.", "",
           markdown_table(comps, ["comparison", "tasks", "datasets", "released", "released_diff_MH", "odds_ratio_MH",
                                  "p_CMH", "repair", "repair_diff", "calls_per_released_ratio"]), "",
           "## 2. Yield and budget curve (all datasets of each arm)", "",
           markdown_table(pooled, ["task", "arm", "datasets", "designs", "released", "released_rate", "released_ci95",
                                   "loop_at_1", "loop_at_2", "loop_at_3", "design_at_1", "design_at_2", "design_at_3"]), "",
           "## 3. First draft (randomisation check) and repair", "",
           "The first draft sees the same prompt in every arm, so its acceptance rate should not differ between arms.", "",
           markdown_table(first, ["task", "arm", "datasets", "first_draft_accepted", "rate", "ci95",
                                  "repaired_after_rejected_first", "repair_rate"]), "",
           "## 4. What the next draft does after a rejection at a stage", "",
           "`next_gets_past`: the next draft of the same loop stops at a later stage or is accepted (a duplicate does not "
           "count); `next_same_stage`: it is rejected at the same stage again.", "",
           markdown_table(trans_rows, ["task", "arm", "rejected_at", "next_drafts", "next_gets_past", "next_accepted",
                                       "next_same_stage", "next_duplicate"]), "",
           "## 5. Cost", "",
           markdown_table(pooled, ["task", "arm", "datasets", "calls_per_design", "calls_per_released",
                                   "out_tokens_per_design", "out_tokens_per_released", "tokens_missing", "drafts",
                                   "duplicate_share"]), "",
           "## 6. Draft outcomes and released programs", "",
           markdown_table(pooled, ["task", "arm", "draft_stages", "distinct_programs", "semantic_pass", "sound", "mean_RE",
                                   "design_error_vs_GT_DSL"]), "",
           "## 7. Per dataset", "",
           markdown_table(per_ds, ["task", "arm", "dataset", "designs", "released_rate", "released_ci95", "loop_at_1",
                                   "loop_at_3", "calls_per_released", "mean_RE"]), "",
           "## 8. Runs", "", markdown_table(runs, ["tag", "finished", "designs", "datasets", "api_errors"]), ""]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(md), encoding="utf-8")
    write_json({"settings": vars(a), "comparisons": comps, "pooled": pooled, "first_draft": first,
                "transitions": trans_rows, "per_dataset": per_ds, "runs": runs}, out.with_suffix(".json"))
    print("\n".join(md))


if __name__ == "__main__":
    main()
