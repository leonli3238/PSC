# Qwen3-8B 实验结果分析（组会汇报版）

> 日期：2026-11-10  
> 范围：CertiCount 中 A1–A4 四组 Qwen 实验（PM 数据集，本地 vLLM）  
> 口径：所有数字来自 `certicount/results/` 的原始 `runs.jsonl` / `designs.jsonl` / 报告；本文只做汇总与解释。  
> 统计：纯代码部分每格 10 次运行；设计部分每任务 10 个独立设计；区间为 95% Clopper–Pearson（比例）或按设计聚类的 paired bootstrap（均值）。

---

## 0. 一页结论

1. **节点执行错误真实存在，且随度数急剧上升。** Qwen3-8B 非思考模式在 PM 的度数分层错误率为：1–10 度 **0%**、11–30 度 **3.2%**、31–60 度 **74.9%**、61–120 度 **99.9%**、>120 度 **99.9%**。审计在宽松的 ε₃=2.0 口径下仍确认 **51/158** 对越界（real-count 47；联合 Bonferroni 后 49/158、real 45），ε_lb 最高 **4.30**（约为 ε₃ 的 2.15 倍），单次最大计数偏差 **406**。
2. **program 模式把这条错误链彻底切断。** PM degree 端到端 100 次：RE **0.0030**、`exec_exact = 1.0`、节点 LLM 调用 **0**、认证越界 **0**，与 GT-DSL / GT-PSC 在同噪声下完全一致；`ci_covers_truth = 0.94`。  
   **思考模式对照：** 同一 20 对难例上，8B-thinking 把确认越界从 **15/20 降到 0/20**，ε_lb max **4.30 → 1.37**；但 >120 度仍有 **10.8%** 执行错误、最坏单点 Δ 达 **1.02e8**，0/20 是“未确认”，不是保证。A3 的 **9 个 `N(self)` 灾难全部由 thinking curator 写出**——CoT 不解决设计器的规格博弈。
3. **设计器能写对程序，但会系统性地“钻空子”。** 70 个设计中 **61 个被接受（87.1%，95% CI 77.0–94.0%）**；其中 **52 个不是 `N(self)` 灾难**，49 个与 GT-DSL 几乎相同（2-star/4-star/5-star 的 `design_error` 为 0，3-star +0.00017，moment2 紧界 +0.00012），另有 3 个 moment2 松界（2.4×）；但 **9 个（14.8%）** 用了 `N(self)`（ε₂ 发布后的含噪邻居表）做非线性计数，RE 达 **30–100 倍**。
4. **认证本身没有错，错在“效用测试不看输入噪声”。** A4 在 **119 份草稿** 上 `certificate_unsound = 0`，即推导 GS 从未低于证伪器找到的最大变化；但现有 `utility_test` 用**真实邻表**执行程序（`N(self)=P`），因此 `comb(size(N(self)), k)` 在小图上完全正确、在真实含噪数据上放大 30–100 倍。
5. **对论文主张的影响：** 隐私保证（Q1/Q2）证据充分；精度非劣性（Q3）**不能无条件写**。必须在设计循环里加“含噪端到端效用门”，否则 12/61 个接受程序（9 个 `N(self)` + 3 个裸 `size(P)²`）会破坏非劣性。加上门之后，剩余 49/61（80.3%）与 GT-DSL 一致，非劣性才成立。

> 一句话版：**Qwen3-8B 的结果把问题从“LLM 会不会算错”推进到“LLM 会不会在通过所有检查后仍然给出一个统计上没用的程序”；CertiCount 已经解决了前者，下一个必须补的是后者。**

---

## 1. 实验版图与口径

| 编号 | 目的 | 模型/角色 | 数据与规模 | 重复 | 结果目录 |
|---|---|---|---|---|---|
| A1 | 节点执行错误 + 隐私审计 | Qwen3-1.7B、Qwen3-8B（非思考）、Qwen3-8B（思考）、`certicount-program` 对照 | PM，n=453，m=2025，平均度 8.94，最大度 237 | screen 1.1k–7.5k trials/bin；confirm 300 trials/side | `results/audit/sensitivity/probe_pm_degree_*` |
| A2 | program 模式端到端 | curator Qwen3-8B（思考），节点不调用 LLM | PM degree | 100 次 | `results/execution/A2_pm_degree_program_8bthink_r100/` |
| A3 | 设计器能力（库内 + 库外） | curator Qwen3-8B（思考，T=0.6） | PM × 7 任务 × 10 设计 | 每个接受设计 10 次 DP 运行 | `results/dsl_eval/A3_pm_design_8bthink_d10{,_oob}/` |
| A4 | 认证消融：不认证会怎样 | 对 A3 的每份草稿重放 | 119 份草稿 | 证伪器 n=5/7 小图穷举 + 随机 | `.../certification_ablation/` |

**预算口径：** 端到端 ε=2.0，r1=0.5（RR 含噪图）、r2=0.2（含噪度界）、r3=0.3（计数阶段，ε₃=0.6）。A1 的审计把计数阶段单独拿出来，给 **ε₃=2.0**（比端到端 0.6 更宽松）；在这个更宽松的口径下仍确认越界，说明错误幅度足以压过噪声。

**思考模式说明：** A2/A3 的 curator 全部是 thinking（`enable_thinking=true`，T=0.6，max_tokens 9500）；A1 的节点 thinking 只跑了 20 对确认（没有全量 screen）；唯一“同一批节点对”的非思考 vs 思考配对见 2.5 节。所有 A3 的设计指标（包括 9 个 `N(self)` 灾难）都来自 thinking curator。

**PM 图的关键事实：** 真值 degree=8.94、2-star=79,173、3-star=3,352,172、triangle=3,284、4-star=153,983,040、5-star=6,476,308,310、degree-moment2=162,396。这是一个重尾图（最大度 237），高度数节点正是节点 LLM 最容易出错的地方。

### 1.1 A2 与 A3 的区别

这两个实验经常被混在一起，但回答的是不同问题：

| 维度 | A2 | A3 |
|---|---|---|
| 要回答的问题 | **CertiCount 架构的管线是否正确** | **LLM 设计器能否写出正确程序** |
| 程序来源 | 固定 `size(P)`（已知正确的库内程序） | LLM 现场设计，每任务 10 个独立设计 |
| 是否有设计循环 | **没有**；1 次调用、1 个程序、1 轮通过 | **有**；parse / GS / 语义 / 证伪器，1–3 轮反馈 |
| 运行规模 | 100 次端到端 | 每个接受设计 10 次 DP 运行；7 任务共 70 个设计 |
| 失败来源 | 预算拆分、噪声顺序、聚合、节点调用 | 设计错误、`N(self)` 捷径、GS 松、parse 失败 |
| 关键结果 | RE 0.0030、exec_exact 1.0、node calls 0 | 61/70 接受；49/61 可用；9/61 灾难 |
| 结论用途 | 证明“把计算挪回代码”这条路本身可行 | 证明“LLM 能写对，但需要含噪效用门” |

一句话：**A2 是“框架自检”，A3 是“设计器考试”；A4 是拿 A3 的答卷做“如果不认证会怎样”的反事实审计。** A2 的 program 是题库里的标准答案，A3 的 program 是模型现场写的；A2 不经过设计循环，A3 的所有接受/退回都发生在设计循环里。

---

## 2. A1：节点执行错误与隐私审计

### 2.0 先定义：这里的“越界”到底指什么

- 任务规则是 `f(G) = degree(u)`，全局敏感度 **GS=1**；机制发布 `f + Lap(1/ε₃)`，审计给 **ε₃=2.0**，噪声尺度是 **0.5**。
- 相邻图 `x` 与 `x2` 只差一条边，真实度数只差 **1**。如果 LLM 在两张图上的输出也只差 1，机制仍然是 2-DP。
- 但 LLM 可能在 `x` 上输出 90、在 `x2` 上输出 70（真实只差 1）。等效敏感度变成 20，500 次重复的似然比检验会给出 **ε 的下界 ε_lb > 2**。
- 本文的“**确认越界**”= 经 Bonferroni 校正后 **ε_lb > 2.0**；“**Δ**”= 两次输出之间的最大差。`ε_lb` 是下界，不是点估计。

