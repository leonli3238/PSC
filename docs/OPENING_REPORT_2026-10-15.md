# 开题报告

**课题名称**：LLM 多智能体边本地差分隐私子结构计数的执行可信性：灵敏度审计与可验证执行

**日期**：2026-10-15

---

## 一、选题背景与意义

### 1.1 研究背景

用自然语言让大语言模型（LLM）直接分析图数据，正在成为一种新的数据分析方式。图上的子结构计数是连接模式分析和稠密子图识别的基础操作，但 LLM 在这类任务上仍不够准确，规模也上不去：在 20–30 个节点的图上，LLM 数三角形的准确率只有 7.21%（Nguyen & Yan 2024）。原因在于，把整张图编码成文本放进 prompt，既受上下文长度限制，又依赖逐项计数的可靠性。

此外，图的边往往编码了敏感关系，例如通信记录、交易往来、医患接触。把这些边直接写进 prompt，会带来泄露个体连接关系的风险。ε-edge LDP 是图上广泛使用的隐私模型：每个用户的邻居表存放在可信的本地服务器上，数据分析方（curator）不可信，任何离开本地的信息都必须满足 ε-edge LDP 。

一个自然的思路是把 LLM 与 edge LDP 结合，用多智能体分解计数任务（下称 PSC 框架）：

- **隐私控制器**：拆分预算 ε = ε1 + ε2 + ε3，用代码执行 DP 机制，包括随机响应（RR）构造噪声图（ε1）、带噪最大度估计与图投影（ε2），以及 Laplace 机制（ε3）；
- **协调者智能体（curator）**：设计或选择分布式计数算法，并聚合各节点的带噪报告；
- **节点智能体**：每个节点只持有自己的邻居表，由 LLM 按算法规则算出本地计数 c_i，加上 Lap(GS/ε3) 后上报。

与"把 RR 噪声图整体交给单个 LLM"的集中式做法（下称 Naive）相比，PSC 框架利用了节点的本地真实邻居信息，同时把每个 LLM 的输入缩小到单个节点的规模。

### 1.2 问题提出

PSC 框架中，DP 机制由代码执行，而本地计数由 LLM 完成。ε-edge LDP 的成立依赖三个条件：

- **C1**：离开节点的只有 RR 边、带噪度数、本地计数加 Laplace 噪声；
- **C2**：被加噪的计数由敏感度 ≤ GS 的**固定函数**产生；
- **C3**：每个量只发布一次。

GS 是针对规则函数 f 推导出的上界：degree 为 1，3-star 为 C(D−1, 2)，triangle 为 d̂max − 1，其中 D 为投影阈值、d̂max 为带噪最大度。当 c_i 由 LLM 产生时，C2 要求 LLM 函数 L 满足"输入翻转一位、输出变化 ≤ GS"，而 LLM 没有这样的保证。因此：

1. **保证缺口**：只有当 LLM 完全按规则算对时，PSC 框架的 DP 保证才在形式上成立。LLM 的错误与输入规模（度数、消息条数）相关，大图上更容易出错；degree 的 GS = 1，最容易越界。
2. **缺少度量**：LLM 执行偏离规则到底会造成多大的实际隐私损失，目前没有面向这一场景的审计方法。
3. **LLM 的价值定位**：如果用代码校验或替换 LLM 的输出来补上缺口，在已有代码可算的任务上 LLM 就变得多余；而真正需要 LLM 的新任务，又写不出校验代码。需要一种既保证 DP、又保留 LLM 作用的执行方式。
4. **威胁模型与成本**：节点 LLM 如果使用远程 API，原始邻居表就离开了"本地可信服务器"的边界，因此节点应采用本地模型。另一方面，节点 LLM 调用量为 O(n)，其中相当一部分花在可以由代码完成的确定性步骤上。

### 1.3 研究意义

- **理论**：回答"当 LLM agent 承担 DP 流水线中的计算时，DP 保证在什么条件下仍然成立"。
- **方法**：把 LLM 的角色从"执行私有计算"转变为"设计可检查灵敏度的程序"，让 DP 保证与 LLM 是否算对解耦，同时保留 LLM 把框架扩展到新子结构任务的价值。
- **实践**：给出精度、隐私、成本三者的取舍，以及节点本地模型的部署方案。
- **评估**：把机制误差与 LLM 执行误差分开度量，为 LLM 与 DP 结合的系统提供评估口径。

---

## 二、国内外研究现状

### 2.1 LLM 图推理与子结构计数

LLM 在环检测、连通性、最短路等图任务上已有较多研究，包括 NLGraph（Wang et al. 2023）、图的文本编码（Fatemi et al. 2023）、GraphWiz（Chen et al. 2024）和 GraphArena（Tang et al. 2025）。Hu et al.（2024）用多智能体把图推理分解到节点上，以提高规模和准确率；近期也有工作把这种分解与 edge LDP 结合，用于子结构计数（Zhang et al. 2026）。子结构计数仍是 LLM 的薄弱环节（Nguyen & Yan 2024）。

