# CS10 补充实验（CSCWD 论文）

三个补充实验全部跑完，工作目录 `certicount/`，模型 Qwen3-8B（vLLM，端口 8003，max_model_len 32768），
α = 5.0（`results/execution/cs0_alpha_selection.json`），ε = 2.0，seed 0，temperature 0.6，
`--prompt generic --own-row-check --tighten 1 --node-bounds --clip-alpha 5.0 --design-concurrency 8`。

* 服务：`scripts/run_cs9.sh serve`（tmux 会话 `certi`），17:32 就绪，全程未中断，**没有任何一次 `--resume` 或目录改名重跑**。
* 三个实验并行在 tmux 会话 `cs10` 的三个窗口（`e1` / `e3` / `e2gate`、`e2nogate`）里跑，共享同一张 H20。
* 每个结果目录跑完都执行了 `scripts/analyze_design_certification.py <dir>`；
  **所有目录所有任务的 `certificate_unsound` 都是 0**（见第 4 节）。
* 所有 `manifest.json` 的 `core_leaks` 和 `core_leaked_tasks` 都是 `[]`（实验 1、2、3 的 5 个新目录全部为空）。

| 实验 | 结果目录 | 设计数 | 墙钟 | 失败重跑 | `call_failed` | `api_error`（重试后成功） |
|---|---|---|---|---|---|---|
| 1 k-star zero-shot | `cs10_node_generic_sim_kstar` | 360 | 238 min | 0 | 0 | 22 |
| 2 gate | `cs10_node_generic_gate_tri` | 120 | 125 min | 0 | 0 | 1 |
| 2 no gate | `cs10_node_generic_nogate_tri` | 120 | 89 min | 0 | 0 | 5 |
| 3 binary / triangle | `fb_binary_triangle_ext` | 90 | 114 min | 0 | 0 | 16 |
| 3 binary / triangle-edge | `fb_binary_triangle_edge_ext` | 90 | 148 min | 0 | 0 | 0 |

三实验并行，总墙钟 18:04 → 22:02（238 min，约 4 h）；单跑一条命令的墙钟估计仍然是 5–10 h（实验 1）、3–4 h/组（实验 2 单组实际 1.5–2 h）、6–7 h（实验 3，实际 2.6 h，因为两个 stage 并行）。

---

## 1. 实验 1：Zero-Shot（generic）提示词重跑 degree / 2-star / 3-star

目录 `results/dsl_eval/cs10_node_generic_sim_kstar`（`--select simulated`，6 数据集 × 3 任务 × 20 设计 = 360 设计，
最多 2,880 次调用，实际 1,182 条草稿）。

**`manifest.json`：`core_leaks = []`，`core_leaked_tasks = []` → 没有提示词泄漏。**

RE 用论文定义 `|f̂ − f| / max(f, 0.001n)`，对被接受设计的全部 100 次运行取平均；列顺序与 Table I 一致。

### 1.1 接受率与平均 RE（generic，zero-shot）

| task | metric | CU | Do | ML | CS | EE | PM | Avg |
|---|---|---|---|---|---|---|---|---|
| degree | accept | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| degree | mean RE | 0.0217 | 0.0178 | 0.0126 | 0.0252 | 0.0086 | 0.0045 | 0.0151 |
| 2-star | accept | 1.0000 | 0.9500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9917 |
| 2-star | mean RE | 0.0985 | 0.0608 | 0.0388 | 0.1067 | 0.0250 | 0.0074 | 0.0562 |
| 3-star | accept | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9500 | 0.9917 |
| 3-star | mean RE | 0.4195 | 0.1783 | 0.0645 | 0.2984 | 0.0402 | 0.0087 | 0.1683 |

每设计平均调用次数：degree 3.14、2-star 3.29、3-star 3.42（上限 8 = 2 release × (3 稿 + 1 tighten)）。

### 1.2 与专家估计逐次完全相同（`identical_estimate`，配对的 GT-DSL-node）

`identical_estimate` = 与被配对的 GT-DSL-node 估计在**同一噪声实例上完全相等**的运行占比（排除两边都为 0 的运行，
`designs.jsonl` 的 `design_exact` 口径）。

| task | CU | Do | ML | CS | EE | PM | Avg |
|---|---|---|---|---|---|---|---|
| degree | 0.8000 | 0.6000 | 0.8500 | 0.7500 | 0.6000 | 0.7000 | 0.7167 |
| 2-star | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| 3-star | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