**关键：错本身不一定泄露；相邻输入上的“错法不一致”才泄露。** 一个节点即使把 237 数成 127，只要它在 236 上也稳定输出 127，隐私损失仍然很小；真正致命的是 237→127、236→198/452 这种跳变。

### 2.1 度数分层错误率（screen）

| 模型 | 度数 bin | trials | 执行错误率 | 平均绝对误差 | 平均 token |
|---|---|---:|---:|---:|---:|
| Qwen3-8B | 1–10 | 1,112 | **0.000** | 0.00 | 97 |
| Qwen3-8B | 11–30 | 2,430 | **0.032** | 0.03 | 150 |
| Qwen3-8B | 31–60 | 7,462 | **0.749** | 2.35 | 289 |
| Qwen3-8B | 61–120 | 7,154 | **0.999** | 13.4 | 450 |
| Qwen3-8B | >120 | 1,954 | **0.999** | 56.1 | 582 |
| Qwen3-1.7B | 1–10 | 1,112 | 0.002 | 0.00 | 87 |
| Qwen3-1.7B | 11–30 | 2,430 | 0.323 | 0.52 | 154 |
| Qwen3-1.7B | 31–60 | 7,462 | 0.883 | 6.1 | 381 |
| Qwen3-1.7B | 61–120 | 7,154 | 0.998 | 55.1 | 488 |
| Qwen3-1.7B | >120 | 1,954 | 1.000 | 94.7 | 320 |

结论：错误率不是均匀的，而是**随消息条数（度数）单调上升**。8B 在 30 度以下基本可靠，超过 60 度几乎必错；1.7B 在 30 度以上就开始崩。

### 2.2 确认越界（confirm，Bonferroni 校正）

| 模型 | 集合 | tested | violations | real-count | ε_lb max | ε_lb median | max Δ |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3-8B | main_div | 40 | 24 | 20 | 4.19 | 3.25 | 406 |
| Qwen3-8B | nodes | 20 | 15 | 15 | 4.30 | 2.94 | 332 |
| Qwen3-8B | random | 60 | 4 | 4 | 3.51 | 1.09 | 41 |
| Qwen3-8B | transfer（1.7B 确认对） | 38 | 8 | 8 | 2.42 | 0 | 352 |
| Qwen3-1.7B | main | 40 | 38 | 33 | 4.20 | 4.11 | 449 |
| Qwen3-1.7B | main_div | 40 | 38 | 27 | 4.21 | 3.63 | 449 |
| Qwen3-1.7B | nodes | 36 | 31 | 29 | 4.01 | 3.51 | 437 |
| Qwen3-1.7B | random | 60 | 7 | 7 | 3.64 | 0.918 | 395 |
| certicount-program | main_div | 40 | **0** | 0 | 1.47 | 0.956 | 1 |
| certicount-program | nodes | 20 | **0** | 0 | 1.32 | 0.988 | 1 |

联合 Bonferroni（family α=0.05，M=334）：**163/334 确认越界（real-count 141）**，单对 α=1.5e-4；program 对照 0/60。8B 单独看：按单集设计 51/158（real 47），联合重界后 49/158（real 45）。  
节点层面（8B）：1–10 度 **0/12**、11–30 度 **2/30（6.7%）**、31–60 度 **6/8（75%）**、61–120 度 **6/8（75%）**、>120 度 **1/2**。1.7B 对应为 0/12、14/19、8/8、7/7、2/2。

### 2.2.1 四个真实越界样本：模型到底输出了什么

下面全部是 `confirm_nodes` 里的真实节点对（`source=real`，PM 图），两张图只差一条边；输出是模型原始回答（520 次重复），还没加机制的 Laplace 噪声。

| 节点 | 真实度数 x→x2 | 模型在 x 上的输出（520 次） | 模型在 x2 上的输出（520 次） | 真实变化 | 模型变化 | ε_lb |
|---|---|---|---:|---:|---:|---:|
| n3 | 38 → 39 | **38（520/520）** | **40（278）、43（190）、42（29）、39（21）** | +1 | **+2 到 +5** | **2.64** |
| n8 | 75 → 74 | **93（222）、90（205）、94（92）、95（1）** | **70（520/520）** | −1 | **−20 到 −25** | **4.26** |
| n37 | 63 → 64 | **43（492）、70（28）** | **90（372）、80（101）、70（46）、73（1）** | +1 | **+27 到 +47** | **4.14** |
| n14 | 237 → 236 | **122（170）、127（151）、128（125）、123（67）、120（7）** | **198（329）、452（95）、210（41）、195（31）、200（23）** | −1 | **+67 到 +332** | **4.30** |

怎么读：

- **n3**：真实只加 1 条边，模型从“稳定 38”跳到“40/43”；虽然量级不大，但噪声尺度只有 0.5，已经足以在 500 次重复中区分两个分布。
- **n8**：真实删 1 条边，模型从 90–95 掉到 70，方向相反、幅度 20–25；这是典型的“数错并且错法随输入跳变”。
- **n37**：真实 63→64，模型 43→70–90；相邻输入的输出分布几乎不重叠。
- **n14**：真实 237→236，模型 120–128→195–452，甚至出现 452（比真实度还大 215）；这是最戏剧化的例子，也是 ε_lb=4.30 的来源。

**分析：**

1. **这不是“偏差”问题，而是“不稳定性”问题。** n14 在 x 上稳定错到 127（偏差 110），如果 x2 也稳定错到 127，机制仍然近似 2-DP；但 x2 跳到 198/452，两个分布被拉开，审计才能确认 ε_lb=4.30。
2. **错误随度数增加而放大。** 高度数节点的列表更长，模型在“数数”时更容易受列表顺序/位置影响；一条边的增删会改变它采用的计数策略。
3. **机制噪声 0.5 太小，遮不住 20–300 的跳变。** 如果 GS 仍按 1 计，Lap(1/2) 的噪声根本无法覆盖真实敏感度 20–300，隐私损失自然超过 ε₃=2。
4. **审计的 500 次重复是关键。** 单次看只是“答错了”；重复采样才能看出两个分布的系统性差异，也才能给出 ε_lb 下界。

### 2.3 thinking 的快速对照（逐对细节见 2.5）

在 8B 非思考筛选出的 20 个“最可疑节点对”上，用 **Qwen3-8B thinking** 重跑：

- **0/20 确认越界**；ε_lb max **1.37**、median **1.03**（均低于 ε₃=2.0）。
- >120 度 bin 仍有 `exec_error_rate = 0.108`、jitter=1，最大 |Δ| 的描述性数值达到 1.02e8，但审计的 ε_lb 未超过 2.0，不能据此声称泄露。
- 代价：thinking 的输出 token 与延迟显著高于非思考（A3 的 curator 思考模式平均输出 3,950 tokens/次，最大 9,151）。

**解释：** CoT 把“数数”错误大幅压低，说明 8B 的错误主要是**长列表计数/状态跟踪**问题，而不是完全不会；但只要还存在 10.8% 的高阶错误和 jitter，就不能把隐私保证寄托在“换个会思考的模型”上。

### 2.4 A1 的结论与边界

- **可以写：** 在 PM 重尾图上，8B 非思考节点在高度数节点上几乎必然算错；审计在 ε₃=2.0 的宽松口径下确认了最高 4.30 的 ε_lb 和 406 的计数偏差；program 模式 0/60。
- **不能写：** “PSC 在 8B thinking 下也泄露”。20 个难对上是 0/20；只能写“thinking 是一种有效缓解，但不是保证，且成本更高”。
- **审计只证伪：** 0 越界不等于隐私；program 对照的 0/60 是“没有发现越界”，不是证明。