我们的前期实验也观察到，集中式输入下 LLM 有多种典型失误：

- 写一段程序后自称"运行结果是 X"，X 实际是编造的；
- 系统性少列度数；
- 在约 15 万 token 的长 prompt 下基本靠猜。

### 2.2 edge LDP 下的图统计

- **基础机制**：随机响应（Warner 1965）、本地差分隐私（Kasiviswanathan et al. 2011）；去中心化社交图的 LDP 合成（Qin et al. 2017）。
- **k-star 与三角形**：Imola、Murakami、Chaudhuri（2021）提出两轮交互的三角形计数，以及基于度数投影的 k-star 计数。后续工作包括：降低通信量（Imola et al. 2022a）、shuffle 模型下的三角形与 4-cycle 计数（Imola et al. 2022b）、三角形计数的下界与改进（Eden et al. 2023）、鲁棒三角形计数（He et al. 2025）、通用图指标框架 LF-GDPR（Ye et al. 2020）。
- **其他图问题**：k-core 分解（Dhulipala et al. 2022）、truss 分解（Zhang et al. 2025）。

这些工作都假设本地计数由确定性代码完成，灵敏度推导直接针对这段代码。

### 2.3 DP 审计与 DP 程序验证

- **黑盒检测 DP 违规**：Ding et al. 2018（统计假设检验）、Bichsel et al. 2018（DP-Finder）。
- **机器学习中的 DP 审计**：Jagielski et al. 2020、Nasr et al. 2021 用构造的相邻输入与 Clopper–Pearson 区间给出 ε 的经验下界；Steinke et al. 2023 提出单次训练审计。
- **静态保证灵敏度**：类型系统与语言层面的方法，如 Fuzz（Reed & Pierce 2010）、LightDP（Zhang & Kifer 2017）、Duet（Near et al. 2019），以及面向 SQL 的 Elastic Sensitivity（Johnson et al. 2018）。

"被加噪的量必须强制满足灵敏度"是 DP 系统的基本要求，审计和验证都有成熟方法。

### 2.4 研究缺口

| 已有工作 | 默认前提 | 缺口 |
|---|---|---|
| edge LDP 图统计 | 本地计算由确定性代码完成 | LLM 作为执行者时，灵敏度没有保证 |
| LLM 多智能体图计算 | LLM 精确执行本地规则 | 缺少对执行偏差的度量与约束，没有分析其对 DP 的影响 |
| DP 审计 | 被审计对象是训练算法或代码 | 没有面向"LLM agent 执行本地计算"的相邻输入构造与审计 |
| DP 语言 / 类型系统 | 程序由人编写 | 没有与"LLM 设计程序"结合，用于扩展任务 |

**说明**：以上缺口判断基于目前掌握的文献。正式投入前需要按 "LLM agent differential privacy"、"DP auditing"、"sensitivity of LLM-generated code"、"verified differential privacy" 等关键词完成检索，确认没有已发表的同类工作（见第九节风险 R1）。

---

## 三、前期工作基础

### 3.1 实验平台与配置

前期基于 AgentScope 1.0 搭建了 edge LDP 下 LLM 子结构计数的实验平台，实现了 Naive、PSC 框架，以及二者的纯代码精确执行版本 GT-Naive 与 GT-PSC（即 LLM 不出错时的误差下限）。

| 项目 | 配置 |
|---|---|
| 数据集 | CU（49 个节点 / 107 条边）、Do（62 / 159）、ML（77 / 254）、CS（86 / 124）、EE（143 / 623）、PM（453 / 2025） |
| 任务 | degree、3-star、triangle |
| 隐私预算 | ε = 2；PSC 按 ε1 = 0.5ε、ε2 = 0.2(ε − ε1)、ε3 = 其余拆分，不需要的步骤置 0，即 degree 的 ε3 = 2，3-star 的 (ε2, ε3) = (0.4, 1.6)，triangle 的 (ε1, ε2, ε3) = (1, 0.2, 0.8)；Naive 把全部预算用于 RR |
| 机制 | floor_tight：3-star 的投影阈值 D 取带噪最大度向下取整，GS = C(D−1, 2)；triangle 的 GS = d̂max − 1；degree 的 GS = 1；输出端把负数截断为 0 |
| 指标 | 相对误差 \|f̂ − f\| / max(f, 0.001n)，每次运行算一次再取平均 |
| 运行次数 | GT-Naive / GT-PSC 1000 次；LLM 每格 10 次（部分配置 20–100 次）；temperature 0，seed 0 |

### 3.2 前期实验结果

**（1）六个数据集上的平均相对误差**

