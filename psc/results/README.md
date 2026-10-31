# 结果目录索引

实验脚本把结果写到 `results/<实验>/<标签>/`。每个运行目录里有 `manifest.json`（配置与源码/数据哈希）、
`runs.jsonl`（逐次结果，含同噪声规则值 `extra.validation`）、`summary.json`、`table.md`、`transcripts.jsonl`
（每次模型调用的完整 prompt 与回复），真实 API 运行另有 `errors.jsonl` 与 `run.log`；不需要 transcripts 时加
`--no-save-transcripts`。`runs.json` 不入库。

除特别说明外，下面都是 `floor_tight` 机制、ε = 2、seed = 0；第 i 次运行的 DP 噪声只由 `(seed, i)` 决定，
所以同一 seed 的不同模型面对的是同一批噪声。

Naive 提示词：2026-10-13 起默认是论文 prompt（`paper`），目录名不带提示词后缀；在此之前，不带后缀的目录用的是
curator system prompt + "Think step by step … JSON"（现在的 `cot`），论文 prompt 的目录带 `_paperprompt`。
以 `manifest.json` 的 `naive_prompt` 为准，旧目录里记作 `default` 的即 `cot`。

## exp1：论文 Table 2

| 目录 | 内容 |
|---|---|
| `exp1/table2.md`、`table2.json` | **Exp1 汇总表**（全模型），由 `scripts/build_exp1_table.py` 生成 |
| `exp1/table2_no_hy.md`、`table2_no_hy.json` | 同上但排除 hy 系列（`--exclude hy3-ioa`）；开题报告与 PPT 使用这一份 |
| `exp1/deepseek-v3/` | DeepSeek-V3（node = curator）：主结果 `tritr-a0`（CU–EE × 3 任务 × 10 次）、`all6` 的 Naive（两种 prompt）、2-star / 3-star 的 prompt 对照、CU/Do 四任务 30 次 |
| `exp1/deepseek-v3-0324/` | DeepSeek-V3-0324：CU 的 PSC，degree / 3-star 各 100 次，带 transcripts |
| `exp1/glm-5.2/` | GLM-5.2：CU 的 Naive，四任务各 10 次 |
| `exp1/gpt-4.1/` | GPT-4.1（node = curator）：CU 四任务 10 次、triangle 20 次、2-star 30 次（两批）、Do 2-star |
| `exp1/gpt-4.1-mini-node_gpt-4.1-curator/` | 节点 gpt-4.1-mini + curator gpt-4.1：CU 的 PSC，三任务各 10 次，带 transcripts（`../psc-trust` 审计 P1 的输入来源） |
| `exp1/hy3-ioa/` | hy3-ioa（node = curator）：五图主结果 `r10_5ds`、原始 `r10`、PM 补跑、CU 四任务 30 次（含 transcripts）、TriTR |
| `exp1/mixed/` | 混合模型：hy3 curator + DeepSeek-V3 节点；hy4 curator + hy3 节点 |
| `exp1/_smoke/` | 冒烟测试，不进汇总表 |

## pilot：CU/Do 四任务（含 2-star）

| 目录 | 内容 |
|---|---|
| `pilot/hy3-ioa_cudo_r10_floor_tight/` | hy3-ioa，Naive/PSC × 10；Do triangle Naive 有 1 次调用重试耗尽 |
| `pilot/hy4-preview-ioa_cudo_r10_floor_tight/` | hy4-preview-ioa，同上 |
| `pilot/mock_cudo_r10_20260929/` | mock（完美推理器），流程验证，见 `docs/PSC_REPRODUCTION_REPORT.md` §36 |
| `pilot/mock_cudo_r10_imola_check_20261009/` | mock，k-star 投影改动后的复核 |

## exp2

| 目录 | 内容 |
|---|---|
| `exp2/mock_kstar_budget_sweep_r10_20261002/` | mock 的 ε 扫描（1.0–3.0），只含 2-star/3-star |

exp3–exp6 目前没有当前机制下的有效结果，历史结果见 `archive/`。

## ground_truth：纯 Python GT