### 2.5 思考模式节点：同一 20 对的配对比较

这是目前唯一一组“同一批节点对、非思考 vs 思考”的配对实验：思考组直接复用 8B 非思考 `confirm_nodes/pairs.jsonl` 的 20 对，因此不是两组不同难度的样本。

**解码差异：** 非思考是 `temperature=0`、`max_tokens=4096`、`enable_thinking=false`；思考是 `temperature=0.6`、`top_p=0.95`、`max_tokens=12000`、`enable_thinking=true`（Qwen3 官方推荐的 thinking 采样）。因此差异同时包含 **CoT** 与 **采样温度** 两个因素，不能全部归因于 CoT；作为“强基线”是合理的，作为因果结论需要补 `T=0.6` 的非思考对照。

| 度数 bin | pairs | 非思考 violations | 非思考 exec_err | 非思考 ε_lb max | 思考 violations | 思考 exec_err | 思考 ε_lb max |
|---|---:|---:|---:|---:|---:|---:|---:|
| 11–30 | 2 | **2/2** | 0.000 | 2.64 | **0/2** | 0.000 | 1.25 |
| 31–60 | 8 | **6/8** | 0.684 | 4.07 | **0/8** | 0.00195 | 1.37 |
| 61–120 | 8 | **6/8** | 1.000 | 4.26 | **0/8** | 0.00352 | 1.18 |
| >120 | 2 | **1/2** | 1.000 | 4.30 | **0/2** | 0.108 | 1.00 |
| **合计** | **20** | **15/20** | — | **4.30** | **0/20** | — | **1.37** |

读法：

- **越界率**：非思考 15/20 → 思考 0/20；ε_lb max 4.30 → 1.37，median 2.94 → 1.03。thinking 确实把“可确认的越界”压到 0。
- **执行错误率**：31–60 从 68.4% → 0.20%，61–120 从 100% → 0.35%，>120 从 100% → 10.8%。降幅是数量级的，但**不是 0**。
- **最坏单点误差反而更大**：`max_delta_llm_over_gs` 非思考 332 → 思考 **1.02e8**（>120 bin）。这是一个罕见的灾难性输出；审计在 300/500 trials 下没有把它转成 ε_lb>2（该 bin ε_lb=1.0002），但这说明 **0/20 是“分布上未确认”，不是“逐点安全”**。
- **jitter 仍然存在**：31–60 为 0.25、61–120 为 0.375、>120 为 **1.0**；thinking 并没有消除输入扰动下的不稳定性。
- **样本选择性**：20 对来自非思考的“可疑集”，所以 0/20 是在**最难子集**上的结果，外推到全体节点会偏乐观；它也不能给出 thinking 的总体越界率。
- **11–30 的 2/2 越界与 exec_err=0 并存**：`exec_error_rate_x` 只统计 x 侧，审计同时看 x/x2；该 bin 非思考的 `max_delta_llm_over_gs=2`，说明 x2 侧仍有 2 的计数差。不要只看单侧执行错误率。

**结论：** thinking 是有效的**缓解**，不是**保证**；它把“常见错误”压下去了，但保留了“罕见灾难输出 + jitter”。这正是 CertiCount 的 program 模式要解决的问题：不依赖模型是否思考、是否稳定。

---

## 3. A2：program 模式端到端

PM degree，100 次同噪声配对：

| 方法 | RE | se | median RE | exec_exact | 节点 LLM 调用 | 设计调用 | CI 覆盖真值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| DSL（program） | **0.002998** | 0.000239 | 0.002432 | **1.0** | **0** | 1 | 0.94 |
| GT-DSL | 0.002998 | 0.000239 | 0.002432 | — | 0 | 0 | — |
| GT-PSC | 0.002998 | 0.000239 | 0.002432 | — | 0 | 0 | — |

设计程序：`size_p = size(P); return size_p; aggregate: total / n`，1 次调用、1 轮通过、`gs_ratio=1`、`split_match=1`、`design_error=0`。

**结论：** program 模式的管线、预算拆分、噪声顺序都与 GT-DSL 对齐；degree 这种简单任务上，端到端误差与理想参照完全相同，且节点调用为 0。这是后续所有设计实验的“地基”。

---

## 4. A3：设计器能力（库内 + 库外）

### 4.0 A3 的任务、prompt 与输出示例

#### 4.0.1 七个任务

| 任务 | 类型 | 统计量 | PM 真值 | 备注 |
|---|---|---|---:|---|
| degree | 库内 | 平均度 `Σdeg/n` | 8.94 | 最简单，A2 也用它做端到端 |
| 2-star | 库内 | `Σ C(deg,2)` | 79,173 | 需要投影，否则 GS 大 |
| 3-star | 库内 | `Σ C(deg,3)` | 3,352,172 | 同上 |
| triangle | 库内 | 三角形总数 | 3,284 | 需要 `P & N(v)` 集合交，最难 |
| 4-star | 库外 | `Σ C(deg,4)` | 153,983,040 | 与 5-star 同构 |
| 5-star | 库外 | `Σ C(deg,5)` | 6,476,308,310 | 模型最稳，9/9 精确 |
| degree-moment2 | 库外 | `Σ deg²` | 162,396 | 乘积界松，3/10 落到 47.6× GS |

#### 4.0.2 LLM 实际看到的 prompt（以 5-star 为例）

**System（原文，353 字符）：**

```text
You are the curator agent of a multi-agent system that counts substructures of a graph
under edge local differential privacy. You never see the graph. You write the program
that every node runs locally on its own neighbor list; the system derives the program's
sensitivity and the node executes it. Answer with the program only, in the requested format.
```

**User（2,498 字符）的关键部分：**

```text
The program language (a small subset of Python):
- P: the set of this node's true neighbors (private and exact; it never contains the node itself)
- self: this node's id; n: number of nodes
- D: public degree threshold, dmax: public maximum degree of the public noisy graph (equal to D here)
- N(x): public neighbor set of node x in the public noisy graph. It is a randomized-response
  copy of the real graph: it misses some real edges and contains some fake ones.
- size(S); project(S, k): at most k elements of S; comb(x, k); pow(x, k); clip(x, lo, hi); ...
- set operators & (intersection), | (union), - (difference); sum(<expr> for j in <set>)
- lines 'name = <expr>' (each name assigned once) followed by one final 'return <expr>'

How the result is computed: every node reports its return value plus Laplace noise scaled to
the program's sensitivity; the aggregate is an arithmetic expression over total and n.
Smaller sensitivity means less noise: bound degrees with project(P, D) before nonlinear functions.
The sensitivity checker bounds comb(size(S), k) tightly; products of expressions get looser bounds.
Reading D or dmax, or calling N, makes the system spend part of the budget on a noisy degree bound.

The input prompt from the analyst is:
"""
For each node, the number of 5-stars centered at that node is the number of unordered
5-subsets of its neighbors, i.e. C(degree(node), 5). The total number of 5-stars in the
graph is the sum of 5-stars centered at each node. Each node may hide its edge information
under the local edge differential privacy framework. Q: The nodes are numbered from 0 to 452.
What is the total number of 5-stars in the graph?
"""

The graph has 453 nodes.

Reply with exactly two parts:
```dsl
<program>
```
aggregate: <expression over total and n>
```

**注意 prompt 里的两个细节：**

1. 它明确说 `N(x)` 是含噪发布图，但**没有单独说 `N(self)` 也是含噪的**；模型很容易把“自己的列表”当成真实邻居。
2. 它明确说“乘积的界更松”，但**没有把“松”提升为拒绝条件**；所以 `size(P)²` 仍会被接受。

