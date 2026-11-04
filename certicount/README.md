# CertiCount — LLM 设计、系统认证、节点执行的边 LDP 子结构计数

**CertiCount**（Certified Counting）是开题课题《LLM 多智能体边本地差分隐私子结构计数的执行可信性：灵敏度审计与可验证执行》
的研究代码。核心方法是"**LLM 只写程序，隐私与计数都由代码保证**"：

1. curator LLM 只看公开信息（任务描述、节点数 n），把计数任务写成一段受限 DSL 程序；
2. 系统解析并类型检查程序，**静态推导其全局敏感度 GS**，生成证书；每个节点用公开参数**自己重新推导 GS** 核验证书；
3. 每个节点用确定性解释器在自己的真实邻居上执行程序，加 `Lap(GS/ε3)` 后上报，汇总端按程序的聚合表达式得到结果。

节点不调用 LLM，被加噪的值始终是程序的精确输出，所以 DP 保证不依赖 LLM 是否算对；库外任务（4-star、5-star、
度二阶矩等）只要能用 DSL 写出，就能自动得到可验证的 GS。

> 原目录名 `psc-trust/`、原包名 `psctrust`，2026-10-31 统一更名为 `certicount`。`results/*/manifest.json` 中记录的是运行当时的旧路径。

## 与复现项目的关系

同级目录 [`../psc`](../psc/README.md)（PSC 论文复现，原名 `psc-reproduction`）是**冻结的基线依赖**：DP 原语（RR、带噪最大度、
图投影、Laplace、预算拆分）、三类智能体、数据集、模型配置（`config.toml` / `.env`）与历史运行结果都来自那里的 `psc` 包，
本项目不修改它。`import certicount` 时若 `psc` 未安装，会依次在 `$PSC_REPRO_ROOT`、`../psc`、`../psc-reproduction`
中查找并加入 `sys.path`。

## 环境与模型配置

```bash
cd /data/workspace/PSC/certicount
source ../.venv/bin/activate      # 与复现项目共用仓库根目录的虚拟环境；依赖见 requirements.txt（-r ../psc/requirements.txt）
python -m pytest tests -q          # 195 个测试通过（1 个跳过），全部离线
```

模型设置沿用复现项目的 `../psc/config.toml` 与 `../psc/.env`（密钥与网关地址只放在 `.env*` 中）：

| 用法 | 参数 | 网关 / 文件 | 可用模型（示例） |
|---|---|---|---|
| 离线（默认） | `--provider mock` | 无 | 规则模型，不花钱 |
| 默认网关 | `--provider openai` | `.env`：`OPENAI_BASE_URL=https://copilot.tencent.com/v2/`，`stream = true` | `hy3-ioa`（默认）、`hy4-preview-ioa`、`deepseek-v3`、`deepseek-v3-0324`、`glm-5.2` |
| GLM（关闭思考） | `--provider openai --profile glm` | 同上 | `glm-5.2` |
| 其他网关 | `--provider openai --profile gpt41 / openrouter / oaifree / oaifree2` | `.env.gpt41`、`.env.gpt`、`.env.oaifree*` | `gpt-4.1`、`gpt-4.1-mini`、`gpt-4o` 等 |
| 自建 / 其他 | `--provider vllm / dashscope / ollama` | `config.vllm*.toml`、`.env` | 见复现项目 README |

模型用 `--node-model`（节点）与 `--curator-model`（curator、隐私控制器、DSL 设计器）指定；`--config` 可换配置文件。
**任何真实模型运行前先加 `--dry-run` 查看计划调用量，确认预算后再去掉。**

## DSL 方法（`certicount/dsl/`）

```
分析者 prompt ─► designer：LLM 写 DSL ─► lang.parse_program：解析 + 类型检查 ─► Program(AST)
                    ▲                          │
                    └── 反馈重写（≤3 轮）◄── check_draft：sensitivity.derive 推 GS / utility_test 查语义 / 证伪器复核 GS
                                               │ 通过
预算拆分（由程序决定）─► 带噪图 G′（ε1，程序读 N(·) 时）─► 带噪最大度 d̂max（ε2）─► PublicParams(n, D, dmax)
   ─► certify 出证书 ─► 节点 verify_certificate 自行重推 GS ─► Interpreter.local（节点本地）+ Lap(GS/ε3)
   ─► Interpreter.aggregate（汇总端）
```