即：k-star（2-star、3-star）在 zero-shot 提示词下仍然是 **100% 逐次相同**，与旧 v1-alt 结果一致；
degree 是 60–85%（旧 v1-alt 是 47–79%），因为它允许 `size(P)` 与 `size(project(P, D))` 两种写法，估计并不总是相同。

### 1.3 被接受设计里的不同 AST 种数、是否等价于专家程序

`distinct_AST` = 对程序做 α-规范化（变量名替换为绑定序号）后的不同 AST 数；`same_as_reference` = 与参考程序
**结构完全相同**的占比（`Program.assigns/ret/aggregate` 逐项相等，变量名也算，`design_quality.same_as_reference`）。

| task | CU | Do | ML | CS | EE | PM | same_as_reference (Avg) |
|---|---|---|---|---|---|---|---|
| degree | 3 | 4 | 3 | 5 | 4 | 4 | 0.6083 |
| 2-star | 7 | 7 | 5 | 6 | 7 | 6 | 0.1009 |
| 3-star | 8 | 7 | 5 | 8 | 8 | 6 | 0.0842 |

规范化后**全部与专家程序等价**（差别只是变量别名/中间赋值，估计逐次相同，见 1.2）；
但严格"结构完全相同"的比例很低（2-star 0.10、3-star 0.08），因为模型习惯先写一个别名赋值。
按纯文本去重会把这类别名变体当成不同程序（2-star 13–20 种、3-star 12–18 种），上表是去掉变量名后的真实 AST 数。

代表性程序（每个任务 2–3 条，均为被接受设计）：

* degree
  * `return size(P) ; aggregate: total / n`
  * `return size(project(P, D)) ; aggregate: total / n`
  * `size_P = size(P) ; return size_P ; aggregate: total / n`
* 2-star
  * `size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total`
  * `projected_P = project(P, D) ; degree = size(projected_P) ; count = comb(degree, 2) ; return count ; aggregate: total`
* 3-star
  * `return comb(size(project(P, D)), 3) ; aggregate: total`
  * `d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total`
  * `projected = project(P, D) ; degree = size(projected) ; stars = comb(degree, 3) ; return stars ; aggregate: total`

### 1.4 与旧 v1-alt 结果逐格对比

旧结果来源：`cs8_node_v1alt_sim_pm_deg2star`（PM degree、2-star）、`cs8_node_v1alt_sim_cudo_3tasks`（CU/Do）、
`cs8_node_v1alt_sim_mlcsee`（ML/CS/EE）、`cs7_node_v1alt_sim`（PM 3-star）。

| task | dataset | v1-alt accept | generic accept | v1-alt RE | generic RE | v1-alt identical | generic identical |
|---|---|---|---|---|---|---|---|
| degree | CU | 1.0000 | 1.0000 | 0.0219 | 0.0217 | 0.6000 | 0.8000 |
| degree | Do | 0.9500 | 1.0000 | 0.0181 | 0.0178 | 0.4737 | 0.6000 |
| degree | ML | 0.9500 | 1.0000 | 0.0130 | 0.0126 | 0.7895 | 0.8500 |
| degree | CS | 0.9500 | 1.0000 | 0.0253 | 0.0252 | 0.6842 | 0.7500 |
| degree | EE | 0.9500 | 1.0000 | 0.0084 | 0.0086 | 0.6316 | 0.6000 |
| degree | PM | 1.0000 | 1.0000 | 0.0055 | 0.0045 | 0.5000 | 0.7000 |
| degree | Avg | 0.9667 | 1.0000 | 0.0154 | 0.0151 | 0.6132 | 0.7167 |
| 2-star | CU | 1.0000 | 1.0000 | 0.0985 | 0.0985 | 1.0000 | 1.0000 |
| 2-star | Do | 1.0000 | 0.9500 | 0.0608 | 0.0608 | 1.0000 | 1.0000 |
| 2-star | ML | 0.9500 | 1.0000 | 0.0388 | 0.0388 | 1.0000 | 1.0000 |
| 2-star | CS | 0.9500 | 1.0000 | 0.1067 | 0.1067 | 1.0000 | 1.0000 |
| 2-star | EE | 0.9500 | 1.0000 | 0.0250 | 0.0250 | 1.0000 | 1.0000 |
| 2-star | PM | 0.9500 | 1.0000 | 0.0074 | 0.0074 | 1.0000 | 1.0000 |
| 2-star | Avg | 0.9667 | 0.9917 | 0.0562 | 0.0562 | 1.0000 | 1.0000 |
| 3-star | CU | 1.0000 | 1.0000 | 0.4195 | 0.4195 | 1.0000 | 1.0000 |
| 3-star | Do | 1.0000 | 1.0000 | 0.1783 | 0.1783 | 1.0000 | 1.0000 |
| 3-star | ML | 0.9500 | 1.0000 | 0.0645 | 0.0645 | 1.0000 | 1.0000 |
| 3-star | CS | 1.0000 | 1.0000 | 0.2984 | 0.2984 | 1.0000 | 1.0000 |
| 3-star | EE | 1.0000 | 1.0000 | 0.0402 | 0.0402 | 1.0000 | 1.0000 |
| 3-star | PM | 1.0000 | 0.9500 | 0.0087 | 0.0087 | 1.0000 | 1.0000 |
| 3-star | Avg | 0.9917 | 0.9917 | 0.1683 | 0.1683 | 1.0000 | 1.0000 |