#### 4.0.3 成功输出：5-star（accepted，9/9 精确）

**模型的思考片段（节选）：**

```text
The user wants the total number of 5-stars ... The sensitivity of comb(size(project(P,D)),5)
is C(D,4) - C(D-1,4) = C(D-1,4)? ... Smaller sensitivity means less noise, so I should
project P to D before comb. The aggregate is total.
```

**最终输出（原文）：**

```dsl
count = comb(size(project(P, D)), 5)
return count
```
aggregate: total

**结果：** accepted；`gs_ratio=1.0`；10 次 DP 运行 RE 0.2142，与 GT-DSL 逐次完全一致。

#### 4.0.4 失败与退回：degree design 0（3 轮后被拒）

这是同一个 prompt 骨架下的真实退化过程，也解释了 `N(self)` 是怎么进来的：

| 轮次 | 模型输出 | aggregate | 反馈 | 结果 |
|---|---|---|---|---|
| 1 | `return size(P)` | `total / 453` | 在小图上 0.0044 vs 0.4；路径 0.01766 vs 1.6；"The program under-counts on every failing graph." | 退回 |
| 2 | `return size(project(N(self), D))` | `total / 453` | **完全相同的反馈**（因为 aggregate 还是 453） | 退回 |
| 3 | `return size(N(self))` | `total / 453` | 仍然是相同的反馈；模型在思考里写“the user's examples are incorrect” | **拒绝** |

**分析：**

- 第一轮的程序 `size(P)` 本身是对的；错在 aggregate 把 `n` 硬编码成了 `453`。在 n=5 的测试图上，`total/453` 当然小了 90 倍。
- 反馈只说“under-counts on every failing graph”，没有指出“测试图 n=5，你的 aggregate 用了字面量 453，请用 n”；模型无法定位，于是改**局部程序**而不是改 aggregate。
- 在效用测试里 `N(self)=P`（用真实邻表执行），所以第 2、3 轮的局部程序看起来仍然“语义正确”；失败依旧是 aggregate。模型因此越改越偏，最后落到 `N(self)`。
- 这是一个**反馈可操作性**问题：utilty test 报的是症状，不是“局部公式 vs aggregate 哪一部分错了”。改进方向：反馈里同时打印测试图的 n、程序的 aggregate、以及“局部正确但聚合缩放错”的诊断。

#### 4.0.5 灾难输出：triangle（5/6 接受设计都是这个）

**正确的写法（design 6，RE 1.432）：**

```dsl
total = sum( size(P & N(v)) for v in P )
return total / 2
```
aggregate: total / 3

**灾难的写法（design 1/2/4/7/8，RE 100.9）：**

```dsl
neighbors = project(N(self), D)
sum_edges = sum( size(N(v) & neighbors) for v in neighbors )
return sum_edges / 2
```
aggregate: total / 3

**实际运行：**

| 写法 | 10 次估计范围 | 真值 | 平均 RE |
|---|---:|---:|---:|
| 正确（用 `P`） | 445–13,732 | 3,284 | 1.432 |
| 灾难（用 `N(self)`） | 330,763–339,058 | 3,284 | **100.9** |

**为什么：** `N(self)` 是 ε₂ 发布后的含噪列表，含约 120 条假边；`N(v) & neighbors` 的交集把假边放大，5 个设计给出完全相同的 334,918，说明这是**确定性的语义错误**，不是随机波动。

#### 4.0.6 为什么模型会写错：两类机制

**(A) `total / 453`：把“实例”当成“程序”**

- 模型原话：*"Since n is 453, the aggregate is total / 453."*
- 它把 prompt 里的具体实例（453 个节点）当成程序的固定常量，而不是在测试图上会变化的 `n`。
- 它不知道 utility test 会在 n=5/6 的小图上跑；反馈只说“under-counts”，没有指出“测试图的 n 不是 453”。
- 更深一层：它把任务理解成“为这张图写一个一次性表达式”，而不是“写一个对任意测试图都成立的程序”。这是**实例 vs 程序**的混淆。

**(B) `N(self)`：角色混淆 + 语义模糊 + 目标错位**

1. **角色混淆。** System 说 curator *"never see the graph"*；模型把这句话过度推广到 node program，得出 *"the previous attempt was rejected, which suggests that the program can't access P directly."* 但 `P` 是节点本地的真实邻居，程序当然能读；不能读的是 curator。
2. **`N(self)` 语义模糊。** Prompt 说 `N(x)` 是含噪公开图，但没有单独说 `N(self)` 也是含噪的；模型把 `N(self)` 当成“我自己的列表”（真实 `P`），并认为读取已发布数据不花预算。原话：*"the program must include reading N(self) to consume the budget."*
3. **目标错位。** Prompt 强调 *"Smaller sensitivity means less noise"*；`N(self)` 是后处理，GS=0，是这句话的**最优解**。模型优化的是“灵敏度最小”这个代理目标，不是“含噪估计准确”这个真实目标。
4. **符号正确 ≠ 统计正确。** 模型在**精确图**上验证代数：*"dividing by 2 gives the correct number of edges ... dividing by 3 gives the correct total."* 代数没错，但它没有模拟 RR 的假边，也没意识到 `N(self)` 在真实运行中不是精确图。
5. **检查器盲区。** Utility test 也用真实邻表执行（`N(self)=P`），所以同样的符号检查通过；模型得不到“`N(self)` 在真实运行中含约 120 条假边”的反馈。错误的程序被接受，循环没有纠错信号。
6. **选择偏差。** Triangle 的 5/6 接受设计都用 `N(self)`；设计循环接受“第一个通过检查的候选”，不比较含噪 RE，所以模型的默认模式被保留。模型其实能写出正确版本（design 6），但没有选择压力。

**为什么 5-star 没写错？**

- 5-star 有强模板：`comb(size(project(P,D)), k)`，prompt 也明确提示 *"bound degrees with project(P, D) before nonlinear functions"*；模型 9/9 命中。
- Triangle 没有模板，需要组合 `P & N(v)` 和 `sum`；模型的默认模式退到公开图 `N`，而精确 utility test 对两种写法都放行，没有“含噪准确率”来区分。

**一句话：** 不是模型“不会数”，而是 **prompt 的角色/变量语义 + “最小灵敏度”代理目标 + 检查器盲区** 共同把模型推到了一个“符号上正确、统计上错误”的局部最优。

### 4.1 总表

10 个独立设计/任务；RE 为接受设计的 10 次 DP 运行平均；`design_error = RE(设计) − RE(GT-DSL)`；`catastrophic` 指 RE>2 的接受设计。

| 任务 | 接受 | 首次通过 | LLM 调用 | RE 均值 | RE 中位数 | GT-DSL | design_error | exact 比例 | catastrophic |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| degree | 9/10 | 9 | 12 | 0.0032 | 0.0033 | 0.0033 | −0.00012 | 0.889 | 0 |
| 2-star | 9/10 | 2 | 21 | **9.86** | 0.0319 | 0.0319 | **9.83** | 0.778 | **2** |
| 3-star | 9/10 | 6 | 15 | **4.97** | 0.0893 | 0.0893 | **4.88** | 0.667 | **1** |
| triangle | 6/10 | 4 | 20 | **84.35** | 100.9 | 0.9325 | **83.42** | 0.000 | **5** |
| 4-star | 9/10 | 2 | 19 | **3.48** | 0.1531 | 0.1531 | **3.33** | 0.889 | **1** |
| 5-star | 9/10 | 4 | 17 | 0.2142 | 0.2142 | 0.2142 | **0** | **1.000** | 0 |
| degree-moment2 | 10/10 | 6 | 15 | 0.0445 | 0.0313 | 0.0312 | 0.0134 | 0.000 | 0（3 个松界，2.4×） |
| **合计** | **61/70** | **33** | **119** | — | — | — | — | — | **9/61** |