语言是 Python 的受限子集，只用 `ast` 解析、从不交给 Python 执行。例如：

```python
# 3-star                                # triangle
return comb(size(project(P, D)), 3)     S = P & N(self)
aggregate: total                        return 0.5 * sum(size(P & N(j)) for j in S)
                                        aggregate: total / 3
```

| 文件 | 作用 |
|---|---|
| `lang.py` | 语法、类型检查、`Program`（AST）、闭包编译的解释器 `Interpreter` |
| `sensitivity.py` | 抽象解释推导 GS（集合：最大规模 / 对称差 / 规模变化；数值：变化量 / 取值范围），证书 `certify` / `verify_certificate` |
| `designer.py` | 设计循环：提示词、回复解析、`check_draft`、离线 `MockDesignerModel` |
| `utility.py` | 效用测试：无噪声、无截断下与暴力计数比对 |
| `falsifier.py` | 证伪器：小图上穷举 / 采样 (G′, P, 翻转) 寻找超过 GS 的反例；`check_derivation` 在同一组小参数下推导 GS 并证伪（设计循环与对拍共用） |
| `fuzz.py` | 推导器对拍：随机生成合法程序（偏向 `P & N(self)` 上的求和与循环变量的行），推导 GS 与证伪器的最大变化比对 |
| `adaptive.py` | 先发度数的自适应选择：共同随机数执行器、NPMLE 度后验、按公开量模拟打分的选择器、候选空间（见下节） |
| `library.py` | 参考程序 `PROGRAMS`、手工 GS `HAND_GS`、库外任务的分析者 prompt |
| `ground_truth.py` | `dp_execute`：纯代码执行任意程序（与 program 模式同 DP 步骤、同随机数顺序）；`gt_dsl`：参考程序的执行，即 GT-DSL |
| `quality.py` | `design_quality`：设计质量打分（结构、预算拆分、GS 比、独立语义测试、证伪） |

验收结果（`results/dsl/dsl_check_20261024/`）：推导 GS 与手工值完全一致（degree 1、k-star C(D−1, k−1)、triangle d̂max−1、
4-star C(D−1,3)、5-star C(D−1,4)、度二阶矩 2D−1）；证伪器在 n = 5 的全部对称图上找到的最大变化恰好等于推导 GS（推导是紧的）；
去掉"G′ 对称"或"self ∉ P"任一事实，三角形只能得到 d̂max；未投影的 k-star 被判"上界过松"退回改写，除以私有量被拒绝，
漏掉 0.5 的三角形被效用测试拒绝；不做 GS 优化时三角形推导为 n−2，与论文一致。

设计循环在接受程序前还用证伪器复核推导（`designer.FALSIFIER_CHECKS`：n = 5、dmax = 3 的全部对称图，n = 7、dmax = 4 的
500 张随机对称图），GS 被反例推翻、或在测试图上运行出错的程序一律退回。推导器本身用随机程序对拍检验（`tests/test_fuzz.py`
120 个，`scripts/run_dsl_fuzz.py` 大规模）：`results/dsl/dsl_fuzz_20261103/` 中 1 万个随机程序 0 个反例。2026-11-03 之前，
`P & N(self)` 上求和的新增项 j = v 的所有 N(v) 都按 dmax − 1 计，漏了 self ∈ N(v)，`sum(size(P & N(j)) + size(N(j)) for j in S)`
一类程序的 GS 被低估（同一批 1 万个程序中 328 个被推翻）；现在只对不含 self 的集合与 N(v) 的交集减 1。库内程序与已有结果
（`results/execution/` 中的全部 DSL 运行）的 GS 不变。

## DSL 评估

两个目标：

