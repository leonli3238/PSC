"""Overall comparison of CertiCount with the PSC architecture (ε = 2, the four PSC tasks, six datasets).

Methods (mean relative error |f_hat - f| / max(f, 0.001 n), lower is better):

* ``PSC (paper)``      -- Table 2 of the PSC paper (its own models and implementation);
* ``PSC (Qwen3)``      -- the PSC multi-agent architecture reproduced with the CertiCount models: curator /
                          privacy controller Qwen3-8B thinking, node agents Qwen3-1.7B, 10 runs (CS1, CS8).
                          PM triangle does not fit the node context and is reported as infeasible;
* ``GT-PSC (code)``    -- the PSC rules executed exactly in code, no model call: PSC without LLM execution error;
                          runs 0-99 of ``cs8_code_all6_r1000`` (the noise of CertiCount's runs);
* ``CertiCount``       -- Qwen3-8B thinking curator writes a DSL program, the nodes run the interpreter (0 node
                          model calls), per-node architecture α = 5, 20 designs x 100 runs, mean over the accepted
                          designs. degree / k-stars: CS7/CS8 (prompt core v1-alt; the language reference itself
                          computes these tasks); triangle: CS9 generic core (shows no triangle program).

Error bars: 95% intervals -- PSC (Qwen3): ±1.96 se over its 10 runs; GT-PSC: over the 100 runs; CertiCount: over
the designs (all runs of a design averaged first).

    ../.venv/bin/python scripts/plot_psc_comparison.py            # results/figures/psc_comparison/
    ../.venv/bin/python scripts/plot_psc_comparison.py --no-plot  # table only
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PSC_ROOT = ROOT.parent / "psc"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PSC_ROOT))

from psc.experiments import DATASETS as PAPER_ORDER, PAPER_TABLE2  # noqa: E402
from psc.ground_truth import relative_error  # noqa: E402

RES = ROOT / "results"
DATASETS = ("PM", "CU", "Do", "ML", "CS", "EE")
TASKS = ("degree", "2-star", "3-star", "triangle")
METHODS = ("PSC (paper)", "PSC (Qwen3)", "GT-PSC (code)", "CertiCount")
RUNS_CODE = 100

CC_DIRS = {
    **{("PM", t): "cs8_node_v1alt_sim_pm_deg2star" for t in ("degree", "2-star")},
    ("PM", "3-star"): "cs7_node_v1alt_sim",
    **{(d, t): "cs8_node_v1alt_sim_cudo_3tasks" for d in ("CU", "Do") for t in ("degree", "2-star", "3-star")},
    **{(d, t): "cs8_node_v1alt_sim_mlcsee" for d in ("ML", "CS", "EE") for t in ("degree", "2-star", "3-star")},
    **{(d, "triangle"): "cs9_node_generic_sim_tri_ow" for d in DATASETS},
}
CC_TRIANGLE_V1ALT = {"PM": "cs7_node_v1alt_sim", "CU": "cs7_node_v1alt_sim_cudo", "Do": "cs7_node_v1alt_sim_cudo",
                     **{d: "cs8_node_v1alt_sim_mlcsee" for d in ("ML", "CS", "EE")}}
PSC_DIRS = ("cs1_pm_8bthink-curator_1.7b-node", "cs8_psc_5ds_kstar_8bthink-curator_1.7b-node",
            "cs1_cudo_triangle_8bthink-curator_1.7b-node", "cs8_psc_triangle_8bthink-curator_1.7b-node")
INFEASIBLE = {("PM", "triangle"): "node prompt exceeds the Qwen3 context"}
CODE_DIR = RES / "execution" / "cs8_code_all6_r1000"
SIZES_FROM = RES / "execution" / "cs9_gt_select_r1000" / "summary.json"


def jsonl(p: Path):
    with p.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def certicount_cell(tag: str, ds: str, task: str) -> dict:
    d = RES / "dsl_eval" / tag
    by_design = defaultdict(list)
    for r in jsonl(d / "runs.jsonl"):
        if r["dataset"] == ds and r["task"] == task and r.get("relative_error") is not None:
            by_design[r["design"]].append(r["relative_error"])
    summ = next(r for r in json.loads((d / "summary.json").read_text())["summary"]
                if r["dataset"] == ds and r["task"] == task)
    means = np.array([np.mean(v) for v in by_design.values()])
    all_runs = np.concatenate([np.array(v) for v in by_design.values()])
    se = float(means.std(ddof=1) / math.sqrt(len(means))) if len(means) > 1 else None
    return {"mean": float(all_runs.mean()), "se": se, "n": int(len(means)), "unit": "designs",
            "accept_rate": summ.get("accept_rate"), "designs": summ.get("designs"), "source": f"dsl_eval/{tag}"}


def psc_cells() -> dict:
    out = {}
    for tag in PSC_DIRS:
        for r in json.loads((PSC_ROOT / "results" / "exp1" / tag / "summary.json").read_text()):
            if r.get("method") != "PSC" or r.get("eps") != 2.0:
                continue
            out[(r["dataset"], r["task"])] = {
                "mean": r["avg_relative_error"], "se": r.get("se_relative_error"), "n": r["runs"], "unit": "runs",
                "rule_relative_error": r.get("rule_relative_error"), "llm_harm": r.get("llm_harm"),
                "lucky_gain": r.get("lucky_gain"), "exec_exact": r.get("exec_exact"),
                "source": f"psc/results/exp1/{tag}"}
    return out


def code_cells(sizes: dict) -> dict:
    vals = defaultdict(list)
    for r in jsonl(CODE_DIR / "runs.jsonl"):
        if r["method"] == "GT-PSC" and r["eps"] == 2.0 and r["run"] < RUNS_CODE:
            vals[(r["dataset"], r["task"])].append(relative_error(r["estimate"], r["truth"], sizes[r["dataset"]]))
    return {k: {"mean": float(np.mean(v)), "se": float(np.std(v, ddof=1) / math.sqrt(len(v))), "n": len(v),
                "unit": "runs", "source": f"execution/{CODE_DIR.name} (runs 0-{RUNS_CODE - 1})"}
            for k, v in vals.items()}


def collect() -> dict:
    sizes = {m["dataset"]: m["n"] for m in json.loads(SIZES_FROM.read_text())["main"]}
    psc, code = psc_cells(), code_cells(sizes)
    cells = {}
    for ds in DATASETS:
        for task in TASKS:
            c = {"PSC (paper)": {"mean": PAPER_TABLE2[task]["PSC"][PAPER_ORDER.index(ds)], "source": "PSC paper Table 2"},
                 "PSC (Qwen3)": psc.get((ds, task)),
                 "GT-PSC (code)": code.get((ds, task)),
                 "CertiCount": certicount_cell(CC_DIRS[(ds, task)], ds, task)}
            if task == "triangle":
                c["CertiCount (v1-alt, leaks the triangle program)"] = certicount_cell(CC_TRIANGLE_V1ALT[ds], ds, task)
            if (ds, task) in INFEASIBLE:
                c["PSC (Qwen3)"] = {"mean": None, "note": INFEASIBLE[(ds, task)]}
            cells[(ds, task)] = c
    return cells


def gmean(xs: list[float]) -> float:
    return float(math.exp(np.mean(np.log(xs))))


def summarize(cells: dict) -> tuple[list[dict], list[dict]]:
    """Per task: geometric means over the datasets every method has, and CertiCount's wins per method."""
    summary, wins = [], []
    for task in TASKS:
        common = [ds for ds in DATASETS if all((cells[(ds, task)].get(m) or {}).get("mean") for m in METHODS)]
        row = {"task": task, "datasets": ",".join(common)}
        for m in METHODS:
            row[m] = gmean([cells[(ds, task)][m]["mean"] for ds in common])
        row["PSC (Qwen3) / CertiCount"] = row["PSC (Qwen3)"] / row["CertiCount"]
        row["GT-PSC / CertiCount"] = row["GT-PSC (code)"] / row["CertiCount"]
        row["PSC (paper) / CertiCount"] = row["PSC (paper)"] / row["CertiCount"]
        summary.append(row)
        for m in METHODS[:-1]:
            avail = [ds for ds in DATASETS if (cells[(ds, task)].get(m) or {}).get("mean")]
            k = sum(cells[(ds, task)]["CertiCount"]["mean"] < cells[(ds, task)][m]["mean"] for ds in avail)
            wins.append({"task": task, "versus": m, "CertiCount_lower": f"{k}/{len(avail)}"})
    return summary, wins