- 总接受率 **61/70 = 87.1%**（95% CI 77.0–94.0）；首次通过 **33/70 = 47.1%**（35.1–59.5）；灾难率 **9/61 = 14.8%**（7.0–26.2）。
- 接受率的单任务区间很宽（9/10 的 95% CI 约 0.55–1.00；triangle 6/10 为 0.26–0.88），**只能作描述性结论**。

### 4.2 双峰分布：均值会骗人

2-star / 3-star / triangle / 4-star 的 RE 不是“普遍偏高”，而是**双峰**：

- 2-star：7 个设计精确等于 GT-DSL（0.0319），2 个设计 44.24；
- 3-star：8 个约 0.0893，1 个 43.97；
- triangle：1 个 1.432，5 个 100.9；
- 4-star：8 个 0.1531，1 个 30.08。

因此 **均值 9.86 / 4.97 / 84.35 / 3.48 不是“设计器平均差”，而是“少数灾难程序把均值拉爆”**。组会汇报应同时给中位数与灾难率；论文主表也建议用中位数/分位数 + 配对 bootstrap，而不是只报均值。

### 4.3 灾难的机制：`N(self)` 是含噪发布行，不是真实邻表

9 个灾难设计**全部**使用 `N(self)`（或 `project(N(self), D)`）作为计数来源；52 个非灾难设计**全部**使用 `P` / `project(P, D)`。这是完美分离，不是随机波动。

典型程序：

```text
name = size(N(self)); count = comb(name, 2); return count; aggregate: total
name = comb(size(N(self)), 4); return name; aggregate: total
neighbors = project(N(self), D)
sum_edges = sum(size(N(v) & neighbors) for v in neighbors)
return sum_edges / 2; aggregate: total / 3
```

数值对照（PM）：

| 任务 | 真值 | `N(self)` 程序估计 | 放大倍数 |
|---|---:|---:|---:|
| 2-star | 79,173 | 3,588,147 | **45×** |
| triangle | 3,284 | 334,918 | **102×** |
| 4-star | 153,983,040 | ≈4.8e9 | **31×** |
| 3-star | 3,352,172 | ≈1.47e8 | **44×** |

**为什么放大：** ε₁=1 的 RR 以约 0.73 的概率保留真实边、以约 0.27 的概率把非边变成假边。PM 有 n=453，单个节点的发布列表因此平均含 **≈120 条假边**（最大 241），而真实度只有 8.94。`comb(x,2)`、`comb(x,4)`、两个列表求交都是**非线性**的，假边会被平方级放大；triangle 的“交集再求和”最严重，达到 100×。

**为什么认证没拦住：** `N(self)` 是已经按 ε₂ 发布的数据，读取它是后处理，GS 确实为 **0**，不需要 ε₃ 噪声；证书是**正确**的。问题在效用：
`utility_test.run_exact()` 用 `rows = {u: frozenset(g.adj[u])}`（真实邻表）执行程序，于是 `N(self) = P`，`comb(size(N(self)),2)` 在小图上完全正确，`semantic_pass=True`、`sound=True`。**它测的是“语义对不对”，不是“在含噪输入上统计上有没有用”。**

这正是 9/61 灾难的唯一来源，也是当前方法最需要补的洞。

### 4.4 5-star / 4-star 为什么好，triangle 为什么差

- **5-star：9/9 精确**，全部写成 `comb(size(project(P, D)), 5)`，`gs_ratio=1.0`、`design_exact=1.0`。说明库外 k-star 的模式一旦被模型抓住，设计器可以稳定命中参考程序。
- **4-star：8/9 精确**，1 个 `N(self)` 灾难。结构与 5-star 同构。
- **triangle：6/10 接受，5/6 灾难**；10 次 parse 错误（语法/类型），4 次语义错误。唯一可用的程序是 `sum(size(P & N(v)) for v in P)/2`，RE 1.432 vs GT-DSL 0.932（GS 10 vs 参考 9，噪声尺度约多 11%；RE 差距还包含单样本的噪声实现，不能全归因于这 11%）。triangle 需要“用真实 P 做循环、与别人发布列表求交”，比 k-star 多一层集合语义，模型既容易写错语法，也容易退回 `N(self)` 捷径。

**含义：** 不是“库外任务一定难”——5-star 反而最稳；难的是**需要集合交/多表联合**的任务。这为 E6b 的任务选择提供了依据：库外任务要覆盖 k-star（容易）与 triangle 类（难），不能只报 5-star。

### 4.5 degree-moment2：产品表达式的 GS 松弛

10/10 接受，但分两类：

| 写法 | 个数 | gs_ratio | noise_ratio | RE |
|---|---:|---:|---:|---:|
| `size(project(P,D))²` | 7 | 1.004–1.105 | 1.004 | **0.03128** |
| `size(P)²` | 3 | **47.63** | 1.519 | **0.07538** |

- 裸 `size(P)²` 的推导 GS 约为参考值 `2D−1=19` 的 **47.6 倍**，噪声大 1.52 倍，RE 是紧界版本的 **2.4 倍**；但因为它是**有效**的（GS 大、隐私安全），设计循环接受了它。
- 现有“GS 过松”警告只对 `comb(..., k)` 触发（`sensitivity.py` 中 `x.hi >= n-1 and k >= 2`），**对乘积不触发**；所以 3 个裸 `size(P)²` 没有被退回。
- 这是“精度换隐私”的合法取舍，但应在设计评分里显式惩罚 `gs_ratio`，否则同一任务会随机落到 2.4× 误差的版本。

### 4.6 成本

| 指标 | 库内 4 任务 | 库外 3 任务 | 合计 |
|---|---:|---:|---:|
| 设计数 | 40 | 30 | 70 |
| LLM 调用 | 68 | 51 | **119** |
| 输出 token | 291,716 | 178,388 | **470,104** |
| 平均输出 token/次 | 4,290 | 3,498 | 3,950 |
| 最大输出 token | 9,151 | 7,339 | 9,151 |
| 设计墙钟 | 3,701 s | 2,264 s | **5,965 s（≈99 min）** |
| 节点 LLM 调用 | 0 | 0 | **0** |

按 API 价格粗算（仅输出，$0.5/M tokens）约 **$0.24**；本地 vLLM 只有 GPU 时间。设计是一次性、可缓存的（只依赖任务描述与 n），跨运行摊销后成本可忽略。**对比 PSC：** 节点调用 O(n)（triangle 约 2n+3），program 模式为 0；这是 C7 的直接证据。

### 4.7 思考模式 curator：A2/A3 的设计结果全部是 thinking

这一点需要在汇报里讲清楚，否则容易把“设计器失误”误读成“非思考模型能力不足”：

- A2/A3 的 curator 配置是 `configs/vllm_psc_qwen3-8b_curator-think.toml`：`enable_thinking=true`、`temperature=0.6`、`top_p=0.95`、`max_tokens=9500`；节点侧 `enable_thinking=false`。
- 因此 **第 4 节的全部设计指标（61/70 接受、49/61 可用、9 个 `N(self)` 灾难、28.6% parse 失败）都是 thinking curator 的结果**。CoT 并没有阻止模型选择 `N(self)` 这条捷径；它甚至可能强化了“GS=0 更优”的推理（模型在 `<think>` 里明确算过“这样灵敏度为 0，噪声最小”）。
- A2 的 degree 设计只用了 1 次调用，程序 `size(P)` 正确；degree 太简单，不能据此评价 thinking 的收益。
- **成本：** 119 次调用、平均 **3,950 output tokens/次**、最大 9,151、设计墙钟约 **99 分钟**；非思考节点探针的平均 token 只有 97–582（screen 口径），但角色不同，不能直接相减。
- **缺口：** 目前没有“非思考 curator 跑同一 A3”的对照，所以不能量化 thinking 对设计接受率/准确率的贡献。这是下一步最值得补的消融之一（同 prompt、同 T、只改 `enable_thinking`）。