| 目标 | 问题 | 参照 | 脚本 | 结果目录 |
|---|---|---|---|---|
| 一 | DSL 相比 Naive、PSC 提升多少 | GT-Naive、GT-PSC、GT-DSL | `scripts/run_execution_compare.py` | `results/execution/<tag>/` |
| 二 | DSL 中 LLM（设计器）带来多少误差 | GT-DSL，同一份噪声逐次配对 | `scripts/run_dsl_design_eval.py` | `results/dsl_eval/<tag>/` |

**GT-DSL** 是"完美设计器"：用任务的参考程序跑与 DSL 完全相同的 DP 流程（同 `[seed, i]` 噪声、同随机数顺序）。节点执行程序本身无误差，
因此每次运行的 `design_error = RE(LLM 设计的程序) − RE(GT-DSL)` 全部来自 LLM 设计（本地函数、GS、预算拆分）。

### 目标一：与 Naive / PSC 对比

```bash
# 离线（mock）
python scripts/run_execution_compare.py --datasets CU --tasks degree,3-star,triangle,4-star \
    --modes gt-naive,naive,gt-psc,baseline,gt-dsl,program --runs 10 --gt-runs 1000 --tag dsl_vs_baselines_mock

# 真实模型（默认网关 hy3-ioa）：先 --dry-run，确认后去掉并换 tag
python scripts/run_execution_compare.py --datasets CU --tasks degree,3-star,triangle,4-star \
    --modes gt-naive,naive,gt-psc,baseline,gt-dsl,program --runs 10 --gt-runs 1000 \
    --provider openai --node-model hy3-ioa --curator-model hy3-ioa --tag dsl_vs_baselines_hy3 --dry-run
```

| 模式 | 方法 | 说明 |
|---|---|---|
| `gt-naive` / `gt-psc` / `gt-dsl` | GT-Naive / GT-PSC / GT-DSL | 纯代码参照，不调模型；次数由 `--gt-runs` 决定 |
| `naive` | Naive | 全部预算给 RR，curator LLM 在带噪图上作答 |
| `baseline` | PSC | 论文原方法：curator 规则 + 节点 LLM |
| `bind` / `guard` / `codecost` | PSC + 防护 | 三元绑定与消息校验 / 改进一（代码守卫）/ 代码发送与聚合 |
| `program` | **DSL** | curator LLM 设计程序，节点解释执行（节点 LLM 调用为 0，设计结果跨运行缓存） |

库外任务只运行 `program` 与 `gt-dsl`（其余模式自动跳过）。`table.md` 有三张表：

- **Goal 1**：`relative_error`；`rule_relative_error` 为同一份噪声下的纯代码值（Naive→GT-Naive、PSC→GT-PSC、DSL→程序自身）；
  `llm_error` = 二者之差，即 LLM 在执行环节带来的误差；`llm_calls` / `node_llm_calls`。
- **Goal 2**：DSL 行与 GT-DSL 逐次配对的 `design_error`、`design_exact`、`gs_ratio`、`split_match` 与实际使用的程序。
- **Details**：节点正确率、守卫回退、被拒消息、违规次数、置信区间覆盖率等。

GT-Naive / GT-PSC 是复现包的实现，RR 抽噪声的顺序与智能体不同，只能**按分布**比较；逐次配对看 `rule_relative_error`。

### 目标二：LLM 设计器误差

```bash
# 离线（mock 设计器写参考程序；--flawed-first 让 k-star 首稿漏掉投影，检验"拒绝—重写"）
python scripts/run_dsl_design_eval.py --datasets CU --designs 5 --runs 10 --flawed-first --tag dsl_eval_mock

# 真实模型：--temperature > 0 才能采样到不同设计；先 --dry-run
python scripts/run_dsl_design_eval.py --datasets CU --designs 10 --runs 10 \
    --provider openai --curator-model hy3-ioa --temperature 0.7 --tag dsl_eval_hy3 --dry-run
```

默认任务为 degree、3-star、triangle、4-star、5-star、degree-moment2；每个任务独立设计 `--designs` 次（不缓存），
每个被接受的设计跑 `--runs` 次并与 GT-DSL 配对。最多调用 `数据集 × 任务 × designs × max-iterations` 次模型。

