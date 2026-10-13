# PSC 项目方法详解

> 本文基于当前工作区中的源码（`psc/`、`scripts/`、`tests/`）、配置（`config.toml`）、论文文本（`paper/psc_acl2026.txt`）、诊断文档（`docs/`）和实验结果（`results/`）整理，按“问题设定 → 隐私原语 → 灵敏度机制 → 分布式算法 → 多智能体编排 → 基线 → 工程与验证 → 实验与对齐”的顺序，逐项说明项目用到的方法、对应代码和设计取舍。
>
> 文中 `文件:行号` 均指当前版本源码位置。

---

## 目录

1. [项目概览](#1-项目概览)
2. [问题设定：ε-edge LDP 下的子结构计数](#2-问题设定ε-edge-ldp-下的子结构计数)
3. [差分隐私原语（`psc/dp.py`）](#3-差分隐私原语pscdppy)
4. [灵敏度与机制配置（`psc/mechanism.py`、`psc/library.py`）](#4-灵敏度与机制配置)
5. [分布式算法库与规则语义（`psc/library.py`、`psc/rules.py`）](#5-分布式算法库与规则语义)
6. [三类智能体（`psc/agents/`）](#6-三类智能体pscagents)
7. [框架编排：PSC / PSC-B / PSC-noDP / Naive（`psc/framework.py`）](#7-框架编排pscframeworkpy)
8. [对照与基线方法](#8-对照与基线方法)
9. [Prompt 设计与回复解析（`psc/prompts.py`）](#9-prompt-设计与回复解析pscpromptspy)
10. [离线 Mock 模型（`psc/mock_model.py`）](#10-离线-mock-模型pscmock_modelpy)
11. [LLM 执行正确性验证：同噪声回放](#11-llm-执行正确性验证同噪声回放)
12. [模型接入、重试与错误记录](#12-模型接入重试与错误记录)
13. [实验体系、随机数与统计方法](#13-实验体系随机数与统计方法)
14. [k-star 机制对齐方法（`psc/alignment.py`）](#14-k-star-机制对齐方法pscalignmentpy)
15. [隐私性分析与信任边界](#15-隐私性分析与信任边界)
16. [当前复现结果与已知差距](#16-当前复现结果与已知差距)
17. [局限与未实现内容](#17-局限与未实现内容)
18. [附录：方法—代码索引](#18-附录方法代码索引)

---

## 1. 项目概览

本项目复现 ACL 2026 论文 *Agent-based Substructure Counting under Local Differential Privacy*，基于 **AgentScope 1.0** 实现多智能体框架。核心思想：

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

---

## 2. 问题设定：ε-edge LDP 下的子结构计数

### 2.1 隐私模型

论文 Definition 1：对任意节点 $v_i$，随机算法 $R_i$ 作用于其邻居向量 $A_i\in\{0,1\}^n$。若对任意仅差一位的 $A_i, A_i'$ 和任意输出集合 $S$ 满足

$$\Pr[R_i(A_i)\in S] \le e^{\varepsilon}\Pr[R_i(A_i')\in S],$$

则 $R_i$ 满足 ε-edge LDP。即保护的是“单条边是否存在”。Curator 不可信，每个用户的连接存放在可信本地服务器。

### 2.2 四类任务（`psc/graph.py:30`）

| 任务 | 真值定义 | 代码 |
|---|---|---|
| degree | 平均度 $2m/n$ | `Graph.average_degree` |
| 2-star | $\sum_i \binom{d_i}{2}$ | `Graph.count_kstars(2)` |
| 3-star | $\sum_i \binom{d_i}{3}$ | `Graph.count_kstars(3)` |
| triangle | 三角形数 | `Graph.count_triangles` |

三角形精确计数用了两种方法（`psc/graph.py:190`）：

- $n\le 300$：局部计数 $t(u)=\frac12\sum_{v\in N(u)}|N(u)\cap N(v)|$，全局 $=\frac13\sum_u t(u)$；
- $n>300$（PM 数据集）：矩阵法 $\frac16\sum_{ij}(A^2)_{ij}A_{ij}=\frac16\mathrm{tr}(A^3)$，用 `np.einsum` 计算。

### 2.3 数据集与统一格式（`scripts/prepare_datasets.py`）

| 缩写 | 名称 | \|V\| | \|E\| | 来源 |
|---|---|---|---|---|
| CU | Contiguous USA | 49 | 107 | KONECT |
| Do | Dolphins | 62 | 159 | KONECT |
| ML | Les Misérables | 77 | 254 | networkx 内置 |
| CS | Ca-sandi_auths | 86 | 124 | Network Repository |
| EE | Email-enron-only | 143 | 623 | Network Repository |
| PM | C. elegans metabolic | 453 | 2025 | KONECT |

预处理方法：

- 解析 KONECT `out.*` 与 MatrixMarket `.mtx`（跳过注释和 `n n m` 头行）；
- `relabel_edges`：把原始 id 按排序映射为 `0..n-1`，去自环、去重、无向化；
- `build_records`：每个数据集生成 4 条附录 A 格式记录（`index / input_prompt / edges / vertex_num / edge_num / answer / task / dataset`）。

`task_prompt`（`psc/graph.py:76`）拼接“任务定义 + LDP 声明 + `Q: The nodes are numbered from 0 to n-1. <问题>`”，保证 Curator 只拿到 $(V(G),Q)$；`ldp=False` 时去掉 LDP 声明，用于无 DP 版本。

### 2.4 评价指标：相对误差（`psc/ground_truth.py:137`）

$$\mathrm{RE}=\frac{|\hat f(G)-f(G)|}{\max\big(f(G),\ \eta\big)},\quad \eta=0.001n$$

$\eta$ 避免真值很小时分母趋零。实验层还计算平均值、标准误、中位数、P95、与论文值的相对差和 log 差（见 §13.4）。

---

## 3. 差分隐私原语（`psc/dp.py`）

所有原语都是**纯代码**，从不交给 LLM 执行，对应论文 Challenge 1。

### 3.1 Warner 随机响应（RR，Algorithm 1 `BuildNoisyGraph`）

- 翻转概率（`dp.py:31`）：
  $$p=\frac{1}{1+e^{\varepsilon}}$$
  对 $\varepsilon>700$ 做溢出保护直接返回 0。
- **只扰动下三角**（`node_noisy_lower_row`，`dp.py:49`）：节点 $i$ 只对 $a_{i,j}\ (j<i)$ 这 $i$ 个比特做 RR，只发布 id 比自己小的噪声邻居。这样每条潜在边只被一个端点扰动一次，避免“双重发布”导致同一边消耗两次预算或出现不一致。
- 合并：`PrivacyController.build_noisy_graph` 收集所有节点发布的 $(i,j)$，用 `Graph.from_edges` 对称化得到 $G'$，再把每个节点在 $G'$ 中的邻居写入其 `noisy_neighbors`。
- 向量化等价实现（`dp.py:71`）：GT 版本一次生成 $n\times n$ 均匀随机矩阵，取严格下三角掩码，`noisy_lower | noisy_lower.T` 恢复对称邻接。

**RR 的密度问题（Challenge 2）**：以 CU、$\varepsilon=2$ 为例，$p\approx0.119$，1069 个非边中约 127 个被翻成边，而 107 条真边保留约 94 条，噪声图边数约为原图的 2 倍，k-star/三角形会被严重高估。这正是 Naive 误差大的来源。

### 3.2 Laplace 机制（Definition 3）

`laplace_noise(sensitivity, eps, rng)`（`dp.py:91`）采样 $\mathrm{Lap}(0,\ GS_f/\varepsilon)$；对非正/非有限预算或负灵敏度直接报错（允许灵敏度为 0，用于度界为 0 时计数恒为常数的情形）。`laplace_mechanism` 返回 $x+\mathrm{Lap}(GS_f/\varepsilon)$。

在 PSC 中用于两处：

1. 带噪度数：$\tilde d_i=d_i+\mathrm{Lap}(1/\varepsilon_2)$（度的灵敏度为 1）；
2. 本地计数上报：$\tilde c_i=c_i+\mathrm{Lap}(GS_f/\varepsilon_3)$。

### 3.3 全局灵敏度优化 GSOptimize（Algorithm 2）

针对 Challenge 3：若不限制度数，三角形灵敏度为 $n-2$、3-star 为 $\binom{n-2}{2}$ 等，噪声过大。方法分三步：

1. **带噪最大度**：每个节点上报 $\tilde d_i$，控制器取 $\max_i \tilde d_i$，按机制配置取整得到投影阈值 $\hat d_{\max}$（见 §4）。
2. **图投影 `graph_projection`**（`dp.py:130`，用于三角形，作用于噪声图）：
   - 以随机排列顺序遍历节点；
   - 若某节点在 $G'$ 中度数 $>\hat d_{\max}$，随机保留 $\hat d_{\max}$ 个邻居；
   - **对称删边**（同时从两端删除），保证结果仍是无向简单图且所有节点度 $\le\hat d_{\max}$。
3. **本地邻居表投影 `project_neighbor_list`**（`dp.py:151`，用于 k-star，没有噪声图）：节点在自己的真实邻居表中随机保留至多 $\hat d_{\max}$ 个，用于后续 update 计算。这与 Imola et al. 2021 的 k-star 算法一致。

投影后灵敏度由 $\hat d_{\max}$ 决定（degree 任务不需要 GS 优化）。

### 3.4 预算分配（Section 4.1，`split_budget`，`dp.py:183`）

默认比例 $r_1=0.5,\ r_2=0.2$：

$$\varepsilon_1=r_1\varepsilon,\quad \varepsilon_2=r_2(\varepsilon-\varepsilon_1),\quad \varepsilon_3=\varepsilon-\varepsilon_1-\varepsilon_2$$

不需要的步骤置 0，剩余比例保持不变：

| 任务 | 需噪声图 | 需 GS 优化 | $\varepsilon=2$ 时 $(\varepsilon_1,\varepsilon_2,\varepsilon_3)$ |
|---|---|---|---|
| degree | 否 | 否 | (0, 0, 2.0) |
| 2-star / 3-star | 否 | 是 | (0, 0.4, 1.6) |
| triangle | 是 | 是 | (1.0, 0.2, 0.8) |
| triangle（PSC-B） | 是 | 否 | (1.0, 0, 1.0) |
| k-star（PSC-B） | 否 | 否 | (0, 0, 2.0) |
| Naive | 全部给 RR | — | (2.0, 0, 0) |

参数校验：$\varepsilon$ 须有限且为正，$r_1,r_2\in[0,1)$，需要某步骤时对应比例必须 $>0$。

---

## 4. 灵敏度与机制配置

### 4.1 DP 框架库（`psc/library.py:182`）

`DPFrameworkSpec` 描述每个任务的：灵敏度文本、是否需要噪声图、是否可做 GS 优化，以及灵敏度计算函数。它既是隐私控制器 LLM 查询的“库”（`dp_library_summary()` 生成文本），也是代码实际使用的参数来源。

| 任务 | 灵敏度（有 GS 优化） | 无优化（PSC-B） |
|---|---|---|
| degree | 1 | 1 |
| 2-star | 由机制配置决定（默认 $\binom{D-1}{1}=D-1$） | 默认 $n-2$ |
| 3-star | 由机制配置决定（默认 $\binom{D-1}{2}$） | 默认 $\binom{n-2}{2}$ |
| triangle | $\max(1,\ \hat d_{\max}-1)$（附录 E “degree−1”） | $n-2$ |

三角形下界取 1，保证 $\hat d_{\max}\le1$ 时 Laplace 尺度仍为正。

### 4.2 k-star 机制配置（`psc/mechanism.py`）

论文对 k-star 的取整方式和灵敏度细节没有唯一说明，项目把可能的解释显式化为 4 个 `MechanismProfile`，GT 与 Agent 共用同一配置：

| 配置 | 取整 | GS 模式 | 物理上限 $[0,n-1]$ | 无优化基准 | 说明 |
|---|---|---|---|---|---|
| `legacy` | ceil | bound：$\binom{D}{k-1}$ | 否 | $n$ → $\binom{n}{k-1}$ | 原始实现 |
| `floor_bound` | floor | bound：$\binom{D}{k-1}$ | 是 | $n-1$ | 引用算法的整数界 |
| `continuous_bound` | floor 投影 | continuous：用连续最大值 $x$ 算 $x$ 或 $x(x-1)/2$ | 是 | $n-1$ | 对应上游 C++ 解读 |
| **`floor_tight`（默认）** | floor | tight：$\binom{D-1}{k-1}$ | 是 | $n-1$ → $\binom{n-2}{k-1}$ | 截断度计数的紧灵敏度 |

`degree_bound(reports, task)`（`mechanism.py:34`）：

- 非 k-star 任务或 `legacy`：$D=\max(1,\lceil \max_i\tilde d_i\rceil)$（三角形始终走这条路径）；
- 其他：$x=\min(\max(\text{raw},0),\ n-1)$，$D=\lfloor x\rfloor$ 或 $\lceil x\rceil$；GS 用度数为 $D$ 或连续值 $x$；
- 返回 `DegreeBound(raw_max, sensitivity_degree, projection_degree)`，分别记录原始连续最大值、算 GS 用的度数、实际投影阈值。

**紧界推导**：固定公开整数 $D$，截断计数 $f_D(d)=\binom{\min(d,D)}{k}$。单比特变化最多使度数变化 1，

$$\max_d |f_D(d+1)-f_D(d)| = \binom{D}{k}-\binom{D-1}{k}=\binom{D-1}{k-1}.$$

因此论文文字中的 $\binom{D}{k-1}$ 是比紧界更松的上界。`tests/test_mechanism.py::test_tight_sensitivity_is_max_single_bit_difference` 用穷举验证了该等式。`floor_tight` 是“按论文公开描述 + 数学紧界选出的实现解释”，**不是已确认的作者代码**。

---

## 5. 分布式算法库与规则语义

### 5.1 算法库 `ALGORITHM_LIBRARY`（`psc/library.py:162`）

每个 `AlgorithmSpec` 包含 Problem / State / Message / Initialization / Send / Update / Aggregation 的自然语言规则，对应附录 E。Curator LLM 从库中选条目，规则文本随后原样下发给节点 LLM。

| 任务 | 是否需要 Send | Update 规则 | Aggregate 规则 |
|---|---|---|---|
| degree | 否 | 数真实邻居个数 | $\sum c_i / n$，负数取 0 |
| k-star | 否 | $\binom{\deg}{k}$（$\deg<k$ 为 0），$\deg$ 为投影后邻居数 | $\sum c_i$，负数取 0 |
| triangle | 是 | 见下 | $\sum c_i / 3$，负数取 0 |

### 5.2 三角形两轮分布式算法（受 Imola et al. 2021/2022 两轮框架启发）

- **Send**（只读噪声邻居）：节点 $j$ 构造 `{Sender_ID: j, Sender_Neighbors: N'(j)}`，发给 $N'(j)$ 中每个节点。
- **Update**（读真实邻居 + 收到的消息）：节点 $i$ 对每条消息，若 `Sender_ID` 不在真实邻居 $N(i)$ 中则丢弃；否则对 $N(i)\cap$ `Sender_Neighbors` 中每个公共邻居计数 +0.5。

即本地计数

$$c_i=\frac12\sum_{j\in N'(i)\cap N(i)} |N(i)\cap N'(j)|.$$

无噪声时，每个三角形 $(i,j,k)$ 让节点 $i$ 从 $j$ 处得到公共邻居 $k$（+0.5）、从 $k$ 处得到 $j$（+0.5），每节点 +1，三个节点共 +3，所以聚合时除以 3。每个三角形“被计两次”所以用 0.5。

两种等价实现（`psc/rules.py`）：

- `update_triangle`：逐消息执行，用于 Mock 与验证；
- `triangle_local_count`：集合运算形式，用于 GT 快速计算。

`tests/test_psc.py::test_triangle_update_rule_example_from_appendix_e` 逐字验证附录 E 的例子（结果 0.5），`test_triangle_rules_recover_exact_count_without_noise` 验证无噪声时恢复精确计数。

### 5.3 `rules.py` 的角色

`rules.py` 是规则文本的**精确代码语义**，被三处共享：

1. GT-Naive / GT-PSC 纯 Python 算法；
2. Mock 模型（“完美 LLM”）；
3. 同噪声回放验证（§11）。

`naive_answer(task, n, noisy_edges)`：在噪声图上做精确计数，代表“完美 Curator”在 Naive 设定下的答案。

---

## 6. 三类智能体（`psc/agents/`）

三者均继承 AgentScope 的 `AgentBase`，使用 `InMemoryMemory`，实现 `observe` / `reply`。

### 6.1 NodeAgent（`node_agent.py`）

**双记忆设计**（对应论文 “Distributed Execution”）：

| 记忆 | 内容 | 访问者 |
|---|---|---|
| `_real_neighbors` | 真实邻居 $N_G(v_i)$，私有 | 仅 update 步骤、本地 RR、带噪度数 |
| `_update_neighbors` | update 实际使用的邻居表（k-star 下为投影后的） | update |
| `noisy_neighbors` | 噪声图 $G'$ 中的邻居 | 仅 send 步骤 |

**本地 DP 例程**（代码，在可信本地服务器执行）：

- `release_noisy_edges`：Alg.1 第 2–4 行，对 $j<i$ 做 RR；
- `report_noisy_degree`：$d_i+\mathrm{Lap}(1/\varepsilon_2)$；
- `bound_degree`：k-star 本地邻居表投影；
- `protected_count`：$c_i+\mathrm{Lap}(GS_f/\varepsilon_3)$。

**LLM 步骤**：

- `_send`：以 `node_send_prompt` 调 LLM，解析出 `{Sender_ID, Sender_Neighbors}`。解析失败时**不发送任何消息**并计 `parse_failures`，不用规则结果兜底，以保证 LLM 错误如实传播；
- `_update`：以 `node_update_prompt` 调 LLM，优先解析 JSON `count`，再退化为“最后一个数字”，都失败则保留原计数并记录错误。

**并发控制**：类级 `asyncio.Semaphore`（`max_concurrency`），防止几百个节点同时打爆 API。

**鲁棒解析**：`_node_id` 同时接受 `12`、`"12"`、`"Node 12"`、整数型浮点，因为 send prompt 以 `Node 12` 形式列出邻居，模型常会照抄。

### 6.2 CuratorAgent（`curator_agent.py`）

- `design_algorithm`（Alg.3 第 9 行）：给出算法库摘要，让 LLM 返回 `{"task": ...}`；非法时用 `infer_task_from_prompt` 规则兜底并记录；
- `aggregate`（Alg.3 第 14 行）：给出所有节点带噪计数与聚合规则，LLM 返回 `{"result": ...}`；
- `answer_with_noisy_graph`：Naive 基线中直接根据噪声边表作答；
- `answer_prompt`：RAW / REFINED 单 LLM 基线；
- `_parse_result`：JSON `result` → 最后一个数字 → 失败返回 0.0 并记录。

### 6.3 PrivacyController（`privacy_controller.py`）

- `select_framework`：唯一使用 LLM 的步骤（复用 Curator 模型），从 DP 框架库选任务；
- `determine_budget`：调用 `split_budget` / `naive_budget`；
- `build_noisy_graph`：汇总节点 RR 输出并下发噪声邻居；
- `gs_optimize`：收集带噪度数 → `degree_bound` → 三角形做图投影并更新噪声邻居、k-star 让每个节点本地投影 → 返回 `(GS_f, d̂max, 投影后 G')`，并在 `degree_trace` 中保存审计信息；
- `collect_reports`：让每个节点加 Laplace 噪声上报。

**关键设计**：隐私保证只依赖控制器的代码，不依赖 LLM。LLM 选错任务时仅打警告（Curator 与控制器不一致会记录 `task_correct=False`），不会绕过噪声。

---

## 7. 框架编排（`psc/framework.py`）

### 7.1 PSCFramework：Algorithm 3 逐行映射

| Alg.3 行 | 实现 |
|---|---|
| 1–3 初始化节点、计数 0 | `_AgentFactory.nodes(graph)`，每节点持有真实邻居 |
| 4 选 DP 框架、拆预算、定灵敏度 | `controller.select_framework` + `determine_budget` |
| 5–6 噪声图 | `split.eps1>0` 时 `controller.build_noisy_graph` |
| 7–8 GS 优化 | `split.eps2>0` 时 `controller.gs_optimize`，否则用无优化灵敏度 |
| 9 设计分布式算法 | `curator.design_algorithm` |
| 10 发送消息 | `fanout_pipeline(nodes, send_instr)` 并行执行 send，然后按 `metadata["recipients"]` 对目标节点 `observe(msg)` **定向投递** |
| 11–12 更新本地计数 | `fanout_pipeline(nodes, update_instr)` |
| 13 Laplace 上报 | `controller.collect_reports`，并通过 `curator.observe` 写入 Curator 记忆 |
| 14 聚合 | `curator.aggregate` |

AgentScope 用法要点：

- 指令以 `Msg` 形式下发，`metadata={"phase": "send"|"update", "task": ...}`，节点 `reply` 按 phase 分派；
- `fanout_pipeline(..., enable_gather=True)` 让所有节点并发执行同一阶段；
- 节点间消息不走广播，而是按接收者列表点对点 `observe`，模拟分布式消息传递。

三个变体：

- **PSC**：完整流程；
- **PSC-B**（`gs_optimization=False`，Exp3）：跳过 GSOptimize，用最坏情况灵敏度；
- **PSC-noDP**（`dp=False`，Exp5）：无 RR、无投影、无 Laplace，节点“噪声邻居”即真实邻居，Curator 收到不含 LDP 声明的 prompt。

每次运行的 LLM 调用数：triangle 为 $2n+3$（n 次 send + n 次 update + 选框架 + 设计 + 聚合），degree / k-star 为 $n+3$。

`RunResult.extra` 保存 `validation`（§11）与 `mechanism_trace`（带噪度数、d̂max、GS、Laplace 尺度、原始计数、逐节点噪声、截断前求和），用于本地审计。

### 7.2 NaiveFramework（Section 2.4）

1. 控制器 LLM 选任务；
2. 全部预算用于 RR 构造 $G'$；
3. 把噪声边表以 RAW 格式插入 `Q: The nodes are numbered from 0 to n−1.` 之后，由 Curator 直接作答（`prompt_style="raw"`）；或用 REFINED 模板（`prompt_style="refined"`，Exp6）。

`validation.rule_estimate` 记录在同一噪声图上精确计数的结果，即“完美 Curator”的答案。Naive 满足 ε-edge LDP 依据是 RR + 后处理不变性（论文 Theorem 1）。

---

## 8. 对照与基线方法

### 8.1 GT 系列（纯 Python，`psc/ground_truth.py`）

论文用“DP 算法的 Python 实现运行 1000 次的平均相对误差”作为参考值（GT）：

- **GT-Naive**：全预算 RR → 在噪声图上精确计数；
- **GT-PSC**：与 Agent 版相同的预算、噪声图、带噪最大度、投影、灵敏度、Laplace 与聚合，只是 send/update 用代码执行；
- **GT-PSC-B**：关闭 GS 优化。

`gt_psc(..., return_trace=True)` 返回 `RunTrace`，包含全部中间量，`audit_dict()` 输出可审计记录。低层函数保留 `legacy` 默认以兼容历史研究脚本，实验入口显式传入所选机制（默认 `floor_tight`）。

### 8.2 附录 B 单 LLM 基线（`psc/baselines.py`）

- **RAW（zero-shot）**：任务定义 + 节点与边字符串，无 LDP 声明，LLM 看到真实边；
- **REFINED**（Nguyen & Yan 2024：Few-Shot + Least-to-Most + 1-hop）：
  1. 子结构定义；
  2. 分步 COT 指令（列邻居 → 算度 → 组合数/公共邻居 → 求和）；
  3. 10 节点示例：固定种子 2024 随机生成 10 节点 38 边图，按 1-based id 程序化写出完整四步推理；
  4. 目标任务与边表；
  5. 每个节点的 1-hop 邻居集合。
- **Naive+REFINED**：把 REFINED 模板用在噪声图上（Exp6）。

这些基线用于衡量 prompt 质量与多智能体分解相对单 LLM 的优势，只有接真实模型才有意义；在 Mock 下它们都精确。

---

## 9. Prompt 设计与回复解析（`psc/prompts.py`）

### 9.1 双通道 prompt

每个 prompt = 自然语言部分 + `<structured_input>{JSON}</structured_input>` 机器可读块：

- Mock 模型只读结构化块执行规则；
- 真实模型调用前由 `chat()` 用 `strip_structured` 删掉该块（`ModelConfig.use_structured_input` 默认只对 mock 为真），保证真实 LLM 只看到论文风格的自然语言 prompt，不会“抄答案”。`tests/test_psc.py::test_structured_input_only_reaches_the_mock` 验证这一点。

### 9.2 系统提示

- `CURATOR_SYSTEM`：强调看不到真实边、负责设计算法与聚合、注意算术；
- `PRIVACY_CONTROLLER_SYSTEM`：只按 JSON 回答所选框架；
- `NODE_SYSTEM`：只管理节点 `{node_id}` 的邻域，严格遵守规则。

### 9.3 各阶段 prompt

| 函数 | 阶段 | 要求输出 |
|---|---|---|
| `task_selection_prompt` | 控制器 / Curator 选任务 | `{"task"}` |
| `node_send_prompt` | 节点 send（邻居以 `Node x` 列出） | `{"Sender_ID","Sender_Neighbors"}` |
| `node_update_prompt` | 节点 update（真实邻居 + 消息列表） | `{"count"}` |
| `curator_aggregate_prompt` | 聚合（带噪计数保留 4 位小数） | `{"result"}` |
| `naive_answer_prompt` | Naive：边表插入 Q 句之后 | `{"result"}` |
| `raw_prompt` / `refined_prompt` | 附录 B | `{"result"}` |

统一结尾指令：“可以逐步思考，最后在 ```json 代码块里给出只含所需键的 JSON”。

### 9.4 解析策略

- `extract_json`：优先取**最后一个**围栏 JSON，其次取最后一个裸 `{...}`，只接受 dict；
- `extract_number`：去掉千分位逗号后取最后一个数（支持科学计数法、`###421` 风格）；
- `insert_edges_into_prompt`：正则定位 `Q: The nodes are numbered from a to b.`，找不到则追加到末尾。

---

## 10. 离线 Mock 模型（`psc/mock_model.py`）

`MockChatModel` 继承 AgentScope `ChatModelBase`，是一个**严格按规则推理的“完美 LLM”**：

- 读取最后一条 user 消息里的 `<structured_input>`，按 `phase` 分派到 `rules.*`；
- 返回与真实模型相同格式的 `ChatResponse`（含 ```json 块），因此整个 AgentScope 流水线（消息传递、解析、聚合）都能离线跑通；
- `error_rate`：只对节点 update 注入 ±1 错误（结果截断到非负），模拟小模型的算术失误，用于敏感性分析（`--mock-error-rate`）。

意义：Mock 下 Agent 版结果在分布上等价于 GT 版（`test_agent_pipeline_matches_ground_truth_distribution`），从而把“框架实现正确性”与“LLM 推理误差”分开。

---

## 11. LLM 执行正确性验证：同噪声回放

`_validate_psc`（`psc/framework.py:285`）在每次 PSC 运行后，用**同一输入、同一份 Laplace 噪声**以代码重算各步骤：

| 字段 | 含义 |
|---|---|
| `send_exact` | 节点 LLM 发出的消息与 `rules.send_message` 一致的个数 |
| `update_exact` | LLM 计数与“对实际收到的消息执行规则”一致（隔离 update 误差） |
| `e2e_exact` | LLM 计数与完美流水线一致（send + update 误差合计） |
| `count_rel_diff` | LLM 计数和与规则计数和的相对差 |
| `aggregate_exact` | Curator 聚合与规则聚合一致（相对/绝对容差 1e-3） |
| `rule_estimate` | 把每个节点实际噪声 $z_i=\tilde c_i-c_i^{\text{LLM}}$ 加到规则计数上再聚合，即配对的 GT-PSC 值 |
| `mismatches` | 最多记录 30 个不一致节点 |

汇总（`validation_summary`，`psc/experiments.py:294`）：

- `node_update_acc`、`node_e2e_acc`、`send_acc`、`aggregate_acc`、`task_acc`；
- `rule_relative_error`：同噪声完美流水线的平均 RE；
- `delta` $=|\overline{\mathrm{RE}}_{\text{LLM}}-\overline{\mathrm{RE}}_{\text{rule}}|$，对应论文 Table 6 的 Δ，但这里是**同噪声配对**，比独立抽样的 GT 更能分离 LLM 误差。

这套方法把最终误差拆成“隐私机制本身的误差”与“LLM 执行误差”两部分。

---

## 12. 模型接入、重试与错误记录

### 12.1 模型工厂（`psc/models.py`）

| provider | 模型类 | Formatter |
|---|---|---|
| openai（及兼容端点） | `OpenAIChatModel` | `OpenAIChatFormatter` |
| dashscope | `DashScopeChatModel`（`enable_thinking=False`） | `DashScopeChatFormatter` |
| ollama | `OllamaChatModel` | `OllamaChatFormatter` |
| mock | `MockChatModel` | `OpenAIChatFormatter` |

角色分工：`node_model` 用于节点 send/update；`curator_model` 用于 Curator 与隐私控制器。

**配置优先级**（`ModelConfig.from_env`）：命令行参数 > 环境变量（`PSC_PROVIDER`、`OLLAMA_MODEL`）> `config.toml`（共享键 + provider 分节）> 内置默认。密钥只来自 `.env`，`load_config_file` 对未知键和未知分节报错。

### 12.2 统一调用与重试（`chat()`，`models.py:255`）

- 关闭 OpenAI 客户端自带重试（`max_retries=0`），由 `chat` 统一重试并**逐次记录**；
- 可重试：HTTP 408/409/429/≥500、`TimeoutError`/`ConnectionError`、openai/httpx 的连接/超时/流中断类异常，以及**空文本回复**；
- 等待时间：$\text{retry\_backoff}\times2^{k-1}$，若服务端给了 `Retry-After` 取较大者；
- 全部重试失败返回空串，由上层解析器记为解析失败，实验不中断；400、鉴权等不可重试错误直接抛出；
- 流式响应：迭代所有 chunk，取最后一个（其中含累积内容）。

### 12.3 错误事件与进度（`psc/events.py`、`psc/progress.py`）

- `ContextVar` 保存“当前运行的记录列表”和“上下文标签”（数据集/任务/方法/第几次），asyncio 子任务自动继承，因此并发运行间不串号；
- `record_error` 同时：追加到当前运行记录、实时写入 `errors.jsonl`（崩溃也不丢）、打 warning 日志；
- 错误类型：`api_error`、`empty_reply`、`call_failed`、`parse_failure`；模型回复最多保留 20000 字符（**保留首尾**，因为 JSON 答案通常在末尾）；
- 进度条同样用 `ContextVar` 注入回调，按模型调用次数推进并显示当前阶段，无进度条时为空操作。

---

## 13. 实验体系、随机数与统计方法

### 13.1 实验清单（`scripts/run_experiments.py`、`scripts/run_ground_truth.py`）

| 实验 | 内容 | 默认数据集 / 方法 |
|---|---|---|
| exp1 | Table 2，$\varepsilon=2$ | 6 图 × 4 任务，Naive / PSC |
| exp2 | 变化 $\varepsilon\in\{1,1.5,2,2.5,3\}$（Fig.2） | CU, Do |
| exp3 | GS 优化效果，PSC vs PSC-B（Table 3） | CU, Do × triangle / k-star |
| exp4 | 预算分配：分别扫描 $r_1$、$r_2\in\{0.1,\dots,0.9\}$（Fig.3） | CU, ML × triangle |
| exp5 | 附录 B Table 4：RAW / REFINED / PSC-noDP | 6 图 |
| exp6 | 附录 B Table 5：Naive vs Naive+REFINED | 6 图 |
| pilot | 真实 LLM 验证：PSC ×10、Naive ×10，含节点级正确率 | CU, Do |
| GT | GT-Naive / GT-PSC / GT-PSC-B，默认 1000 次 | 6 图 |

`--dry-run` 只打印预计调用数（如 CU/Do pilot 共 160 次运行、约 5950 次调用）。

### 13.2 随机数设计

- Agent 实验：第 $i$ 次运行的全部 DP 噪声来自 `np.random.default_rng([seed, i])`，结果与并发度、完成顺序无关（`test_parallel_runs_are_reproducible_and_overlap`）；
- GT 实验：每格 `default_rng(seed)` 顺序消费；
- 注意：两者相同 seed 并不代表逐次噪声相同；评价 LLM 执行差异应读 pilot 中的 `rule_relative_error`；
- 同一运行序号下，同图 2-star 与 3-star 在相同消费路径上共享基础噪声，两任务同时变差不能当作独立证据。

### 13.3 两级并发

- `parallel_runs`：`asyncio.Semaphore` 控制跨所有数据集/任务/方法同时执行的运行数；
- `max_concurrency`：`NodeAgent` 类级信号量限制节点 LLM 并发；Curator 调用不受其限制；
- 所有框架在任何运行开始前一次性构建，因为每个框架都会重置类级信号量，正在执行的运行必须共享同一个。

### 13.4 统计量（`error_statistics`，`psc/experiments.py:145`）

- `avg_relative_error`：平均 RE；
- `se_relative_error`：$s/\sqrt{N}$（ddof=1）；
- `median_relative_error`、`p95_relative_error`；
- `paper_relative_gap` $=|\overline{\mathrm{RE}}/\text{paper}-1|$；
- `paper_log_gap` $=|\ln(\overline{\mathrm{RE}}/\text{paper})|$，对倍数偏差对称，用于机制选择。

`experiments.py` 内置论文 Table 2/3/4/5 的参考值，`table2_markdown` 自动在每行下方附论文值。

### 13.5 结果产物与可追溯性（`psc/artifacts.py`）

- `new_run_directory`：`mkdir(exist_ok=False)`，已有 tag 直接拒绝，防止覆盖历史结果；省略 tag 自动加时间戳；
- `runs.jsonl`：每完成一次运行立即追加（`allow_nan=False`）；
- `manifest.json`：Python 版本、机制配置、运行参数、`psc/`、`scripts/` 源码与所用数据文件的 SHA-256，**不写入密钥**；
- 全部完成后写 `summary.json`、`runs.json`、`table.md`，另有 `errors.jsonl`、`run.log`。

---

## 14. k-star 机制对齐方法（`psc/alignment.py`）

目的：历史 `legacy` 的 GT-PSC 在 k-star（特别是 2-star）上与论文存在持续差距，需要在不接触作者代码的前提下，从候选解释中选出最接近论文的一种。

### 14.1 配对向量化模拟

- 关键观察：度截断后 k-star 计数只依赖 $\min(d_i, D)$，与具体删哪些邻居无关，所以**不需要构造投影图**，直接在度向量上计算；
- 每批最多 1024 次，一次生成 $(\text{size}, n)$ 的度噪声矩阵：$\tilde d=d+\mathrm{Lap}(1/(0.2\varepsilon))$；
- 报告噪声利用 Laplace 可缩放性：先生成标准 Laplace 之和 $S=\sum_i L_i$，再乘以 $GS/\varepsilon_3$；
- **公共随机数（common random numbers）**：所有候选共享同一批度噪声和报告噪声，只改参数策略，候选间差异不被抽样噪声掩盖；
- 同时计算有优化（GT-PSC，$\varepsilon_3=0.8\varepsilon$）与无优化（GT-PSC-B，$\varepsilon_3=\varepsilon$）两种情形；
- 最终估计 $\max(0,\ \sum_i\binom{\min(d_i,D)}{k}+\frac{GS}{\varepsilon_3}S)$。

说明：生产代码还会为邻居选择消耗额外随机数，因此这里与生产的一致是**分布意义**上的，而非逐种子一致。

### 14.2 选择与确认（`scripts/align_gt_psc.py`）

1. 发现阶段：六图 × {2-star, 3-star} × {GT-PSC, GT-PSC-B}，每格 5000 次（seed 9292026）；
2. 评分：对所有有论文值的单元格（Table 2 全部 + Table 3 的 CU/Do）求 `paper_log_gap` 平均，得 `joint_log_gap`，按其升序排序；
3. 确认阶段：用**独立随机流**（seed 9292027，必须与发现 seed 不同）每格 1000 次，只重跑 `legacy` 与被选配置，**不重新选择**，避免对随机流过拟合；
4. 不会自动修改默认配置，由人工决定。

结果（`results/alignment/profiles_20260929/`）：

| 配置 | Table 2 log gap | Table 3 PSC-B log gap | 联合 log gap | 最大相对差 |
|---|---|---|---|---|
| **floor_tight** | 0.2903 | 0.0521 | **0.2308** | 0.7838 |
| floor_bound | 0.3275 | 0.0679 | 0.2626 | 0.8303 |
| continuous_bound | 0.3489 | 0.0679 | 0.2786 | 0.8533 |
| legacy | 0.3712 | 0.0836 | 0.2993 | 0.8826 |

确认流中 floor_tight 与 legacy 分别为 0.2308 与 0.2925，排序不变，因此默认改为 `floor_tight`。选择依据是论文公开数值，**不声称复原了作者代码**。

### 14.3 诊断中用到的其他方法（`docs/KSTAR_DIAGNOSIS_2026-09-28.md`、`results/audit/`）

- 用独立脚本从度向量重算，与 1200 次生产 `RunTrace` 逐项核对（计数、GS、预算一致，聚合浮点差最大约 9.4e-10）；
- 每图 5 万次向量化模拟做消融：只改 floor、只改紧界、两者都改、去掉邻居投影、固定 $D$ 为真实最大度（离线反事实）、扫描 $\varepsilon_2$；
- 分析“带噪最大值的向上选择效应”：CU 真实最大度 8，平均 $D\approx14.86$，3-star 的 GS 随 $D$ 二次增长；
- 截断前后 RE 对比、零输出率统计，说明非负截断不是大误差来源；
- 对上游 Imola et al. 2021 的 C++ 实现（`EvalLossLocal.cpp`）做翻译核对（`verify_upstream_translation.py`）。

---

## 15. 隐私性分析与信任边界

1. **组合定理**：PSC 三个阶段分别消耗 $\varepsilon_1,\varepsilon_2,\varepsilon_3$，按顺序组合总计 $\varepsilon=\varepsilon_1+\varepsilon_2+\varepsilon_3$（论文 Theorem 2）；Naive 只做一次 RR（Theorem 1）。
2. **后处理不变性**：send 只读噪声邻居（RR 输出），聚合只读带 Laplace 噪声的上报，Curator 的所有计算都是 DP 输出的后处理。
3. **下三角 RR**：每条边只由一个端点扰动，避免同一比特被两次发布。
4. **灵敏度前提**：update 读真实邻居，其结果的灵敏度由投影阈值保证（对称删边保证三角形推导成立；k-star 本地投影保证 $\binom{D-1}{k-1}$ 成立）。
5. **代码执行噪声**：所有加噪都在控制器/节点本地代码中完成，与 LLM 是否遵守指令无关。
6. **需要注意的边界**：
   - 节点 LLM 在“可信本地服务器”读取真实邻居，这一假设来自论文设定；
   - 紧界推导针对理想的截断计数函数；若节点 LLM 输出任意错误值，灵敏度论证并不自动覆盖，文档中已明确；
   - `mechanism_trace`、GT 的 `runs.jsonl` 含原始计数和逐节点噪声，只用于本地审计，**不能作为公开隐私输出**，`manifest.json` 中有提示。

---

## 16. 当前复现结果与已知差距

### 16.1 GT 列（`floor_tight`，1000 次，$\varepsilon=2$）

来源：`results/ground_truth/gt_all_r1000_floor_tight_20260930/table.md`

| 任务 | 方法 | 本项目 Avg. | 论文 Avg. |
|---|---|---|---|
| degree | GT-Naive | 2.3578 | 2.3581 |
| degree | GT-PSC | 0.0118 | 0.0119 |
| 2-star | GT-Naive | 6.0349 | 6.0297 |
| 2-star | GT-PSC | 0.1039 | 0.0647 |
| 3-star | GT-Naive | 10.1851 | 10.2058 |
| 3-star | GT-PSC | 0.3756 | 0.3649 |
| triangle | GT-Naive | 4.1541 | 4.1610 |
| triangle | GT-PSC | 0.8833 | 0.8737 |

- GT-Naive 24 个单元格与论文偏差均 < 1%；
- degree / triangle 的 GT-PSC 基本一致；
- 3-star 平均值接近，但逐格仍有偏差（如 CU 0.6954 vs 0.8035，CS 0.6475 vs 0.5410）；
- **2-star 仍比论文高约 60%**，是未消除的主要差距，只改取整和灵敏度无法解释全部，需要作者 k-star 库/GT 脚本的具体参数（D、GS、$\varepsilon_3$、报告噪声、聚合与截断位置）才能进一步定位。

### 16.2 真实 LLM pilot（CU / Do，每格 10 次，floor_tight）

来源：`results/pilot/hy3-ioa_cudo_r10_floor_tight/`、`results/pilot/hy4-preview-ioa_cudo_r10_floor_tight/`

- 节点 update 正确率 99.2%–100%，三角形 send 正确率 100%，聚合正确率 100%，任务识别 100%；
- PSC 的 `delta` 大多为 0 或 < 0.006，即误差几乎全部来自隐私机制，而不是 LLM 推理；
- Naive 的 LLM 结果与同噪声规则答案接近（Do/triangle 在 hy3-ioa 下 Δ≈0.17 为最大值）；
- PSC 比 Naive 低 1–2 个数量级，与论文结论一致。

### 16.3 Mock 版（`results/archive/exp1/mock/`）

PSC 平均 RE：degree 0.0142、2-star 0.1237、3-star 0.4562、triangle 0.8928（历史 legacy 机制）。Exp2 复现了“$\varepsilon=3$ 时三角形 GT-Naive 反超 GT-PSC”；Exp4 复现了 CU 误差随 $\varepsilon_1$ 单调上升、ML 先降后升，以及 $\varepsilon_2$ 过大/过小都会使误差上升的现象。

---

## 17. 局限与未实现内容

- 未实现附录 C 的 token 统计（Exp8）与附录 D 的节点采样扩展（Exp9，Facebook / Bible 大图）；
- 不支持断点续跑（`runs.jsonl` 只用于中断后检查已完成记录）；
- k-star 机制仍是“公开描述 + 数学紧界”的重建解释；
- PM（453 节点）的 Naive triangle prompt 约 15 万 token，受上下文长度与成本限制；
- 隐私控制器使用的 LLM、10 节点示例图、k-star 投影对象、d̂max 取整方式等是论文未明确、由本实现补充的细节（见 README “论文未明确、由本实现补充的细节”）。

---

## 18. 附录：方法—代码索引

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
| 机制配置 | 四种 k-star 配置 | `psc/mechanism.py:66` `PROFILES` |
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
| 工程 | 错误记录 | `psc/events.py` |
| | 进度条 | `psc/progress.py` |
| | 防覆盖目录与清单 | `psc/artifacts.py` |
| 实验 | 运行器与统计 | `psc/experiments.py` |
| 对齐 | 配对候选比较 | `psc/alignment.py`、`scripts/align_gt_psc.py` |
| 数据 | 下载与预处理 | `scripts/prepare_datasets.py` |
| 测试 | 机制、流水线、协议桩 | `tests/test_mechanism.py`、`tests/test_psc.py`、`tests/test_openai_path.py` |
