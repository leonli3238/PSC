"""Build ``results.md``: Exp1 results grouped by model, one table per model.

Each table holds, per task, the reproduced Naive (one row per prompt) and
PSC / TriTR rows next to the paper's Naive / PSC numbers (Table 2) and the
pure-Python GT-Naive / GT-PSC of this implementation.

Runs whose model call exhausted its retries (``call_failed``) are dropped (†).
Naive replies are re-parsed with the current parser; a cell is marked ‡ when
the archived estimate differs, and the note gives the re-computed mean.

Example::

    python scripts/build_results_md.py --out results.md
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from psc.experiments import DATASETS, PAPER_TABLE2  # noqa: E402
from psc.graph import load_dataset  # noqa: E402
from psc.ground_truth import relative_error  # noqa: E402
from psc.prompts import extract_json, extract_number  # noqa: E402

EXP1 = Path("results/exp1")
GT_DIR = "results/ground_truth/gt_all_r1000_floor_tight_20260930"
TASKS = ("degree", "2-star", "3-star", "triangle")
PROMPT_ORDER = ("paper", "paper-direct", "paper-bidir", "cot")

# Reply patterns the current parser still reads wrongly, with the rewrite that
# lets it read the intended answer.
KNOWN_BUGS = {
    # the ``###421`` marker rule takes the "3" of a ``### 3. ...`` Markdown heading
    "heading": (re.compile(r"^(#{1,6})\s*\d+\.", re.M), r"\1"),
    # LaTeX thousands separators: ``49{,}705`` / ``47,\!349`` / ``47\,349`` are read as the last group
    "latex_comma": (re.compile(r"(?<=\d)(?:\{,\}|,\\!|\\,)(?=\d)"), ","),
}
BUG_TEXT = {
    "old": "被当时的解析器取错数（当前解析器已能正确解析）",
    "heading": "被当前解析器的 `###` 规则取成标题序号（如 `### 3.` 中的 3）",
    "latex_comma": "的答案写成 LaTeX 千分位（`49{,}705`、`47,\\!349`），当前解析器只取到最后三位",
}

# (title, description, sources, notes); a source is a list of directories that
# are de-duplicated together (one campaign split over several directories).
SECTIONS = [
    (
        "GPT-4.1",
        "节点 = curator = gpt-4.1；`gpt41-oaifree_*` 走 hub.oaifree.com 网关，其余走 api.oaipro.com（`.env.gpt41`）。",
        [
            ["gpt41-oaifree_exp1_CU_degree-2-star-3-star-triangle_r10_floor_tight_Naive"],
            ["openai_gpt-4.1_floor_tight_20261014_153755_281075"],
            ["openai_gpt-4.1_floor_tight_20261014_155709_945010"],
            ["gpt41_exp1_CU_2-star_r30_Naive"],
            ["gpt41-oaifree_exp1_CU_triangle_r20_Naive"],
        ],
        [
            "GPT-4.1 几乎每次都写 Python 代码再自称“运行结果是 X”，X 是编造的（同一个数如 3142、4952、11094 会跨任务重复出现），"
            "所以 Naive 误差主要由“编出来的数有多大”决定。`gpt41_exp1_CU_2-star_r30_Naive` 中 30 次全部与噪声图精确值不符，"
            "26 次属于“伪造代码输出”（相对噪声图精确值偏差中位数 +62%），只有 4 次逐节点手算（偏差中位数 7.6%）。",
            "有些回复没有给出最终数字，解析器从公式或正文中取到 3、4、-12 等无关数字，`parse_failures` 仍为 0："
            "`…153755` 中 CU 3-star 3 次、Do 3-star 3 次，`…155709` 中 CU triangle 4 次。去掉这些运行后，"
            "`…153755` 的 CU 3-star 为 15.70、Do 3-star 为 9.24，`…155709` 的 CU triangle 为 8.39。",
        ],
    ),
    (
        "GLM-5.2",
        "节点 = curator = glm-5.2，关闭 thinking（`extra_body.thinking.type = disabled`），未保存 transcripts。",
        [["glm-5.2_exp1_CU_degree-2-star-3-star-triangle_r10_floor_tight_Naive"]],
        [
            "GLM-5.2 列出的度数系统性偏小（估计值约为噪声图精确值的 0.6 倍），抵消了加噪带来的偏大，所以 2-star、3-star 的误差"
            "反而低于 GT-Naive 下限，不代表算得更准。triangle 则会编造大量不存在的三角形（如 CU 第 1 次列出 2579 个，其中只有 103 个真实存在）。",
        ],
    ),
    (
        "DeepSeek-V3（1226）",
        "节点 = curator = deepseek-v3。",
        [
            ["dsv3-1226_exp1_all6_r10_floor_tight_Naive"],
            ["dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0"],
            ["dsv3-1226_exp1_all6_r10_floor_tight_Naive_paperprompt"],
            ["dsv3-1226_exp1_CU-Do_2-star_r10_floor_tight_Naive_paperprompt"],
            ["dsv3-1226_exp1_CU-Do_degree-2-star-3-star-triangle_r30_floor_tight_Naive_paper-directprompt"],
            ["dsv3-1226_exp1_CU-Do_2-star_r10_floor_tight_Naive_paper-directprompt"],
            ["dsv3-1226_exp1_CU-Do_3-star_r10_floor_tight_Naive_paper-directprompt"],
            ["dsv3-1226_exp1_CU-Do_3-star_r10_floor_tight_Naive_paper-bidirprompt"],
        ],
        ["`paper-direct` 禁止推理后模型只能猜数，误差比其他 prompt 高一个数量级。"],
    ),
    (
        "DeepSeek-V3-0324",
        "节点 = curator = deepseek-v3-0324。",
        [["dsv3-0324_exp1_CU_degree-3star_r100_floor_tight_PSC"]],
        [
            "节点更新 9800 次中 9799 次与规则一致；curator 汇总 degree 97/100、3-star 92/100 正确。3-star 的 8 次错误里有 7 次"
            "是不做计算直接输出 `{\"result\": 0}`（10 到 13 个输出 token），而带噪计数之和实际为 99 到 460。",
        ],
    ),
    (
        "hy3-ioa",
        "节点 = curator = hy3-ioa。",
        [
            ["hy3_exp1_r10", "hy3_exp1_pm_rest"],
            ["hy3_exp1_CU_all4_r30_Naive"],
            ["hy3_exp1_CU_all4_r30_Naive_transcripts"],
            ["hy3-ioa_exp1_CU-Do_r10_floor_tight_TriTR-a0"],
        ],
        [
            "hy3-ioa 带隐藏推理（`hy3_exp1_CU_all4_r30_Naive_transcripts` 中每次约 0.8 万到 6.5 万输出 token，可见回复很短），"
            "Naive 结果基本等于 GT-Naive 下限：该目录 120 次中 110 次与噪声图精确值一致（容许四舍五入）。",
            "TriTR 的 degree 与 PSC 机制相同，所以数值一样。",
        ],
    ),
    (
        "curator hy3-ioa + 节点 deepseek-v3",
        "Naive 只调用 curator，等同 hy3-ioa 的 Naive。",
        [["hy3-dsv3-1226_exp1_CU-Do_degree-2-star-3-star-triangle_r20_floor_tight_Naive-PSC_paper-directprompt"]],
        ["hy3 在 `paper-direct` 下仍会隐藏推理，degree 回答为 `454/49` 这样的分数，旧解析器取了分母 49。"],
    ),
    (
        "curator hy4-preview-ioa + 节点 hy3-ioa",
        "Naive 只调用 curator，等同 hy4-preview-ioa 的 Naive。",
        [["hy4-curator_hy3-node_exp1_ML_triangle-3star_r10_Naive-PSC"]],
        [
            "PSC 节点更新 3-star 770/770、triangle 767/770 与规则一致，curator 汇总 20/20 正确，误差与同噪声下精确执行"
            "（3-star 0.2837、triangle 0.4101）几乎相同。Naive 修正解析后 3-star 2.14、triangle 0.6000，也与同噪声的精确计数"
            "（2.14、0.6005）一致。",
        ],
    ),
    (
        "curator gpt-4.1 + 节点 gpt-4.1-mini",
        "本组只跑了 PSC，走 api.oaipro.com。Naive 只调用 curator，等同 GPT-4.1 的 Naive，表中 Naive 行取自第 1 节。",
        [
            ["gpt41mini-node_gpt41-curator_exp1_CU_3-star_r10_PSC"],
            ["gpt41mini-node_gpt41-curator_exp1_CU_triangle_r10_PSC"],
        ],
        [
            "节点更新 3-star 490/490、triangle 481/490 与规则一致，curator 汇总 19/20 正确（3-star 第 4 次 548.54，应为 546.54）。"
            "误差与同噪声下精确执行（3-star 1.0229、triangle 1.1723）几乎相同，所以和 hy3-ioa 的 PSC 数值一样。",
            "这 10 次比 1000 次的 GT-PSC 高（3-star 0.6954、triangle 1.00），是前 10 个噪声样本本身偏大，不是模型误差。",
            "同一个 curator 下，PSC 把 3-star 误差从 Naive 的 14.70 降到 1.02、triangle 从 8.36 降到 1.17。GPT-4.1 的 Naive 远差于"
            " GT-Naive（10.07、1.44），主要是编造数字（见第 1 节）；PSC 把计数拆给节点后，gpt-4.1-mini 也几乎不出错。",
        ],
    ),
]

# Naive calls only the curator, so a mixed section without its own Naive runs shows
# the Naive of the section whose model is its curator.
NAIVE_FROM = {"curator gpt-4.1 + 节点 gpt-4.1-mini": "GPT-4.1"}

EXCLUDED = [
    "`hy3_exp1_r10_5ds`：`hy3_exp1_r10` 前五个数据集的合并副本，避免重复计数。",
    "`gpt41-oaifree_exp1_CU-Do_2-star_r30_Naive`：第 1 次运行就被 429 限流中断，只有空的 transcripts，没有 `runs.jsonl`。",
    "`_smoke_hy3-dsv3-1226`：冒烟测试，没有运行结果。",
    "`table2.md` / `table2.json`：此前由 `scripts/build_exp1_table.py` 生成的 DeepSeek-V3 与 hy3-ioa 汇总表，本文件已包含其中的数据。",
]


def fmt(x: float) -> str:
    return f"{x:.2f}" if abs(x) >= 1 else f"{x:.4f}"


def prompt_label(row: dict) -> str | None:
    if row["method"] != "Naive":
        return None
    p = row["extra"].get("naive_prompt")
    return "cot" if p in (None, "default") else p


def reparse(reply: str) -> float | None:
    """The current ``CuratorAgent._parse_result`` without the agent."""
    payload = extract_json(reply)
    if payload and "result" in payload:
        try:
            return float(payload["result"])
        except (TypeError, ValueError):
            pass
    return extract_number(reply)


def corrected(reply: str, archived: float) -> tuple[str, float] | None:
    """``(reason, value)`` when the reply's answer differs from the archived estimate."""
    def differs(v: float | None) -> bool:
        return v is not None and not math.isclose(v, archived, rel_tol=1e-9, abs_tol=1e-9)

    now = reparse(reply)
    if differs(now):
        return "old", now
    for reason, (pattern, repl) in KNOWN_BUGS.items():
        if pattern.search(reply):
            fixed = reparse(pattern.sub(repl, reply))
            if differs(fixed):
                return reason, fixed
    return None