节点与 curator 使用同一模型。PM 的智能体运行不完整，Avg. 取 CU–EE 五个数据集的平均。

| 任务 | 方法 | CU | Do | ML | CS | EE | PM | Avg.（CU–EE） |
|---|---|---|---|---|---|---|---|---|
| degree | GT-Naive | 1.0684 | 1.1766 | 1.1339 | 3.2738 | 1.7038 | 5.7901 | 1.6713 |
| degree | Naive · DeepSeek-V3 | 0.9893 | 1.0541 | 1.0549 | 2.4359 | 2.3291 | - | 1.5726 |
| degree | Naive · hy3-ioa | 1.0991 | 1.1673 | 1.1583 | 3.2726 | 1.7093 | 7.1925† | 1.6813 |
| degree | GT-PSC | 0.0182 | 0.0140 | 0.0096 | 0.0208 | 0.0053 | 0.0030 | 0.0136 |
| degree | PSC · DeepSeek-V3 | 0.0243 | 0.0214 | 0.0079 | 0.0192 | 0.0166 | - | 0.0179 |
| degree | PSC · hy3-ioa | 0.0160 | 0.0139 | 0.0077 | 0.0180 | 0.0060 | 0.0038 | 0.0123 |
| 3-star | GT-Naive | 10.0666 | 6.7418 | 1.9979 | 29.8181 | 7.4814 | 5.0049 | 11.2212 |
| 3-star | Naive · DeepSeek-V3 | 10.6460 | 6.1865 | 1.9605 | 27.1507 | 4.3452 | - | 10.0578 |
| 3-star | Naive · hy3-ioa | 10.5680 | 6.6208 | 2.1267 | 29.2204 | 7.5672† | - | 11.2206 |
| 3-star | GT-PSC | 0.6954 | 0.3472 | 0.2596 | 0.6475 | 0.1797 | 0.1239 | 0.4259 |
| 3-star | PSC · DeepSeek-V3 | 1.0875 | 0.5581 | 0.3208 | 0.8729 | 0.2514 | - | 0.6181 |
| 3-star | PSC · hy3-ioa | 1.0229 | 0.4907 | 0.2837 | 0.7564 | 0.2370 | - | 0.5581 |
| triangle | GT-Naive | 1.4433 | 1.8661 | 0.5647 | 6.9952 | 1.9952 | 12.0601 | 2.5729 |
| triangle | Naive · DeepSeek-V3 | 1.4860 | 4.5474 | 0.9974 | 3.5024 | 1.0063 | - | 2.3079 |
| triangle | Naive · hy3-ioa | 1.5561 | 1.8653 | 0.6120† | 6.3016† | 2.2253 | 81.1538 | 2.5121 |
| triangle | GT-PSC | 1.0028 | 0.8431 | 0.3949 | 1.6068 | 0.4059 | 1.0462 | 0.8507 |
| triangle | PSC · DeepSeek-V3 | 1.1506 | 0.4846 | 0.4096 | 1.3031 | 0.4071 | - | 0.7510 |
| triangle | PSC · hy3-ioa | 1.1723 | 0.4877 | 0.4097 | 1.2766 | 0.3238 | - | 0.7340 |

† 剔除了模型调用重试耗尽的运行，按其余运行计算。

**（2）CU 上的更多模型**

GT-Naive / GT-PSC 为 1000 次的均值；LLM 行为 10–100 次运行的均值。*斜体*行为原论文 Table 2 的 CU 结果（节点 gpt-4.1-mini、curator gpt-4.1，每格 10 次）。

| 方法 | degree | 3-star | triangle |
|---|---|---|---|
| GT-Naive | 1.07 | 10.07 | 1.44 |
| Naive · GPT-4.1 | 1.15 | 14.70 | 8.36 |
| Naive · GLM-5.2 | 0.93 | 7.11 | 13.36 |
| Naive · hy3-ioa | 1.07 | 10.10 | 1.52 |
| GT-PSC | 0.0182 | 0.6954 | 1.00 |
| PSC · 节点 gpt-4.1-mini + curator gpt-4.1 | 0.0167 | 1.02 | 1.17 |
| PSC · DeepSeek-V3-0324 | 0.0225 | 0.6987 | - |
| PSC · 节点 DeepSeek-V3 + curator hy3-ioa | 0.0196 | 0.8239 | 0.9952 |
| *论文 · Naive* | *1.10* | *109.33* | *9.12* |
| *论文 · PSC* | *0.0174* | *0.7325* | *0.7939* |

**（3）LLM 执行质量**

"执行正确率"指 LLM 结果与同一批噪声下 GT 结果一致的运行占比；"节点 / 聚合正确率"指对应步骤与规则一致的比例。表中为 CU–EE 平均。