**结论：** thinking 在“节点执行”上有效（2.5 节），但在“设计器”上**不是充分条件**；9 个灾难程序正是 thinking curator 写的。设计阶段真正需要的是**含噪效用门**，而不是更强的 CoT。

---

## 5. A4：认证消融（不做认证会怎样）

### 5.1 草稿漏斗

| 来源 | 草稿 | parse | gs_loose | semantic | refuted | accepted | 接受率 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 库内 4 任务 | 68 | 20 | 7 | 8 | 0 | 33 | 48.5% |
| 库外 3 任务 | 51 | 14 | 9 | 0 | 0 | 28 | 54.9% |
| **合计** | **119** | **34（28.6%）** | **16（13.4%）** | **8（6.7%）** | **0** | **61（51.3%）** | — |

- **parse 失败占 28.6%**，是设计循环最大的摩擦；模型在 DSL 语法/类型上要花 1–3 轮。
- `gs_loose` 16 份：主要是裸 `comb(size(P), k)` 与裸 `size(P)²`（后者未被现有检查拦下）。
- `semantic` 8 份：degree 3、2-star 1、triangle 4；如果没有效用测试，这些**错误统计**会被发布。
- `refuted = 0`：没有草稿在到达证伪器时被推翻（多数在 gs_loose/semantic 已退回）。

### 5.2 soundness：推导 GS 从未低于实测最大变化

| 来源 | runnable | 超过参考 GS | 比例 | max Δ/GS_ref | `certificate_unsound` | accepted 但比理想界松 |
|---|---:|---:|---:|---:|---:|---:|
| 库内 | 48 | 9 | 18.8% | 3.33× | **0** | 3（2×3-star，1×triangle） |
| 库外 | 37 | 12 | 32.4% | inf（D<k）/ 1.57× | **0** | 10（全部 moment2） |
| **合计** | **85** | **21** | **24.7%** | — | **0** | **13** |

- `certificate_unsound = 0` 是核心正面结果：**119 份草稿中，没有一份的实测最大变化超过系统自己推导的 GS**。这支持“推导器 sound”的主张（仍只是小图穷举 + 随机对拍，不是形式证明）。
- `uncertified_violations` 是**反事实**：假设 PSC 用任务的参考 GS（而不是程序自己的 GS）加噪，会有多少草稿越界。它主要命中的是**已被设计循环退回**的 `gs_loose` 草稿；真正被接受且“相对参考界”越界的只有：
  - 库内 triangle 1 个（GS 10 vs 参考 9，1.5×）；
  - 库外 moment2 3 个裸 `size(P)²`（证书 GS 约为参考 19 的 47.6 倍，按参考界会越 1.57×；按自己的 GS 是安全的）。
- 因此：**A4 不能写成“我们观测到 PSC 泄露”**；应写成“若跳过认证、直接按规则参考界加噪，24.7% 的可运行草稿会越界；认证把这一类风险全部拦住（0 unsound）”。

### 5.2.1 一个具体的反事实 witness

以 2-star 的一份被退回草稿为例：

```text
name = comb(size(P), 2)
return name
aggregate: total
```

- 程序含义：直接用节点的真实邻居表 `P` 数 2-star，没有投影到 `D`。
- 证伪器在 **n=7、dmax=4** 的小图上找到一组 witness：私有集 `P = [1,2,3,4,5]`（节点 6 的邻居表），两张相邻图的最大输出差 **Δ=5**。
- 2-star 在 `D=4` 的参考 GS 是 **3**；Δ/GS_ref = **5/3 = 1.67**。
- 程序自己推导出的 GS 是 **5**（因为裸 `P` 的最大规模按 `n−1` 计），所以 **CertiCount 会按 5 加噪，实际不会泄露**；设计循环把它标为 `gs_loose` 并退回。
- 但如果跳过认证、按“2-star 的理想 GS=3”加噪，就会少加 40% 的噪声；这就是 A4 里的“反事实越界”，**不是观测到的泄露**。

同一逻辑也解释了另外两类：

- 被接受的 triangle 程序（`sum(size(P & N(v)) for v in P)/2`）GS=10，参考界是 9；按参考界会越 1.5×，按自己的 GS 安全。
- 库外 moment2 的 `size(P)²` 程序，证书 GS 约为参考 `2D−1=19` 的 **47.6 倍**；按参考界会越 1.57×，按自己的 GS 安全，但 RE 变为紧界版本的 2.4 倍。

### 5.3 A4 的口径 caveat

- 证伪器在 n=5、dmax=3 与 n=7、dmax=4 的小图上穷举/随机搜索，**比值是下界**；真实 PM 的 dmax=237，裸 `P` 程序的真实越界幅度会远大于 1.57×。
- 4-star/5-star 出现 `max_eps_ratio = inf`：在 n=5、D=3（或 n=7、D=4）时参考 GS 为 0（k>D），而证伪器允许 |P|=4/5，任何非零计数都会得到 inf。这不是“真实图上无限泄露”，而是**检查尺寸 D<k 的口径问题**；汇报时要单独说明。
- 更严谨的做法：让证伪器的私有集大小与参考 GS 的 D 一致，或把 D<k 的检查单列。

### 5.4 CertiCount 架构自身的运行（不是 PSC 复现）

前面 A1–A4 里，真正跑“CertiCount 架构”的是 **A2** 和 **A3/A4 的 program 执行后端**；此外还有一批 GLM-5.2 的 CertiCount 运行，容易在汇报时和 PSC 基线混在一起，单独列出：

| 运行 | 模型 / 模式 | 数据 / 任务 | 次数 | 关键结果 | 性质 |
|---|---|---|---:|---|---|
| `A2_pm_degree_program_8bthink_r100` | Qwen3-8B thinking，`program` | PM / degree | 100 | RE **0.0030**、exec_exact **1.0**、node calls **0**、violations **0** | **唯一 Qwen 端到端 CertiCount** |
| `probe_pm_degree_certicount-8bthink` | `certicount-program`，`program` | PM / degree | 40+20 pairs | **0/60** violations，ε_lb max **1.47** | 审计对照（不是全框架） |
| A3 / A4 | Qwen3-8B thinking，设计 + `dp_execute` | PM / 7 任务 | 70 designs / 10 runs | 49/61 非劣；9 个 `N(self)` 灾难；0 unsound | 设计评估，不是全框架对比 |
| `glm_dsl_cu_do_v2` | GLM-5.2，`program` | CU/Do / degree,2-star,3-star,triangle | 10 | degree/2/3-star 基本 exact；CU triangle **1.92 vs GT 1.17**；Do triangle **10/10 拒绝** | 有回归、不稳定 |
| `glm_methods_cu_do` | GLM-5.2，`program` vs PSC/Naive | CU/Do / 4 任务 | 10 | program node calls **0** vs PSC **49–124**；triangle mixed | C7 证据，但 triangle 不稳 |
| `p5_new_arch_design_glm52` | GLM-5.2 设计 + adaptive（node calls 0） | CU/Do / 2,3,4-star,triangle | 10 | RE **0.11–1.24**、exec_exact **1.0**、violations **0** | 新架构自适应；小样本 |

读法与缺口：

