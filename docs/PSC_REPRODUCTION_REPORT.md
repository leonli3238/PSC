# PSC 复现：方法、审计、k-star 诊断与工作计划（整合版）

> 本文整合了 2026-09-28 至 2026-09-30 期间的 9 份文档，删除重复叙述，相互矛盾或已过时的结论按时间先后标注。原文档与本文章节对应如下：
>
> | 原文档 | 并入位置 |
> |---|---|
> | `PSC_METHODS_ANALYSIS.md` | 第一部分（方法）、§16 结果、§36 局限、附录 B 代码索引 |
> | `AUDIT_2026-09-28.md` | §16.3 legacy pilot、第三部分（审计发现）、§30 EE triangle、第六部分优先级表 |
> | `KSTAR_DIAGNOSIS_2026-09-28.md` | 第四部分 §21–§27 |
> | `PSC_SOURCE_RESEARCH_2026-09-28.md` | §28 上游源码、§29 机制族下界、§32 作者实现检索、第五部分 |
> | `PSC_CAUSES_AND_SOLUTIONS_2026-09-28.md` | §24 原因归纳、第五部分（落点与评估） |
> | `GTPSC_PAPER_ALIGNMENT_PLAN_2026-09-28.md` | §14 候选选择、§26 PSC-B 约束、§33 对齐原则 |
> | `EXECUTION_PLAN_2026-09-28.md` | 第六部分（四阶段计划） |
> | `RUN_CUDO_10.md` | 第七部分（运行说明） |
> | `PSC_AUTHOR_INQUIRY_DRAFT.md` | 附录 A（原文保留） |
>
> **时间口径**：
>
> - 第一部分按 2026-09-30 的代码整理，`文件:行号` 以该版本为准，之后可能偏移；
> - 第三、四部分的诊断写于 2026-09-28，当时默认机制是 `legacy`（ceil 取整 + $\binom{D}{k-1}$）；2026-09-29 起默认改为 `floor_tight`（§14）；
> - 之后新增的 TriTR、`adaptive_2star`、Naive+Code、`--naive-prompt`、`--save-transcripts` 等功能不在本文范围内，见 `README.md`；
> - 第六部分计划项的“当前状态”列是 2026-10-15 按代码核对的结果。

---

## 目录

**第一部分 方法**