| 任务 | 模型 | Naive 执行正确率 | PSC 节点正确率 | PSC 聚合正确率 |
|---|---|---|---|---|
| degree | DeepSeek-V3 | 60% | 0.998 | 0.88 |
| degree | hy3-ioa | 94% | 0.998 | 1.00 |
| 3-star | DeepSeek-V3 | 8% | 1.000 | 0.86 |
| 3-star | hy3-ioa | 44% | 1.000 | 1.00 |
| triangle | DeepSeek-V3 | 0% | 0.765 | 0.94 |
| triangle | hy3-ioa | 33% | 0.998 | 1.00 |

在 CU 上，gpt-4.1-mini 节点的 update 正确率为 degree 490/490、3-star 490/490、triangle 481/490；gpt-4.1 curator 的聚合正确率为 degree 8/10、3-star 9/10、triangle 10/10。degree 的两次聚合错误都是对 49 个带噪度数求和时少算约 1，使误差从 0.0160 升到 0.0167。

**主要观察**

1. **PSC 的精度优势主要来自机制。** GT-Naive 与 GT-PSC 的 CU–EE 平均误差分别为：
   - degree：1.67 对 0.0136；
   - 3-star：11.22 对 0.426；
   - triangle：2.57 对 0.851，差距明显小于前两个任务。在 CU 上只有 1.44 对 1.00。
2. **集中式下 LLM 的执行偏差强烈依赖模型。**
   - GPT-4.1 在 CU 上的 triangle 误差为 8.36、3-star 为 14.70，远高于 GT-Naive 的 1.44、10.07，主要原因是编造程序输出；GLM-5.2 的 triangle 为 13.36，会列出大量不存在的三角形。
   - hy3-ioa 接近 GT-Naive（triangle 1.52，3-star 10.10）。
   - DeepSeek-V3 的执行正确率只有 60% / 8% / 0%，但均值反而低于 GT-Naive：噪声图上的子结构本来就偏多，LLM 少数反而让误差变小。所以均值接近不等于算对。
3. **PSC 下 LLM 执行误差很小，但不为零，且没有保证。**
   - hy3-ioa 的节点正确率为 0.998–1.000，误差与 GT-PSC 几乎相同。
   - DeepSeek-V3 的 triangle 节点正确率只有 0.765，聚合正确率为 0.86–0.94。
   - DeepSeek-V3-0324 在 CU 上 100 次 3-star 中，有 7 次 curator 不做求和、直接输出 0。
4. **部分配置下 PSC 估计的实用性有限。** CU triangle 的 GT-PSC 误差为 1.00，与"恒输出 0"相同。1000 次中有 31% 被截断为 0，另有 22% 误差大于 1。

---

## 四、研究目标与研究内容

### 4.1 总体目标

在不修改 DP 机制（RR、Laplace、投影、ε 拆分）的前提下，回答并解决：**LLM 执行会破坏 DP 的前提吗？能否测出来、能否修复？如何在修复的同时保留 LLM 的价值？**

### 4.2 研究问题

| 编号 | 研究问题 |
|---|---|
| RQ1 | LLM 节点的输出是否满足"相邻输入下变化 ≤ GS"？不满足时，实测隐私损失 ε 的下界是多少？ |
| RQ2 | 越界与哪些因素有关：模型能力、图规模、节点度数、消息条数、任务？ |
| RQ3 | 能否构造一种执行方式，使 DP 保证不依赖 LLM 是否算对，同时 LLM 仍承担不可替代的工作？ |
| RQ4 | 各种执行方式在精度、隐私、成本上的取舍如何？在大图上是否依然成立？ |

### 4.3 研究内容

**内容一：机制误差与执行误差分离的评估口径**

把方法的误差拆成两部分：

- 机制误差：GT-Naive / GT-PSC，即纯代码执行，与模型无关；
- 执行误差：同一批噪声下 LLM 结果与 GT 结果之差。

报告执行正确率、执行偏差，以及 LLM 出错导致误差变大 / 变小的分量。此外，curator 可以利用公开的 GS、ε3、n 给出估计值的置信区间（纯后处理，不消耗预算），区间覆盖 0 时提示"估计与 0 不可区分"。

**内容二：LLM 节点的实测灵敏度与隐私审计（对应 RQ1、RQ2）**

- **形式化**：f 为规则函数，L 为 LLM 函数（含解析失败时的回退值），发布机制为 M(x) = L(x) + Lap(GS/ε3)。
- **构造相邻输入**：只翻转私有邻居表 P 的一位，消息与公开参数保持不变。3-star 需要处理投影耦合，即 |P| = D 时的替换操作。所有相邻对都用 Δf ≤ GS 的断言自检。
- **相邻对选取策略**：
  - S1 随机：估计平均越界率；
  - S2 规则变化最大：选使 Δf 接近 GS 的翻转；
  - S3 错误诱导：针对常见错误设计翻转，如把发送者算作共同邻居、误采纳非邻居消息、长列表中间元素漏数；
  - S4 边界情形：3-star 的 d = 2 / 3 边界和 |P| = D，degree 的长列表。

  S1 与 S2–S4 分开报告。