| 目录 | 内容 |
|---|---|
| `ground_truth/gt_all_r1000_floor_tight_20260930/` | **当前 GT**：GT-Naive、GT-PSC、GT-PSC-B，6 个数据集 × 4 任务 × 1000 次；Table 2 的 GT 行取自这里 |
| `ground_truth/all6_r1000_psc_vs_tritr_a0_20261009/` | GT-PSC 对 GT-TriTR（α = 0），6 × 4 × 1000 |
| `ground_truth/all6_r1000_tritr_a5_20261009/`、`all6_r1000_tritr_a150_20261009/` | GT-TriTR，α = 5、150 |
| `ground_truth/all6_r1000_tritr_a0_nambudget_20261009/` | GT-TriTR，α = 0，NAM-DPRD 的 0.1/0.45/0.45 预算拆分 |
| `ground_truth/all6_r1000_continuous_bound_20261009/` | 候选机制 `continuous_bound` |
| `ground_truth/gt_kstar_r1000_adaptive_2star_20261002/` | 候选机制 `adaptive_2star` |
| `ground_truth/gt_kstar_eps2_*_floor_tight_20261002/` | k-star 的 ε2/ε3 拆分扫描（4 组） |
| `ground_truth/cudo_gtpsc_r1000_diagnosis/` | CU/Do k-star GT-PSC 诊断，1000 次 |
| `ground_truth/cudo_gtpsc_r10_floor_tight/`、`gt_cudo_r10_20260929/` | CU/Do 10 次 GT，带 trace，用于和智能体运行对照 |

## 机制对齐、审计与资料

| 目录 | 内容 |
|---|---|
| `alignment/profiles_20260929/`、`profiles_20261002_adaptive/` | k-star 候选机制的六图比较与独立随机流确认（`scripts/align_gt_psc.py`） |
| `audit/2026-09-28/`、`audit/2026-10-02/` | 离线诊断脚本和输出，对应 `docs/PSC_REPRODUCTION_REPORT.md` 第三、四部分 |
| （已移出）`audit/sensitivity/`、`audit/2026-10-17/` | 灵敏度审计与断裂点算例属于开题研究，现位于 `../psc-trust/results/audit/` |
| `research/2026-09-28-author-implementation/` | 作者实现检索记录和上游 Imola et al. 源码，对应 `docs/PSC_REPRODUCTION_REPORT.md` §28、§29、§32 |

## archive：不再作为证据使用

保持原来的 `<实验>/<标签>/` 结构，只是移到了 `archive/` 下。

| 目录 | 归档原因 |
|---|---|
| `archive/exp1/dsv3-0324_exp1_all6_r10_floor_tight_Naive{,_paperprompt}/` | 跑在答案解析器修复之前，个别格子是解析错误（如把邻居列表拼成一个大数） |
| `archive/exp1/hy3-curator_dsv3-node_exp1_CU_r1_floor_tight_{smoke,statevar}/` | 单次调试，用于定位节点 prompt 的状态变量名问题（修复前 degree 节点 17/49 正确，修复后 49/49） |
| `archive/exp1/mock/`、`mock_err10/`，`archive/exp2…exp6/mock/` | `legacy` 机制下的 mock 结果 |
| `archive/exp1…exp6/qwen3-8b+32b_*/`、`archive/pilot/qwen3-8b+32b_smoke/` | Qwen3-8B node + Qwen3-32B curator（关闭思考），跑在解析器和状态变量名修复之前；Naive 答案多为与图无关的占位数，triangle 节点正确率接近 0；exp6 未跑完 |
| `archive/pilot/hy3-ioa_r3/`、`hy3-ioa_r3_v2/`、`hy3-ioa_fixcheck/`、`openai_hy3-ioa/`、`smoke/`、`mock_dryrun/` | `floor_tight` 之前的早期 pilot；`hy3-ioa_r3_v2` 是两份 9 月 28 日审计文档的依据 |
| `archive/ground_truth/table2/`、`exp2/` | `legacy` 机制的 1000 次 GT；degree、triangle 与当前相同，k-star 不同 |