| 指标 | 含义 |
|---|---|
| `accept_rate` / `first_try_rate` / `mean_iterations` / `mean_llm_calls` | 设计循环能否收敛、要几轮 |
| `distinct_programs` / `same_as_reference` | 写出几种程序、是否与参考程序结构相同 |
| `split_match` | 预算拆分（是否读 N(·)、是否需要度数上界）与参考一致 |
| `gs_ratio` / `gs_ratio_max` | 推导 GS ÷ 参考 GS（设计期参考界 D = min(n−1, 10)），1 为最优；`gs_ratios` 另给 `--bounds` 下的值 |
| `semantic_pass` | 独立语义测试：`--utility-graphs` 张最多 `--utility-max-n` 个节点的随机图，种子与设计循环不同 |
| `sound` | 证伪器未找到超过 GS 的反例（`--no-falsify` 关闭） |
| `relative_error` / `gt_dsl_relative_error` | 设计程序与 GT-DSL 的平均相对误差 |
| `design_error` / `design_error_max` / `design_exact` | 设计带来的误差（平均、最差设计）、估计值与 GT-DSL 完全相同的运行占比 |

输出：`table.md`、`summary.json`、`designs.jsonl`（每个设计：程序、反馈历史、质量）、`runs.jsonl`（每次运行的配对值、GS、d̂max、预算拆分）。

一个设计循环拦不住、但这里能发现的例子：`return comb(size(project(P, 2 * D)), 3)` 能通过语法、"上界过松"和效用测试，
但 `gs_ratio = C(19,2)/C(9,2) ≈ 4.75`，配对误差随之变大（`tests/test_dsl_eval.py`）。

## 先发度数的自适应选择（`dsl/adaptive.py`）

PSC 预先固定 (ε1, ε2, ε3)，并投影到带噪最大度 D。这里先用 ε2 发布带噪度数 y（Alg. 2 第 1–3 行），再由只看公开量
（n、ε、ε2、y、D）的选择器选一个候选：DSL 程序、代替 D 的界 B（投影与 GS 都用 B）、RR 预算 ε1；其余步骤用 ε3 = ε − ε2 − ε1。

- **隐私**：选择是 y 的后处理，每个候选在剩余步骤上恰好花 ε − ε2，由纯 DP 的自适应顺序组合，总预算仍为 ε；GS 仍由推导器在 B 处推出。
- **选择**：NPMLE 对 y 去卷积，得到度分布与各节点的经验贝叶斯后验。不读 N(·) 的程序只依赖 |P|，用解释器算出计数表 f(d)，
  在后验度序列上做蒙特卡洛；读 N(·) 的程序还依赖结构，在三类合成图（Chung–Lu、一维几何 α = 2、一维阈值几何，聚集由低到高）上
  以已发布的 D 为条件模拟，三类得分取几何平均（结构先验）。`margin`：最优候选的预测得分须比默认低这个比例才切换。
- **候选**：k-star 为 B ∈ {1, …, D}；三角形为 B = round(f·D)（f ∈ {1, 0.75, 0.5, 0.35}）× ε1 ∈ {0.4, 0.6, …, 1.4}。
- **共同随机数**：每次运行的度噪声、RR 均匀数、投影种子、Laplace 噪声各一条流（`run_streams`），默认设置、选择结果与全部候选在同一份噪声上配对。

```bash
python scripts/run_adaptive.py --runs 1000 --workers 8 --tag adaptive_r1000   # 6 图 × {2-star, 3-star, triangle}，8 进程约 47 分钟
```

结果（`results/adaptive/adaptive_r1000_20261104/`，ε = 2，每格 1000 次，6 图平均相对误差；括号内为相对默认的变化，以及配对差异显著
（|z| > 1.96）变好 / 变差的数据集个数）：