- **统计方法**：
  - "稳健越界"：x 与 x′ 各自的重复输出完全一致，且 Δ_LLM > GS。此时 ε_emp = ε3·Δ_LLM/GS 可作为下界报告。
  - "疑似越界"：重复之间不一致时追加采样，用 Clopper–Pearson 区间给出 ε_lb，只有 ε_lb > ε3 才计为越界。
- **输入来源**：从已有实验的对话记录重构节点输入，并做 prompt 往返一致校验；新配置用"严格按规则执行"的模拟模型生成同种子输入。

**内容三：保证不依赖 LLM 正确性的执行框架（对应 RQ3，主要方法贡献）**

在 PSC 框架上做两版改进。DP 机制（RR、带噪最大度与投影、Laplace、ε 拆分）和三类智能体的分工都保持不变，只改变本地计数由谁、以什么方式完成。

| 版本 | 改动位置 | 本地计数的产生方式 | DP 性质 |
|---|---|---|---|
| 基线 | — | 节点 LLM 按规则文本直接算出计数 | 仅在 LLM 无错时成立 |
| 改进一：受约束的节点执行 | 节点智能体 | 节点 LLM 通过本地工具完成计算，结果经代码守卫后才进入加噪 | 可证明满足 DP |
| 改进二：程序化执行 | curator 与节点智能体 | curator LLM 设计本地计算程序，系统推导并检查灵敏度，节点在本地执行 | DP 由程序结构保证，与 LLM 正确性无关 |

**改进一：受约束的节点执行**

保留"节点 LLM 执行规则"的形态，在节点内部加三层约束，全部在本地完成：

1. **消息预过滤**：代码先剔除非真实邻居发来的消息，再交给 LLM。这样可以消除"误采纳非邻居消息"一类错误；前期统计显示，triangle 的 update prompt 可因此缩短约 44%。
2. **工具调用**：节点 LLM 不再自己逐项数，而是调用 `intersect`、`comb` 等本地工具。工具内部绑定节点的私有邻居表，LLM 只传发送者编号等引用，不能替换输入。LLM 同时以结构化格式输出中间结果（如各发送者的共同邻居列表），代码按约束校验：共同邻居必须同时在两张表中，且不能是发送者或自己。违反约束则反馈并重问。
3. **守卫**：进入 Laplace 之前，用代码重算规则函数；LLM 结果与重算值不一致时采用代码值。被加噪的量因此恒等于规则函数，C2 严格成立。守卫的回退率作为 LLM 执行质量的指标。

改进一的局限是：凡是能写守卫的任务，都已经有代码可以直接算，LLM 在本地计算阶段只起编排作用（第九节风险 R3）。它适合作为"在现有架构上可证明地补上缺口"的工程方案，也是改进二的对照。

**改进二：程序化执行（主要方法贡献）**

把 LLM 的作用从"执行私有计算"前移到"设计计算"：

1. **受限 DSL**：节点本地计算用一种小型领域语言表达。原语包括私有邻居集 P、公开带噪图 G′、公开阈值 D、集合交、计数、截断、组合数等。
2. **灵敏度推导**：借鉴 Fuzz / LightDP 的思路，为原语标注对"P 翻转一位"的灵敏度，并按组合规则静态推导程序的灵敏度上界。无法推导的程序由运行时截断兜底。
3. **LLM 的角色**：curator 在原有的"算法设计"阶段，只依据公开信息（任务描述、G′、d̂max）把自然语言任务翻译成 DSL 程序。系统返回推导出的 GS，若上界过松，LLM 可以迭代改写程序。设计阶段只接触公开信息，不消耗隐私预算。
4. **本地执行**：程序在节点本地确定性执行。执行误差为 0，原始数据不出节点，节点 LLM 调用从 O(n) 降到 O(1)。
5. **扩展任务**：在 degree、3-star、triangle 上，改进二应与 GT-PSC 的分布一致；在库外任务上（候选：k ≥ 4 的 k-star、路径 / wedge 类计数、局部聚类相关的组合量等，具体集合在文献检索后确定），检验 LLM 设计的程序能否给出正确的灵敏度和可用的精度。

**内容四：精度—隐私—成本取舍与大图扩展（对应 RQ4）**

- **成本优化**：
  - 节点 send 消息改由代码生成，属于已发布数据的后处理，前期统计中这部分约占输出 token 的 23%；
  - 缓存只依赖公开信息的算法设计步骤；公共 prompt 前缀缓存；超时与重试。

  所有优化都要说明 DP 影响：禁止把多个节点合批到一个 prompt；禁止按私有信息路由模型，否则会形成旁路泄露。