class Cell:
    def __init__(self) -> None:
        self.errors: list[float] = []
        self.fixed: list[float] = []
        self.failed = 0
        self.misparsed: dict[str, int] = defaultdict(int)
        self.by_source: dict[str, list[float]] = defaultdict(list)

    def mean(self, values: list[float] | None = None) -> float:
        values = self.errors if values is None else values
        return sum(values) / len(values)

    def se(self) -> float | None:
        n = len(self.errors)
        if n < 2:
            return None
        m = self.mean()
        return math.sqrt(sum((e - m) ** 2 for e in self.errors) / (n - 1)) / math.sqrt(n)

    def text(self, short: bool = False) -> str:
        mark = ("†" if self.failed else "") + ("‡" if self.misparsed else "")
        if not self.errors:
            return f"-{mark}"
        if short:
            return f"{fmt(self.mean())} ({len(self.errors)}){mark}"
        se, mean = self.se(), fmt(self.mean())
        # the standard error keeps the mean's number of decimals
        body = mean if se is None else f"{mean} ± {se:.{len(mean.split('.')[1])}f}"
        return f"{body} ({len(self.errors)}){mark}"


def load_section(sources: list[list[str]], n_of: dict[str, int]) -> dict[tuple, Cell]:
    cells: dict[tuple, Cell] = defaultdict(Cell)
    for group in sources:
        label = "+".join(group)
        rows: dict[tuple, dict] = {}
        for d in group:
            for line in (EXP1 / d / "runs.jsonl").read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if row["eps"] != 2.0:
                    continue
                key = (row["dataset"], row["task"], row["method"], row["extra"]["run"])
                # a successful re-run replaces a failed one, otherwise the first copy wins
                if key not in rows or (_failed(rows[key]) and not _failed(row)):
                    rows[key] = row
        for (dataset, task, method, run), row in rows.items():
            cell = cells[(method, prompt_label(row), dataset, task)]
            if _failed(row):
                cell.failed += 1
                continue
            n = n_of[dataset]
            err = relative_error(row["estimate"], row["truth"], n)
            fixed_est = row["estimate"]
            fix = corrected(row["extra"]["reply"], row["estimate"]) if row["extra"].get("reply") else None
            if fix is not None:
                cell.misparsed[fix[0]] += 1
                fixed_est = fix[1]
            cell.errors.append(err)
            cell.fixed.append(relative_error(fixed_est, row["truth"], n))
            cell.by_source[label].append(err)
    return cells