**结论：k-star 上与 GT-DSL 持平不是 v1-alt 提示词带出来的。** 换成 zero-shot generic 后，2-star / 3-star
的 18 个格子的 RE 与 v1-alt **四位小数完全相同**、`identical_estimate` 仍是 100%；degree 甚至略好
（RE 0.0151 vs 0.0154，identical 0.717 vs 0.613，接受率 1.000 vs 0.967）。新增接受率差异只是抽样波动。

---

## 2. 实验 2：Zero-Shot 下干净的模拟门控消融（Triangle）

三组：`simulated` 复用 `cs9_node_generic_sim_tri_ow` 的 triangle 部分；`gate` = `cs10_node_generic_gate_tri`；
`nogate` = `cs10_node_generic_nogate_tri`。后两组参数完全相同（`--select first`，3 稿 + tighten 1，
own-row-check 开），只差 `--noisy-gate`。`--select first` 与 `--own-row-check`、`--tighten 1` 没有冲突
（先用 `--dry-run` 确认，再用 mock 设计师离线跑通一遍）。

注意三组的差别不只是门控：sim 组是 `--select simulated`（rows / matrix 两个 release + 运行时选择，
每设计最多 6 次调用），gate / nogate 是 `--select first`（单 release、3 稿，每设计最多 4 次调用）。

| group | metric | CU | Do | ML | CS | EE | PM | Avg |
|---|---|---|---|---|---|---|---|---|
| simulated (reuse) | accept | 0.9500 | 0.8000 | 0.9000 | 0.9500 | 0.9500 | 0.9500 | 0.9167 |
| simulated (reuse) | mean RE | 0.8537 | 0.6119 | 0.2296 | 1.3722 | 0.2666 | 0.2744 | 0.6014 |
| simulated (reuse) | RR-bias share | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| simulated (reuse) | calls / design | 4.45 | 4.90 | 4.40 | 4.75 | 4.25 | 4.20 | 4.49 |
| noise-free gate | accept | 0.4500 | 0.5000 | 0.4500 | 0.5000 | 0.6000 | 0.6500 | 0.5250 |
| noise-free gate | mean RE | 1.0465 | 0.7280 | 0.2328 | 1.4199 | 0.2326 | 0.1263 | 0.6310 |
| noise-free gate | RR-bias share | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| noise-free gate | calls / design | 2.55 | 2.45 | 2.50 | 2.35 | 2.35 | 2.10 | 2.38 |
| no gate | accept | 0.4500 | 0.6500 | 0.5000 | 0.4500 | 0.6500 | 0.5000 | 0.5333 |
| no gate | mean RE | 0.9909 | 0.7079 | 0.2353 | 1.3517 | 0.3796 | 0.2670 | 0.6554 |
| no gate | RR-bias share | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0769 | 0.0000 | 0.0128 |
| no gate | calls / design | 2.45 | 2.15 | 2.55 | 2.35 | 2.25 | 2.40 | 2.36 |

被接受设计数（每格 20 个设计）：sim 19/16/18/19/19/19；gate 9/10/9/10/12/13；nogate 9/13/10/9/13/10。
RR-bias 判定：被接受设计里公共图上无噪声估计的**中位** RE ≥ τ = 2 的比例（`noise_free_pass` 为 False；
它同时是 `noise_free_bias` = 两张公共 Holme–Kim 图上该中位 RE 的最大值）。按六网络合并计，三组分别
**0/110、0/63、1/64** 个被接受设计（表里 Avg 列是六个数据集份额的等权平均，所以 no gate 是 0.0128 而不是 1/64 = 0.0156）。