- **补充实验**：token 与时延统计；大图（> 1000 个节点）上的节点采样扩展。大图上 LLM 错误更显著，是审计和修复最有区分度的场景。
- **消融矩阵**：执行方式 {基线、改进一、改进二} × 节点模型 {gpt-4.1-mini、本地 Qwen、更弱模型} × 6 图 × 3 任务。

**内容五（扩展）：复合查询规划与隐私预算记账**

curator 把复杂问题分解为若干库任务或 DSL 程序的组合。隐私控制器按顺序组合分配预算，并复用已发布的数据（例如带噪度数可供 degree 与 3-star 共用）。只使用标准组合定理，不引入新机制。

---

## 五、研究方法与技术路线

```
          ┌──────────── 诊断 ────────────┐
实验平台 → │ 内容一：评估口径（机制 / 执行分离） │
(已完成)   │ 内容二：灵敏度审计 + 错误分类      │ → 保证缺口的存在性与严重程度
          └──────────────────────────────┘
                         │
          ┌──────────── 方法 ────────────┐
          │ 改进一：预过滤 + 工具 + 守卫        │
          │ 改进二：LLM 设计程序 + 灵敏度检查   │ → 保证与 LLM 正确性解耦
          └──────────────────────────────┘
                         │
          ┌──────────── 评估 ────────────┐
          │ 内容四：精度—隐私—成本消融         │
          │ token 统计、大图扩展                │
          └──────────────────────────────┘
                         │
                  扩展：内容五 复合查询
```

**关键技术点**

1. **相邻输入构造的正确性**：每个任务都要实现相邻操作并断言 Δf ≤ GS，单元测试覆盖每个任务。
2. **非确定性处理**：temperature 0 的 API 也不完全确定。对同一输入重复 r 次，用混合 Laplace 分布计算 ε_emp，并在细网格上用尾部极限校验；同时单独报告同输入下的抖动基线。
3. **失败回退的处理**：解析失败或 API 失败时节点保留旧值。这本身不构成越界，作为随机事件计入混合分布；只有当 x 与 x′ 的失败率显著不同时，才报告为隐私影响。
4. **DSL 灵敏度推导**：先覆盖 degree、3-star、triangle 的程序结构，验证推导出的 GS 与手工推导一致（分别为 1、C(D−1, 2)、d̂max − 1），再扩展到新原语。
5. **威胁模型一致**：主实验采用节点本地模型（vLLM 部署的 Qwen 等），远程 API 结果只作补充。

---

## 六、实验方案

### 6.1 设置

- **数据集**：CU、Do、ML、CS、EE、PM，大图扩展实验另选。
- **任务**：degree、3-star、triangle，以及改进二的库外任务。
- **预算与机制**：ε = 2，拆分方式与机制同 3.1 节（floor_tight）。
- **随机性**：seed = 0；不同执行方式在同一批噪声上配对比较。

### 6.2 评价指标

| 维度 | 指标 |
|---|---|
| 精度 | 平均相对误差、中位数、P95、配对标准误；机制层 1000 次，执行层看同噪声差值 |
| 执行质量 | 节点 / send / 聚合正确率、执行正确率、执行偏差、守卫回退率 |
| 隐私 | 越界率（Wilson CI）、ε_emp 的最大值 / P95 / 中位数、ε_emp > ε3 与 > 2ε3 的比例、总 ε 的实测下界 ε1 + ε2 + ε_emp |
| 成本 | LLM 调用次数、输入 / 输出 token、墙钟时间、费用 |

### 6.3 审计实验阶段

| 阶段 | 内容 | 规模（约） |
|---|---|---|
| P1 试点 | CU × 3 任务，gpt-4.1-mini，每个节点 m = 4 个相邻对，每个输入重复 r = 3 次 | 4.4k 次调用，约 $3 |
| P2 大图 | PM × {degree, 3-star}，EE × 3 任务，按度数分层抽 60 个节点 | 约 10k 次调用，约 $10–15 |
| P3 模型对比 | 本地 Qwen 与一个更弱的模型（**作为主实验**） | 每个模型约 10k 次，本地运行 |
| P4 修复对比 | 基线、改进一、改进二，在越界最多的 2–3 个配置上 | 每个版本约 3k 次 |

### 6.4 判定标准

- **未发现越界**：结论限定为"在所测配置下 LLM 输出未越过 GS"，研究重点转向改进二的可证明保证、库外任务扩展与成本。
- **发现越界**：报告最坏的 ε_emp 及其触发条件（错误类型、输入规模、模型），并用基线与两版改进的对比说明修复效果。

预期 CU 的 3-star / triangle 很难越界（GS 为 13–34，而 LLM 误差只有 ±0.5–2）；degree（GS = 1）和大图（PM、EE）最可能越界。

---