def _failed(row: dict) -> bool:
    return any(e.get("kind") == "call_failed" for e in row["extra"].get("errors", []))


def method_rows(cells: dict[tuple, Cell], method: str) -> list[tuple[str, str | None]]:
    prompts = {k[1] for k in cells if k[0] == method}
    if method != "Naive":
        return [(method, None)] if prompts else []
    return [(f"Naive · {p}", p) for p in PROMPT_ORDER if p in prompts]


def build_section(idx: int, title: str, desc: str, sources: list[list[str]], notes: list[str],
                  cells: dict[tuple, Cell], gt: dict, out: list[str],
                  borrowed: dict[tuple, Cell] | None = None, borrowed_from: str | None = None) -> None:
    """``borrowed``: Naive cells of the section titled ``borrowed_from`` (same curator),
    shown in the table only; their notes stay in that section."""
    datasets = [d for d in DATASETS if any(k[2] == d for k in cells)]
    tasks = [t for t in TASKS if any(k[3] == t for k in cells)]
    shown = {**cells, **(borrowed or {})}
    srcs = "、".join("+".join(f"`{d}`" for d in g) for g in sources)
    out += [f"## {idx}. {title}", "", f"{desc}来源目录：{srcs}", ""]
    out.append("| Task | 方法 · prompt | " + " | ".join(datasets) + " |")
    out.append("|---|---|" + "---|" * len(datasets))

    def emit(task: str, label: str, values: list[str], italic: bool = False) -> None:
        if italic:
            label, values = f"*{label}*", [v if v == "-" else f"*{v}*" for v in values]
        out.append(f"| {task} | {label} | " + " | ".join(values) + " |")

    def ours(task: str, method: str, prompt: str | None) -> list[str]:
        return [shown[(method, prompt, d, task)].text() if (method, prompt, d, task) in shown else "-"
                for d in datasets]

    for task in tasks:
        naive = method_rows(shown, "Naive")
        for label, prompt in naive or [("Naive", "x")]:
            if borrowed and any(k[0] == "Naive" and k[1] == prompt for k in borrowed):
                label += f"（= {borrowed_from}）"
            emit(task, label, ours(task, "Naive", prompt))
        emit(task, "Naive（论文）", [fmt(PAPER_TABLE2[task]["Naive"][DATASETS.index(d)]) for d in datasets], True)
        emit(task, "GT-Naive（本实现）", [fmt(gt[("GT-Naive", d, task)]) for d in datasets], True)
        emit(task, "PSC", ours(task, "PSC", None))
        emit(task, "PSC（论文）", [fmt(PAPER_TABLE2[task]["PSC"][DATASETS.index(d)]) for d in datasets], True)
        emit(task, "GT-PSC（本实现）", [fmt(gt[("GT-PSC", d, task)]) for d in datasets], True)
        if method_rows(cells, "TriTR"):
            emit(task, "TriTR", ours(task, "TriTR", None))
    out.append("")

    auto = []
    for (method, prompt, d, task), cell in sorted(cells.items(), key=lambda kv: _order(kv[0])):
        name = method if prompt is None else f"{method} · {prompt}"
        if cell.failed:
            what = "全部 " if not cell.errors else ""
            auto.append(f"† {name} · {d} · {task}：{what}{cell.failed} 次运行模型调用重试耗尽，未计入")
        if cell.misparsed:
            what = "；".join(f"{k} 次回复{BUG_TEXT[reason]}" for reason, k in cell.misparsed.items())
            auto.append(
                f"‡ {name} · {d} · {task}：{what}；按回复中的最终答案重算为 {fmt(cell.mean(cell.fixed))}（表中为存档值 {fmt(cell.mean())}）"
            )
    out += [f"- {line}" for line in auto + notes]
    if auto or notes:
        out.append("")

    merged = [(k, c) for k, c in sorted(cells.items(), key=lambda kv: _order(kv[0])) if len(c.by_source) > 1]
    if merged:
        out += ["<details><summary>合并单元格的分来源结果</summary>", ""]
        for (method, prompt, d, task), cell in merged:
            name = method if prompt is None else f"{method} · {prompt}"
            parts = "；".join(f"`{s}` {fmt(sum(v) / len(v))} ({len(v)})" for s, v in cell.by_source.items())
            out.append(f"- {name} · {d} · {task}：{parts}")
        out += ["", "</details>", ""]