| 任务 | GT-PSC | 默认（配对） | 自适应（margin 0.1） | 自适应（无 margin） | GT-Tuned（只用 n 调参） | 静态最优（真实图上选，仅参照） | GT-TriTR |
|---|---|---|---|---|---|---|---|
| 2-star | 0.1051 | 0.1045 | 0.1016（−2.8%，1/0） | 0.0988（−5.5%，3/0） | 0.0911（−12.9%，3/1） | 0.0872 | 0.2248 |
| 3-star | 0.3811 | 0.3784 | 0.2870（−24.2%，3/0） | 0.2799（−26.0%，6/0） | 0.2721（−28.1%，3/1） | 0.2352 | 0.2434 |
| triangle | 0.8851 | 0.9108 | 0.6444（−29.3%，4/0） | 0.6301（−30.8%，4/1） | 0.7448（−18.2%，3/2） | 0.5272 | 0.5437 |

- 默认设置经同一执行器与 GT-PSC 同分布（18 格 |z| 最大 2.71，Bonferroni 校正后不显著）。
- 带 margin 时 18 格中没有一格显著变差；收益集中在 D 高估严重的小图（CU、Do、CS 的 3-star 与三角形）和 PM 三角形（−50%，选中 B ≈ 0.67D）。
- GT-Tuned 能调 ε2，在小图上更好，但在 ML、EE、PM 上显著变差（EE 三角形 +64%，PM 3-star +108%）。
- GT-TriTR（逐节点阈值）在三角形 6 图中 4 图、3-star 的 PM / ML / CS 上仍优于自适应。
- margin = 0.1 是看过 EE 三角形 30 次试跑后定的，尚未在独立的图上验证；自适应只在纯代码执行器中实现，尚未接入智能体框架。

## 其他研究内容

主线是"先能测、再能管、最后能换"：

| 研究内容（开题报告 §3.3） | 模块 | 脚本 | 结果目录 |
|---|---|---|---|
| 内容一：机制误差与执行误差分离 + curator 置信区间 | `evaluation.py` | `scripts/analyze_errors.py` | `results/evaluation/` |
| 内容二：LLM 节点灵敏度审计（RQ1、RQ2；P1–P3） | `audit.py` | `scripts/run_sensitivity_audit.py` | `results/audit/sensitivity/` |
| 内容三：三元绑定、消息强校验、证书式下发、攻击实验（P5） | `binding.py`、`messages.py`、`attacks.py` | `scripts/run_attacks.py` | `results/attacks/` |
| 内容四·改进一：预过滤 + 代码守卫 | `agents.py`（`execution="guard"`） | `scripts/run_execution_compare.py` | `results/execution/` |
| 内容四·改进二：DSL 方法与评估 | `dsl/` | `scripts/run_dsl_check.py`、`run_execution_compare.py`、`run_dsl_design_eval.py` | `results/dsl/`、`results/execution/`、`results/dsl_eval/` |
| 内容五：精度—隐私—成本（P4）、token 统计 | `framework.py`、`cost.py` | `scripts/run_execution_compare.py`、`scripts/analyze_cost.py` | `results/execution/`、`results/cost/` |
| 内容六：复合查询与预算记账 | `composite.py` | `scripts/run_composite.py` | `results/composite/` |

```bash
# 以下命令都不调用付费模型（mock / 纯代码）
python scripts/run_dsl_check.py --flawed-first --tag dsl_check                    # DSL 验收：推导 GS = 手工 GS、证伪器、效用测试、设计循环
python scripts/run_dsl_fuzz.py --count 10000 --workers 8 --tag dsl_fuzz          # 推导器对拍：随机程序的推导 GS vs 证伪器
python scripts/run_attacks.py --datasets CU,EE --runs 10 --tag p5                 # P5：四类攻击 × 未开启/开启防御
python scripts/run_execution_compare.py --datasets CU,EE --runs 10 \
    --tasks degree,3-star,triangle,4-star,degree-moment2 --mock-error-rate 0.05 --tag p4_mock   # P4：同噪声下各执行方式
python scripts/analyze_errors.py --tag exp1_decomposition                         # 内容一：复现结果的误差分解
python scripts/analyze_cost.py --tag cost                                         # 内容五：token 与调用量
python scripts/run_composite.py --datasets CU,EE --runs 100 --tag composite       # 内容六：复合查询
python scripts/run_sensitivity_audit.py --provider mock \
    --source results/exp1/gpt-4.1-mini-node_gpt-4.1-curator/gpt41mini-node_gpt41-curator_exp1_CU_degree_r10_PSC --tag _mock_check
```