## 七、预期成果与创新点

### 7.1 预期成果

1. **审计工具**：相邻输入构造、ε_emp 计算与统计检验的实现，附测试。
2. **审计数据集与报告**：多模型、多图、多任务的越界率与 ε_emp 分布，以及错误类型与协变量的关系。
3. **可验证执行框架**：改进一（预过滤、工具调用、守卫）作为可开关的节点执行选项；改进二的 DSL、灵敏度推导器与 LLM 程序设计循环。
4. **评估报告**：精度—隐私—成本曲线、token 统计与大图扩展实验。
5. **学术论文 1 篇**（目标：安全 / 隐私或数据库方向的会议），以及开源代码。

### 7.2 创新点（以文献检索确认为前提）

1. **问题**：指出并形式化"LLM agent 作为 DP 执行者"时的保证缺口，即 GS 针对规则函数，而被加噪的是 LLM 输出。给出面向该场景的相邻输入构造与审计方法，首次量化实测 ε。
2. **方法**：LLM 设计受限 DSL 程序，系统自动推导并检查灵敏度，再在本地执行。DP 保证与 LLM 是否算对无关，LLM 的价值转移到把框架扩展到新子结构任务上。
3. **评估**：机制误差与执行误差分离的评估口径，区分精度提升中机制与 LLM 各自的贡献。

---

## 八、可行性分析

- **平台基础**：实验平台已完成，支持同噪声回算、逐节点噪声记录、完整对话记录和不可覆盖的结果目录，审计可以直接复用。
- **数据基础**：已有多个模型的节点对话记录（gpt-4.1-mini、DeepSeek-V3、hy3 等），P1 的大部分原始输入无需重新运行 DP 流水线。
- **离线验证**：模拟模型在统计上与 GT-PSC 等价，可以在不调用 API 的情况下验证审计与两版改进的正确性。
- **算力与费用**：P1 约 $3，P2 约 $10–15；P3 在本地 vLLM 上运行，只需机时。
- **理论基础**：三个任务的灵敏度推导与 DP 审计统计方法已整理完毕；DSL 灵敏度推导可借鉴成熟的类型系统工作，三个任务的程序结构简单（集合交、计数、组合数），实现难度可控。

---

## 九、风险与对策

| 编号 | 风险 | 对策 |
|---|---|---|
| R1 | **新意未确认**："被加噪量必须满足灵敏度"是 DP 基本原则，审计也有成熟方法 | 开题后第一项工作是文献检索；新意定位在"LLM agent 作为执行者"这一场景，以及改进二 |
| R2 | **审计可能找不到越界**（小图上 GS 远大于 LLM 误差） | 主线不押在"找到越界"上：缺口在形式上已经成立，审计用于量化严重程度；主要贡献是改进二；同时用 degree、大图、弱模型与 S3 错误诱导策略提高检出率 |
| R3 | **守卫会让 LLM 多余**：能写守卫说明已有代码，需要 LLM 的场景又写不出守卫 | 改进一只作为工程方案和对照；改进二让 LLM 负责设计，并在库外任务上体现其价值 |
| R4 | DSL 表达能力不足，或推导出的灵敏度过松 | 先覆盖三个任务并与手工推导对齐；过松时允许 LLM 迭代改写；无法静态推导的部分用运行时截断兜底 |
| R5 | API 非确定性、限流与超时 | 每个输入重复 r 次并报告抖动基线；疑似越界追加采样；主实验改用本地模型 |
| R6 | 远程 API 下原始邻居表外发，讨论灵敏度意义有限 | 明确采用节点本地模型的威胁模型；远程模型结果只作补充 |
| R7 | 大图 prompt 过长、费用高（PM triangle 单个 prompt 可达数万 token） | 分层抽样节点，PM triangle 默认不做；先跑 P1 再确定规模；改进二的本地执行本身就能消除这项成本 |

---

## 十、进度安排

| 时间 | 工作 | 交付 |
|---|---|---|
| 2026-10 下旬 – 11 月上旬 | 文献检索确认新意；整理评估口径 | 文献综述；评估口径说明 |
| 2026-11 | 审计工具与测试；P1 试点（CU × 3 任务） | 审计工具；第一版越界表与 ε_emp 分布 |
| 2026-12 | P2 大图、P3 本地 / 弱模型；错误类型自动分类 | 审计报告（RQ1、RQ2） |
| 2027-01 – 02 | 改进一；改进二的 DSL 与灵敏度推导器原型，三个任务对齐 GT-PSC | 可验证执行框架 |
| 2027-03 | P4 修复对比；改进二的库外任务；token 统计与大图扩展 | 精度—隐私—成本曲线（RQ3、RQ4） |
| 2027-04 | 扩展：复合查询规划与预算记账（视进度） | 扩展实验 |
| 2027-04 – 05 | 论文撰写与投稿；代码整理开源 | 论文初稿、代码仓库 |