**一句话结论**：模拟门控组在接受率（0.9167 vs 0.5250 / 0.5333）和平均 RE（0.6014 vs 0.6310 / 0.6554）上**都更好**，
但收益基本来自"两个 release + 运行时选择"（调用次数也多约 1.9×）；**noise-free 门控本身相对无门控几乎没有差别**
（接受率 0.5250 vs 0.5333，RE 0.6310 vs 0.6554，RR 偏置设计 0 vs 1/78），在这个 zero-shot 提示词与 own-row-check 下
门控是"几乎免费的安全网"而不是收益来源。

---

## 3. 实验 3：RQ3 Binary Rejection 组补齐 PM / Do / CS

`ARMS=binary DATASETS=PM,Do,CS SUFFIX=_ext scripts/run_cscwd_fb.sh all` 生成
`fb_binary_triangle_ext`、`fb_binary_triangle_edge_ext`（各 90 设计，共 180 设计、946 草稿）；
check（68 tests）→ dry（每 stage 最多 540 调用）→ 两个 stage 并行 → 每目录 `analyze_design_certification.py` → privacy guard（0 problem）
→ `summarize_fb_ablation.py`。`--suffixes ",_ext"` 默认就同时汇总 `_ext`，所以
`results/reports/fb_ablation.md/json` 里 full / binary / none 三组都已是六个网络（每任务每臂 180 设计，两任务合计 360）。

### 3.1 三组在 Triangle / Triangle-Edge 上的累计认证率（六网络汇总，Fig. 3 用）

按设计循环（每个 design 有 rows / matrix 两个 loop）计：

| task | arm | designs | released | k=1 | k=2 | k=3 |
|---|---|---|---|---|---|---|
| triangle | full | 180 | 164 (0.9111) | 0.2611 | 0.4194 | 0.5500 |
| triangle | binary | 180 | 134 (0.7444) | 0.2250 | 0.3389 | 0.3972 |
| triangle | none | 180 | 153 (0.8500) | 0.2389 | 0.4083 | 0.4861 |
| triangle-edge | full | 180 | 79 (0.4389) | 0.0500 | 0.1528 | 0.2528 |
| triangle-edge | binary | 180 | 50 (0.2778) | 0.0556 | 0.1083 | 0.1472 |
| triangle-edge | none | 180 | 57 (0.3167) | 0.0583 | 0.1194 | 0.1694 |

按设计（一个设计只要任一 loop 在 k 稿内被接受就算认证，180 设计/格）：

| task | arm | k=1 | k=2 | k=3 |
|---|---|---|---|---|
| triangle | full | 0.5000 | 0.7444 | 0.9111 |
| triangle | binary | 0.4278 | 0.6389 | 0.7444 |
| triangle | none | 0.4556 | 0.7500 | 0.8500 |
| triangle-edge | full | 0.0944 | 0.2833 | 0.4444 |
| triangle-edge | binary | 0.1056 | 0.2111 | 0.2778 |
| triangle-edge | none | 0.1167 | 0.2278 | 0.3167 |

（两表都保留 4 位小数；重画 Fig. 3 时建议用第二张"按设计"的口径，第一张是 loop 口径，两者形状一致。）

### 3.2 Binary 对 Diagnostic Repair / Binary 对 Independent Resampling

Mantel–Haenszel 风险差（按 (task, dataset) 分层）与连续性校正 CMH 检验，六个网络：
`full` = 诊断反馈（Diagnostic Repair），`none` = 独立重采样（Independent Resampling）。

| 对比 | 范围 | 认证数 (a vs b) | 差值 (百分点) | 95% CI | CMH p |
|---|---|---|---|---|---|
| binary − full | 合计 | 184/360 vs 243/360 | −16.4 | [−22.5, −10.3] | 6.2e−07 |
| binary − full | 仅 Triangle | 134/180 vs 164/180 | −16.7 | [−24.0, −9.3] | 5.3e−05 |
| binary − full | 仅 Triangle-Edge | 50/180 vs 79/180 | −16.1 | [−25.8, −6.4] | 2.2e−03 |
| binary − none | 合计 | 184/360 vs 210/360 | −7.2 | [−13.4, −1.1] | 0.031 |
| binary − none | 仅 Triangle | 134/180 vs 153/180 | −10.6 | [−18.6, −2.5] | 0.019 |
| binary − none | 仅 Triangle-Edge | 50/180 vs 57/180 | −3.9 | [−13.2, +5.4] | 0.489 |