`--source` 的相对路径先按当前目录解析，找不到时再到复现目录（`../psc/`）下找。所有脚本的结果目录已存在时拒绝覆盖。
`--mock-error-rate` 让 mock 节点以给定概率算错 ±1，用来模拟 LLM 执行错误。

## 设计要点

### 执行方式（`framework.py::TrustedPSCFramework`）

| 选项 | 含义 | DP 性质 |
|---|---|---|
| `baseline_options()` | 论文 PSC：curator 规则直接下发，节点 LLM 计数，无校验 | 仅在 LLM 无错、curator 与消息可信时成立 |
| `TrustOptions(execution="llm")` | + 三元绑定 + 消息强校验（内容三，强制项） | 闭合断裂点②③；断裂点①仍在 |
| `TrustOptions(execution="guard")` | + 预过滤非邻居消息 + 代码守卫（改进一） | 被加噪值恒为绑定函数，C2 严格成立 |
| `TrustOptions(execution="program")` | curator 设计 DSL 程序，节点验证证书后本地解释执行（改进二） | 由程序结构保证，与 LLM 正确性无关；节点 LLM 调用为 0 |
| `send_by_code` / `aggregate_by_code` | send 消息与聚合由代码完成 | 均为已发布数据的后处理 |

同一 `rng` 下各执行方式消耗 DP 随机数的顺序相同，因此**在同一批噪声上配对比较**；不带绑定、校验与攻击时，
结果与复现项目的 `PSCFramework` 逐位相同（`tests/test_trust.py::test_every_mode_equals_the_reproduction_on_identical_noise`）；
`gt_dsl` 与 program 模式逐次相同（`tests/test_dsl_eval.py`）。

### 三元绑定与消息校验（内容三）

- 任务由隐私控制器决定；规则文本、本地函数、投影方式取自节点侧绑定表（`binding.BINDINGS`），curator 下发的规则
  只要与绑定不一致（任务不同或文本被改）即拒绝，`on_violation="fallback"` 降级为库内算法、`"reject"` 拒绝本次运行。
- GS 由节点用公开 d̂max 通过与控制器**同一个**函数（`psc.library.DPFrameworkSpec.sensitivity` + 机制配置）重算，不接受外部数值。
- 消息校验（`messages.validate_messages`）：发送者取自通道身份且必须 ∈ N′(i)、每个发送者一条、消息中编号须等于通道身份、
  列表须等于公开 G′ 的对应行、载荷只能是两个整数字段（自由文本一律丢弃）。只用公开信息，不耗预算。
- 库外任务只能走 DSL + 证书路径（`binding.check_program`）。

### 攻击实验（P5，`results/attacks/p5_cu_ee_r10/`，每数据集 10 次）

未防御节点按"完全服从"的最坏 LLM 建模；防御节点运行本项目的真实检查。

| 攻击 | CU 未防御 | CU 防御 | EE 未防御 | EE 防御 |
|---|---|---|---|---|
| 恶意规则（triangle，恢复 0–9 号边） | 成功率 0.80 | 0（rule_tampered） | 0.79 | 0 |
| 恶意规则（degree） | 1.00 | 0 | 1.00 | 0 |
| 任务不一致（实际 ε3，声称 0.8） | 最大 1.49 | ≤ 0.27 | 最大 23.75 | ≤ 0.34 |
| 文本注入 | 1.00（FPR 0） | 0（malformed_payload） | 1.00 | 0 |
| 整数伪造（k = 100，优势 = TPR − FPR） | 0.76 | ≈ 0（−0.07） | 0.59 | ≈ 0（0.08） |