def fmt(v) -> str:
    if v is None:
        return "-"
    return f"{v:.4f}" if v < 10 else f"{v:.2f}"


def write_tables(cells: dict, summary: list[dict], wins: list[dict], out: Path) -> None:
    lines = ["# CertiCount vs the PSC architecture (ε = 2)", "",
             "Mean relative error, lower is better. `PSC (Qwen3)`: PSC multi-agent architecture with the CertiCount "
             "models (curator Qwen3-8B thinking, nodes Qwen3-1.7B), 10 runs. `GT-PSC (code)`: PSC rules in code, runs "
             "0-99 (CertiCount's noise). `CertiCount`: 20 designs x 100 runs, accepted designs; degree / k-stars from "
             "CS7/CS8 (v1-alt core), triangle from CS9 (generic core, no leak). `rule` = GT-PSC on the PSC (Qwen3) "
             "runs' own noise; `llm_harm` = error the node agents add by mis-executing it.", "",
             "## Per cell", "",
             "| task | dataset | PSC (paper) | PSC (Qwen3) | rule | llm_harm | GT-PSC (code) | CertiCount | "
             "CC accept | CC v1-alt (leak) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for task in TASKS:
        for ds in DATASETS:
            c = cells[(ds, task)]
            p = c["PSC (Qwen3)"] or {}
            v1 = c.get("CertiCount (v1-alt, leaks the triangle program)")
            lines.append(f"| {task} | {ds} | {fmt(c['PSC (paper)']['mean'])} | "
                         f"{fmt(p.get('mean')) if p.get('mean') is not None else 'infeasible'} | "
                         f"{fmt(p.get('rule_relative_error'))} | {fmt(p.get('llm_harm'))} | "
                         f"{fmt(c['GT-PSC (code)']['mean'])} | **{fmt(c['CertiCount']['mean'])}** | "
                         f"{c['CertiCount']['accept_rate']:.2f} | {fmt(v1['mean']) if v1 else ''} |")
    lines += ["", "## Geometric mean over the datasets every method has", "",
              "| task | datasets | " + " | ".join(METHODS) + " | PSC (Qwen3) / CC | GT-PSC / CC | PSC (paper) / CC |",
              "|---|---|" + "---|" * (len(METHODS) + 3)]
    for r in summary:
        lines.append(f"| {r['task']} | {r['datasets']} | " + " | ".join(fmt(r[m]) for m in METHODS) +
                     f" | {r['PSC (Qwen3) / CertiCount']:.1f}x | {r['GT-PSC / CertiCount']:.2f}x | "
                     f"{r['PSC (paper) / CertiCount']:.2f}x |")
    lines += ["", "## Cells where CertiCount's mean is lower", "", "| task | versus | CertiCount lower |", "|---|---|---|"]
    lines += [f"| {w['task']} | {w['versus']} | {w['CertiCount_lower']} |" for w in wins]
    lines += ["", "Sources: " + "; ".join(sorted({c[m]['source'] for c in cells.values() for m in METHODS
                                                    if (c.get(m) or {}).get('source')})), ""]
    (out / "table.md").write_text("\n".join(lines), encoding="utf-8")
    data = {f"{ds}/{task}": c for (ds, task), c in cells.items()}
    (out / "data.json").write_text(json.dumps({"cells": data, "summary": summary, "wins": wins}, indent=1),
                                   encoding="utf-8")


STYLE = {"PSC (paper)": dict(color="#9e9e9e", hatch="//"), "PSC (Qwen3)": dict(color="#d62728"),
         "GT-PSC (code)": dict(color="#ff9f40"), "CertiCount": dict(color="#1f77b4")}


def plot(cells: dict, summary: list[dict], out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "pdf.fonttype": 42, "ps.fonttype": 42})
    width = 0.2
    x = np.arange(len(DATASETS))

    fig, axes = plt.subplots(1, 4, figsize=(15, 3.6), sharey=False)
    for ax, task in zip(axes, TASKS):
        for i, m in enumerate(METHODS):
            xs = x + (i - 1.5) * width
            for xi, ds in zip(xs, DATASETS):
                c = cells[(ds, task)].get(m) or {}
                v = c.get("mean")
                if v is None:
                    ax.text(xi, 0.03, "n/a", ha="center", va="bottom", fontsize=7.5, fontweight="bold",
                            color=STYLE[m]["color"], rotation=90, transform=ax.get_xaxis_transform())
                    continue
                se = c.get("se")
                err = None
                if se:
                    lo = max(v - 1.96 * se, v * 0.05)
                    err = [[v - lo], [1.96 * se]]
                ax.bar(xi, v, width, color=STYLE[m]["color"], hatch=STYLE[m].get("hatch"), edgecolor="white",
                       linewidth=0.4, yerr=err, error_kw=dict(elinewidth=0.6, capsize=1.2, ecolor="#333333"))
        ax.set_yscale("log")
        ax.set_xticks(x)
        ax.set_xticklabels(DATASETS)
        ax.set_title(task)
        ax.grid(axis="y", which="major", alpha=0.3)
    axes[0].set_ylabel("mean relative error (log)")
    handles = [Patch(facecolor=STYLE[m]["color"], hatch=STYLE[m].get("hatch"), edgecolor="white", label=m)
               for m in METHODS]
    fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.02))
    fig.text(0.5, -0.02, "ε = 2. PSC (Qwen3): curator Qwen3-8B, node agents Qwen3-1.7B, 10 runs (PM triangle: node prompt "
             "exceeds the context). GT-PSC: PSC rules in code. CertiCount: 20 designs x 100 runs, 0 node LLM calls. "
             "Bars: 95% CI.", ha="center", fontsize=7)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    for ext in ("png", "pdf"):
        fig.savefig(out / f"fig_psc_per_dataset.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    xt = np.arange(len(TASKS))
    for i, m in enumerate(METHODS):
        vals = [r[m] for r in summary]
        ax.bar(xt + (i - 1.5) * width, vals, width, color=STYLE[m]["color"], hatch=STYLE[m].get("hatch"),
               edgecolor="white", linewidth=0.4, label=m)
    for j, r in enumerate(summary):
        top = max(r[m] for m in METHODS)
        ax.text(j, top * 1.6, f"PSC (Qwen3) / CertiCount = {r['PSC (Qwen3) / CertiCount']:.0f}x\n"
                f"GT-PSC / CertiCount = {r['GT-PSC / CertiCount']:.1f}x", ha="center", va="bottom", fontsize=6.5)
    ax.set_yscale("log")
    ax.set_ylim(top=ax.get_ylim()[1] * 12)
    ax.set_xticks(xt)
    ax.set_xticklabels([f"{r['task']}\n({r['datasets'].count(',') + 1} datasets)" for r in summary])
    ax.set_ylabel("geometric mean of relative error (log)")
    ax.grid(axis="y", which="major", alpha=0.3)
    ax.legend(ncol=4, frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, 1.13))
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(out / f"fig_psc_summary.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(RES / "figures" / "psc_comparison"))
    ap.add_argument("--no-plot", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cells = collect()
    summary, wins = summarize(cells)
    write_tables(cells, summary, wins, out)
    if not a.no_plot:
        plot(cells, summary, out)
    print((out / "table.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