（`fb_ablation.json` 里给出的是 `full − binary` 与 `binary − none`，本表把第一条取了相反数（CI 上下限同时取反）；
差值与 p 直接取自 `released_diff_MH` / `p_CMH`。）

### 3.3 Self-Row / Sensitivity Tightness 被拒之后，下一稿通过该阶段的比例（binary 组）

| task | 被拒阶段 | 下一稿数 | 下一稿走到更后阶段或接受 | 下一稿直接接受 | 下一稿同一阶段再被拒 |
|---|---|---|---|---|---|
| triangle | self-row (`own_row`) | 89 | 0.1461 | 0.0337 | 0.5618 |
| triangle | sensitivity tightness (`gs_loose`) | 140 | 0.2857 | 0.1929 | 0.6071 |
| triangle-edge | self-row (`own_row`) | 110 | 0.2000 | 0.0545 | 0.4545 |
| triangle-edge | sensitivity tightness (`gs_loose`) | 111 | 0.0901 | 0.0450 | 0.5045 |

对照（同表其它两臂）：full 组 own_row→0.7286 / 0.8095、gs_loose→0.8608 / 0.7500；none 组 own_row→0.2772 / 0.2308、
gs_loose→0.4435 / 0.2288。binary 组在 self-row 与 tightness 两类可修复拒绝上都是三组里最差的，
说明"只说 rejected"时模型既不知道该改哪一处，也倾向于原样重交（同阶段再被拒 45–61%）。
首次即接受率（randomisation check）：full 0.2611/0.0500、binary 0.2250/0.0556、none 0.2389/0.0583——三组相当。

### 3.4 与旧结论（只有 CU/EE/ML）对比

| 指标 | 旧（CU/EE/ML，180 设计/组） | 新（六网络，360 设计/组） |
|---|---|---|
| binary − full（合计） | −18.3 点，p = 1.5e−04 | −16.4 点，p = 6.2e−07 |
| binary − none（合计） | −8.3 点，p = 0.094（不显著） | −7.2 点，p = 0.031（显著） |

**结论没有变化，而且更强**：binary 明显落后诊断反馈（差距从 18.3 点收到 16.4 点，但因为样本翻倍，
p 从 10⁻⁴ 量级降到 10⁻⁷）；binary 也落后独立重采样，旧结果只是趋势（p = 0.094），六网络下变成显著（−7.2 点，p = 0.031）。
即"只给驳回判决"既不如诊断修复，也不如等预算的独立重采样——检查器本身不产生价值，反馈的**内容**才产生价值。

---

## 4. Table II 用：草稿总数、证伪器、反事实回放

### 4.1 新增草稿与总数

口径（可复现）：**一条草稿 = 策展模型的一条回复**，即 `designs.jsonl` 每行 `stages` 的长度之和，等于该行的
`llm_calls`，也等于 `analyze_design_certification.py` 的 `drafts`（每个目录两种算法完全相等）。

| 实验 | 目录 | 设计 | 草稿（全部） | runnable 草稿 | 证伪器推翻 DeriveGS 界 | 反事实 > 参考 GS |
|---|---|---|---|---|---|---|
| 1 | `cs10_node_generic_sim_kstar` | 360 | 1182 | 929 | 0 | 156 (0.1679) |
| 2 | `cs10_node_generic_gate_tri` | 120 | 286 | 164 | 0 | 27 (0.1646) |
| 2 | `cs10_node_generic_nogate_tri` | 120 | 283 | 168 | 0 | 32 (0.1905) |
| 3 | `fb_binary_triangle_ext` | 90 | 431 | 258 | 0 | 79 (0.3062) |
| 3 | `fb_binary_triangle_edge_ext` | 90 | 515 | 236 | 0 | 162 (0.6864) |
| **合计** | | **780** | **2697** | **1755** | **0** | **456 (0.2598)** |

* 三个新实验共新增 **2,697 条草稿**（其中 **1,755 条 runnable**；runnable = 能解析并执行的反事实回放草稿）。
* 证伪器推翻 DeriveGS 界的草稿 **0 条**（应然值），即推导器在所有新草稿上都没有给出不成立的上界——
  五个目录、所有任务的 `certificate_unsound` 都是 0。
