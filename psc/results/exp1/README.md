# exp1 结果目录（按模型分类）

本目录存放论文 Table 2（Exp1）的智能体运行结果。2026-10-18 起按**使用的模型**分组，一级目录是模型（或模型组合），二级目录仍是原来的运行标签。

## 目录结构

| 目录 | node 模型 | curator 模型 | 内容 |
|---|---|---|---|
| `deepseek-v3/` | DeepSeek-V3 | DeepSeek-V3 | 主结果 `tritr-a0`（CU–EE × 3 任务 × 10 次，含 Naive / PSC / TriTR 与 GT 对照）；`all6` 的 Naive 两种 prompt；2-star / 3-star 的 prompt 对照；CU/Do 四任务 30 次 |
| `deepseek-v3-0324/` | DeepSeek-V3-0324 | DeepSeek-V3-0324 | CU 的 PSC，degree / 3-star 各 100 次，带逐调用 transcripts |
| `glm-5.2/` | GLM-5.2 | GLM-5.2 | CU 的 Naive，四任务各 10 次 |
| `gpt-4.1/` | GPT-4.1 | GPT-4.1 | CU 四任务 10 次、triangle 20 次、2-star 30 次（两批）、Do 2-star |
| `gpt-4.1-mini-node_gpt-4.1-curator/` | gpt-4.1-mini | gpt-4.1 | CU 的 PSC，degree / 3-star / triangle 各 10 次，带 transcripts；审计 P1 的输入来源 |
| `hy3-ioa/` | hy3-ioa | hy3-ioa | 五图主结果 `r10_5ds`、原始 `r10`、PM 补跑、CU 四任务 30 次（含 transcripts）、TriTR |
| `mixed/` | 混合 | 混合 | hy3 curator + DeepSeek-V3 节点；hy4 curator + hy3 节点 |
| `_smoke/` | — | — | 冒烟测试，不进汇总表 |

一级目录名即 `manifest.json` 里的 `settings.node_model`；node 与 curator 不同时，目录名写成 `节点-curator`，或放入 `mixed/`。新增运行请按同一规则归位，不要直接堆在 `exp1/` 根下。

## 汇总表（放在根目录）

| 文件 | 说明 |
|---|---|
| `table2.md` / `table2.json` | 全模型汇总，含 hy 系列 |
| `table2_no_hy.md` / `table2_no_hy.json` | 排除 hy 系列；开题报告与 PPT 引用这一份 |

重新生成：

```bash
.venv/bin/python scripts/build_exp1_table.py --out results/exp1/table2
.venv/bin/python scripts/build_exp1_table.py --exclude hy3-ioa --out results/exp1/table2_no_hy
```

`--exclude` 接受逗号分隔的模型标签（当前可选 `DeepSeek-V3`、`hy3-ioa`），只影响汇总表，不移动任何运行目录。

## 运行目录内容

每个运行目录仍包含 `manifest.json`（配置与代码/数据哈希）、`runs.jsonl`（逐次结果，含同噪声规则值）、`summary.json`、`table.md`；真实 API 运行另有 `errors.jsonl` 与 `run.log`，带 `--save-transcripts` 的还有 `transcripts.jsonl`。

## 与旧路径的对应

旧路径 `results/exp1/<标签>/` 现在统一为 `results/exp1/<模型>/<标签>/`，标签本身未改。脚本、`README.md`、`results/README.md` 与 `docs/RESEARCH_NOTES_2026-10-18.md` 中的路径已同步；若在旧文档或命令里看到旧路径，按“标签名前缀 → 模型目录”的规则替换即可：

| 标签前缀 | 模型目录 |
|---|---|
| `dsv3-1226_` | `deepseek-v3/` |
| `dsv3-0324_` | `deepseek-v3-0324/` |
| `glm-5.2_` | `glm-5.2/` |
| `gpt41-`、`gpt41_`、`openai_gpt-4.1_` | `gpt-4.1/` |
| `gpt41mini-node_gpt41-curator_` | `gpt-4.1-mini-node_gpt-4.1-curator/` |
| `hy3_exp1_`、`hy3-ioa_` | `hy3-ioa/` |
| `hy3-dsv3-1226_`、`hy4-curator_hy3-node_` | `mixed/` |
| `_smoke_` | `_smoke/` |