def _order(key: tuple) -> tuple:
    method, prompt, d, task = key
    m = ("Naive", "PSC", "TriTR").index(method) if method in ("Naive", "PSC", "TriTR") else 9
    p = PROMPT_ORDER.index(prompt) if prompt in PROMPT_ORDER else -1
    return (TASKS.index(task), m, p, DATASETS.index(d))


def build_overview(sections: list[tuple[str, dict]], gt: dict, out: list[str]) -> None:
    out += [
        "## 总览：CU 数据集",
        "",
        "单元格为 `均值 (运行次数)`，详细数值、标准误和其他数据集见各模型小节。",
        "",
        "| 模型 | 方法 · prompt | " + " | ".join(TASKS) + " |",
        "|---|---|" + "---|" * len(TASKS),
    ]

    def ref(label: str, method: str, values: list[float]) -> None:
        out.append(f"| *{label}* | *{method}* | " + " | ".join(f"*{fmt(v)}*" for v in values) + " |")

    for method in ("Naive", "PSC", "TriTR"):
        for title, cells in sections:
            for label, prompt in method_rows(cells, method):
                if not any(k[2] == "CU" and k[0] == method and k[1] == prompt for k in cells):
                    continue
                vals = [cells[(method, prompt, "CU", t)].text(short=True) if (method, prompt, "CU", t) in cells
                        else "-" for t in TASKS]
                out.append(f"| {title} | {label} | " + " | ".join(vals) + " |")
        if method != "TriTR":
            ref("论文", method, [PAPER_TABLE2[t][method][0] for t in TASKS])
            ref("GT（本实现）", f"GT-{method}", [gt[(f"GT-{method}", "CU", t)] for t in TASKS])
    out.append("")


