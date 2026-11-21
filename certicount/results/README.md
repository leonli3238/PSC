# CertiCount 实验结果

整理日期：2026-11-21。本目录已完成实体清理和归并，不再使用导航软链接；根目录只保留本索引与分类目录。实验内部的原始记录、结果数值和历史 manifest 未改写。

## 目录分类

| 目录 | 内容 |
|---|---|
| [`reports/`](reports/) | 跨实验汇总：CS4/5、CS6、CS7；`sensitivity/` 下为探测联合报告 |
| [`dsl_eval/`](dsl_eval/) | LLM 程序设计评估、离线草稿回放；认证消融随所属实验保留 |
| [`evolve/`](evolve/) | 提示词自进化训练、最佳提示词与进化轨迹 |
| [`execution/`](execution/) | 机制/执行对比、纯代码基线、α 扫描与选择记录 |
| [`evaluation/`](evaluation/) | PSC 机制误差与执行误差分解，与执行对比区分存放 |
| [`dsl/`](dsl/) | 推导器验证、fuzz 与证伪对拍 |
| [`audit/`](audit/) | 敏感性审计、Qwen 探测及程序负对照原始数据；已合并原 `qwen/` 的独有数据 |
| [`attacks/`](attacks/) | 攻击与防御实验、诚实运行代价 |
| [`cost/`](cost/) | 调用数、token 与成本分析 |
| [`composite/`](composite/) | 组合查询、计划与预算账本 |
| [`logs/`](logs/) | 命令日志、离线回放日志、CS8 服务及后台执行日志 |
| [`cs8_state/`](cs8_state/) | 驱动控制状态，不是统计结果；保留原路径 |

每个实验只保留一个实体位置。阶段名仍是 `CS0`—`CS8`，目录名对应原 tag；执行对比、设计评估、自进化训练等不同用途不混成同一统计表。

## 常用汇总

- [CS4/5：在线检查、自进化及留出评估](reports/cs45_summary.md)
- [CS6：提示词 core、推导器、重启/选择及再进化](reports/cs6_summary.md)
- [CS7：per-node 模拟选择与 own-row 消融](reports/cs7_summary.md)
- [Qwen 探测联合报告](reports/sensitivity/probe_pm_degree_report/report.md)
- [程序对照联合报告](reports/sensitivity/probe_pm_degree_report_certicount/report.md)

## 当前 CS8 结果

| 实验 | 覆盖范围 | 结果表 |
|---|---|---|
| 纯代码基线 | PM/CU/Do/ML/CS/EE × degree、2-star、3-star、triangle；每格每模式 1000 次 | [执行对比](execution/cs8_code_all6_r1000/table.md) |
| PSC 误差分解 | 合并 CS1、CS8 的 PSC 原始运行；`keep_failed=false` | [误差分解](evaluation/cs8_psc_decomposition/table.md) |
| PM 设计扩展 | degree、2-star；每任务 20 个独立设计 | [PM](dsl_eval/cs8_node_v1alt_sim_pm_deg2star/table.md) |
| CU/Do 设计扩展 | degree、2-star、3-star；每格 20 个独立设计 | [CU/Do](dsl_eval/cs8_node_v1alt_sim_cudo_3tasks/table.md) |
| ML/CS/EE 设计扩展 | degree、2-star、3-star、triangle；每格 20 个独立设计 | [ML/CS/EE](dsl_eval/cs8_node_v1alt_sim_mlcsee/table.md) |

三个设计扩展组均采用 Qwen3-8B、`v1-alt`、per-node、α=5、ε=2、模拟评分选择，每个接受设计运行 100 次。PM 的其他任务及 CU/Do 的 triangle 需关联 CS7；CS8 的模拟搜索结果不是提示词自进化的独立收益。

PSC 原始运行仍位于相邻项目的 [PSC `exp1` 目录](../../psc/results/exp1/)，未在本次整理中移动或删除。误差分解排除了失败运行，应同时检查原始失败率。

### 自进化对照

- 训练：[`CS5 PSC`](evolve/cs5_evolve_psc/table.md)、[`CS5 node`](evolve/cs5_evolve_node/table.md)、[`CS6c PSC`](evolve/cs6c_evolve_psc/table.md)。
- 最新同配置评估：[`CS6c 自进化`](dsl_eval/cs6c_psc_evolved-r4-mings/table.md) 与 [`CS6c 未进化`](dsl_eval/cs6c_psc_v1-r4-mings/table.md)，均为四重启、`min_gs` 选择。
- 当前观察是设计成本改善而非稳定精度提升；早期退化、失败设计与重复实验均保留。

## 本次删除范围