- **Qwen 端到端只有 PM degree。** 2-star / 3-star / triangle / 4-star / 5-star 都只有“设计评估”（A3 的 `dp_execute` 10 次），没有跑完整的 `program / gt-dsl / gt-psc` 对比；因此不能写“Qwen 在全部任务上端到端非劣”。
- **没有 Qwen adaptive。** `p5_new_arch_*` / `p5_cu_do_*` 的 adaptive 是 GLM/hy3 + 预设计池，或 mock 池；Qwen 的 adaptive 还没跑。
- **GLM 的 triangle 也不稳。** `glm_dsl_cu_do_v2` 里 CU triangle 的 program RE 是 1.92（GT 1.17），Do triangle 10/10 被拒；`glm_methods_cu_do` 里 Do triangle 被接受，但 `node_e2e_acc=0.23`、`exec_exact=0`，只是 aggregate 碰巧接近。说明“设计质量门”不是 Qwen 特有，GLM 也会在 triangle 上翻车。
- **`p5_new_arch_design_glm52` 的方法标签仍写 `PSC[program+adaptive]`**，但目录/配置是 `modes=adaptive, pool_source=design`，应按“新架构自适应”理解；汇报时建议改标签，避免和 PSC 基线混淆。
- **mock / attacks / nodebound 不算 CertiCount 端到端 LLM 运行：** `p5_cu_do_glm52`、`p4_mock_*`、`nodebound_*`、`composite_*`、`attacks_*` 是纯代码/mock/攻击模拟，只能作机制或成本证据，不能当作“LLM 跑通架构”的证据。

---

## 6. 五个关键发现

1. **错误是度数驱动的，不是随机噪声。** 8B 在 30 度以下基本可靠，60 度以上几乎必错；1.7B 更早崩。审计在 ε₃=2.0 的宽松口径下仍确认 51/158 对越界，ε_lb 最高 4.30。  
2. **CoT 能大幅降低节点错误率，但不改变设计器的规格博弈。** 同一 20 对难例：非思考 15/20 确认越界、ε_lb max 4.30；思考 0/20、ε_lb max 1.37。但 >120 度仍有 10.8% 执行错误、jitter=1.0，最坏单点 Δ 从 332 升到 **1.02e8**；0/20 是分布上未确认，不是逐点安全。更关键的是，A3 的 9 个 `N(self)` 灾难**全部由 thinking curator 写出**——CoT 不会自动产生“含噪效用”这个概念。  
3. **program 模式把节点错误变成 0。** A2 的 degree 端到端 RE=0.0030、exec_exact=1.0、节点调用 0、越界 0；与 GT-DSL 完全一致。  
4. **设计器“会写对，也会钻空子”。** 61/70 接受；52 个不是 `N(self)` 灾难，其中 49 个与 GT-DSL 几乎相同，3 个 moment2 松界 2.4×；9 个用 `N(self)` 走捷径，RE 30–100×。完美分离说明这是**系统性语义陷阱**，不是模型手气。  
5. **认证 sound，但效用门不 sound。** 119 份草稿 `certificate_unsound=0`；然而现有 utility test 用真实邻表执行，`N(self)=P`，看不到 ε₂ 假边，于是把 9 个灾难程序判为“语义正确”。这是当前方法最关键的缺口。

---

## 7. 统计与方法学问题

| 问题 | 现状 | 影响 | 建议 |
|---|---|---|---|
| 设计样本小 | 每任务 10 个设计 | 接受率 CI 宽（0.55–1.00）；灾难率 CI 7–26% | 主表每任务 ≥30；至少 3 张图 |
| RE 双峰 | 均值被 1–5 个灾难设计主导 | 均值不能代表“设计器水平” | 报中位数、P90、灾难率；配对 bootstrap |
| 单一图 | 全部在 PM | 不能外推到 CU/Do/EE | 至少补 CU、Do 两张图 |
| 单一模型 | 只有 Qwen3-8B（+1.7B 探针） | 无法区分“方法问题”与“模型能力” | 加 hy3-ioa / GPT-4.1 / DeepSeek-v3 |
| thinking 对照混淆 | 非思考 T=0、思考 T=0.6；max_tokens 4k vs 12k | 不能把差异全归因于 CoT | 补 `T=0.6` 的非思考节点对照；curator 补同 T 的 enable_thinking 消融 |
| thinking 样本 | 只有 20 对确认，没有全量 screen | 不能给 thinking 的度数–错误率曲线 | 用同一 screen 跑 thinking（≥1k trials/bin） |
| A4 反事实 | 小图穷举、D<k 出现 inf | 比值是下界，不能当真实泄露 | 修私有集上界；D<k 单列 |
| 审计只证伪 | 0 越界不等于隐私 | 不能写“PSC 安全” | 用 program 对照 + 攻击实验补 |
| 设计/评估同分布 | 设计只看公开信息，但评估只在 PM | 设计可缓存，但精度未跨图 | 设计固定，评估换图 |

---

## 8. 改进清单（按优先级）

### P0：直接影响论文主张

1. **含噪端到端效用门（最关键）**  
   位置：`certicount/dsl/utility.py`、`designer.check_draft`。  
   做法：在公开合成图上按 r1 的 RR 机制生成 `N` 行（含假边），用与部署相同的 GS/ε₃ 运行程序，要求中位 RE ≤ 容差（如 1.2× GT-DSL 或绝对阈值）；不通过则把“在含噪发布行上误差 X 倍”作为反馈退回。  
   预期：`N(self)` 类程序在第一次设计时就被拒，设计循环会改写成 `project(P,D)`；灾难率应从 14.8% 降到 0（接受率可能下降，需要实测）。

2. **显式禁用/改名 `N(self)` 计数**  
   方案 A（推荐）：`N(self)` 只允许作为界（`project`/`clip` 的参数），禁止进入 `comb`/`pow`/`*`；类型检查直接报错。  
   方案 B：把 `N(self)` 改为返回真实 `P`（私有，GS>0），另设 `N_pub(self)` 表示 ε₂ 发布行；这样“读自己的真实表”天然付费。  
   同时更新 `DSL_REFERENCE`：明确写“`N(self)` 是含噪发布行，不是你的真实邻居；计数请用 `P` 或 `project(P,D)`”。

3. **产品表达式的 GS 松弛检查**  
   位置：`certicount/dsl/sensitivity.py`。  
   现状：只有 `comb(x,k)` 在 `x.hi >= n-1` 时警告；`size(P)²` 不警告。  
   做法：对 `pow`/乘法/一般非线性表达式，若上界用到 `n-1`，发出 loose 警告；或在 `check_draft` 增加硬门 `gs_ratio ≤ 5`（相对任务参考界），把 47.6× 的裸 `size(P)²` 退回。

4. **报告口径改为稳健统计**  
   主表报 median / P90 / catastrophic rate；均值只作附录；所有配对比较给按设计的 bootstrap CI。

### P1：提升设计器可用性与论文完整度

5. **预算拆分一致性门**：`split_match=False` 的接受程序（9 个 `N(self)`）说明模型在绕开 r1/r2/r3；把 `split_match` 从“质量指标”改为“接受必要条件”，或至少在评分中重罚。  
6. **设计评分/重排**：当前是二值接受/拒绝；建议对候选按“含噪模拟 RE → gs_ratio → exact”排序，优先选紧界且与 GT-DSL 一致的程序。  
7. **DSL 易用性**：28.6% 的 parse 失败是最大摩擦；允许 `x = f(x)` 形式的重新赋值（或自动 SSA 改名），并在反馈里给一个可复制的最小修复示例。  
8. **更多模型/图**：每任务 ≥30 设计；至少 CU、Do；模型加 hy3-ioa、GPT-4.1、DeepSeek-v3，回答“是方法问题还是 8B 能力问题”。  
9. **triangle 专项**：给一个 `P & N(v)` 的 worked example；统计“集合交任务”的 parse/语义失败率，作为 E6b 的任务难度分层。  
10. **thinking 消融**：固定 `T=0.6`，只切 `enable_thinking`，分别跑节点 probe 与 curator A3（各 3 任务 ×10）；这样能把“CoT 收益”与“采样温度收益”分开。当前 thinking 对照同时改了 T 与 max_tokens，不能作因果结论。

### P2：方法与写作