def build_gt(gt: dict, out: list[str]) -> None:
    out += [
        "## 0. 参考：纯 Python GT（与模型无关，1000 次）",
        "",
        "GT-Naive 是“在噪声图上精确计数”的误差，即 Naive 在 LLM 不出错时的下限；GT-PSC 是 PSC 在节点和 curator 都不出错时的误差。"
        "各模型表格中的 GT 行即取自此表的“本实现”行。",
        "",
        "| Task | Method | " + " | ".join(DATASETS) + " |",
        "|---|---|" + "---|" * len(DATASETS),
    ]
    for task in TASKS:
        for method in ("GT-Naive", "GT-PSC"):
            out.append(f"| {task} | {method}（本实现） | " + " | ".join(fmt(gt[(method, d, task)]) for d in DATASETS) + " |")
            out.append(f"| {task} | *{method}（论文）* | "
                       + " | ".join(f"*{fmt(v)}*" for v in PAPER_TABLE2[task][method]) + " |")
    out.append("")


HEADER = """# Exp1 复现结果与论文 Table 2 对比（按模型）

- 指标：平均相对误差 `|f̂ − f| / max(f, 0.001n)`，ε = 2，机制 `floor_tight`（TriTR 为 `tritr_alpha0`），seed = 0。
- 每个模型一张表，每个任务依次列出：本项目复现的 Naive（每种 prompt 一行）、*论文 Naive*、*GT-Naive*、本项目复现的 PSC、*论文 PSC*、*GT-PSC*，以及（若有）TriTR。
- 单元格格式：`均值 ± 标准误 (有效运行次数)`；*斜体* 行为参考值（论文 Table 2 或本实现的纯 Python GT，GT 为 1000 次的均值）；`-` 表示本项目未运行。
- 同一模型、同一方法、同一 prompt 的多次实验（不同目录）合并计算；同一目录内按 `(dataset, task, method, run)` 去重。seed 相同，所以不同目录的第 i 次运行使用相同噪声图，合并后的差异仅来自 LLM 输出。
- 模型调用重试耗尽（`call_failed`）的运行不计入，以 † 标出。
- ‡ 表示部分回复的数被解析器取错（见各小节注释），表中保留存档值。
- Naive 的 prompt：`paper` = 论文原始 prompt（当前默认）；`paper-direct` = paper + “只输出最终数字”；`paper-bidir` = 早期试验过的 paper 变体（当前代码中已移除）；`cot` = curator 系统提示 + 逐步推理/JSON 指令（2026-10-13 之前的默认）。
- 数据来源：`results/exp1/` 下各目录的 `runs.jsonl`；GT 来自 `results/ground_truth/gt_all_r1000_floor_tight_20260930`。本文件由 `scripts/build_results_md.py` 生成。
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="results.md")
    args = ap.parse_args()

    n_of = {d: next(iter(load_dataset(args.data, d).values())).vertex_num for d in DATASETS}
    gt = {(r["method"], r["dataset"], r["task"]): r["avg_relative_error"]
          for r in json.loads(Path(GT_DIR, "summary.json").read_text(encoding="utf-8"))}

    loaded = [(title, load_section(sources, n_of)) for title, _, sources, _ in SECTIONS]
    by_title = dict(loaded)
    out = [HEADER]
    build_gt(gt, out)
    build_overview(loaded, gt, out)
    for i, ((title, desc, sources, notes), (_, cells)) in enumerate(zip(SECTIONS, loaded), 1):
        src = NAIVE_FROM.get(title)
        cover = {(k[2], k[3]) for k in cells}
        borrowed = {k: c for k, c in by_title[src].items() if k[0] == "Naive" and (k[2], k[3]) in cover} if src else None
        build_section(i, title, desc, sources, notes, cells, gt, out, borrowed, src)
    out += ["## 未纳入的目录", ""] + [f"- {line}" for line in EXCLUDED] + [""]
    Path(args.out).write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
