# PSC：LLM 多智能体边 LDP 子结构计数

仓库分为两个独立项目，共用根目录的虚拟环境 `.venv`（`python3 -m venv .venv && .venv/bin/pip install -r psc/requirements.txt`）：

| 目录 | 项目 | 内容 | 说明 |
|---|---|---|---|
| [`psc/`](psc/README.md) | PSC 复现 | 论文 *Agent-based Substructure Counting under Local Differential Privacy*（ACL 2026）的复现：Naive、PSC（Alg. 1–3）、GT-Naive / GT-PSC / GT-PSC-B、TriTR 对照、Exp1–Exp6，以及全部复现结果、复现档案与模型配置（`config.toml` / `.env`） | 冻结基线；`psc` 包（原目录名 `psc-reproduction`） |
| [`certicount/`](certicount/README.md) | **CertiCount** | 开题课题《执行可信性：灵敏度审计与可验证执行》：LLM 设计 DSL 程序、系统推导 GS 并认证、节点解释执行的可验证计数方法及其评估（对比 Naive / PSC、LLM 设计误差），以及误差分解、灵敏度审计、三元绑定与消息校验、攻击实验、代码守卫、成本与复合查询 | 新项目；`certicount` 包，依赖 `psc` |

开题报告、答辩讲稿与研究笔记在 `certicount/docs/`；复现档案在 `psc/docs/PSC_REPRODUCTION_REPORT.md`。

```bash
cd psc && ../.venv/bin/python -m pytest tests -q         # 复现
cd certicount && ../.venv/bin/python -m pytest tests -q   # CertiCount（全部离线）
```