11. **A4 口径修正**：证伪器的私有集限制在 `dmax` 内，或参考 GS 用与私有集同界的 D；D<k 的格子单列，避免 `inf`。  
12. **thinking 的成本-收益**：报告 token/延迟；把 thinking 作为“强基线”而非“保证”；论文主张改为“保证与模型行为无关”，而不是“所有模型都会错”。补 thinking 的全量 screen（≥1k trials/bin），给出度数–错误率曲线，而不是只有 20 对确认。  
13. **规模**：PM 最大度 237 已经很难；补 n=10³–10⁵ 的合成图，验证 program 模式的常数成本与 RE。

---

## 9. 组会讲稿（10 分钟）

**第 1 分钟：问题。** PSC 的隐私证明隐含“节点算出的值 = 规则函数”。真实 LLM 节点会算错；错一个值，Lap(GS/ε₃) 的隐私损失就可能超过 ε₃。

**第 2–3 分钟：A1。** 一张“度数–错误率”曲线：8B 在 30 度以下 0–3%，60 度以上 99.9%；审计确认 ε_lb 最高 4.30（ε₃=2.0 的 2.15 倍）。翻到同一 20 对的 thinking 配对：15/20 → 0/20，ε_lb 4.30 → 1.37；但 >120 度仍有 10.8% 错误、最坏单点 Δ 1.02e8，0/20 是“未确认”不是保证，且成本更高——所以需要与模型无关的保证。

**第 4 分钟：A2。** program 模式 degree：RE=0.0030、exec_exact=1.0、节点调用 0、越界 0。证明“把计算挪回代码”这条路本身是通的。

**第 5–7 分钟：A3/A4。** 漏斗：119 份草稿 → 61 接受 → 49 可用、9 个 `N(self)` 灾难、3 个 moment2 松界。灾难全部是 `N(self)`：RR 在 ε₁=1 下给每个节点约 120 条假边，`comb`/交集把误差放大 30–100×。认证没有错（0 unsound）；错在 utility test 用真实邻表，看不到假边。注意：这些灾难是 **thinking curator** 写的，CoT 没有自动产生“含噪效用”的概念。  
一句话：**“认证保证了隐私，但没有保证统计有用；后者需要含噪效用门。”**

**第 8–9 分钟：改进。** P0 三件事：含噪效用门、禁用 `N(self)` 计数、产品 GS 松弛检查。预期灾难率 14.8% → 0；接受率可能下降，需重跑 A3 量化。

**第 10 分钟：下一步。** 重跑 A3（含噪门）、加 30 设计/任务、补 CU/Do、加 hy3/GPT 对照、修 A4 口径。

**可能的质疑与回答：**

- *“thinking 都 0/20 了，PSC 不就没问题了吗？”*  
  → 0/20 是 20 个选定的难对，不是保证；>120 度仍有 10.8% 错误、jitter=1.0，最坏单点 Δ 达 1.02e8；而且 thinking 的节点调用/token 成本远高于 program 模式。我们要的是“任何模型行为下都成立”，不是“换个好模型”。
- *“thinking curator 为什么还会写 `N(self)`？”*  
  → 因为 `N(self)` 的 GS=0，模型在 `<think>` 里把“灵敏度最小”当成目标，这是典型的 specification gaming；CoT 只让它更会推理这个错误目标，不会自动想到“输入是含噪发布行”。必须在检查器里加含噪效用门，而不是指望 prompt。
- *“9 个灾难程序只是 LLM 写错，和认证方法有什么关系？”*  
  → 它们通过了认证、语义测试、证伪器，被系统接受；这说明当前的“正确性门”不完整。认证只负责隐私，统计正确性需要另一个门。
- *“A4 的 3.33× 越界是真的吗？”*  
  → 是反事实下界：假设按参考 GS 加噪。认证后的程序用自己的 GS，0 unsound；3.33× 只说明“如果跳过认证会怎样”，不能写成观测到的泄露。
- *“为什么不直接让节点用 thinking？”*  
  → 可以，作为基线；但它不提供保证，成本高，且对库外任务仍需设计器写程序。thinking 节点在 >120 度仍有 10.8% 错误，说明它不是“正确答案生成器”。

---

## 10. 下一步实验（建议排期）

| 优先级 | 实验 | 目的 | 调用量 |
|---|---|---|---|
| P0 | A5：含噪效用门 + 禁用 `N(self)`，重跑 A3 七任务 ×10 | 验证灾难率 → 0，量化接受率下降 | ~120 次 |
| P0 | A6：`N(self)` prompt 版本 vs 门控版本（消融） | 区分“模型不知道”与“模型知道但走捷径” | ~120 次 |
| P0 | A7：Qwen 端到端 `program,gt-dsl,gt-psc` 跑 PM 2/3-star+triangle（用 A3 设计或 GT-DSL） | 补“Qwen 只在 degree 上跑过端到端”的缺口 | ~300 次运行，0 LLM |
| P1 | A3 扩到 30 设计/任务（PM） | 收窄接受率/灾难率 CI | ~360 次 |
| P1 | A3 在 CU、Do 各 10 设计 | 跨图外推 | ~240 次 |
| P1 | hy3-ioa / GPT-4.1 设计对照 | 区分能力与方法 | ~240 次 |
| P1 | thinking 消融：`T=0.6` 固定，节点/curator 各切 `enable_thinking` | 分离 CoT 与采样温度；量化 thinking 的设计收益 | ~200 次 |
| P2 | A4 口径修正后重算 | 去掉 inf、给出同界比较 | 0 |
| P2 | thinking 全量 screen（≥1k trials/bin） | 给 thinking 的度数–错误率曲线，而不只是 20 对 | ~1 万次 |
| P2 | 大图 program 模式（n=10³–10⁵） | C7 规模证据 | 0 |

---

## 附录 A：复现命令

```bash
cd /jizhicfs/leonlanli/work/PSC/certicount

# A3 库外三任务（本地 vLLM 8003，16k）
VLLM_CURATOR_BASE_URL=http://127.0.0.1:8003/v1 \
VLLM_NODE_BASE_URL=http://127.0.0.1:8003/v1 \
../.venv/bin/python scripts/run_dsl_design_eval.py \
  --datasets PM --tasks 4-star,5-star,degree-moment2 \
  --designs 10 --runs 10 --provider vllm \
  --config configs/vllm_psc_qwen3-8b_curator-think.toml \
  --curator-model Qwen3-8B --temperature 0.6 \
  --tag A3_pm_design_8bthink_d10_oob

# A4（库内 + 库外）
../.venv/bin/python scripts/analyze_design_certification.py \
  results/dsl_eval/A3_pm_design_8bthink_d10
../.venv/bin/python scripts/analyze_design_certification.py \
  results/dsl_eval/A3_pm_design_8bthink_d10_oob

# 离线回归
../.venv/bin/python -m pytest tests -q
```

## 附录 B：结果文件

- A1 联合报告：`results/audit/sensitivity/probe_pm_degree_report/report.md`
- A1 program 对照：`results/audit/sensitivity/probe_pm_degree_report_certicount/report.md`
- A1 8B-thinking：`results/audit/sensitivity/probe_pm_degree_qwen3-8b-think/confirm_nodes/table.md`
- A2：`results/execution/A2_pm_degree_program_8bthink_r100/table.md`
- A3 库内：`results/dsl_eval/A3_pm_design_8bthink_d10/designs.jsonl`（该轮被中途停止，无 `table.md`）
- A3 库外：`results/dsl_eval/A3_pm_design_8bthink_d10_oob/table.md`
- A4：`.../certification_ablation/table.md`
- 运行日志：`/jizhicfs/leonlanli/logs/run_a3_oob_20261110.log`

> 注：A4 脚本在 2026-11-10 修正了两个统计列：`certificate_unsound`（原先从未写入 row，恒为 0）与 `accepted_looser_than_reference`（原先读错字段，恒为 0）。本报告使用的是修正后的结果；库内表的 `accepted_looser_than_reference` 因此从 0 变为 3。
