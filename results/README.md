# 结果目录索引

实验脚本把结果写到 `results/<实验>/<标签>/`。每个运行目录里有 `manifest.json`（配置与源码/数据哈希）、
`runs.jsonl`（逐次结果，含同噪声规则值 `extra.validation`）、`summary.json`、`table.md`，真实 API 运行另有
`errors.jsonl` 与 `run.log`，带 `--save-transcripts` 的还有 `transcripts.jsonl`。`runs.json` 不入库。

除特别说明外，下面都是 `floor_tight` 机制、ε = 2、seed = 0；第 i 次运行的 DP 噪声只由 `(seed, i)` 决定，
所以同一 seed 的不同模型面对的是同一批噪声。

## exp1：论文 Table 2

| 目录 | 内容 |
|---|---|
| `exp1/table2.md`、`table2.json` | **Exp1 汇总表**，由 `scripts/build_exp1_table.py` 从下面几个目录生成 |
| `exp1/dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0/` | **主结果**：node、curator 均为 DeepSeek-V3；Naive、PSC、TriTR（α = 0）；CU–EE × degree/3-star/triangle × 10 次；附 GT-PSC、GT-TriTR |
| `exp1/hy3_exp1_r10_5ds/` | **主结果**：node、curator 均为 hy3-ioa；Naive、PSC；CU–EE；从 `hy3_exp1_r10/` 中取出这 5 个数据集（`merge.json`）。PM 行由汇总脚本另从下面两个目录读取 |
| `exp1/hy3_exp1_r10/` | hy3 的原始运行，含 PM 的 degree 与 Naive triangle；Naive 有 13 次运行调用重试耗尽 |
| `exp1/hy3_exp1_pm_rest/` | hy3 的 PM 补跑，未完成：PSC triangle 只有 7 次，Naive 3-star 10 次全部调用失败 |
| `exp1/dsv3-0324_exp1_CU_degree-3star_r100_floor_tight_PSC/` | DeepSeek-V3-0324 在 CU 上的 PSC，degree/3-star 各 100 次，带逐调用 transcripts |
| `exp1/dsv3-1226_exp1_all6_r10_floor_tight_Naive/` | DeepSeek-V3 的 Naive，6 个数据集，默认 prompt |
| `exp1/dsv3-1226_exp1_all6_r10_floor_tight_Naive_paperprompt/` | 同上，`--naive-prompt paper`（只发论文附录的 prompt） |
| `exp1/hy3-ioa_exp1_CU-Do_r10_floor_tight_TriTR-a0/` | hy3-ioa 的智能体版 TriTR，CU/Do |

## pilot：CU/Do 四任务（含 2-star）

| 目录 | 内容 |
|---|---|
| `pilot/hy3-ioa_cudo_r10_floor_tight/` | hy3-ioa，Naive/PSC × 10；Do triangle Naive 有 1 次调用重试耗尽 |
| `pilot/hy4-preview-ioa_cudo_r10_floor_tight/` | hy4-preview-ioa，同上 |
| `pilot/mock_cudo_r10_20260929/` | mock（完美推理器），流程验证，见 `docs/RUN_CUDO_10.md` |
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
| `audit/2026-09-28/`、`audit/2026-10-02/` | 离线诊断脚本和输出，对应 `docs/AUDIT_2026-09-28.md`、`docs/KSTAR_DIAGNOSIS_2026-09-28.md` |
| `research/2026-09-28-author-implementation/` | 作者实现检索记录和上游 Imola et al. 源码，对应 `docs/PSC_SOURCE_RESEARCH_2026-09-28.md` |

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
