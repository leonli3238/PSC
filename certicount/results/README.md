# CertiCount 结果目录

每个目录含 `summary.json`、`table.md`、`manifest.json`（设置与 certicount / psc 源码哈希）；目录名即 `--tag`，已存在则拒绝覆盖。
除 `audit/sensitivity/p1_cu_gpt41mini` 外均为离线运行（mock 或纯代码），不涉及付费 API。

| 目录 | 内容 |
|---|---|
| `dsl/dsl_check_20261024/` | 改进二验收：7 个程序 × 5 个 D 的推导 GS 与手工 GS、事实消融、证伪器（对称穷举 / 非对称采样）、效用测试、mock 设计循环（首稿故意不投影） |
| `dsl/dsl_fuzz_20261103/` | 推导器对拍：1 万个随机程序，n = 5、dmax = 3 全部对称图与 n = 7、dmax = 4 的 200 张随机图，0 个反例、0 个运行错误；`table.md` 末尾为最松的 10 个界 |
| `adaptive/adaptive_r1000_20261104/` | （历史记录，方法已删除）先发度数的自适应选择：6 图 × {2-star, 3-star, triangle} × 1000 次，默认 / 自适应（有无 margin）/ GT-Tuned / 静态与逐次最优 / GT-PSC / GT-TriTR；`runs.jsonl` 为逐次结果（含每个静态候选的误差） |
| `pool/pool_glm52_design_20261105/` | （历史记录，方法已删除）GLM-5.2 设计程序池：4 任务 × 3 次调用（12 次请求）；`pools.json` 为各设计者（hand / llm / random）的池，`designs.jsonl` 为每个提议及其闸门结果与公开得分，`transcripts.jsonl` 为全部提示词与回复（只含公开信息） |
| `pool/pool_glm52_r200_20261105/` | （历史记录）上述池的纯代码评估（复用设计，0 次调用）：6 图 × 4 任务 × 200 次，默认 / 各池自适应 / 逐次最优 / GT-TriTR |
| `attacks/p5_cu_ee_r10/` | P5：CU、EE × 四类攻击 × 未防御 / 防御，各 10 次；诚实运行的防御代价 |
| `execution/p4_mock_err005_cu_ee_r10/` | P4：CU、EE × degree / 3-star / triangle / 4-star / 度二阶矩 × 五种执行方式，mock 节点 5% ±1 错误，同噪声配对，10 次；`runs.jsonl` 为逐次结果 |
| `execution/nodebound_smoke/`、`nodebound_alpha{2,5,10}/` | 逐节点度界（edge clipping，Imola et al. 2022）小测试：CU、Do × 2/3/4-star、triangle × 200 次，GT-PSC / GT-DSL / GT-DSL-node（α = 0, 2, 5, 10） |
| `execution/cu_3star_dsl/` | CU 3-star 的 DSL（program 模式，mock 设计器）10 次 |
| `execution/<tag>/`（`run_execution_compare.py` 新版） | DSL 评估目标一：GT-Naive / Naive / GT-PSC / PSC / GT-DSL / DSL 对比；`table.md` 含 Goal 1、Goal 2（与 GT-DSL 配对）与明细三张表 |
| `dsl_eval/<tag>/`（`run_dsl_design_eval.py`） | DSL 评估目标二：每任务多次独立设计的质量（接受率、GS 比、预算拆分、独立语义测试、证伪）与同噪声配对的设计误差；`designs.jsonl`、`runs.jsonl` 为逐设计 / 逐次结果 |
| `evaluation/exp1_decomposition_20261024/` | 内容一：复现项目 `results/exp1` 全部 31 个目录、225 个格子的机制 / 执行误差分解与置信区间覆盖率 |
| `cost/cost_cu_gpt41mini/` | 内容五：gpt-4.1-mini 节点 + gpt-4.1 curator（CU）各阶段调用与 token；五个数据集上各执行方式的调用模型 |
| `composite/composite_cu_ee_r100/` | 内容六：聚类系数、degree + 3-star、星形轮廓三个计划，100 次；账本 |
| `audit/sensitivity/p1_cu_gpt41mini/` | （旧审计流程：代入损失筛查 + 追加采样，已替换）审计 P1 试点（CU，gpt-4.1-mini，1020 个相邻对），见研究笔记 §7；`sources` 中的绝对路径是拆分前的旧位置 |
| `audit/sensitivity/_mock_err0.0/`、`_mock_err0.05/` | （旧审计流程）审计管线的 mock 验证（误差 0 / 5%） |
| `audit/2026-10-17/` | 断裂点算例与证伪的离线脚本（`falsify.py`、`examples.py`、`guess.py`、`dmax_below_true.py`、`llm_error_cases.py`） |

`audit/` 下的 `plan.json`、`samples.jsonl` 含真实邻居表，只能放在可信存储中。