---

## 参考文献

1. Zhang Y., Wang K., Ni W., Zhang Y., Zhang W. Agent-based Substructure Counting under Local Differential Privacy. ACL 2026.
2. Dwork C., Roth A. The Algorithmic Foundations of Differential Privacy. Foundations and Trends in TCS, 2014.
3. Warner S. L. Randomized Response: A Survey Technique for Eliminating Evasive Answer Bias. JASA, 1965.
4. Kasiviswanathan S. P., Lee H. K., Nissim K., Raskhodnikova S., Smith A. What Can We Learn Privately? SIAM J. Comput., 2011.
5. Qin Z., Yu T., Yang Y., Khalil I., Xiao X., Ren K. Generating Synthetic Decentralized Social Graphs with Local Differential Privacy. CCS 2017.
6. Imola J., Murakami T., Chaudhuri K. Locally Differentially Private Analysis of Graph Statistics. USENIX Security 2021.
7. Imola J., Murakami T., Chaudhuri K. Communication-Efficient Triangle Counting under Local Differential Privacy. USENIX Security 2022.
8. Ding Z., Wang Y., Wang G., Zhang D., Kifer D. Detecting Violations of Differential Privacy. CCS 2018.
9. Bichsel B., Gehr T., Drachsler-Cohen D., Tsankov P., Vechev M. DP-Finder: Finding Differential Privacy Violations by Sampling and Optimization. CCS 2018.
10. Jagielski M., Ullman J., Oprea A. Auditing Differentially Private Machine Learning: How Private is Private SGD? NeurIPS 2020.
11. Nasr M., Song S., Thakurta A., Papernot N., Carlini N. Adversary Instantiation: Lower Bounds for Differentially Private Machine Learning. IEEE S&P 2021.
12. Steinke T., Nasr M., Jagielski M. Privacy Auditing with One (1) Training Run. NeurIPS 2023.
13. Reed J., Pierce B. C. Distance Makes the Types Grow Stronger: A Calculus for Differential Privacy. ICFP 2010.
14. Zhang D., Kifer D. LightDP: Towards Automating Differential Privacy Proofs. POPL 2017.
15. Near J. P. et al. Duet: An Expressive Higher-Order Language and Linear Type System for Statically Enforcing Differential Privacy. OOPSLA 2019.
16. Johnson N., Near J. P., Song D. Towards Practical Differential Privacy for SQL Queries. VLDB 2018.
17. Imola J., Murakami T., Chaudhuri K. Differentially Private Triangle and 4-Cycle Counting in the Shuffle Model. CCS 2022.
18. Eden T., Liu Q. C., Raskhodnikova S., Smith A. Triangle Counting with Local Edge Differential Privacy. arXiv:2305.02263, 2023.
19. He Y., Wang K., Zhang W., Lin X., Zhang Y., Ni W. Robust Privacy-Preserving Triangle Counting under Edge Local Differential Privacy. PACMMOD 3(3), 2025.
20. Ye Q., Hu H., Au M. H., Meng X., Xiao X. LF-GDPR: A Framework for Estimating Graph Metrics with Local Differential Privacy. IEEE TKDE, 2020.
21. Dhulipala L., Liu Q. C., Raskhodnikova S., Shi J., Shun J., Yu S. Differential Privacy from Locally Adjustable Graph Algorithms: k-Core Decomposition, Low Out-Degree Ordering, and Densest Subgraphs. FOCS 2022.
22. Zhang Y., Ni W., Wang K., He Y., Li C. Truss Decomposition under Edge Local Differential Privacy. ICDE 2025.
23. Nguyen L., Yan Y. Evaluating the Structural Awareness of Large Language Models on Graphs: Can They Count Substructures? 2024.
24. Wang H., Feng S., He T., Tan Z., Han X., Tsvetkov Y. Can Language Models Solve Graph Problems in Natural Language? NeurIPS 2023.
25. Fatemi B., Halcrow J., Perozzi B. Talk Like a Graph: Encoding Graphs for Large Language Models. arXiv:2310.04560, 2023.
26. Chen N., Li Y., Tang J., Li J. GraphWiz: An Instruction-Following Language Model for Graph Computational Problems. KDD 2024.
27. Tang J., Zhang Q., Li Y., Li J. GraphArena: Benchmarking Large Language Models on Graph Computational Problems. ICLR 2025.
28. Hu Y., Lei R., Huang X., Wei Z., Liu Y. Scalable and Accurate Graph Reasoning with LLM-based Multi-Agents. arXiv:2410.05130, 2024.
29. Gao D. et al. AgentScope 1.0: A Developer-Centric Framework for Building Agentic Applications. arXiv:2508.16279, 2025.

注：第 8–16 条投稿前需逐条核对出处。