防御后被加噪的计数与诚实输入完全相同，伪造攻击剩下的"命中"只是诚实计数 + 噪声的偶然超阈值（优势在 0 附近波动）。
诚实运行上消息通过率 100%（CU 7k+、EE 54k+ 条），计数变化 0。

### P4（mock，节点注入 5% 的 ±1 错误，`results/execution/p4_mock_err005_cu_ee_r10/`）

同噪声下 guard 与 program 的执行正确率均为 1、误差等于同噪声规则值；baseline / bind 的节点正确率约 0.95；
program 的节点 LLM 调用为 0（设计结果跨运行缓存），`send_by_code` 让 triangle 的调用从 2n+3 降到 n+2。

## 目录

```
certicount/
  __init__.py      复现目录定位（$PSC_REPRO_ROOT → ../psc → ../psc-reproduction）、DATA_DIR / RESULTS_DIR
  evaluation.py    内容一：误差分解、curator 置信区间（只覆盖 Laplace 部分）
  audit.py         内容二：相邻输入、S1–S4 选取、混合 Laplace 隐私损失、Clopper–Pearson ε 下界
  binding.py       内容三：任务—函数—投影—GS 绑定表、规则/任务/GS/证书检查
  messages.py      内容三：消息强校验
  attacks.py       内容三：四类攻击、服从型执行者、防御代价；框架攻击钩子
  agents.py        TrustedNodeAgent：llm / guard / program 三种执行、通道身份、代码 send
  framework.py     TrustedPSCFramework：在复现的 DP 代码上组合以上选项
  dsl/             DSL 方法：lang、sensitivity、designer、utility、falsifier、library、ground_truth（GT-DSL）、quality
  cost.py          内容五：transcripts 成本统计、各执行方式的调用模型、禁止的优化
  composite.py     内容六：预算账本、复合查询计划、发布结果复用、LLM 分解与校验
  artifacts.py     结果目录、清单与表格
scripts/
  run_dsl_check.py          DSL 验收            run_execution_compare.py   方法 / 执行方式对比（目标一）
  run_dsl_design_eval.py    设计器误差（目标二）  run_attacks.py             攻击实验
  run_composite.py          复合查询            run_sensitivity_audit.py   灵敏度审计
  analyze_errors.py         误差分解            analyze_cost.py            成本统计
  md_to_pdf.py              docs/ 下 Markdown 转 PDF
tests/             test_dsl / test_dsl_eval / test_fuzz / test_search / test_adaptive / test_trust / test_audit / test_eval_cost_composite
docs/              开题报告、答辩讲稿、PPT 提示词、研究笔记
results/           见 results/README.md
```

## 已知问题

- **小图上正确程序被误拒**：设计期参考界为 D = min(n−1, 10)，n ≤ 11 时 D = n−1，`sensitivity` 的"上界过松"判据
  （`x.hi >= n−1`）会把已投影的 k-star / 度二阶矩程序也判为过松，设计循环必然失败。CU、EE 等数据集不受影响；
  计划的修复是按程序结构跟踪上界来源（是否被 D、dmax 等公开阈值限住），只对未被限住的参数报警，尚未实现。
- **设计期参考界**：`gs_ratio` 的主值取自参考界 D = min(n−1, 10)，与运行时的 d̂max 不同；`run_gs_ratio`（每次运行的实际 GS 比）
  与 `gs_ratios`（多个界）可作补充。

## 尚未完成（按开题排期）

- **真实 LLM 的 DSL 评估**：目标一、目标二的脚本已支持真实模型，结果只在 mock 上跑过；DSL 尚缺 wedge / 路径类原语。
- **审计主实验 P2 / P3**：EE 分层 60 节点、本地 vLLM Qwen 与弱模型（需机时或 API 预算，未运行）；大图（> 1000 节点）节点采样扩展。
- **真实模型上的 P4**。
- **改进一的工具调用**（`intersect`、`comb` 等绑定私有表的工具）：当前改进一只有预过滤与守卫两层。
- **文献系统检索**（开题报告 R1）与 2-star 机制口径（见复现档案）。