以下 8 组实验已永久删除，共 49 个文件。依据是对应方法或流程已退役、没有现行读取依赖，不是根据日期、模型名称或实验效果筛选。

| 已删除目录 | 原因 |
|---|---|
| `adaptive/adaptive_r1000_20261104/` | 自拟自适应方法的代码、运行脚本与测试已删除 |
| `pool/pool_glm52_design_20261105/` | 已退役的程序池设计 |
| `pool/pool_glm52_r200_20261105/` | 上述程序池的评估 |
| `execution/p5_cu_do_r10/` | 使用旧 adaptive 模式和旧程序池 |
| `execution/p5_cu_do_glm52/` | 使用旧 adaptive 模式和旧程序池 |
| `execution/p5_new_arch_design_glm52/` | 使用已删除的在线程序池设计模式 |
| `audit/sensitivity/_mock_err0.0/` | 已替换的 plug-in 筛查/追加采样流程的 mock 验证 |
| `audit/sensitivity/_mock_err0.05/` | 同上；当前审计测试自行生成独立样本 |

退役依据见项目 `README.md` 的自适应/程序池与审计说明。旧研究笔记中的相关数值属于历史记录，不代表对应结果目录仍存在。

## 实际归并与去重

| 原位置 | 当前实体位置或处理 |
|---|---|
| 根目录 `cs45_summary.md`、`cs6_summary.md`、`cs7_summary.md` | `reports/` 下同名文件 |
| 根目录 7 个 `*.log` | `logs/` 下同名文件；未截断日志 |
| `audit/sensitivity/probe_pm_degree_report/` | `reports/sensitivity/probe_pm_degree_report/` |
| `audit/sensitivity/probe_pm_degree_report_certicount/` | `reports/sensitivity/probe_pm_degree_report_certicount/` |
| `qwen/probe_pm_degree_certicount-program/` | `audit/sensitivity/probe_pm_degree_certicount-program/`，完整保留程序负对照 |
| `qwen/` 两模型目录的不同 `server.jsonl` | 对应 `audit/sensitivity/probe_pm_degree_qwen3-{1.7b,8b}/server_qwen_snapshot.jsonl`，两份不同快照均保留 |
| `qwen/` 两模型目录、`raw_probe_pm_degree_1.7b_8b/`、`tables/` 中其他文件 | 178 个文件与原审计记录逐文件 SHA-256 一致，删除重复副本；联合报告改存上方报告目录 |
| 上次创建的 `by_stage/` 与报告/日志导航 | 移除全部 68 个软链接，`by_stage/` 已删除 |

实际迁移 46 个保留文件，移除的退役结果与重复副本合计 475,780,964 字节（约 453.74 MiB 文件内容）。迁移前后校验了全部保留文件的内容一致性；本次只更新索引与路径相关代码，没有重跑模型实验或重写已有统计报告。

## 保留与复现边界

- CS0—CS8、α 选择 JSON、最佳提示词、原始 JSONL、认证消融、失败/反例、重启和选择对照均保留。`r2`、`repeat3`、`alt`、`legacy`、`noown` 是试验臂，不是冗余文件。
- A2/A3、[A3 部分运行](dsl_eval/A3_pm_design_8bthink_d10_partial12calls/)、P1 真实试点、P4 mock、nodebound 扫描及程序负对照仍有验证价值；A3 缺最终汇总的记录不纳入完整结果比较，但不删除原始草稿。
- [`glm_dsl_cu_do_v2`](execution/glm_dsl_cu_do_v2/) 与 [`glm_methods_cu_do`](execution/glm_methods_cu_do/) 中的原始和 `*_rebuilt` 结果保留修正链，不能互相覆盖。
- `manifest.json` 保留历史设置、来源和旧路径；创建时间不是完成时间，源码哈希不是结果文件校验和。旧 Qwen 路径按上方迁移表解释。
- 区分独立设计数与每程序噪声重复数；精度通常只统计接受设计，必须一起看接受率。未发现证伪反例不等同于完整隐私证明。
- `audit/` 内的 `plan.json`、`samples.jsonl`、服务器记录等可能含真实邻居表与输入；只放在可信存储中，不整体发布。

## 后续输出约定

原始实验仍使用 `results/<kind>/<tag>/`，既有核心实验路径不变，避免破坏回放和完成状态判断。三个阶段汇总脚本默认输出到 `results/reports/`，CSCWD/CS8 驱动日志输出到 `results/logs/`；`scripts/probe_h20.sh` 的跨模型报告默认输出到 `results/reports/sensitivity/`，可通过 `REPORTS` 指定其他报告根目录。不要重新复制 Qwen 原始目录或恢复软链接导航。