1. [项目概览](#1-项目概览)
2. [问题设定：ε-edge LDP 下的子结构计数](#2-问题设定ε-edge-ldp-下的子结构计数)
3. [差分隐私原语](#3-差分隐私原语pscdppy)
4. [灵敏度与机制配置](#4-灵敏度与机制配置)
5. [分布式算法库与规则语义](#5-分布式算法库与规则语义)
6. [三类智能体](#6-三类智能体pscagents)
7. [框架编排](#7-框架编排pscframeworkpy)
8. [对照与基线方法](#8-对照与基线方法)
9. [Prompt 设计与回复解析](#9-prompt-设计与回复解析pscpromptspy)
10. [离线 Mock 模型](#10-离线-mock-模型pscmock_modelpy)
11. [LLM 执行正确性验证：同噪声回放](#11-llm-执行正确性验证同噪声回放)
12. [模型接入、重试与错误记录](#12-模型接入重试与错误记录)
13. [实验体系、随机数与统计方法](#13-实验体系随机数与统计方法)
14. [k-star 机制对齐与 floor_tight 的选定](#14-k-star-机制对齐与-floor_tight-的选定)
15. [隐私性分析与信任边界](#15-隐私性分析与信任边界)

**第二部分 复现结果**

16. [当前复现结果](#16-当前复现结果)

**第三部分 审计发现**

17. [论文自身未规定或不一致的细节](#17-论文自身未规定或不一致的细节)
18. [Agent 能力的验证范围](#18-agent-能力的验证范围)
19. [评估、解析与可追溯性问题](#19-评估解析与可追溯性问题)
20. [隐私信任边界尚未落实为部署保证](#20-隐私信任边界尚未落实为部署保证)

**第四部分 k-star 与 triangle 差距诊断**

21. [三种比较对象](#21-三种比较对象)
22. [legacy k-star 机制与 pilot 大误差的来源](#22-legacy-k-star-机制与-pilot-大误差的来源)
23. [长期差距：5 万次独立对照](#23-长期差距5-万次独立对照)
24. [误差来源归纳](#24-误差来源归纳)
25. [取整、灵敏度、预算、投影、截断的消融](#25-取整灵敏度预算投影截断的消融)
26. [GT-Naive 与 GT-PSC-B 的表格约束](#26-gt-naive-与-gt-psc-b-的表格约束)
27. [固定 D 为真实最大度的反事实](#27-固定-d-为真实最大度的反事实)
28. [与上游 Imola 2021 源码的对照](#28-与上游-imola-2021-源码的对照)
29. [机制族的理想下界](#29-机制族的理想下界)
30. [EE triangle 的局部差距](#30-ee-triangle-的局部差距)
31. [诊断结论](#31-诊断结论)
32. [作者实现检索](#32-作者实现检索)
33. [贴近论文时的选择原则](#33-贴近论文时的选择原则)

**第五部分 改进方案**

34. [带噪度数 + 组合数矩校正估计器](#34-带噪度数--组合数矩校正估计器)

**第六部分 工作计划**

35. [四阶段执行计划](#35-四阶段执行计划)

**第七部分 运行说明与局限**

36. [CU / Do 每项 10 次的运行说明](#36-cu--do-每项-10-次的运行说明)
37. [局限与未实现内容](#37-局限与未实现内容)

**附录**

- [附录 A 作者询问信草稿](#附录-a-作者询问信草稿未发送)
- [附录 B 方法—代码索引](#附录-b-方法代码索引)
- [附录 C 诊断产物与复现命令](#附录-c-诊断产物与复现命令)

---

# 第一部分 方法

## 1. 项目概览

本项目复现 ACL 2026 论文 *Agent-based Substructure Counting under Local Differential Privacy*（2026.acl-long.1032），基于 **AgentScope 1.0** 实现多智能体框架。核心思想：

- 不可信的 **Curator（策展人）LLM** 只看到节点集合与问题 $(V(G), Q)$，看不到边；
- 每个节点由一个 **Node Agent（节点智能体）** 管理其真实邻居表（位于“可信本地服务器”）；
- **Privacy Controller（隐私控制器）** 以**代码**执行全部 DP 机制（RR、Laplace、图投影、预算拆分），不依赖 LLM 遵守指令；
- LLM 只负责：识别任务/设计算法、节点级 send/update 推理、结果聚合。

整体数据流：

```text
Analyst prompt (V(G), Q)
        │
        ▼
PrivacyController ──(LLM: 选 DP 框架)──► 预算拆分 ε1/ε2/ε3、灵敏度 GS_f
        │                                     │
        │ ε1: RR 噪声图 (Alg.1, 代码)          │ ε2: 带噪最大度 + 图投影 (Alg.2, 代码)
        ▼                                     ▼
NodeAgents: noisy_neighbors  ◄──────────  d̂max / 投影后的 G′ 或 本地邻居表
        │
Curator ──(LLM: 从算法库选 send/update/aggregate 规则)
        │
NodeAgents ──(LLM: send, 仅读噪声邻居)──► fanout_pipeline + observe 定向投递
NodeAgents ──(LLM: update, 读真实邻居 + 收到的消息)──► 本地计数 c_i
        │
PrivacyController ── ε3: c_i + Lap(GS_f/ε3) (代码)
        │
Curator ──(LLM: 按聚合规则求和/除 n/除 3，负数截断为 0)──► 估计值 f̂
```

项目同时实现了：纯 Python 的 GT-Naive / GT-PSC / GT-PSC-B、Naive 基线、附录 B 的 RAW / REFINED 单 LLM 基线、离线“完美 LLM” Mock、逐步验证、机制候选对齐与完整实验脚本（Exp1–Exp6 + pilot）。

## 2. 问题设定：ε-edge LDP 下的子结构计数

### 2.1 隐私模型

论文 Definition 1：对任意节点 $v_i$，随机算法 $R_i$ 作用于其邻居向量 $A_i\in\{0,1\}^n$。若对任意仅差一位的 $A_i, A_i'$ 和任意输出集合 $S$ 满足

$$\Pr[R_i(A_i)\in S] \le e^{\varepsilon}\Pr[R_i(A_i')\in S],$$

则 $R_i$ 满足 ε-edge LDP，即保护“单条边是否存在”。Curator 不可信，每个用户的连接存放在可信本地服务器。

### 2.2 四类任务（`psc/graph.py:30`）

| 任务 | 真值定义 | 代码 |
|---|---|---|
| degree | 平均度 $2m/n$ | `Graph.average_degree` |
| 2-star | $\sum_i \binom{d_i}{2}$ | `Graph.count_kstars(2)` |
| 3-star | $\sum_i \binom{d_i}{3}$ | `Graph.count_kstars(3)` |
| triangle | 三角形数 | `Graph.count_triangles` |

三角形精确计数（`psc/graph.py:190`）：$n\le 300$ 用局部计数 $t(u)=\frac12\sum_{v\in N(u)}|N(u)\cap N(v)|$，全局 $=\frac13\sum_u t(u)$；$n>300$（PM）用 $\frac16\mathrm{tr}(A^3)$，`np.einsum` 计算。

### 2.3 数据集与统一格式（`scripts/prepare_datasets.py`）

| 缩写 | 名称 | \|V\| | \|E\| | 来源 |
|---|---|---|---|---|
| CU | Contiguous USA | 49 | 107 | KONECT |
| Do | Dolphins | 62 | 159 | KONECT |
| ML | Les Misérables | 77 | 254 | networkx 内置 |
| CS | Ca-sandi_auths | 86 | 124 | Network Repository |
| EE | Email-enron-only | 143 | 623 | Network Repository |
| PM | C. elegans metabolic | 453 | 2025 | KONECT |

六张图的节点数、边数与论文 Table 1 一致，任务真值与当前图的精确计数一致。预处理：

- 解析 KONECT `out.*` 与 MatrixMarket `.mtx`（跳过注释和 `n n m` 头行）；
- `relabel_edges`：原始 id 排序映射为 `0..n-1`，去自环、去重、无向化；
- `build_records`：每个数据集生成 4 条附录 A 格式记录（`index / input_prompt / edges / vertex_num / edge_num / answer / task / dataset`）。

`task_prompt`（`psc/graph.py:76`）拼接“任务定义 + LDP 声明 + `Q: The nodes are numbered from 0 to n-1. <问题>`”，保证 Curator 只拿到 $(V(G),Q)$；`ldp=False` 时去掉 LDP 声明，用于无 DP 版本。

### 2.4 评价指标：相对误差（`psc/ground_truth.py:137`）

$$\mathrm{RE}=\frac{|\hat f(G)-f(G)|}{\max\big(f(G),\ \eta\big)},\quad \eta=0.001n$$

RE 越小越好，不是准确率。实验层还计算平均值、标准误、中位数、P95、与论文值的相对差和 log 差（§13.4）。

## 3. 差分隐私原语（`psc/dp.py`）

所有原语都是**纯代码**，从不交给 LLM 执行（论文 Challenge 1）。

### 3.1 Warner 随机响应（RR，Algorithm 1 `BuildNoisyGraph`）

- 翻转概率（`dp.py:31`）：$p=\frac{1}{1+e^{\varepsilon}}$，$\varepsilon>700$ 时直接返回 0 防溢出。
- **只扰动下三角**（`node_noisy_lower_row`，`dp.py:49`）：节点 $i$ 只对 $a_{i,j}\ (j<i)$ 做 RR，每条潜在边只被一个端点扰动一次，避免同一边消耗两次预算或出现不一致。
- 合并：`PrivacyController.build_noisy_graph` 收集所有节点发布的 $(i,j)$，用 `Graph.from_edges` 对称化得到 $G'$，再写入各节点 `noisy_neighbors`。
- 向量化等价实现（`dp.py:71`）：GT 版本一次生成 $n\times n$ 均匀随机矩阵，取严格下三角掩码，`noisy_lower | noisy_lower.T` 恢复对称邻接。

**RR 的密度问题（Challenge 2）**：CU、$\varepsilon=2$ 时 $p\approx0.119$，1069 个非边中约 127 个被翻成边，107 条真边保留约 94 条，噪声图边数约为原图 2 倍，k-star/三角形被严重高估。这是 Naive 误差大的来源。

### 3.2 Laplace 机制（Definition 3）

`laplace_noise(sensitivity, eps, rng)`（`dp.py:91`）采样 $\mathrm{Lap}(0,\ GS_f/\varepsilon)$；非正/非有限预算或负灵敏度报错（允许灵敏度为 0）。`laplace_mechanism` 返回 $x+\mathrm{Lap}(GS_f/\varepsilon)$。PSC 中用于：

1. 带噪度数：$\tilde d_i=d_i+\mathrm{Lap}(1/\varepsilon_2)$（度的灵敏度为 1）；
2. 本地计数上报：$\tilde c_i=c_i+\mathrm{Lap}(GS_f/\varepsilon_3)$。

固定灵敏度时，$n$ 个独立 Laplace 报告之和的标准差为 $\sqrt{2n}\,GS/\varepsilon_3$；degree 再除 $n$，triangle 再除 3，k-star 直接求和。

### 3.3 全局灵敏度优化 GSOptimize（Algorithm 2）

针对 Challenge 3：不限制度数时三角形灵敏度为 $n-2$、3-star 为 $\binom{n-2}{2}$，噪声过大。

1. **带噪最大度**：每个节点上报 $\tilde d_i$，控制器取 $\max_i \tilde d_i$，按机制配置取整得投影阈值 $\hat d_{\max}$（§4）。
2. **图投影 `graph_projection`**（`dp.py:130`，三角形，作用于噪声图）：按随机排列遍历节点；度数 $>\hat d_{\max}$ 时随机保留 $\hat d_{\max}$ 个邻居；**对称删边**，保证仍是无向简单图且所有度 $\le\hat d_{\max}$。
3. **本地邻居表投影 `project_neighbor_list`**（`dp.py:151`，k-star，无噪声图）：节点在真实邻居表中随机保留至多 $\hat d_{\max}$ 个，与 Imola et al. 2021 的 k-star 算法一致。

### 3.4 预算分配（Section 4.1，`split_budget`，`dp.py:183`）

默认 $r_1=0.5,\ r_2=0.2$：$\varepsilon_1=r_1\varepsilon,\ \varepsilon_2=r_2(\varepsilon-\varepsilon_1),\ \varepsilon_3=\varepsilon-\varepsilon_1-\varepsilon_2$。不需要的步骤置 0，剩余比例保持不变（论文第 6 页）：

| 任务 | 需噪声图 | 需 GS 优化 | $\varepsilon=2$ 时 $(\varepsilon_1,\varepsilon_2,\varepsilon_3)$ |
|---|---|---|---|
| degree | 否 | 否 | (0, 0, 2.0) |
| 2-star / 3-star | 否 | 是 | (0, 0.4, 1.6) |
| triangle | 是 | 是 | (1.0, 0.2, 0.8) |
| triangle（PSC-B） | 是 | 否 | (1.0, 0, 1.0) |
| k-star（PSC-B） | 否 | 否 | (0, 0, 2.0) |
| Naive | 全部给 RR | — | (2.0, 0, 0) |

参数校验：$\varepsilon$ 须有限且为正，$r_1,r_2\in[0,1)$，需要某步骤时对应比例必须 $>0$。

## 4. 灵敏度与机制配置

### 4.1 DP 框架库（`psc/library.py:182`）

`DPFrameworkSpec` 描述每个任务的灵敏度文本、是否需要噪声图、是否可做 GS 优化以及灵敏度函数。它既是隐私控制器 LLM 查询的“库”（`dp_library_summary()`），也是代码实际使用的参数来源。

| 任务 | 灵敏度（有 GS 优化） | 无优化（PSC-B） |
|---|---|---|
| degree | 1 | 1 |
| 2-star | 由机制配置决定（默认 $\binom{D-1}{1}=D-1$） | 默认 $n-2$ |
| 3-star | 由机制配置决定（默认 $\binom{D-1}{2}$） | 默认 $\binom{n-2}{2}$ |
| triangle | $\max(1,\ \hat d_{\max}-1)$（附录 E “degree−1”） | $n-2$ |

三角形下界取 1，保证 $\hat d_{\max}\le1$ 时 Laplace 尺度仍为正。

### 4.2 k-star 机制配置（`psc/mechanism.py`）

论文对 k-star 的取整和灵敏度没有唯一说明，项目把可能的解释显式化为 `MechanismProfile`，GT 与 Agent 共用同一配置：

| 配置 | 取整 | GS 模式 | 物理上限 $[0,n-1]$ | 无优化基准 | 依据 |
|---|---|---|---|---|---|
| `legacy` | ceil | bound：$\binom{D}{k-1}$ | 否 | $n$ → $\binom{n}{k-1}$ | 原始实现；PSC 论文第 3 页写法 |
| `floor_bound` | floor | bound：$\binom{D}{k-1}$ | 是 | $n-1$ | Imola 2021 论文正文的整数阈值 |
| `continuous_bound` | floor 投影 | continuous：用连续最大值 $x$ 算 $x$ 或 $x(x-1)/2$ | 是 | $n-1$ | Imola 2021 C++ 源码行为（§28） |
| **`floor_tight`（默认）** | floor | tight：$\binom{D-1}{k-1}$ | 是 | $n-1$ → $\binom{n-2}{k-1}$ | 截断度计数的紧灵敏度 |

（之后又增加了 `adaptive_2star`，见 README。）

`degree_bound(reports, task)`（`mechanism.py:34`）：非 k-star 任务或 `legacy` 时 $D=\max(1,\lceil \max_i\tilde d_i\rceil)$（三角形始终走这条路径）；其他配置 $x=\min(\max(\text{raw},0),\ n-1)$，$D=\lfloor x\rfloor$；返回 `DegreeBound(raw_max, sensitivity_degree, projection_degree)`。$D<k$ 时局部计数恒为 0，紧 GS 也为 0，按确定性结果处理，不把非法组合数或负尺度传入机制。

**紧界推导**：固定公开整数 $D$，截断计数 $f_D(d)=\binom{\min(d,D)}{k}$。单比特变化最多使度数变化 1，

$$\max_d |f_D(d+1)-f_D(d)| = \binom{D}{k}-\binom{D-1}{k}=\binom{D-1}{k-1}.$$

所以论文文字中的 $\binom{D}{k-1}$ 是更松的上界（2-star 为 $D$ 对 $D-1$，3-star 为 $\binom{D}{2}$ 对 $\binom{D-1}{2}$）。`tests/test_mechanism.py::test_tight_sensitivity_is_max_single_bit_difference` 穷举验证该等式。该推导只针对理想截断计数函数，不覆盖任意错误的 LLM 输出（§20）。`floor_tight` 是“按论文公开描述 + 数学紧界选出的实现解释”，**不是已确认的作者代码**。

## 5. 分布式算法库与规则语义

### 5.1 算法库 `ALGORITHM_LIBRARY`（`psc/library.py:162`）

每个 `AlgorithmSpec` 包含 Problem / State / Message / Initialization / Send / Update / Aggregation 的自然语言规则（附录 E）。Curator LLM 从库中选条目，规则文本原样下发给节点 LLM。

| 任务 | 需要 Send | Update 规则 | Aggregate 规则 |
|---|---|---|---|
| degree | 否 | 数真实邻居个数 | $\sum c_i / n$，负数取 0 |
| k-star | 否 | $\binom{\deg}{k}$（$\deg<k$ 为 0），$\deg$ 为投影后邻居数 | $\sum c_i$，负数取 0 |
| triangle | 是 | 见下 | $\sum c_i / 3$，负数取 0 |

### 5.2 三角形两轮分布式算法（受 Imola et al. 2021/2022 启发）

- **Send**（只读噪声邻居）：节点 $j$ 构造 `{Sender_ID: j, Sender_Neighbors: N'(j)}`，发给 $N'(j)$ 中每个节点。
- **Update**（读真实邻居 + 收到的消息）：节点 $i$ 对每条消息，若 `Sender_ID` 不在 $N(i)$ 中则丢弃；否则对 $N(i)\cap$ `Sender_Neighbors` 中每个公共邻居计数 +0.5。

即 $c_i=\frac12\sum_{j\in N'(i)\cap N(i)} |N(i)\cap N'(j)|$。无噪声时每个三角形让三个节点各 +1，共 +3，所以聚合除以 3。

两种等价实现（`psc/rules.py`）：`update_triangle`（逐消息，用于 Mock 与验证）与 `triangle_local_count`（集合运算，用于 GT）。`test_triangle_update_rule_example_from_appendix_e` 验证附录 E 的例子（结果 0.5，见 §17 的原文矛盾），`test_triangle_rules_recover_exact_count_without_noise` 验证无噪声时恢复精确计数。

### 5.3 `rules.py` 的角色

`rules.py` 是规则文本的精确代码语义，被 GT 算法、Mock 模型和同噪声回放验证（§11）共享。`naive_answer(task, n, noisy_edges)` 在噪声图上精确计数，代表“完美 Curator”在 Naive 下的答案。

## 6. 三类智能体（`psc/agents/`）

三者均继承 AgentScope 的 `AgentBase`，使用 `InMemoryMemory`，实现 `observe` / `reply`。

### 6.1 NodeAgent（`node_agent.py`）

| 记忆 | 内容 | 访问者 |
|---|---|---|
| `_real_neighbors` | 真实邻居 $N_G(v_i)$，私有 | update、本地 RR、带噪度数 |
| `_update_neighbors` | update 实际使用的邻居表（k-star 下为投影后） | update |
| `noisy_neighbors` | 噪声图 $G'$ 中的邻居 | 仅 send |

本地 DP 例程（代码）：`release_noisy_edges`（Alg.1 第 2–4 行）、`report_noisy_degree`、`bound_degree`（k-star 本地投影）、`protected_count`（$c_i+\mathrm{Lap}(GS_f/\varepsilon_3)$）。

LLM 步骤：

- `_send`：以 `node_send_prompt` 调 LLM，解析 `{Sender_ID, Sender_Neighbors}`。解析失败时**不发送消息**并计 `parse_failures`，不用规则结果兜底；
- `_update`：以 `node_update_prompt` 调 LLM，优先解析 JSON `count`，再退化为“最后一个数字”，都失败则保留原计数并记录错误。

并发控制用类级 `asyncio.Semaphore`（`max_concurrency`）。`_node_id` 同时接受 `12`、`"12"`、`"Node 12"`、整数型浮点——旧版只接受数字时，`hy3-ioa_r3` 有 19 次 triangle send 因模型照抄 `"Node 13"` 被拒绝，修复后 send 正确率恢复为 333/333（§16.3）。

### 6.2 CuratorAgent（`curator_agent.py`）

- `design_algorithm`（Alg.3 第 9 行）：给出算法库摘要，LLM 返回 `{"task": ...}`；非法时用 `infer_task_from_prompt` 兜底并记录；
- `aggregate`（Alg.3 第 14 行）：给出所有节点带噪计数与聚合规则，LLM 返回 `{"result": ...}`；
- `answer_with_noisy_graph`：Naive 基线；`answer_prompt`：RAW / REFINED 基线；
- `_parse_result`：JSON `result` → 最后一个数字 → 失败返回 0.0 并记录。

### 6.3 PrivacyController（`privacy_controller.py`）

- `select_framework`：唯一使用 LLM 的步骤（复用 Curator 模型），从 DP 框架库选任务；
- `determine_budget`：`split_budget` / `naive_budget`；
- `build_noisy_graph`：汇总节点 RR 输出并下发噪声邻居；
- `gs_optimize`：收集带噪度数 → `degree_bound` → 三角形做图投影、k-star 让节点本地投影 → 返回 `(GS_f, d̂max, 投影后 G')`，审计信息存 `degree_trace`；
- `collect_reports`：让每个节点加 Laplace 噪声上报。

隐私保证只依赖控制器代码。LLM 选错任务时只打警告并记录 `task_correct=False`，不会绕过噪声（这一处理的问题见 §18）。

## 7. 框架编排（`psc/framework.py`）

### 7.1 PSCFramework：Algorithm 3 逐行映射

| Alg.3 行 | 实现 |
|---|---|
| 1–3 初始化节点、计数 0 | `_AgentFactory.nodes(graph)` |
| 4 选 DP 框架、拆预算、定灵敏度 | `controller.select_framework` + `determine_budget` |
| 5–6 噪声图 | `split.eps1>0` 时 `controller.build_noisy_graph` |
| 7–8 GS 优化 | `split.eps2>0` 时 `controller.gs_optimize`，否则用无优化灵敏度 |
| 9 设计分布式算法 | `curator.design_algorithm` |
| 10 发送消息 | `fanout_pipeline(nodes, send_instr)` 并行 send，再按 `metadata["recipients"]` 对目标节点 `observe(msg)` **定向投递** |
| 11–12 更新本地计数 | `fanout_pipeline(nodes, update_instr)` |
| 13 Laplace 上报 | `controller.collect_reports`，经 `curator.observe` 写入 Curator 记忆 |
| 14 聚合 | `curator.aggregate` |

指令以 `Msg` 下发，`metadata={"phase": "send"|"update", "task": ...}`；`fanout_pipeline(..., enable_gather=True)` 并发执行同一阶段；节点间消息点对点 `observe`，不走广播。

三个变体：**PSC**（完整流程）、**PSC-B**（`gs_optimization=False`，Exp3，最坏情况灵敏度）、**PSC-noDP**（`dp=False`，Exp5，无 RR/投影/Laplace，Curator 收到不含 LDP 声明的 prompt）。

每次运行的 LLM 调用数：triangle 为 $2n+3$，degree / k-star 为 $n+3$。`RunResult.extra` 保存 `validation`（§11）与 `mechanism_trace`（带噪度数、d̂max、GS、Laplace 尺度、原始计数、逐节点噪声、截断前求和）。

### 7.2 NaiveFramework（Section 2.4）

1. 控制器 LLM 选任务；2. 全部预算用于 RR 构造 $G'$；3. 把噪声边表插入 `Q: The nodes are numbered from 0 to n−1.` 之后由 Curator 直接作答（`prompt_style="raw"`），或用 REFINED 模板（Exp6）。

`validation.rule_estimate` 记录同一噪声图上精确计数的结果。Naive 满足 ε-edge LDP 依据是 RR + 后处理不变性（论文 Theorem 1）。

## 8. 对照与基线方法

### 8.1 GT 系列（纯 Python，`psc/ground_truth.py`）

论文用“DP 算法的 Python 实现运行 1000 次的平均 RE”作为 GT。GT 是隐私算法的误差，不是图的真值（真值在本项目记为 truth）。

- **GT-Naive**：全预算 RR → 噪声图上精确计数；
- **GT-PSC**：与 Agent 版相同的预算、噪声图、带噪最大度、投影、灵敏度、Laplace 与聚合，send/update 用代码执行；
- **GT-PSC-B**：关闭 GS 优化。

`gt_psc(..., return_trace=True)` 返回 `RunTrace`，`audit_dict()` 输出可审计记录。低层函数保留 `legacy` 默认以兼容历史研究脚本，实验入口显式传入所选机制。

### 8.2 附录 B 单 LLM 基线（`psc/baselines.py`）

- **RAW（zero-shot）**：任务定义 + 节点与真实边字符串，无 LDP 声明；
- **REFINED**（Nguyen & Yan 2024：Few-Shot + Least-to-Most + 1-hop）：子结构定义 → 分步 COT 指令 → 10 节点示例（固定种子 2024 生成 38 边图，程序化写出四步推理）→ 目标任务与边表 → 每个节点的 1-hop 邻居；
- **Naive+REFINED**：REFINED 模板用于噪声图（Exp6）。

这些基线只有接真实模型才有意义；Mock 下都精确。

## 9. Prompt 设计与回复解析（`psc/prompts.py`）

### 9.1 双通道 prompt

每个 prompt = 自然语言部分 + `<structured_input>{JSON}</structured_input>` 机器可读块。Mock 只读结构化块；真实模型调用前 `chat()` 用 `strip_structured` 删掉该块（`ModelConfig.use_structured_input` 默认只对 mock 为真），真实 LLM 不会“抄答案”。`test_structured_input_only_reaches_the_mock` 验证这一点。

### 9.2 系统提示

`CURATOR_SYSTEM`（看不到真实边、负责设计与聚合、注意算术）、`PRIVACY_CONTROLLER_SYSTEM`（只按 JSON 回答所选框架）、`NODE_SYSTEM`（只管理节点 `{node_id}` 的邻域，严格遵守规则）。

### 9.3 各阶段 prompt

| 函数 | 阶段 | 要求输出 |
|---|---|---|
| `task_selection_prompt` | 控制器 / Curator 选任务 | `{"task"}` |
| `node_send_prompt` | 节点 send（邻居以 `Node x` 列出） | `{"Sender_ID","Sender_Neighbors"}` |
| `node_update_prompt` | 节点 update（真实邻居 + 消息列表） | `{"count"}` |
| `curator_aggregate_prompt` | 聚合（带噪计数保留 4 位小数） | `{"result"}` |
| `naive_answer_prompt` | Naive：默认 `paper` 不加 system prompt 和结尾指令，`cot` 才加 | 自由文本取最后一个数（`cot` 为 `{"result"}`） |
| `raw_prompt` / `refined_prompt` | 附录 B | `{"result"}` |

统一结尾指令（`paper` 除外）：“可以逐步思考，最后在 ```json 代码块里给出只含所需键的 JSON”。

### 9.4 解析策略

- `extract_json`：优先最后一个围栏 JSON，其次最后一个裸 `{...}`，只接受 dict；
- `extract_number`：去千分位逗号后取最后一个数（支持科学计数法、`###421`；之后又加了 `\boxed{}` 优先）；
- `insert_edges_into_prompt`：正则定位 `Q: The nodes are numbered from a to b.`，找不到则追加。

宽松解析的已知问题见 §19.2。

## 10. 离线 Mock 模型（`psc/mock_model.py`）

`MockChatModel` 继承 `ChatModelBase`，是严格按规则推理的“完美 LLM”：读取最后一条 user 消息中的 `<structured_input>`，按 `phase` 分派到 `rules.*`，返回与真实模型同格式的 `ChatResponse`，整个 AgentScope 流水线可离线跑通。`error_rate` 只对节点 update 注入 ±1 错误（截断到非负），用于敏感性分析（`--mock-error-rate`）。

Mock 下 Agent 版结果在分布上等价于 GT 版（`test_agent_pipeline_matches_ground_truth_distribution`）。注意 Mock 与 GT 共用 `rules.py` 和 DP 原语，这只证明编排自洽，不是论文正确性的独立证明（§19.4）。

## 11. LLM 执行正确性验证：同噪声回放

`_validate_psc`（`psc/framework.py:285`）在每次 PSC 运行后，用**同一输入、同一份 Laplace 噪声**以代码重算：

| 字段 | 含义 |
|---|---|
| `send_exact` | 节点 LLM 消息与 `rules.send_message` 一致的个数 |
| `update_exact` | LLM 计数与“对实际收到的消息执行规则”一致（隔离 update 误差） |
| `e2e_exact` | LLM 计数与完美流水线一致（send + update 合计） |
| `count_rel_diff` | LLM 计数和与规则计数和的相对差 |
| `aggregate_exact` | Curator 聚合与规则一致（`rel_tol=abs_tol=1e-3`，不是逐位精确） |
| `rule_estimate` | 把每个节点实际噪声 $z_i=\tilde c_i-c_i^{\text{LLM}}$ 加到规则计数上再聚合，即配对 GT-PSC 值 |
| `mismatches` | 最多 30 个不一致节点 |

汇总（`validation_summary`，`psc/experiments.py:294`）：`node_update_acc`、`node_e2e_acc`、`send_acc`、`aggregate_acc`、`task_acc`、`rule_relative_error`（同噪声完美流水线的平均 RE），以及 `delta` $=|\overline{\mathrm{RE}}_{\text{LLM}}-\overline{\mathrm{RE}}_{\text{rule}}|$。

`delta` 与论文 Table 6 口径不同：论文与独立 GT 比较，这里是同噪声配对，更适合定位推理问题；接近 0 不表示更接近论文，也会抵消跨次正负误差（后续已增加 `delta_signed`、`exec_deviation` 等列，见 README）。这套方法把最终误差拆成“隐私机制本身的误差”与“LLM 执行误差”。

## 12. 模型接入、重试与错误记录

### 12.1 模型工厂（`psc/models.py`）

| provider | 模型类 | Formatter |
|---|---|---|
| openai（及兼容端点） | `OpenAIChatModel` | `OpenAIChatFormatter` |
| dashscope | `DashScopeChatModel`（`enable_thinking=False`） | `DashScopeChatFormatter` |
| ollama | `OllamaChatModel` | `OllamaChatFormatter` |
| mock | `MockChatModel` | `OpenAIChatFormatter` |

`node_model` 用于节点 send/update；`curator_model` 用于 Curator 与隐私控制器。配置优先级：命令行 > 环境变量（`PSC_PROVIDER`、`OLLAMA_MODEL`）> `config.toml`（共享键 + provider 分节）> 内置默认。密钥只来自 `.env`，`load_config_file` 对未知键和分节报错。

### 12.2 统一调用与重试（`chat()`，`models.py:255`）

- 关闭 OpenAI 客户端自带重试（`max_retries=0`），由 `chat` 统一重试并逐次记录；
- 可重试：HTTP 408/409/429/≥500、超时/连接/流中断类异常，以及**空文本回复**；
- 等待 $\text{retry\_backoff}\times2^{k-1}$，服务端给 `Retry-After` 时取较大者；
- 全部失败返回空串，由上层记为解析失败，实验不中断；400、鉴权等直接抛出；
- 流式响应取最后一个 chunk（含累积内容）。

### 12.3 错误事件与进度（`psc/events.py`、`psc/progress.py`）

- `ContextVar` 保存当前运行的记录列表和上下文标签（数据集/任务/方法/第几次），asyncio 子任务自动继承，并发运行不串号；
- `record_error` 同时追加到运行记录、实时写 `errors.jsonl`、打 warning；错误类型 `api_error`、`empty_reply`、`call_failed`、`parse_failure`；回复最多保留 20000 字符（保留首尾）；
- 进度条同样用 `ContextVar` 注入回调，按调用次数推进。

## 13. 实验体系、随机数与统计方法

### 13.1 实验清单（`scripts/run_experiments.py`、`scripts/run_ground_truth.py`）

| 实验 | 内容 | 默认数据集 / 方法 |
|---|---|---|
| exp1 | Table 2，$\varepsilon=2$ | 6 图 × 4 任务，Naive / PSC |
| exp2 | $\varepsilon\in\{1,1.5,2,2.5,3\}$（Fig.2） | CU, Do |
| exp3 | GS 优化效果，PSC vs PSC-B（Table 3） | CU, Do × triangle / k-star |
| exp4 | 预算分配：分别扫描 $r_1$、$r_2\in\{0.1,\dots,0.9\}$（Fig.3） | CU, ML × triangle |
| exp5 | 附录 B Table 4：RAW / REFINED / PSC-noDP | 6 图 |
| exp6 | 附录 B Table 5：Naive vs Naive+REFINED | 6 图 |
| pilot | 真实 LLM 验证：PSC、Naive，含节点级正确率 | CU, Do |
| GT | GT-Naive / GT-PSC / GT-PSC-B，默认 1000 次 | 6 图 |

`--dry-run` 只打印预计调用数。论文设置：node=GPT-4.1-mini、curator=GPT-4.1、temperature=0，每格 10 次（论文第 6 页）。

### 13.2 随机数设计

- Agent 实验：第 $i$ 次运行的全部 DP 噪声来自 `np.random.default_rng([seed, i])`，结果与并发度、完成顺序无关（`test_parallel_runs_are_reproducible_and_overlap`）；
- GT 实验：每格 `default_rng(seed)` 顺序消费；且 GT 的矩阵 RR 消耗 $n^2$ 个随机数，Agent 逐行 RR 消耗 $n(n-1)/2$ 个。所以两者相同 seed 不代表逐次噪声相同；评价 LLM 执行差异应读 pilot 的 `rule_relative_error`；
- 同一运行序号下，同图 2-star 与 3-star 在相同消费路径上共享基础噪声（例如 CU 三次 pilot 的 D 在两个任务上都是 19、12、13），两任务同时变差不能当作独立证据，但这不会让单项均值有偏。

### 13.3 两级并发

`parallel_runs`（跨所有设置同时执行的运行数）与 `max_concurrency`（`NodeAgent` 类级信号量，不限 Curator）。所有框架在任何运行开始前一次性构建，因为每个框架都会重置类级信号量。

### 13.4 统计量（`error_statistics`，`psc/experiments.py:145`）

`avg_relative_error`、`se_relative_error`（$s/\sqrt{N}$，ddof=1）、`median_relative_error`、`p95_relative_error`、`paper_relative_gap` $=|\overline{\mathrm{RE}}/\text{paper}-1|$、`paper_log_gap` $=|\ln(\overline{\mathrm{RE}}/\text{paper})|$（对倍数偏差对称，用于机制选择）。`experiments.py` 内置论文 Table 2/3/4/5 参考值，`table2_markdown` 在每行下方附论文值。

### 13.5 结果产物与可追溯性（`psc/artifacts.py`）

- `new_run_directory`：`mkdir(exist_ok=False)`，已有 tag 直接拒绝；省略 tag 自动加时间戳；
- `runs.jsonl`：每完成一次运行立即追加（`allow_nan=False`）；
- `manifest.json`：Python 版本、机制配置、运行参数、`psc/`、`scripts/` 源码与数据文件的 SHA-256，不写密钥；
- 全部完成后写 `summary.json`、`runs.json`、`table.md`，另有 `errors.jsonl`、`run.log`。

## 14. k-star 机制对齐与 floor_tight 的选定

目的：`legacy` 的 GT-PSC 在 k-star（尤其 2-star）上与论文有持续差距（§23），需在不接触作者代码的前提下从候选解释中选出最接近论文的一种。

### 14.1 配对向量化模拟（`psc/alignment.py`）

- 度截断后 k-star 计数只依赖 $\min(d_i, D)$，与删哪些邻居无关，所以直接在度向量上计算，不构造投影图；
- 每批最多 1024 次，一次生成 $(\text{size}, n)$ 的度噪声矩阵 $\tilde d=d+\mathrm{Lap}(1/(0.2\varepsilon))$；
- 报告噪声利用 Laplace 可缩放性：先生成 $S=\sum_i L_i$（标准 Laplace），再乘 $GS/\varepsilon_3$；
- **公共随机数**：所有候选共享同一批度噪声和报告噪声，只改参数策略；
- 同时计算 GT-PSC（$\varepsilon_3=0.8\varepsilon$）与 GT-PSC-B（$\varepsilon_3=\varepsilon$）；
- 估计 $\max(0,\ \sum_i\binom{\min(d_i,D)}{k}+\frac{GS}{\varepsilon_3}S)$。

生产代码还为邻居选择消耗额外随机数，因此与生产的一致是**分布意义**上的。

### 14.2 选择与确认（`scripts/align_gt_psc.py`）

1. 发现阶段：六图 × {2-star, 3-star} × {GT-PSC, GT-PSC-B}，每格 5000 次（seed 9292026）；
2. 评分：对所有有论文值的唯一单元格（Table 2 的 12 个 k-star GT-PSC + Table 3 的 4 个 CU/Do GT-PSC-B）求 `paper_log_gap` 平均，即 $J=\mathrm{mean}_{cell}|\ln(\mathrm{RE}/\mathrm{RE}_{paper})|$；Table 2 与 Table 3 分数分开展示，避免互相抵消；
3. 确认阶段：用**独立随机流**（seed 9292027）每格 1000 次，只重跑 `legacy` 与被选配置，不重新选择；
4. 不自动修改默认配置，由人工决定。

结果（`results/alignment/profiles_20260929/`）：

| 配置 | Table 2 log gap | Table 3 PSC-B log gap | 联合 log gap | 最大相对差 |
|---|---|---|---|---|
| **floor_tight** | 0.2903 | 0.0521 | **0.2308** | 0.7838 |
| floor_bound | 0.3275 | 0.0679 | 0.2626 | 0.8303 |
| continuous_bound | 0.3489 | 0.0679 | 0.2786 | 0.8533 |
| legacy | 0.3712 | 0.0836 | 0.2993 | 0.8826 |

确认流中 floor_tight 与 legacy 分别为 0.2308 与 0.2925，排序不变，2026-09-29 起默认改为 `floor_tight`。此前 5 万次配对实验中，3-star 逐格相对差距均值从 22.7% 降到 11.8%，最差单格从 51.2% 降到 22.7%。选择依据是论文公开数值，**不声称复原了作者代码**；跨随机流确认只排除挑种子，不能消除“按公开表格选配置”本身的偏向。它总体更接近论文，但不保证每一格都改善，2-star 仍有明显差距（§16.1）。

## 15. 隐私性分析与信任边界

1. **组合定理**：PSC 三阶段分别消耗 $\varepsilon_1,\varepsilon_2,\varepsilon_3$，总计 $\varepsilon$（Theorem 2）；Naive 只做一次 RR（Theorem 1）。
2. **后处理不变性**：send 只读噪声邻居，聚合只读带 Laplace 噪声的上报。
3. **下三角 RR**：每条边只由一个端点扰动。
4. **灵敏度前提**：update 读真实邻居，其灵敏度由投影阈值保证（对称删边保证三角形推导成立；k-star 本地投影保证 $\binom{D-1}{k-1}$ 成立）。
5. **代码执行噪声**：所有加噪在控制器/节点本地代码完成，与 LLM 是否遵守指令无关。
6. 需要注意的边界见 §20。

---

# 第二部分 复现结果

## 16. 当前复现结果

### 16.1 GT 列（`floor_tight`，1000 次，$\varepsilon=2$）

来源：`results/ground_truth/gt_all_r1000_floor_tight_20260930/table.md`。论文平均值按六个已发表单元格重算，末位可能与论文表格直接打印的 Avg. 不同。

| 任务 | 方法 | 本项目 Avg.（floor_tight） | legacy Avg.（历史 1000 次） | 论文 Avg. |
|---|---|---|---|---|
| degree | GT-Naive | 2.3578 | — | 2.3581 |
| degree | GT-PSC | 0.0118 | 0.01181 | 0.0119 |
| 2-star | GT-Naive | 6.0349 | — | 6.0297 |
| 2-star | GT-PSC | 0.1039 | 0.11419（+76.6%） | 0.0647 |
| 3-star | GT-Naive | 10.1851 | — | 10.2058 |
| 3-star | GT-PSC | 0.3756 | 0.44732（+22.6%） | 0.3649 |
| triangle | GT-Naive | 4.1541 | — | 4.1610 |
| triangle | GT-PSC | 0.8833 | 0.88327（+1.1%） | 0.8737 |

- GT-Naive 24 个单元格与论文偏差均 < 1%。这降低了数据读取、任务定义、RR 概率整体错误的可能性，但不等于逐条边都与作者版本一致；
- degree / triangle 的 GT-PSC 均值基本一致，但 triangle 均值掩盖了 EE 的局部偏差（§30）；
- 3-star 平均值接近，但逐格仍有偏差（如 CU 0.6954 vs 0.8035，CS 0.6475 vs 0.5410）；
- **2-star 仍比论文高约 60%**，是未消除的主要差距（legacy 下六图单项高约 53%–88%）。只改取整和灵敏度无法解释（§25、§29）。

### 16.2 真实 LLM pilot（CU / Do，每格 10 次，floor_tight）

来源：`results/pilot/hy3-ioa_cudo_r10_floor_tight/`、`results/pilot/hy4-preview-ioa_cudo_r10_floor_tight/`

- 节点 update 正确率 99.2%–100%，三角形 send 正确率 100%，聚合正确率 100%，任务识别 100%；
- PSC 的 `delta` 大多为 0 或 < 0.006，误差几乎全部来自隐私机制，而不是 LLM 推理；
- Naive 的 LLM 结果与同噪声规则答案接近（Do/triangle 在 hy3-ioa 下 Δ≈0.17 为最大值）；
- PSC 比 Naive 低 1–2 个数量级，与论文结论一致。

### 16.3 早期 pilot（legacy，`hy3-ioa_r3_v2`，每格 3 次）

`hy3-ioa` 同时担任 node 与 curator，CU/Do × 四任务 × PSC/Naive，每格 3 次，共 48 次运行。来源 `results/archive/pilot/hy3-ioa_r3_v2/summary.json`。

| 数据集 | 任务 | PSC | 同噪声代码规则 | 论文 PSC | 当前/论文 |
|---|---|---:|---:|---:|---:|
| CU | degree | 0.0297 | 0.0297 | 0.0174 | 1.71 |
| CU | 2-star | 0.3248 | 0.3240 | 0.0929 | 3.50 |
| CU | 3-star | 2.0191 | 2.0191 | 0.7325 | 2.76 |
| CU | triangle | 1.9326 | 1.9326 | 0.7939 | 2.43 |
| Do | degree | 0.0205 | 0.0194 | 0.0162 | 1.26 |
| Do | 2-star | 0.1973 | 0.1973 | 0.0679 | 2.91 |
| Do | 3-star | 0.7596 | 0.7596 | 0.3816 | 1.99 |
| Do | triangle | 0.5688 | 0.5688 | 0.8628 | 0.66 |

- 1332 次节点 update 中 1331 次与完美规则流水线一致（99.92%），triangle send 333/333，24 次聚合 23 次在容差内，解析失败 0。剩余差错：Do degree 中 Node 60 把 1 算成 0（原始回复未保存，无法区分模型算错与宽松解析）；CU 2-star 一次聚合输出 639.3549、规则值约 638.3553（使三次平均 RE 增加约 0.00079）；
- 旧版 `hy3-ioa_r3` 节点 e2e 为 1275/1332，主要是 §6.1 所述 `"Node 13"` 解析问题。两版后两次运行噪声不同，不能用最终 RE 升降归因修复收益；
- 这些 pilot 数字没有超出当时机制的经验波动范围（§22.3），表面上 2–3.5 倍于论文主要是机制噪声和 3 次抽样波动；
- **Naive 未复现论文的“单 LLM 大量推理误差”**：CU 上 Naive 与同噪声代码结果几乎一致，例如 CU triangle Naive RE=1.4269（论文 9.1228），CU 3-star 10.0445（论文 109.3320）；CU triangle 的 PSC 甚至高于 Naive（1.9326 vs 1.4269），但 3 次不足以确定稳定排序。模型、prompt 和样本数不同，不能期待 PSC/Naive 优势倍率与论文一致。

### 16.4 Mock 版（`results/archive/exp1/mock/`）

PSC 平均 RE：degree 0.0142、2-star 0.1237、3-star 0.4562、triangle 0.8928（legacy 机制）。Exp2 复现了“$\varepsilon=3$ 时三角形 GT-Naive 反超 GT-PSC”；Exp4 复现了 CU 误差随 $\varepsilon_1$ 单调上升、ML 先降后升，以及 $\varepsilon_2$ 过大/过小都使误差上升。

---

# 第三部分 审计发现

审计（2026-09-28）结论：主要流程和小图上的模型执行已验证，但尚不能称为论文实验的完整复现。主要问题是 k-star 机制结果持续偏离论文、triangle 局部差距被总体均值掩盖、真实实验覆盖不足、评估口径不完全可比。模型算术错误已很少，继续优化节点 prompt 很难消除大部分误差。

## 17. 论文自身未规定或不一致的细节

- **triangle 灵敏度**：论文第 5 页 Algorithm 2 返回最大度作为灵敏度，第 3 页讨论上界为最大度，第 16 页 DP 库示例写 `degree-1`。项目采用附录的“最大度减一”，有来源但不能称为论文各处一致；
- **附录 E triangle 示例**：从 0 开始只加 0.5，最终状态却写成 1；项目按规则结果写 0.5（`library.py`、测试），是合理修正，因此不能说“逐字对应”；
- **k-star**：真实邻居投影、最大度取整、灵敏度（第 3 页写 $\binom{D}{k-1}$）没有完整规定；
- **triangle 投影**：无向图删边的对称性和处理顺序未规定；项目按随机节点顺序对称删边；
- degree/k-star 的完整库条目和部分 few-shot 内容由项目补充；隐私控制器使用的 LLM、10 节点示例图等也是项目补充（README“论文未明确、由本实现补充的细节”）。

复现报告应分别列出“原文明确要求”“原文不明确的选择”“纠正原文矛盾”，不能把选择写成作者已确认的事实。

## 18. Agent 能力的验证范围

`CuratorAgent.design_algorithm` 让 LLM 返回四个任务标签之一，再 `get_algorithm(task)` 取固定规则；隐私控制器同样返回 task 再取固定 DP 框架。已验证的是有限任务集合上的识别、规则执行和聚合，没有评估 LLM 生成或调整 send/update/aggregate，也没有验证新增任务、未知任务或不同表述下的算法建立能力。论文同样依赖知识库，不应夸大为“从零发明算法”；但 `task_acc=1` 也不足以证明完整的算法设计能力。

选任务解析失败时会用 `infer_task_from_prompt` 回退；Curator 与控制器标签不一致时只警告并继续执行，可能让执行算法与噪声校准不匹配。应分别记录原始识别准确率和回退后的结果，参数与算法不一致时终止该次运行或标为无效（2026-10-15 核对：仍只警告）。

## 19. 评估、解析与可追溯性问题

### 19.1 指标口径

- `delta` 与论文 Table 6 口径不同（§11），且会抵消跨次误差。应同时给出逐次绝对差、`mean(abs(a−b)/d)`、有符号偏差、分位数与节点误差分布（已部分实现：`delta_signed`、`exec_deviation` 等，见 README）；
- 随机源只由 `[seed, run_index]` 组成，不同任务共享随机模式；GT 与 Agent 相同 seed 不对应同一噪声图（§13.2）。应记录随机数方案版本，区分固定噪声配对实验与独立随机重复。

### 19.2 数值解析

- `extract_number` 把回复中最后一个数字当答案：`Unable to finish. Last processed Node 12.` 会被解析为 12，不计入 parse_failure；
- `float(payload['count'])` / `float(payload['result'])` 不检查有限性，`NaN` 与 `1e309` 都能进入后续计算（本地探针验证；没有证据表明已污染已有 pilot）；
- send 解析只规范化类型，不核验 Sender_ID 与发送节点一致、范围有效、邻居唯一及自环。

建议：严格结果 schema、有限数检查、输出范围/身份检查；无法解析与合法零计数分开统计；语义校验与重新请求作为单独实验条件记录（具体规则见 §35 工作包 2.3）。

### 19.3 运行成本与长尾

`hy3-ioa_r3_v2` 共 1785 次逻辑调用，另 4 次重试，无最终失败。其中 3 次返回仅含 thinking 的空文本，单次耗时约 553–801 秒，另有一次超时。PSC 每次运行耗时中位数约 686 秒（含并发等待），最长约 1566 秒。重试提高完成率，但没有解决长尾延迟。当时 `models.py` 没有记录 usage/finish_reason（之后已记录 input/output tokens）。按调用规则，六数据集四任务 PSC+Naive 各 10 次约 44700 次逻辑调用（不含重试）。

### 19.4 可追溯性与测试独立性

| 问题（2026-09-28） | 状态 |
|---|---|
| 未完整记录 seed/run_index、代码版本与未提交差异、依赖版本、数据哈希、prompt 哈希、实际模型标识、正常回复、usage、finish_reason；成功解析但算错的调用没有原始回复 | 部分解决：`manifest.json` 记录源码/数据哈希与参数；`--save-transcripts` 可保存完整回复和 token；finish_reason、prompt 哈希仍未记录 |
| `asyncio.gather` 完成后才写 per-run 结果，中断会丢已完成结果 | 已解决：`runs.jsonl` 逐次追加 |
| 相同 tag 覆盖已有结果 | 已解决：`exist_ok=False` |
| 不支持断点续跑 | 未解决 |
| Mock 与 GT 共用 `rules.py` 和 DP 原语，Mock 通过只证明编排自洽；统计一致性测试只检查一个小图的 2-star，允许均值相差 25% | 未解决：需要独立公式/已核实伪代码测试（§35 工作包 1.2 的独立校验器） |

## 20. 隐私信任边界尚未落实为部署保证

- 论文第 3 页假设节点邻接数据保存在可信本地服务器。`NodeAgent._update` 把真实或裁剪后的邻居直接写入 prompt，而真实模型配置把 node 与 curator 交给同一 provider/端点。除非该模型服务位于每个节点的可信边界内，第三方推理服务在加噪前已拿到真实邻接信息，后续 Laplace 不能补回这一步。公开基准图适合功能实验，但不能据此宣称真实私有图上的端到端 LDP 部署；
- 框架在中心进程构造全图；`mechanism_trace`、`raw_count_sum`、GT 的 `runs.jsonl` 含原始计数和逐节点噪声，只能作为可信离线审计材料，不能作为公开隐私输出（`manifest.json` 中有提示）。部署设计应明确节点进程、模型服务、日志存储和 curator 的信任归属；
- 噪声按理想计数函数的灵敏度校准，而进入 `protected_count` 的实际值来自任意 LLM 输出。仅靠“加了 Laplace”不能证明实际函数保持同一灵敏度，需要说明“模型遵循固定计数规则”的假设，或采用能约束实际释放函数的受审计计算机制。范围裁剪可给出粗界，但不能自动恢复理想函数的精细灵敏度。这是隐私保证的实现条件，不是数值误差已由隐私泄漏造成的证据。

---

# 第四部分 k-star 与 triangle 差距诊断

本部分写于 2026-09-28，除特别说明外“当前机制”指 `legacy`。诊断只新增独立脚本与结果，未修改生产代码，未调用模型 API。

## 21. 三种比较对象

论文 GT-PSC 是 Python 隐私算法 1000 次的平均 RE，不是误差为零的原图答案；论文 agent 实验每格 10 次。下表把 LLM pilot、同噪声规则回算、本地 GT 与论文 GT 分开：

| 数据集/任务 | LLM pilot，3 次 | pilot 同噪声规则回算 | 本地 GT（legacy，1000 次） | 论文 GT-PSC |
|---|---:|---:|---:|---:|
| CU / 2-star | 0.3248 | 0.3240 | 0.1787 | 0.1062 |
| Do / 2-star | 0.1973 | 0.1973 | 0.1064 | 0.0585 |
| CU / 3-star | 2.0191 | 2.0191 | 0.8730 | 0.8035 |
| Do / 3-star | 0.7596 | 0.7596 | 0.4326 | 0.3434 |

这 12 次 k-star pilot 的 666 个节点 update 全部与规则一致，原始计数和等于真值，任务选择全部正确。同噪声回算证明模型没有增加主要误差，但不能证明当前机制等同作者实现。

## 22. legacy k-star 机制与 pilot 大误差的来源

### 22.1 机制

k-star 不构造 RR 噪声图，不执行 send，不会发生 triangle 的噪声邻居消息错误。$\varepsilon=2$ 时：

```text
真实邻居 -> d_i
             +-> 每节点加 Lap(2.5) -> 取所有节点最大值 -> 向上取整为 D
             +-> 本地度裁剪到 min(d_i,D)
                         |
                     C(min(d_i,D),k)    [LLM 计算]
                         |
              每节点加独立 Lap(C(D,k-1)/1.6)
                         |
                  所有节点求和，最终截断到非负
```

$$\varepsilon_1=0,\ \varepsilon_2=0.4,\ \varepsilon_3=1.6,\quad D=\max\big(1,\lceil\max_i(d_i+\mathrm{Lap}_i(1/\varepsilon_2))\rceil\big)$$
$$c_i=\binom{\min(d_i,D)}{k},\quad GS_2=D,\ GS_3=\tfrac{D(D-1)}{2},\quad Y=\max\big(0,\ \textstyle\sum_i c_i+\sum_i Z_i\big),\ Z_i\sim\mathrm{Lap}(GS_k/\varepsilon_3)$$

固定 $D$ 时报告噪声总和标准差为 $\sqrt{2n}\,GS_k/\varepsilon_3$；3-star 的 GS 随 $D$ 二次增长。

### 22.2 例子：CU / 3-star 与 CU、Do / triangle

CU / 3-star 第 1 次 pilot：$n=49$，真实最大度 8，真值 494，所有节点原始计数和正好 494；$D=19$，$GS=\binom{19}{2}=171$，每节点 Laplace 尺度 106.875，固定该 $D$ 的聚合噪声标准差约 1058.01。噪声和 +1956.198，输出 2450.198，与规则回算完全一致。三次输出 2450.198、1036.068、0，平均 RE=2.0191。这里的高误差不需要任何 LLM 错误即可产生；第三次是负估计截断后的合法零值。

triangle 还叠加了 RR/投影后的计数偏差。CU 第 1 次真值 57，规则计数加 Laplace 前为 92/3=30.6667，聚合噪声约 +242.8013，最终 273.468。Do 第 1 次真值 95，加噪前 101，聚合噪声约 −134.1971，截断前 −33.1971，最后输出 0。输出 0 是规则的正常结果，不能单独认定为调用失败。

### 22.3 3 次均值的经验波动

对 CU/Do 各任务追加 5000 次纯代码运行（`default_rng([9131,i])`），再从 RE 样本重采样 50000 组、每组 3 次（seed 119），得到三次均值的经验分布。这只刻画当前实现的波动，不是论文结果的置信区间。

| 数据集/任务 | 5000 次代码平均 RE | 三次均值经验 95% 区间 | pilot 同噪声规则 RE |
|---|---:|---:|---:|
| CU/degree | 0.0186 | [0.0053, 0.0365] | 0.0297 |
| CU/2-star | 0.1715 | [0.0472, 0.3555] | 0.3240 |
| CU/3-star | 0.8611 | [0.2592, 2.0213] | 2.0191 |
| CU/triangle | 1.0067 | [0.3590, 2.2174] | 1.9326 |
| Do/degree | 0.0139 | [0.0040, 0.0269] | 0.0194 |
| Do/2-star | 0.1050 | [0.0297, 0.2140] | 0.1973 |
| Do/3-star | 0.4267 | [0.1153, 0.8791] | 0.7596 |
| Do/triangle | 0.8421 | [0.2703, 1.7340] | 0.5688 |

pilot 数字没有超出机制的经验波动范围，CU/3-star 接近上界。所以 pilot 远差于论文的表面倍率不等于同样大的长期机制差距；但这也不消除 §23 的持续差距。

## 23. 长期差距：5 万次独立对照

独立脚本直接从度向量计算组合数、阈值和报告噪声，不调用生产 rules 或 GS 函数。先对六图 × 两任务 × 100 次生产 `RunTrace` 做独立公式核对（共 1200 次，覆盖实际裁剪场景）：原始计数、GS、预算全部一致，聚合浮点差最大 9.4e-10。再对每图执行 5 万次向量化模拟，候选共享标准 Laplace 度噪声与报告噪声。

| 数据集 | legacy 2-star | 论文 2-star | legacy 3-star | 论文 3-star |
|---|---:|---:|---:|---:|
| CU | 0.1743 | 0.1062 | 0.8821 | 0.8035 |
| Do | 0.1042 | 0.0585 | 0.4231 | 0.3434 |
| ML | 0.0835 | 0.0444 | 0.2758 | 0.2077 |
| CS | 0.2308 | 0.1210 | 0.8181 | 0.5410 |
| EE | 0.0492 | 0.0295 | 0.1931 | 0.1647 |
| PM | 0.0451 | 0.0284 | 0.1261 | 0.1290 |
| 六图平均 | 0.1145 | 0.0647 | 0.4530 | 0.3649 |

2-star 六图均偏高，平均高约 77%；3-star 并非全部差很多：PM 已接近，CU 约高 10%，CS 约高 51%。论文没有给每格标准误，不能用本地标准误代替双方比较所需的不确定性。

## 24. 误差来源归纳

**原因一：把一个节点的最坏情况尺度应用到所有节点。** GS 是全体节点共用的上界，degree=2 的节点和 degree=D 的节点使用相同噪声尺度，零均值不能消除方差。给定 $D$，2-star 总报告噪声方差为 $2n(D/\varepsilon_3)^2$，3-star 为 $2n(\binom{D}{2}/\varepsilon_3)^2$。“每节点计数简单”与“最终估计准确”是两回事。PM 真实最大度 237，度数均方根仅约 18.93，统一最坏尺度在不均匀图上代价尤其明显。

**原因二：小图的带噪最大度有向上选择效应，3-star 又将其二次放大。** 每个度报告噪声均值为零，但取最大值会选到偏大的噪声项：

| 数据集 | 真实最大度 | 平均 D | D 小于真实最大度的比例 |
|---|---:|---:|---:|
| CU | 8 | 14.860 | 0% |
| Do | 12 | 17.463 | 0.078% |
| ML | 36 | 36.515 | 33.526% |
| CS | 12 | 16.305 | 1.190% |
| EE | 42 | 42.541 | 33.256% |
| PM | 237 | 237.502 | 33.592% |

CU 的 5 万次样本没有任何真实邻居裁剪，全部误差来自报告噪声与最终截断，Do 也几乎如此。D 偏高主要放大方差，不意味着每次估计都偏高。ML/EE/PM 有明显枢纽节点，D 均值接近真实最大度；约三分之一运行会裁剪最高度节点，但平均计数损失小：2-star 约 1.18% / 0.52% / 0.30%，3-star 约 3.51% / 1.85% / 0.83%。

**原因三：预算开销和裁剪增加代价，但不是全部差距。** 最大度阶段用 0.4、报告阶段用 1.6，与同 GS 下直接用 2 相比报告噪声尺度增加 25%——这是估计最大度的成本，不是预算丢失。减小 $\varepsilon_2$ 又会增大 D 的噪声，所以单独提高 $\varepsilon_3$ 不一定改善结果。

**原因四：评估把两个问题叠在一起。** pilot 每项 3 次，论文 GT 每项 1000 次，前者与本地大样本的差距主要是抽样波动（§22.3）；而 2-star 本地长期均值约 0.114、论文约 0.065，增加次数不会消除。应把“本地 LLM 相对本地代码的执行误差”与“本地机制相对论文的差距”分开报告。

**原因五：作者实际机制与公开描述之间缺少可验证的连接**（§28、§29）。

## 25. 取整、灵敏度、预算、投影、截断的消融

所有候选共享其余基础随机量：

| 候选 | 六图平均 2-star RE | 六图平均 3-star RE |
|---|---:|---:|
| legacy：ceil + $\binom{D}{k-1}$ | 0.1145 | 0.4530 |
| 只改 floor | 0.1090 | 0.4145 |
| 只改紧界 $\binom{D-1}{k-1}$ | 0.1086 | 0.4135 |
| floor + 紧界（即 floor_tight） | 0.1031 | 0.3760 |
| 论文 | 0.0647 | 0.3649 |

- 3-star 因二次灵敏度对“减一”非常敏感，组合调整能解释相当一部分误差量级；但均值接近不等于逐项对齐，例如组合调整后 CU 为 0.6999（论文 0.8035）、CS 为 0.6636（论文 0.5410）；
- 2-star 即便组合调整，仍比论文均值高约 59.5%。更早的 1 万次 ceil/floor 配对诊断中，只改取整使 CU 2-star 0.17141→0.15983、Do 0.10433→0.09840，六图改善约 0.04%–6.8%；
- **预算**：跳过噪声图后按 $\varepsilon_2:\varepsilon_3=1:4$ 重分配，总预算仍为 2，没有预算浪费。单独扫描 $\varepsilon_2\in\{0.2,\dots,1.2\}$、$\varepsilon_3=2-\varepsilon_2$：CU / 2-star 最低约 0.1604、Do 最低约 0.1015（都在 $\varepsilon_2=0.6$），仍高于论文 0.1062/0.0585；ML、EE、PM 更偏好把预算留给报告阶段。这组候选里不存在统一调一个比例就对齐六图的结果（不是对所有连续预算的穷尽证明）；
- **投影**：去掉邻居投影后 ML 2-star 0.08346→0.08051，PM 0.04514→0.04484，仍远高于论文 0.0444、0.0284，投影不是 2-star 差距的主要解释。该对照不满足原 GS 前提，只用于归因；
- **非负截断**：对非负真值不会增大绝对误差。CU / 3-star 截断前 RE=1.0811，截断后 0.8821，约 20.19% 输出为零。截断降低误差，不是大 RE 的来源。按节点先截断与先求和后截断是不同机制，项目执行后者。

## 26. GT-Naive 与 GT-PSC-B 的表格约束

按依赖顺序定位：GT-Naive 的 RR/任务计数 → GT-PSC-B 的局部计数、基础 GS、报告噪声、聚合 → GT-PSC 新增的最大度、预算、投影、优化 GS。GT-PSC-B 不做最大度估计和投影；若它已偏离，就不能把 GT-PSC 的差距全部归因于 noisy max。PSC-B 也改变报告预算，比较时要记录。

**RR 期望恒等式**：设 $p=1/(1+e^\varepsilon)$、$q=1-2p$、$N=n-1$，

$$E[T_2(\mathrm{RR}(G))]=q^2T_2(G)+pq(N-1)\cdot2m+np^2\tbinom{N}{2}$$
$$E[T_3(\mathrm{RR}(G))]=q^3T_3(G)+pq^2(N-2)T_2(G)+p^2q\tbinom{N-1}{2}\cdot2m+np^3\tbinom{N}{3}$$

把论文 GT-Naive 的大幅正偏近似为有符号 RE 后反推，六图 $T_2/T_3$ 与当前真值相对差异均 < 0.5%。这进一步降低了任务定义或真值相差很大的可能性，但不能证明边集合与作者完全相同。

**PSC-B 报告尺度**：固定准确原始计数，用 Laplace 和的闭式分布计算期望 RE，与 Table 3 对照（legacy 尺度）：

| 数据集/任务 | 当前 PSC-B 理论 RE | 论文 PSC-B | 论文点值当期望反推的尺度/当前尺度 |
|---|---:|---:|---:|
| CU/2-star | .44858 | .4487 | 1.0003 |
| Do/2-star | .29732 | .2580 | .8667 |
| CU/3-star | 5.17179 | 4.6370 | .8864 |
| Do/3-star | 2.71710 | 2.4373 | .8780 |

比例不统一，不能乘全局校准常数，更不能按数据集写系数；反推只定位所需变化量，也可能包含有限样本波动。

## 27. 固定 D 为真实最大度的反事实

直接固定 $D$ 为真实最大度，去掉估计 D 的误差，仍保留每节点独立报告、$\varepsilon_3=1.6$：ML / 2-star RE 仍为 0.0794（论文 0.0444），PM 仍为 0.0448（论文 0.0284）。CU 的高误差可以大量归因于 D 高估，但 ML/PM 的 2-star 差距不能用相同理由解释。使用真实最大度只是离线反事实，不是可部署的隐私方法。

## 28. 与上游 Imola 2021 源码的对照

USENIX Security 2021（Imola、Murakami、Chaudhuri）Section 4.1 / Algorithm 1 使用本地度裁剪、组合数计数和独立 Laplace 报告，源码对应 `CalcNSMaxDeg`、`CalcNLocSt`（固定版本 `a0707f6`，`cpp/EvalLossLocal.cpp`）。该源码是 2021 年基础算法，不是 PSC 作者实现。

| 环节 | PSC 项目（legacy） | Imola 2021 C++ 源码 |
|---|---|---|
| 带噪最大度 M | $\max_i(d_i+\mathrm{Lap}(1/\varepsilon_2))$ | 同样估计，另外限制在 $[0,n-1]$ |
| 本地投影阈值 | ceil(M) | floor(M) |
| 2-star 灵敏度 | ceil(M) | 连续 M |
| 3-star 灵敏度 | $\binom{\lceil M\rceil}{2}$ | $M(M-1)/2$ |
| $\varepsilon=2$ 的预算 | 最大度 0.4，报告 1.6 | 默认最大度 0.2，报告 1.8 |
| 报告节点数 | 全体 n | 全体 n |
| 星计数的最终非负截断 | 有 | `CalcNLocSt` 和 loss 评估路径没有 |
| 无优化最大度 | n | n−1 |

基础论文正文把 floor(M) 作为下一轮输入，C++ 却对 GS 保留连续 M，两者不能混为同一变体。

**翻译核对**：从源码提取上述两个函数的原始函数体，仅用固定噪声序列替换随机采样器；六图 × 两种预算共 1200 个样本与独立 Python 公式比较，2-star 最大绝对差约 2.62e-10、3-star 约 8.85e-9，采样调用数一致（不声称随机数流相同，也没有运行完整原程序）。

每图 5 万次同基础噪声模拟（新固定种子，数值与 §23 略有差异）：

| 机制 | 2-star | 3-star |
|---|---:|---:|
| legacy | 0.11418 | 0.45134 |
| C++ 的 floor 投影 + 连续 GS，保留 PSC 预算与截断（≈ continuous_bound） | 0.11162 | 0.43252 |
| 基础论文的 floor 投影 + 整数 GS，保留 PSC 预算与截断（≈ floor_bound） | 0.10870 | 0.41305 |
| C++ 默认预算 0.2/1.8、原报告与 loss 语义 | 0.14476 | 1.03660 |
| 上一项 + PSC 最终非负截断 | 0.14426 | 0.75547 |
| PSC 论文 Table 2 | 0.0647 | 0.3649 |

这些变体没有解释 2-star 差距；照搬上游默认预算反而因最大度噪声更大使 CU/CS 恶化。

## 29. 机制族的理想下界

**机制族**：本地度裁剪、共同灵敏度、所有节点独立 Laplace 报告、直接求和、最终非负截断。给这一族过于有利的条件：

1. 免费知道当前图，枚举 $D=0,\dots,n-1$ 选使期望 RE 最小的整数阈值；
2. 省去最大度估计的开销，把完整 $\varepsilon=2$ 用于计数报告；
3. 使用紧 GS $\binom{D-1}{k-1}$，允许最终非负截断。

2-star 结果：

| 数据集 | 最佳整数 D | 机制族最优期望 RE | 论文 GT-PSC |
|---|---:|---:|---:|
| CU | 7 | 0.06233 | 0.1062 |
| Do | 11 | 0.04898 | 0.0585 |
| ML | 35 | **0.06067** | **0.0444** |
| CS | 11 | 0.11443 | 0.1210 |
| EE | 40 | **0.03646** | **0.0295** |
| PM | 236 | **0.03571** | **0.0284** |

ML、EE、PM 的论文点值低于这个理想化机制族的最小期望。若论文均值能稳定复现，则至少有一项假设不同：实际输入图、灵敏度/报告机制、报告独立性或同尺度假设、聚合/校正估计器、评估实现。它不支持继续把问题归咎于 ceil 或 $\varepsilon_2$ 比例。这不是所有 LDP 算法的下界，也不是论文错误的证明；论文报告的是 1000 次有限样本均值，没有逐次结果和方差，有限样本均值可以低于期望。

**随机 D 为什么不能解决**：给定 D 后风险为 $R(D)$，若报告噪声独立于选择 D 的随机量，则 $E_D[R(D)]\ge\min_D R(D)$。

**期望误差闭式**：设真值 $T=\sum_i\binom{d_i}{k}$，裁剪后无噪声总计数 $A(D)=\sum_i\binom{\min(d_i,D)}{k}$（$0\le A\le T$），报告尺度 $b$，$S=\sum_i L_i$（$L_i$ iid 标准 Laplace），$Y=\max(0,A+bS)$，$H_n(t)=E[(S-t)_+]$，$B=T-A$。由 $S$ 的对称性：

$$E|Y-T| = B + 2b\,H_n(B/b) - b\,H_n(A/b)$$

$b=0$ 时为 $|A-T|$；最后一项是最终非负截断减少的绝对误差。$S$ 是两个独立 Gamma$(n,1)$ 之差，对 $s\ge0$：

$$f_S(s)=\tfrac12\sum_{j=0}^{n-1} w_j\, e^{-s}\frac{s^j}{j!},\quad w_j=\frac{(2n-2-j)!}{(n-1-j)!\,(n-1)!\,2^{2n-2-j}},\quad \sum_j w_j=1$$

由此积分得 $H_n$，脚本用对数概率计算避免溢出。验证：$n=1$ 与单 Laplace 闭式一致；$H_n(0)=\Gamma(n+\frac12)/(\sqrt\pi\,\Gamma(n))$；$n\in\{1,2,49,77,143,453\}$、四组 A/T/b、各 30 万个 Gamma 差样本与闭式比较，全部在六倍标准误内（最大 2.37 个标准误），覆盖 $b=0$、$A=0$、$A=T$、$0<A<T$。

**为什么给足报告预算是有利边界**：$A\ge T/2$ 时 $B\le A$，风险对 $b$ 的导数为 $2J(B/b)-J(A/b)\ge0$，其中 $J(t)=E[S\,\mathbb 1(S>t)]$ 随 $t$ 减少；$A<T/2$ 时至少一半噪声满足 $S\le0$，期望 RE $\ge (T-A)/(2T)>1/4$。表中所有最优 2-star RE 都小于 1/4，所以更小的报告 $\varepsilon$ 不会产生更优解，枚举结论可推广到全部 $\varepsilon_3\le2$。

## 30. EE triangle 的局部差距

triangle 的六图均值接近论文，但 EE 当前 0.4059、论文 0.2803，高 44.8%。EE 再跑 5000 次得 0.39993（均值标准误约 0.00373）；加 Laplace 前平均聚合计数约 609.80，真值 889。差距在新随机流下持续存在，但尚无证据唯一归因于投影。

拆分方法（尚未执行）：同一原图、同一 RR 抽样、同一带噪度数和同一标准 Laplace 向量下记录五个量：$T$（原图精确数）、$Y_{RR}$（未投影噪声图、按 PSC 真实邻居/update 规则计算，不是简单数噪声图的三角形）、$Y_{proj}$（投影后同规则）、$Y_{noise}$（加 Laplace、截断前）、$Y_{final}=\max(0,Y_{noise})$。逐次验证有符号恒等式

$$Y_{final}-T=(Y_{RR}-T)+(Y_{proj}-Y_{RR})+(Y_{noise}-Y_{proj})+(Y_{final}-Y_{noise})$$

RE 含绝对值，不能把各阶段 RE 直接相加。先比较随机节点顺序与固定节点顺序的对称投影，必要时再实现“同时保留选择的交集”等有明确定义的无向有界投影候选；候选共享事先定义的随机优先级并保持各自宣称的边缘分布。不投影和单边裁剪只能作为离线反事实，不能因误差更低就并入同一隐私参数下的正式比较。另需小图穷举检查：固定噪声消息图，逐比特改变真实邻居，检查局部计数差分。

## 31. 诊断结论

1. pilot 的大误差来自隐私机制噪声和 3 次抽样波动；换成精确节点计数几乎得到相同结果。k-star 的主要问题不在 prompt 或节点计数能力，没有证据支持“换更强 LLM 就能对齐论文 GT”；
2. 本地机制的长期均值与论文确有差距。3-star 对取整和组合数上界敏感，floor_tight 已解释大部分；2-star 不能由取整、紧界、预算比例或投影解释，且 ML/EE/PM 的论文点值低于该机制族的理想期望下界；
3. 尚无证据唯一确定作者实现与本项目在哪一处不同，不能表述为“已找到唯一代码 bug”或“作者一定用了更小噪声”。需要作者 k-star 库与 GT 脚本中的 D、GS、$\varepsilon_3$、报告噪声、聚合与截断位置、数据预处理版本（附录 A）；
4. 正式比较使用固定机制、足够 DP 重复和同噪声规则参考；增加次数会让 pilot 接近本地 GT，但不会消除本地 GT 对论文的差距。

## 32. 作者实现检索

截至 2026-09-28，未找到能确认属于 PSC 作者的公开实现。“未找到”不能推出“作者没有公开”。

| 来源 | 核验结果 | 限制 |
|---|---|---|
| ACL 官方论文页 | 2026.acl-long.1032，题名与五位作者一致；无代码链接 | 页面上的 GitHub 链接是 ACL Anthology 自身仓库 |
| 官方 PDF | 重新下载，SHA256 与本地 PDF 一致；嵌入 URI 无仓库链接 | 不能排除未链接的外部仓库 |
| ACL 附件 | 只有 Responsible NLP Checklist，无代码包或算法附件；Checklist 无代码地址 | Checklist 也没有承诺公开代码 |
| 第一作者 ACL 页 / ORCID | ORCID 0009-0002-3988-730X；researcher-urls 为空，既往论文含 ICDE 2025 LDP truss、EDBT 2024 bipartite community search | 公开信息可能不完整 |
| GitHub repo/README/issues 搜索 | 题名命中的只有 SecAI_Radar 文献列表；GT-PSC、DOI 无结果 | 不等于全代码搜索（未登录） |
| arXiv API | 精确短题名无结果 | 不排除其他题名的预印本 |
| 作者主页 | UNSW 第一作者地址 403，另一作者主页超时 | 无法核验 |
| 常规搜索 | 无可引用结果（Google 需 JS、DuckDuckGo 人机验证、Bing 不相关） | 不作为不存在代码的证据 |

链接：

- PSC 页面：https://aclanthology.org/2026.acl-long.1032/
- PSC PDF：https://aclanthology.org/2026.acl-long.1032.pdf
- Checklist：https://aclanthology.org/attachments/2026.acl-long.1032.checklist.pdf
- 第一作者 ACL 页面：https://aclanthology.org/people/yuting-zhang/
- ORCID：https://orcid.org/0009-0002-3988-730X
- 引用论文：https://www.usenix.org/conference/usenixsecurity21/presentation/imola
- 引用论文代码：https://github.com/LDPGraphStatistics/LDPGraphStatistics
- 核验源码固定版本：https://github.com/LDPGraphStatistics/LDPGraphStatistics/blob/a0707f6fc26b855c0ed5e8f052cc4117768948ed/cpp/EvalLossLocal.cpp

下载、搜索返回和文件哈希保存在 `results/research/2026-09-28-author-implementation/`，上游源码按 MIT 许可保留 LICENSE。

## 33. 贴近论文时的选择原则

这些原则约束了 §14 的候选选择，也适用于以后的机制调整：

- 固定论文明确的部分：任务定义、原图与真值、$\varepsilon=2$、RE 定义；保留 PSC 的估计最大度、投影、节点报告、聚合结构；GT 与 agent 共用配置，不能只改 GT 输出；
- 候选必须有依据（论文文字、引用源码、数学推导），不做任意参数堆叠；主比较固定 $\varepsilon_2=0.4$、$\varepsilon_3=1.6$，不逐数据集改预算或机制；允许不同任务因数学定义使用不同 GS；
- 按节点提前截断、重复发布求平均等没有原文依据的操作不作为候选；不满足所选 GS 前提的组合只作定位；
- 评分用逐格 log 比例，按唯一单元格计权，同时报告每格差距和最大差距；显著变差的单格必须解释，不能用许多小格的改善掩盖大幅退步；
- 运行次数：新组合每格 5000 次，排名接近的关键候选补到 20000 次；配置冻结后用预先固定的新随机流生成每格 1000 次的论文格式结果；用独立 1000 次组均值分布检查小样本不确定性，不通过重复运行挑最接近论文的一组；
- Exp2 的 ε 趋势可作辅助一致性检查，图中读数注明读图误差；
- 不能为贴表格数字无依据地缩小噪声，不能预先承诺全部格子误差 < 5%，论文表值不进入估计器运行时；按表值选择的配置要注明“选择用到了论文表值”，留一数据集检查只是稳定性分析，不是未见测试集；
- 若共同尺度独立报告族内的候选都不能进一步贴近 2-star，停止该族内的取整/预算重跑，保留最佳有依据配置和剩余差距。

---

# 第五部分 改进方案

## 34. 带噪度数 + 组合数矩校正估计器

两条路线要分开：

- **忠实复现路线**：保留 floor_tight（及 legacy 等候选）作为“按公开描述实现”的基线，登记每个变体的数据哈希、ε 分配、取整、GS 和截断位置，默认基线不因某候选更接近论文而被覆盖；向作者索取材料（附录 A）；取得后先对齐度向量、真值，再比较 M、D、GS、$\varepsilon_3$、噪声、聚合，不只比较最终 RE；若取不到，结果标为按公开描述实现并报告未解释差距。
- **降低实际误差路线**：本节的新估计器。它与 PSC 是不同的估计器，必须单独命名、单独记录预算，不能替换原表并宣称论文复现成功，也不主张方法新颖性。（README 中的 `adaptive_2star` 是另一条为贴近论文而调参的路线，与本节无关。）

### 34.1 方法

对只依赖度数的 k-star，每个节点只发布一次 $y_i=d_i+\mathrm{Lap}(0,b)$，$b=1/\varepsilon$。在论文的每节点单比特 ε-edge LDP 定义下度数灵敏度为 1，后续星计数只用 $y_i$，属于后处理；2-star 与 3-star 可复用同一次发布。这里不宣称完整图转录满足相同 ε 的 relationship DP；若要同时保护无向边两端，需重新按 relationship DP 分配两端预算。

$\binom{y_i}{k}$ 不是无偏估计。由 $E[L]=0$、$E[L^2]=2b^2$、$E[L^3]=0$：

$$\hat T_2=\sum_i\Big[\frac{y_i(y_i-1)}{2}-b^2\Big],\qquad \hat T_3=\sum_i\Big[\frac{y_i(y_i-1)(y_i-2)}{6}-b^2(y_i-1)\Big]$$

两式在最终截断前对真实总计数无偏。节点侧不能先把 $y_i$ 或校正项截为非负；最终求和后可选截断，但此后不再严格无偏。

方差依赖各节点实际度数的矩，而不是统一最坏尺度。2-star 单节点方差为 $2b^2(d_i-\frac12)^2+5b^4$，总方差 $2b^2\sum_i(d_i-\frac12)^2+5nb^4$，与 legacy 的 $2n(D/\varepsilon_3)^2$ 本质不同：枢纽节点不再让所有低度节点付出同样代价，也不需要 noisy max 和 0.4/1.6 两轮。但方差仍随度数增长，最坏情况仍可达 $nD^2$ 量级；3-star 依赖度数四阶量，仍有 Laplace 多项式的尾部风险。

### 34.2 已有纯代码结果（$\varepsilon=2$，每图 10 万次，含最终截断）

| 数据集 | 新候选 2-star RE | 新候选 3-star RE |
|---|---:|---:|
| CU | 0.03951 | 0.07476 |
| Do | 0.02649 | 0.04610 |
| ML | 0.01504 | 0.02626 |
| CS | 0.03820 | 0.06897 |
| EE | 0.00929 | 0.01650 |
| PM | 0.00279 | 0.00479 |
| **六图平均** | **0.02189** | **0.03956** |
| legacy 六图平均 | 0.11418 | 0.45134 |
| 论文 GT-PSC | 0.0647 | 0.3649 |

相对 legacy 平均 RE 降低约 80.8% 和 91.2%。验证：$d=0..453$、两种任务共 908 组噪声矩代数检查；每图截断前平均估计与无偏期望一致；JSON 记录解析方差、经验方差和标准误。这是固定 $\varepsilon=2$ 的纯代码结果，不是集成后或真实模型的性能承诺。新估计器不属于 §29 的机制族，误差更低不与该族下界矛盾。

### 34.3 集成方案（尚未实施）

计算路径：可信节点代码计算真实 degree → 只发布一次 $y_i$ → 代码计算校正多项式并求和 → 可选非负截断 → curator 返回数值或解释。LLM 仍可解释任务、选择算法或处理已发布的 $y_i$；确定性多项式优先交给工具。研究 LLM 算术时可增加只接收同一组 $y_i$ 的 LLM 后处理分支，与精确代码参考配对评估。

信息边界：真实 degree 的计算和加噪在可信节点执行；外部 LLM 只拿公开任务和已发布数据；已用完整 ε 发布 $y_i$ 后，不再同时发布消耗额外预算的真实计数报告；反复重新扰动并对外发布会累积隐私开销；不能把私有 degree 直接当噪声尺度而沿用原 DP 论证。

| 文件 | 修改目的 | 必须核对的行为 |
|---|---|---|
| 新增 `psc/kstar_estimators.py` | 两种校正估计器，接受 noisy degree 和 scale | 输入为实数；不提前截断；返回截断前/后值 |
| `psc/agents/node_agent.py` | 复用或封装可信 degree 发布 | 每个任务组只发布一次 |
| `psc/agents/privacy_controller.py` | 增加 degree 发布策略 | 不再执行 noisy max 和计数报告两轮 |
| `psc/framework.py` | 显式机制分支和 trace | 记录发布数据、scale、输出、预算；不通过私有图临时挑分支 |
| `psc/experiments.py` 与运行脚本 | 分别登记 GT、LLM 后处理和旧 PSC | 方法名、噪声记录与比较口径分离；不覆盖旧结果 |
| `tests/` | 数学与信息流约束 | 小 degree、负 noisy degree、多项式均值/方差、同噪声回算、预算不重复消费 |

### 34.4 采用前的评估

1. 固定数据、公式、seed 规则和指标，使用独立于探索阶段的验证种子。不同机制可共享标准 Laplace 向量，但须按各自 scale 变换；
2. 先做六图 × 两任务 × $\varepsilon\in\{1,2,3\}$ 的纯代码比较，记录平均 RE、标准误、中位数、P95、截断前偏差/方差和零输出率（目前只完成 $\varepsilon=2$）；
3. 同时比较平均效应与尾部风险，不能因六图平均下降就接受某数据集高分位恶化，不依据论文点值回选 seed 或参数；
4. 纯代码稳定后，在同一已发布数据上比较代码与 LLM 后处理，执行失败、解析失败、算术错误分别计数；
5. 对外区分 $E|\hat f-f|/d$ 与 $|E\hat f-f|/d$；多次采样只用于离线估计误差分布，不能把多次公开发布的平均当成单次 $\varepsilon=2$ 的结果。

---

# 第六部分 工作计划

## 35. 四阶段执行计划

目标是形成可解释、可回放的复现结果：先确定代码机制，再固定评估系统，然后完成主实验，最后补消融和扩展。规划总工程量约 14–22 人日（不含 API 与 CPU 运行），主要不确定因素是未知机制细节和实际模型吞吐。阶段一未定时可以开发阶段二的通用日志工具，但正式批量模型运行必须等实验协议冻结。

| 阶段 | 核心问题 | 主要交付物 | 进入下一阶段的条件 |
|---|---|---|---|
| 1. 对齐代码机制 | k-star 和 EE triangle 的差距从哪一步产生？ | 机制规格、独立校验器、逐阶段诊断、差距归因表 | 已确认错误已修复；未确定部分有明确候选和证据边界 |
| 2. 建立可回放评估 | 同一输入、同一噪声下，模型和系统分别错在哪里？ | 噪声记录、调用轨迹、严格解析、断点续跑、统一指标 | 离线回放与并发一致性通过，失败不再静默变成成功 |
| 3. 完成论文主实验 | 按论文角色、数据和次数，结果如何？ | Table 2 对照、运行明细、不确定性和成本 | 48 个实验格都有明确完成状态，论文值与本地 GT/LLM 分开报告 |
| 4. 完成消融与扩展 | 收益分别来自什么，边界在哪里？ | Exp2–9 对照、归因、成本、大图采样 | 每项论文结论都有对应实验或明确的未验证说明 |

### 35.1 优先级与当前状态

| 优先级 | 工作 | 完成标准 | 当前状态（2026-10-15） |
|---|---|---|---|
| P0 | 冻结代码/数据/配置与随机流，补齐逐次轨迹 | 每个异常可定位到输入、DP 各阶段、原始输出和解析结果；修复前后可重放同一噪声 | 部分：`manifest.json`、`mechanism_trace`、`RunTrace`、`--save-transcripts`；无 NoiseTape 与回放工具 |
| P0 | 对齐 k-star 的 GS、预算和报告机制 | 持续差距有独立推导或作者代码证据解释；不以缩小噪声贴表为目标 | 部分：`mechanism.py`、`align_gt_psc.py`、默认 floor_tight；2-star 未解释 |
| P0 | 拆分 EE triangle 的 RR、投影和 Laplace 贡献 | 解释约 0.400 vs 0.2803 的差距 | 未做（§30） |
| P1 | 严格数值解析、任务一致性检查、失败口径 | 语义无效输出不再被误认为成功；保留原始失败和回退统计 | 未做：仍是最后一个数字兜底、任务不一致只警告 |
| P1 | 按论文模型/次数补六数据集主实验 | node/curator 配置可核实，每格 ≥10 次，独立 GT ≥1000 次，报告不确定性 | 进行中：已有 gpt41/gpt41-mini 等 exp1 结果和 floor_tight 1000 次 GT |
| P1 | 同一模型上补 PSC-noDP、RAW/REFINED、PSC-B 和预算消融 | 能分别判断多 agent 分解、模型能力、隐私机制、GS 优化和提示词的贡献 | 入口已有（exp3–exp6、`--with-nodp`） |
| P1（私有数据部署时） | 落实节点可信边界与发布接口 | 真实邻接与未加噪轨迹只在授权环境可见，实际释放函数的隐私条件明确 | 未做（§20） |
| P2 | Exp7 模型对照、Exp8 token 统计、Exp9 采样大图 | 形成附录对应证据，采样不确定性与 DP/模型误差分开 | 未做 |

### 35.2 阶段一：对齐纯代码机制（4–6 人日）

**1.1 冻结起点和机制规格。** 保存完整可复现源码快照（含未提交修改和相关未跟踪源码、依赖版本、数据/论文哈希、参数；排除 `.env`、密钥、缓存）。新增 `docs/MECHANISM_SPEC.md`（未建），按任务记录 RR、预算、投影对象、灵敏度、报告机制、聚合和截断，每项给出来源页码并标注“论文明确 / 论文矛盾 / 项目补充 / 诊断候选”。技术推导只使用原文、作者代码和其引用的原始论文。

**1.2 最少量的离线诊断数据。** `RunTrace` 与 `dp.py` 的可选 trace 默认不改变行为、不额外消耗随机数，需记录：原图 n/m、度向量、最大度、真值与数据哈希；ε1/ε2/ε3、逐节点 noisy degree、取整前后 D、GS、实际 Laplace 尺度；RR 后图、投影后图及其哈希；投影的节点顺序、保留的邻居、度变化、删边总数；原始/投影后本地计数、加噪前总计数、逐节点噪声、加噪后报告；聚合与截断前后值。另建独立参考校验器（如 `psc/audit_reference.py`），直接从度向量、邻接集合和公式计算，不导入 `rules.update`、`rules.aggregate` 或被校验的 GS 函数；只用于审计，不作为模型失败时的答案兜底。

**1.3 k-star 逐项检验**（每次只改一个因素；已完成部分见第四部分）：

| 顺序 | 检验 | 方法 | 状态 |
|---|---|---|---|
| K1 | 计数正确性 | 从度向量独立算 $\binom{d_i}{k}$，验证裁剪后恰为 $\binom{\min(d_i,D)}{k}$ | 完成（§23，1200 次 trace 核对） |
| K2 | 预算解释 | 从推导到实际日志核对 ε3，无预算丢失或重复消耗 | 完成（§25） |
| K3 | 灵敏度定义 | 分别列出数学紧界、论文上界、项目实现 | 完成（§4.2） |
| K4 | 噪声实现 | 固定 D 下验证每节点均值 0、方差 $2(GS/\varepsilon_3)^2$ | 部分（§29 闭式验证） |
| K5 | D 的分布 | D−d_max、裁剪比例、物理上界、ceil/floor 配对差异 | 完成（§24） |
| K6 | 最终截断 | 截断前有符号偏差、方差、负值比例、截断后 RE | 完成（§25） |

**1.4 EE triangle**：按 §30 的五量分解与投影候选执行。

**1.5 实验矩阵与归因：**

| 轮次 | 范围 | 重复数 | 用途 |
|---|---|---:|---|
| 开发诊断 | CU/Do 的 2-star、3-star，EE triangle | 每格先 1000 | 定位主要因素，保存逐阶段分布 |
| 重点确认 | 仍有差距的任务与候选 | 每格 5000 | 均值、标准误、分位数、配对差异 |
| 回归 | 六图 × 四任务 × GT-Naive/GT-PSC | 每格 1000 | 确保修复不影响已对齐部分 |
| 保留验证 | 冻结后用独立种子库 | 每格 1000 | 防止在已见种子和论文数字上反复调参 |

大量运行只存紧凑逐次统计，全量中间图只用于固定诊断样本和异常样本。均值和标准误以整次运行为单位，不把同一运行的多个节点当独立实验。输出 `results/alignment/<experiment_id>/`（`manifest.json`、`runs.jsonl`、`stage_summary.csv`、`hypotheses.csv`）与 `docs/ALIGNMENT_FINDINGS.md`；每项假设判为“证实 / 排除 / 证据不足”，记录效应大小、实现与来源。

完成标准：独立计数与预算检查通过，确认的错误已修复，重点差距定位到阶段和参数，无法核实的作者细节有清楚范围。不设“必须落入论文均值 5% 以内”之类拟合目标；论文缺少方差，论文点值未落入本地置信区间也不自动构成显著差异。若无法严格对齐，可进入阶段二，但后续主实验必须标为“按公开描述实现”。

### 35.3 阶段二：建立可回放评估（4–6 人日）

**2.1 显式化随机性**（建议新增 `psc/randomness.py`、`psc/trace.py`，未建）：

| 对象 | 必需内容 |
|---|---|
| experiment_id | 不可覆盖的实验标识、代码快照、参数和数据版本 |
| run_id | 数据集、任务、方法、ε、重复序号、模型配置、实验版本 |
| noise_id | 配对样本标识与各阶段基础随机量哈希 |
| NoiseTape | 按规范边顺序存的 RR uniforms、度噪声标准 Laplace 向量、投影随机优先级、报告标准 Laplace 向量 |
| mechanism_id | 预算、GS、取整、投影、聚合和截断规则的版本 |
| llm_replicate | 固定噪声下的模型重复序号，与 DP 重复序号分开 |

用独立阶段子流，用稳定哈希或显式编码生成种子（不用 Python 内置 `hash()`）；不同数据集/任务默认用不同子流，需要配对时通过明确的 pairing_group 共享。同机制的 GT/agent 可重用同一噪声图与实际噪声；不同 ε 或 GS 的方法可共享 uniforms 和标准 Laplace Z 再各自变换，但不能给 ε1 不同的 Naive 与 PSC 强行使用同一张已扰动的图。历史结果保留原 RNG 版本，不能把随机流变更前后的结果当成修复前后配对。

**2.2 记录全部调用。** 每次逻辑调用有稳定 call_id，每次网络尝试有 attempt_id；记录 agent/阶段/节点/输入哈希/实际 prompt/原始回复/解析结果/校验结果/异常原因/重试/耗时/实际模型标识。usage、finish_reason、request_id 只在接口返回时记录，缺失写 null，不伪造。日志不含凭据；真实邻居、未加噪计数及包含它们的 prompt 只存可信审计存储。聚合 prompt 把数值格式化到 4 位小数，应同时保存原始报告与显示数值，增加 `aggregate_reference_displayed` 与 `aggregate_reference_full_precision`，把舍入差异与算术误差分开；改变显示精度需要 prompt 版本号。

**2.3 统一解析与失败语义**（建议新增 `psc/parsing.py`，未建）：

- 只接受完整结果 JSON、完整单个数值文本或明确的最终答案标记，拒绝正文中任意的最后一个数字；
- 拒绝 bool、NaN、Inf、溢出及字段类型不匹配，保留原文和失败原因；
- send 核验 Sender_ID 与调用节点一致、编号范围、列表格式；格式规范化与语义改写分开记录，不能悄悄改成正确邻居集合；
- degree/k-star 局部计数应为非负整数，triangle 应为规则允许的半整数；类型合法但算错的值保留为模型错误，不用 GT 替换；
- curator/controller 任务不一致时该次标为无效；代码回退若保留，记录原始与回退后结果，并与无回退实验分开命名；
- 固定三类状态：调用可用但模型算错 / 协议或解析失败 / 框架执行失败；区分合法零估计与失败后零兜底。现有容错策略（send 丢弃、update 保持初值、aggregate 返回零）作为明示的 pipeline policy 记录；严格模式报告缺失，不把缺失当正确零；
- 不通过反复重跑挑成功答案；基础设施的可重试错误按预先固定的策略恢复并保留全部尝试。

**2.4 执行器与持久化。** 已实现：逐次 `runs.jsonl`、防覆盖目录、`--dry-run`（pilot/exp1）、`--methods`（exp1/exp2/exp3）。未实现：原子 checkpoint、`--resume`、`--experiment-file`、由记录重建 summary、噪声版本选择。resume 只复用数据、机制、prompt、解析策略、模型配置都一致的完整结果；中断的单次运行可用固定 tape 从头重跑并记录新增成本；不承诺远端请求 exactly-once。

**2.5 指标拆分。** 设 a 为 LLM 估计，b 为同机制同噪声的规则估计，d=max(truth, 0.001n)：

| 指标 | 定义/用途 |
|---|---|
| RE_LLM | mean(\|a−truth\|/d)，最终效果 |
| RE_paired_rule | mean(\|b−truth\|/d)，该批样本的机制效果 |
| delta_mean_RE | \|mean(RE_LLM)−mean(RE_rule)\|，旧口径，可能抵消 |
| mean_abs_RE_gap | mean(\|RE_LLM−RE_rule\|)，避免跨次抵消 |
| mean_normalized_estimate_gap | mean(\|a−b\|/d)，直接度量输出偏离，避免真值两侧等 RE 掩盖差异 |
| signed_bias / quantiles / zero_rate | 偏高偏低、长尾与截断 |
| node/send/aggregate accuracy | 只用于定位局部推理，不作为独立 DP 重复数 |
| coverage / failure rates | planned/completed/invalid/fallback 数量 |
| delta_GT_reference | 与独立 GT 均值比较，标明 GT 样本数，不与配对 delta 混淆 |

置信区间按完整运行抽样；共享 noise_id 时对配对差值 bootstrap。十次结果提供全部逐次值；扩大重复数作为预先定义的补充实验，保留原十次表。（README 中已实现的 `delta_signed`、`exec_deviation` 等覆盖了其中一部分。）

**2.6 验收。** 固定 tape 下 GT/mock/规则逐阶段一致；并发 1/8 时机制和排序一致；改解析器回放同一原始回复得到预期结果；NaN/Inf/正文数字探针被拒绝；中断恢复不丢数据、不重复统计；汇总可由运行记录重建；日志无凭据。真实接口预检只验证可用性、角色配置、追踪和失败记录，不以模型高准确率筛样本。交付 `scripts/replay_experiment.py`、统一实验配置模板、回归测试、小型回放样例与 `docs/EVALUATION_PROTOCOL.md`（均未建）。

### 35.4 阶段三：补齐论文主实验（2–3 人日，API 另计）

**3.1 冻结协议。** 用单独的论文配置（计划为 `configs/paper.toml`；目前可用 `config.toml` 的 `--profile gpt41` 或 `oaifree` 加 `--node-model gpt-4.1-mini --curator-model gpt-4.1`）：node=GPT-4.1-mini、curator=GPT-4.1、temperature=0、ε=2、六图四任务、PSC/Naive 每格 10 次。执行前核实模型可用性与返回标识，不把 OpenAI-compatible provider 名称等同于论文模型；原版本不可用或别名指向不同快照时记录并独立命名。控制器模型、stream、token 上限、超时、重试、并发、prompt/解析版本、回退策略写入 manifest。选 10 个固定 DP 重复编号，独立 GT 种子库每格 ≥1000 次；固定十次主表后才按事先规则决定是否增加到 30 次，新增结果单列。

**3.2 预检与正式运行分开。** 先在 CU/Do/EE 的代表性调用上预检 node send、update、aggregate、Naive 大 prompt、stream 重试和 usage；预检前后改配置的调用不计入正式实验。PM 的 Naive triangle prompt 约 15 万 token，需先确认能放入实际上下文，不能静默截断或更换图表示后仍标“同条件”。模型质量差不是删除样本的理由；接口配置错误、意外截断或日志损坏才是修协议的依据。

**3.3 分批完成 Table 2：**

| 批次 | 数据集 | 10 次 PSC+Naive 的逻辑调用数 | 目的 |
|---|---|---:|---|
| A | CU、Do | 5,950 | 验证小图与角色模型 |
| B | ML、CS | 8,550 | 覆盖不同度分布 |
| C | EE | 7,350 | 验证 triangle 差距 |
| D | PM | 22,850 | 大 prompt 与高阶计数 |
| 合计 | 六图 | 44,700 | 480 次完整运行 |

GT-Naive/GT-PSC 共 48 格各 1000 次（48,000 次纯代码运行），计算成本与 LLM 调用分开统计；机制变更使受影响格子的旧数据不能直接复用。用预检得到的每阶段平均 token、p50/p95 延迟和吞吐预测预算，不用 hy3-ioa 的耗时直接外推。

**3.4 输出与解释。** Table 2 全表列出论文点值、独立 GT、同噪声规则、LLM 均值、标准差/区间、十次明细、覆盖率、失败与兜底次数、调用与 token 成本；EE triangle、PM k-star 必须逐项显示，exact count 保留为独立列。回答：GT 是否支持机制对齐；LLM 在同机制上增加多少误差；PSC 相对 Naive 是否改善、改善多少；差异是否可由模型配置、prompt、机制或未知论文细节解释。原模型不可用或机制细节无法确认时，结论限制为“公开描述复现 / 替代模型实验”。

### 35.5 阶段四：消融与扩展（4–7 人日，运行另计）

执行顺序 Exp3 → Exp5/Exp6 → Exp2/Exp4 → Exp7/Exp8 → Exp9。原论文设置保留，额外诊断条件单独标记。

| 实验 | 设计 | 回答的问题 |
|---|---|---|
| Exp3 | CU/Do × 2-star/3-star/triangle × PSC/PSC-B × 10 | GS 优化贡献多少？去掉该步同时改变 ε2 和 ε3，主对照按论文定义；“固定报告预算只改 GS”只能作额外诊断 |
| Exp5 | 六图 × 四任务 × RAW/REFINED/PSC-noDP × 10 | 无 DP 时是否仍需多 Agent 分解？按节点度、消息数、prompt 长度分组看 update 误差；核对非 DP 模式的 system prompt 不再声称只能看到噪声图 |
| Exp6 | 六图 × 四任务 × Naive RAW/REFINED × 10 | 提示词增强对噪声图是否仍有效？ |
| Exp2 | CU/Do × 四任务 × PSC/Naive × ε∈{1,1.5,2,2.5,3} × 10 | 精度与 ε 的关系和方法排序是否稳定？ |
| Exp4 | CU/ML triangle，r1、r2 ∈ {0.1,0.3,0.5,0.7,0.9}，每格 10 次 | RR 质量、D 估计和报告噪声如何相互影响？调参用开发种子，结果用保留种子，不把单数据集最优预算称为普适参数 |
| Exp7 | CU/Do × 四任务 × 额外模型组合 × 10 | 换模型后差异集中在哪一环？论文组合为 GPT、DeepSeek-Chat-V3.1、Qwen3-8B/Qwen-plus；hy3-ioa 作额外外推；每种角色分配是单独实验 |
| Exp8 | 图描述 token + 完整 pipeline usage | 固定 tokenizer 下的图描述 token（与 Table 7 同口径）、真实 input/output/cached/thinking token、重试成本；不同供应商 tokenizer 不等价，费用按执行时价格 |
| Exp9 | Facebook/Bible，均匀无放回采 200 节点，triangle | 采样、DP、LLM 各贡献多少误差？ |

Exp9：先用 exact count 验证三角形包含概率 $p=\binom{s}{3}/\binom{n}{3}$，估计 $\hat T=T_{sample}/p$；用大量纯代码子图评估采样方差与零三角形比例，再在固定子图上跑 DP 和 LLM。先固定 10 个子图、每个 1 个 DP 重复，方差大的子图再补多个 DP 重复；以子图为组估计不确定性。保存原始节点 ID 映射、节点列表、诱导子图边、采样 seed、noise_id 和缩放因子。采样本身不保证隐私，不能未经证明声称隐私放大；大图 GT 用稀疏/集合算法，避免稠密矩阵乘法。

复用完全相同配置的主实验结果时，按当前调用架构的新增逻辑调用（不含重试、预检、补充重复）：

| 实验 | 新增调用 |
|---|---:|
| Exp2：复用 ε=2 | 23,800 |
| Exp3：只新增 PSC-B | 4,620 |
| Exp4：复用 r1=0.5 主实验点（r2 网格不含 0.2，复用 2,580） | 23,220 |
| Exp5：无 DP 三方法 | 44,700 |
| Exp6：只新增 Naive+REFINED | 480 |
| Exp7：两组额外论文模型组合 | 11,580 |
| Exp9：两图各 10 个子图、每图 200 节点 | 8,060 |
| 阶段四合计 | 116,460 |
| 主实验 + 阶段四 | 161,160 |

Exp8 尽量复用前面日志，不追加调用。以上不是已发生费用。交付 `docs/ABLATION_FINDINGS.md`、曲线/表格、每个结论的证据路径与 Exp9 的误差分解。

### 35.6 工作包依赖

| 工作包 | 文件范围（新增名为建议） | 依赖 |
|---|---|---|
| A1 机制规格和基线冻结 | `docs/MECHANISM_SPEC.md`、快照工具 | 现有审计 |
| A2 中间量与独立校验 | `psc/dp.py`、`ground_truth.py`、`audit_reference.py`、`scripts/audit_mechanism.py` | A1 |
| A3 根因修复和回归 | 受证据支持的 dp/library/rules 变更、独立测试 | A2 |
| B1 随机记录和回放 | `psc/randomness.py`、`trace.py`、`framework.py`、`scripts/replay_experiment.py` | A2 |
| B2 调用追踪与解析 | `models.py`、`events.py`、`parsing.py`、`agents/` | B1 |
| B3 checkpoint/汇总/配置 | `experiments.py`、两个 runner、`configs/` | B1/B2 |
| C1 冻结正式协议并主实验 | `configs/paper.toml`、Table 2 配置、结果 | A3、B3 |
| D1 消融和模型/成本分析 | runner/配置、报告 | C1 |
| D2 采样与稀疏大图 | `psc/sampling.py`、`graph.py`、采样 runner | C1、阶段二日志 |

---

# 第七部分 运行说明与局限

## 36. CU / Do 每项 10 次的运行说明

在仓库根目录运行，沿用 `config.toml` 中的 hy3-ioa 和 `.env`：

```bash
cd /data/workspace/PSC
.venv/bin/python scripts/run_experiments.py --exp pilot --provider openai --datasets CU,Do --runs 10 --mechanism floor_tight --dry-run
.venv/bin/python scripts/run_experiments.py --exp pilot --provider openai --datasets CU,Do --runs 10 --mechanism floor_tight --tag hy3-ioa_cudo_r10_floor_tight --verbose
```

- 默认三项任务（degree、triangle、3-star；2-star 的 GT-PSC 机制未与论文对齐，默认不跑），PSC 和 Naive 每格各 10 次：2 × 3 × 2 × 10 = 120 次完整实验，约 4740 次模型调用（不含重试）；
- 加 `--tasks degree,2-star,3-star,triangle` 恢复四项任务：160 次实验，约 5950 次调用；保留两种范围的结果时用不同 tag；
- 并发来自 `config.toml`，启动时打印实际解析出的模型和机制；
- 结果在 `results/pilot/<tag>/`，目录已存在时需换 tag，省略 `--tag` 自动生成带时间戳的目录。逐次追加日志不等于支持断点续跑。

| 文件 | 含义 |
|---|---|
| summary.json / table.md | 每格平均 RE、标准误、同噪声规则 RE、节点/聚合正确率 |
| runs.json | 全部完成后的逐次结果与机制 trace |
| runs.jsonl | 每完成一次立即写入，中断后仍可检查已完成记录 |
| manifest.json | 机制配置、数据/源码哈希、实际模型和运行设置 |
| errors.jsonl / run.log | API 重试、解析失败等日志 |

纯 Python GT（默认 GT-Naive、GT-PSC、GT-PSC-B，每格 10 次，共 240 次；只要 GT-PSC 加 `--methods GT-PSC`；稳定参照可设 `--runs 1000`）：

```bash
.venv/bin/python scripts/run_ground_truth.py --datasets CU,Do --runs 10 --mechanism floor_tight --trace --tag cudo_gt_r10_floor_tight
```

GT 与 Agent 的随机流不同（§13.2），评价模型执行差异应读 pilot 的 `rule_relative_error`。旧版对照加 `--mechanism legacy` 和新 tag，不要把新旧版本的 runs 混在一起平均。

机制诊断用的 GT 命令示例：

```bash
.venv/bin/python scripts/run_ground_truth.py --datasets CU,Do --tasks 2-star,3-star \
  --methods GT-PSC --eps 2.0 --runs 1000 --seed 20260928 --tag alignment_initial_cu_do
.venv/bin/python scripts/run_ground_truth.py --datasets EE --tasks triangle \
  --methods GT-PSC --eps 2.0 --runs 5000 --seed 20260928 --tag alignment_initial_ee
```

论文角色配置的模板（阶段三协议冻结后才用于正式运行；仍继承 `.env` 端点与配置文件的 stream/retry 设置）：

```bash
.venv/bin/python scripts/run_experiments.py --exp exp1 --provider openai \
  --node-model gpt-4.1-mini --curator-model gpt-4.1 \
  --datasets CU,Do --runs 10 --seed 20260928 --tag paper_main_cu_do
```

floor_tight 引入时（2026-09-29）的离线验证产物：`results/alignment/profiles_20260929/`（候选比较与独立确认）、`results/pilot/mock_cudo_r10_20260929/`（160 次 mock 流程，5950 次本地调用，解析失败 0）、`results/ground_truth/gt_cudo_r10_20260929/`（240 次 GT 与 trace）。当时 `python -m pytest tests -q` 40 项全部通过（含本地流式 API 协议桩服务器；DashScope 有一项弃用警告）。

## 37. 局限与未实现内容

- 未实现附录 C 的 token 统计（Exp8）与附录 D 的节点采样扩展（Exp9，Facebook / Bible 大图）；
- 不支持断点续跑；
- k-star 机制仍是“公开描述 + 数学紧界”的重建解释，2-star 差距未解释，EE triangle 差距未拆分；
- PM（453 节点）的 Naive triangle prompt 约 15 万 token，受上下文长度与成本限制；
- 宽松数值解析、任务不一致只警告、节点 LLM 读取真实邻居的信任假设仍未处理（§18–§20）；
- 隐私控制器使用的 LLM、10 节点示例图、k-star 投影对象、d̂max 取整方式等是论文未明确、由本实现补充的细节。

---

## 附录 A 作者询问信草稿（未发送）

收件人可使用论文首页公开的第一作者邮箱 `yutingz@cse.unsw.edu.au`。作者和联系地址来自与官方 SHA256 一致的论文，不使用同名 GitHub 账户推断身份。

> 注：草稿写于 2026-09-28，描述的是 legacy 机制（灵敏度 $\binom{D}{k-1}$），ML 的 0.083 也是 legacy 结果。发送前应改为当前 floor_tight 的描述与数值（floor 取整、$\binom{D-1}{k-1}$），并考虑补充 2026-10-14 分析中关于 2-star 报告尺度的论证（见 `docs/PROJECT_AND_AGENT_IMPROVEMENT_ANALYSIS_2026-10-14.md`）。

```text
Subject: Request for GT-PSC implementation and k-star mechanism details (ACL 2026)

Dear Yuting Zhang and coauthors,

I am working on reproducing your paper, "Agent-based Substructure Counting under Local Differential Privacy" (ACL 2026, 2026.acl-long.1032). I found the paper and Responsible NLP Checklist on ACL Anthology, but could not locate the implementation. Would you be willing to share the repository or the Python scripts for GT-PSC and GT-PSC-B, particularly the 2-star and 3-star experiments in Tables 2 and 3?

Our implementation follows the public description: for epsilon=2 and k-star counting, epsilon1=0, epsilon2=0.4, and epsilon3=1.6. We estimate the maximum from independently Laplace-perturbed degrees, clip local degrees to the resulting threshold D, compute C(min(d_i,D),k), add independent Laplace noise of scale C(D,k-1)/epsilon3 at every node, and sum the reports before clamping the final result to zero.

Across six datasets, our GT-Naive values are close to Table 2. However, the 2-star GT-PSC errors remain higher. For example, on Les Miserables we obtain approximately 0.083, compared with 0.0444 in Table 2. Our graph has 77 nodes, 254 edges, maximum degree 36, and 2-star count 2808. We have also compared the rounding behavior in Imola et al.'s 2021 public implementation, but this does not explain the difference.

It would be very helpful to clarify:

1. The exact k-star sensitivity formula and whether it uses a shared maximum degree, each node's degree, or another bound.
2. How the noisy maximum is rounded for projection and for sensitivity; whether the true local neighbor lists are clipped.
3. The actual epsilon allocation and Laplace scale used for k-star reporting when the noisy-graph stage is omitted.
4. Whether every node reports independent noise and whether any correction, filtering, averaging, or clipping is applied before or after aggregation.
5. Whether you could share the preprocessed graphs or their degree sequences, the complete k-star DP/algorithm library entries, and the per-run GT results or seeds for Tables 2 and 3.

Our current checks identify a mismatch with this particular interpretation of the mechanism, not a conclusion about your implementation. We would appreciate any guidance on the intended implementation details.

Thank you for your time and for the paper.

Best regards,
[Your name]
```

## 附录 B 方法—代码索引

行号以 2026-09-30 版本为准。

| 类别 | 方法 | 位置 |
|---|---|---|
| 隐私原语 | RR 翻转概率 | `psc/dp.py:31` `flip_probability` |
| | 节点下三角 RR | `psc/dp.py:49` `node_noisy_lower_row` |
| | 向量化噪声图 | `psc/dp.py:71` `build_noisy_graph` |
| | Laplace 机制 | `psc/dp.py:91` `laplace_noise` / `laplace_mechanism` |
| | 带噪最大度 | `psc/dp.py:121` `estimate_degree_bound` |
| | 图投影（对称删边） | `psc/dp.py:130` `graph_projection` |
| | 邻居表投影 | `psc/dp.py:151` `project_neighbor_list` |
| | 预算拆分 | `psc/dp.py:183` `split_budget` / `naive_budget` |
| 机制配置 | k-star 配置 | `psc/mechanism.py:66` `PROFILES` |
| | 度界计算 | `psc/mechanism.py:34` `degree_bound` |
| | k-star 灵敏度 | `psc/mechanism.py:46` `kstar_sensitivity` |
| 知识库 | 分布式算法库 | `psc/library.py:162` `ALGORITHM_LIBRARY` |
| | DP 框架库 | `psc/library.py:241` `DP_FRAMEWORK_LIBRARY` |
| | 三角形灵敏度 | `psc/library.py:219` `_triangle_gs` |
| 规则语义 | send / update / aggregate | `psc/rules.py` |
| 智能体 | 节点智能体 | `psc/agents/node_agent.py` |
| | Curator | `psc/agents/curator_agent.py` |
| | 隐私控制器 | `psc/agents/privacy_controller.py` |
| 编排 | PSC / PSC-B / PSC-noDP | `psc/framework.py:76` `PSCFramework` |
| | Naive | `psc/framework.py:219` `NaiveFramework` |
| | 同噪声验证 | `psc/framework.py:285` `_validate_psc` |
| 基线 | GT-Naive / GT-PSC | `psc/ground_truth.py:64` / `:71` |
| | RAW / REFINED | `psc/baselines.py`、`psc/prompts.py:274` / `:288` |
| Prompt | 双通道与解析 | `psc/prompts.py` |
| 模型 | 工厂、重试 | `psc/models.py:148` / `:255` |
| Mock | 完美推理器 | `psc/mock_model.py` |
| 工程 | 错误记录 / 进度条 / 防覆盖目录与清单 | `psc/events.py`、`psc/progress.py`、`psc/artifacts.py` |
| 实验 | 运行器与统计 | `psc/experiments.py` |
| 对齐 | 配对候选比较 | `psc/alignment.py`、`scripts/align_gt_psc.py` |
| 数据 | 下载与预处理 | `scripts/prepare_datasets.py` |
| 测试 | 机制、流水线、协议桩 | `tests/test_mechanism.py`、`tests/test_psc.py`、`tests/test_openai_path.py` |

## 附录 C 诊断产物与复现命令

| 路径 | 内容 |
|---|---|
| `results/audit/2026-09-28/diagnostics.json` | CU/Do 各 5000 次与 EE triangle 5000 次纯代码诊断、三次均值重采样（§22.3、§30） |
| `results/audit/2026-09-28/ee_triangle_check.json` | EE triangle 5000 次复核（§30） |
| `results/audit/2026-09-28/kstar_diagnosis.py` / `.json` | k-star 独立公式核对与 5 万次消融；含标准误、配对 RE 变化、裁剪损失、零输出率、截断前后 RE、平均报告尺度、输入文件哈希（§23–§27） |
| `results/research/2026-09-28-author-implementation/source_manifest.json` | 检索来源、上游源码 commit、文件哈希（§32） |
| 同目录 `upstream/EvalLossLocal.cpp`、`upstream/LICENSE` | 引用论文官方源码快照 |
| 同目录 `research_mechanism.py` / `mechanism_research.json` | 上游变体、风险闭式校验、全部阈值枚举（§28、§29） |
| 同目录 `upstream_function_harness.cpp`、`verify_upstream_translation.py`、`upstream_translation_check.json` | C++ 原函数的噪声配对验证 |
| 同目录 `table_constraints.py` / `.json` | GT-Naive 反推真值与 PSC-B 尺度约束（§26） |
| 同目录 `noisy_degree_candidate.py` / `.json` | 矩校正估计器及验证（§34） |
| `results/alignment/profiles_20260929/` | 四个候选配置的比较与独立确认（§14） |

```bash
.venv/bin/python results/audit/2026-09-28/kstar_diagnosis.py
.venv/bin/python results/research/2026-09-28-author-implementation/research_mechanism.py
g++ -std=c++17 -O2 results/research/2026-09-28-author-implementation/upstream_function_harness.cpp -o /tmp/psc_upstream_function_harness
.venv/bin/python results/research/2026-09-28-author-implementation/verify_upstream_translation.py
.venv/bin/python results/research/2026-09-28-author-implementation/noisy_degree_candidate.py
.venv/bin/python scripts/align_gt_psc.py --runs 5000 --confirm-runs 1000
```