* 若不做认证、按 PSC 方式用参考 GS 校准噪声，会有 **456 / 1,755 = 26.0%** 的 runnable 草稿超过参考 GS
  （triangle-edge 的 binary 组最高，68.6%），这是"必须认证"的直接证据。

**关于原来的 2,471**：仓库里没有任何文件记录这个数字（`docs/`、`results/reports/`、git 历史均无），
按上面的口径把所有论文用到的 `dsl_eval` 设计目录（CS7 四臂 + CS8 + CS9 四项 + FB 十二项，共 21 个目录）相加是
**10,601 条草稿 / 2,330 设计**，远大于 2,471；与 2,471 最接近的自然子集是 **CS7 + CS8（per-node，v1-alt，7 个目录）= 2,407 条 / 680 设计**
（差 64 条，2.6%），再加早期 PM 探针（`cs2` 63 条 / `cs3` 68 条，旧格式无 `stages` 字段，按 transcripts 计）得到 2,470 / 2,475，
即 2,471 落在"CS7+CS8+早期 PM 探针"的 ±4 条范围内，推断历史目录被后来的 `--resume`/重跑覆盖过，无法精确复现。给出三种总数：

| 口径 | 旧 | 新增 | 新总数 |
|---|---|---|---|
| A：全部论文 `dsl_eval` 设计目录（CS7+CS8+CS9+FB） | 10,601 | 2,697 | **13,298** |
| B：CS7+CS8 per-node 主实验（最接近 2,471） | 2,407 | 2,697 | **5,104** |
| C：论文数字直接相加（假定范围与新增不重叠） | 2,471 | 2,697 | **5,168** |

建议 Table II 采用口径 A 并在脚注写明"draft = 一条策展回复，含被拒稿"，这样新总数 13,298（其中 runnable 未统计旧目录，旧目录按同一脚本可复算）。

---

## 5. 运行记录（可复现）

```bash
export VLLM_CURATOR_BASE_URL=http://127.0.0.1:8003/v1 VLLM_NODE_BASE_URL=http://127.0.0.1:8003/v1
COMMON="--runs 100 --eps 2.0 --seed 0 --design-concurrency 8 --provider vllm \
  --config configs/vllm_qwen3-8b-think_design.toml --curator-model Qwen3-8B --temperature 0.6 \
  --node-bounds --clip-alpha 5.0 --prompt generic --own-row-check --tighten 1"

# 实验 1
../.venv/bin/python scripts/run_dsl_design_eval.py $COMMON --noisy-gate --select simulated \
  --datasets PM,CU,Do,ML,CS,EE --tasks degree,2-star,3-star --designs 20 --tag cs10_node_generic_sim_kstar
# 实验 2（gate / no gate）
../.venv/bin/python scripts/run_dsl_design_eval.py $COMMON --noisy-gate --select first \
  --datasets PM,CU,Do,ML,CS,EE --tasks triangle --designs 20 --tag cs10_node_generic_gate_tri
../.venv/bin/python scripts/run_dsl_design_eval.py $COMMON --select first \
  --datasets PM,CU,Do,ML,CS,EE --tasks triangle --designs 20 --tag cs10_node_generic_nogate_tri
# 实验 3
ARMS=binary DATASETS=PM,Do,CS SUFFIX=_ext scripts/run_cscwd_fb.sh all
# 校验（每个目录）
../.venv/bin/python scripts/analyze_design_certification.py results/dsl_eval/<tag>
../.venv/bin/python scripts/summarize_fb_ablation.py --suffixes ",_ext" --out results/reports/fb_ablation.md
```

* dry-run 计划调用数：实验 1 2,880、实验 2 每组 480、实验 3 每 stage 540（均在跑前确认）。
* 日志：`results/logs/cs10_exp1.log`、`cs10_exp2_gate.log`、`cs10_exp2_nogate.log`、`cs10_exp3.log`、
  `fb_binary_triangle_ext.log`、`fb_binary_triangle_edge_ext.log`；服务日志 `results/logs/cs9_serve_8b.log`。
* 没有删除或覆盖任何已有 `results/` 目录；新目录只有上述 5 个（`cs10_*`、`fb_binary_*_ext`）与
  `results/reports/cs10_supplement.md`。
