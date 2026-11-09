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
python -m pytest tests -q          # 208 个测试通过（1 个跳过），全部离线
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

## 隐私模型

本项目的所有隐私声明都按下面的定义理解（与 PSC 原文 Definition 1 一致）。

- **保护对象与相邻关系（按节点）**：节点 i 的私有数据是它的邻接向量 A_i ∈ {0,1}^n（真实邻居表 P）。节点 i 在一次运行中
  发布的全部内容（RR 行、带噪度数、加噪计数）构成随机化器 R_i；对只差一位的 A_i、A_i′ 与任意输出集合 S，
  P[R_i(A_i) ∈ S] ≤ e^ε · P[R_i(A_i′) ∈ S]。其他节点的数据视为固定；第二轮用到的公开历史（噪声图 G′、d̂max、消息、
  逐节点界 D_i）是公开量或其他节点输出的后处理，按自适应顺序组合计入。
- **信任边界与攻击者**：curator 与汇总端不可信，可见全部公开交互；节点运行在可信本地服务器上（真实邻居表、解释器、
  投影顺序、Laplace 噪声都在本地）；节点间信道带发送方身份（伪造与重复由消息校验处理）。`llm` 模式下节点 LLM
  会读到私有表，只有节点模型部署在本地可信边界内时才满足这一假设。
- **保证（program 模式）**：若 (1) 推导的 GS 对 DSL 语义成立，(2) 节点按该语义执行——每次运行一个与 P 无关的投影顺序，
  程序里所有 `project` 调用共用（`lang.order_projector`、`TrustedNodeAgent.bound_degree`），则每个节点满足
  (ε1 + ε2 + ε3)-edge LDP；`nodebound` 模式的逐节点界 D_i 是 ε2 发布的后处理（Imola et al. 2022 的 edge clipping），
  ε1 + ε2 + ε3 = ε 不变。(1) 目前由手工核对、证伪器穷举
  （覆盖全部投影顺序）与随机程序对拍支撑，**尚无形式证明**。
- **LLM 模式**：加噪的是 LLM 的输出，GS 只对规则函数成立，上述保证不成立；内容二的审计度量的就是这一缺口。审计按
  黑盒 DP 审计的标准流程（见下文"灵敏度审计"）在记录的公开历史下度量第三步的条件损失，只有 Clopper–Pearson 下界
  （Bonferroni 校正）ε_lb > ε3 才算越界；ε1、ε2 是上界，不与之相加成"总 ε 下界"（见 `audit.py` 模块说明）。
- **关系级口径**（一条无向边 (u, v)，攻击者看到全部节点的发布）：这条边同时出现在 u、v 的向量里。RR 只由一个端点发布
  （下三角），带噪度数与计数报告两端都会变，所以每次运行的边级预算是 ε1 + 2ε2 + 2ε3：三角形默认拆分在 ε = 2 时为 3，
  无 RR 的 k-star / degree 为 2ε = 4。本项目主张按节点的定义；若要声明关系级 ε，需要把 ε2、ε3 减半，并在同一口径下
  重跑全部基线。

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
| `clipping.py` | 逐节点度界 `edge_clipping_bounds`：D_i = ⌊max(d_i + Lap(1/ε2), 0) + α⌋（Imola et al. USENIX Security 2022，见下文） |
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

投影语义（2026-11-07 统一）：推导器假设一次运行里所有 `project` 调用共用一个与 P 无关的顺序。此前节点对
`project(P, D)` 返回控制器另抽的随机子集、其余调用取最小编号，二者混用会让 `size(project(P, D) - project(project(P, 2 * D), D))`
（推导 GS = 6）在 D = 10 时实际变化约 5、最大 9（`tests/test_trust.py` 回归测试）；`dp_execute` 与复合查询同样如此。
现在节点保留 PSC 抽出的投影表（随机数不变，与复现同噪声相等的测试照旧通过），再用独立子流把它补成一个均匀随机顺序，
程序的全部投影都用这个顺序；证伪器对每张小图枚举节点 0 在顺序中的全部位置（按顶点改名对称，覆盖所有顺序），
对拍因此慢约 5 倍。库内参考程序只调用一次 `project(P, D)`（或只用其大小），结果不变。
旧的 program 模式运行里含多个 / 嵌套 `project` 的设计程序按旧语义执行，
不应再引用。

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
| `bind` / `codecost` | PSC + 防护 | 三元绑定与消息校验 / 代码发送与聚合 |
| `program` | **DSL** | curator LLM 设计程序，节点解释执行（节点 LLM 调用为 0，设计结果跨运行缓存） |
| `nodebound` / `gt-dsl-node` | DSL-node / GT-DSL-node | 同上，但每个节点用自己的界 D_i（edge clipping，见下节；`--clip-alpha` 设 α） |

库外任务只运行 `program` 与 `gt-dsl`（其余模式自动跳过）。`table.md` 有三张表：

- **Goal 1**：`relative_error`；`rule_relative_error` 为同一份噪声下的纯代码值（Naive→GT-Naive、PSC→GT-PSC、DSL→程序自身）；
  `llm_error` = 二者之差，即 LLM 在执行环节带来的误差；`llm_calls` / `node_llm_calls`。
- **Goal 2**：DSL 行与 GT-DSL 逐次配对的 `design_error`、`design_exact`、`gs_ratio`、`split_match` 与实际使用的程序。
- **Details**：节点正确率、被拒消息、违规次数、置信区间覆盖率等。

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

## 逐节点度界：edge clipping（`dsl/clipping.py`，`nodebound` 模式）

PSC 把每个节点的邻居表都投影到同一个公开界 d̂max（n 个带噪度数的最大值，Imola et al. 2021 的做法），大多数节点的
度远小于 d̂max，而 k-star 的 GS = C(D−1, k−1) 随界迅速增长。这里改用 Imola, Murakami, Chaudhuri（USENIX Security 2022）
提出的 **edge clipping**：

- 节点 i 照常用 ε2 发布带噪度数 y_i = d_i + Lap(1/ε2)，并把自己的邻居表截断到 D_i = ⌊max(y_i, 0) + α⌋；
- 程序在 D = D_i 处推导 GS（同一个推导器、同一张证书，节点核验后执行），报告 `count + Lap(GS(D_i)/ε3)`；
- 读噪声图的程序仍用公开行界 dmax = d̂max（由同一批 y_i 算出，后处理），只有 D 变为逐节点；库内三角形程序不调用
  `project(P, D)`，GS = d̂max − 1，估计不受影响。

**隐私**：y_i 是 ε2-DP 的发布（灵敏度 1）；D_i 是它的后处理；给定 D_i，程序在公开 D_i 处的 GS 证书保证计数报告是
ε3-DP；与 RR（ε1）顺序组合，仍为 ε1 + ε2 + ε3 = ε，预算拆分事先固定，与原 PSC 相同。α ≥ 0 是与数据无关的公开超参数
（α 越大截断越少、偏差越小，噪声越大）。没有任何基于数据的选择，因而不需要额外的隐私论证。

```bash
python scripts/run_execution_compare.py --datasets CU,Do --tasks 2-star,3-star,4-star,triangle \
    --modes gt-psc,gt-dsl,gt-dsl-node --runs 200 --tag nodebound_smoke                 # 纯代码，0 次模型调用
python scripts/run_execution_compare.py ... --modes program,nodebound --clip-alpha 2   # 智能体框架中的同一流程
```

小规模测试（ε = 2，每格 200 次，平均相对误差；`results/execution/nodebound_smoke/`、`nodebound_alpha{2,5,10}/`）：

| 数据集 | 任务 | GT-DSL（全局 d̂max） | α = 0 | α = 2 | α = 5 | α = 10 |
|---|---|---|---|---|---|---|
| CU | 2-star | 0.149 | 0.352 | 0.151 | **0.101** | 0.156 |
| CU | 3-star | 0.709 | 0.423 | **0.312** | 0.437 | 0.821 |
| CU | 4-star | 2.884 | **0.743** | 1.055 | 1.683 | 3.617 |
| Do | 2-star | 0.086 | 0.287 | 0.128 | **0.059** | 0.083 |
| Do | 3-star | 0.314 | 0.333 | 0.178 | **0.173** | 0.329 |
| Do | 4-star | 0.846 | 0.388 | **0.337** | 0.537 | 1.036 |
| CU / Do | triangle | 1.010 / 0.852 | 1.003 / 0.780 | — | — | — |

- k 越大，逐节点界的收益越明显（4-star 误差降到 1/4–1/2）；2-star 的 GS 本来就小，α = 0 时截断偏差占主导反而变差。
- α 的最佳值随任务与图变化；这里只是在两张小图上的扫描，**不能据此在同一批图上挑 α 后再报告**，正式实验应固定 α
  （或在独立的图上选定）。三角形的估计量不变，差别只来自随机数顺序（逐节点投影多消耗了随机数）。
- 三角形的逐节点做法（RR 矩阵无偏校正 + 灵敏度 κ·d̃_i）就是 Imola et al. 2022 的估计器，复现包中为 GT-TriTR。

> 此前这里是"先发度数的自适应选择"（NPMLE 后验 + 合成图打分选择器 + margin 0.1）和"LLM 设计程序池"，
> 二者均为本项目自拟、未经文献检验的方法，已删除（`dsl/adaptive.py`、`dsl/pool.py`、`scripts/run_adaptive.py`、
> `scripts/run_pool.py` 及其测试）。`results/adaptive/`、`results/pool/` 只作历史记录，代码已无法重跑。

## 灵敏度审计（`audit.py`，内容二）

LLM 模式下被加噪的是 LLM 的输出 L(x)，而噪声按规则函数 f 的 GS 标定。审计把 M(x) = L(x) + Lap(GS/ε3) 当作黑盒，
按 DP 审计文献的标准流程求隐私损失的统计下界：

1. **相邻输入**（Jagielski et al. 2020；Nasr et al. 2021）：记录的节点输入 x 与翻转私有邻居表一位的 x′；
   S1 随机选位，S2 选使规则函数变化最大的位（不看模型的最强相邻对）。
2. **Monte Carlo 采样**：每次独立调用模型，再抽一次新的 Laplace 噪声。
3. **在独立的选择样本上定检验事件**（Ding et al. 2018，StatDP）：阈值事件 {s·z ≥ t} 只在 select 样本上选定。
4. **在评估样本上求 Clopper–Pearson 下界**（Jagielski et al. 2020 算法 2，δ = 0）：
   ε_lb = log(CP_lower(P[M(x) ∈ S]) / CP_upper(P[M(x′) ∈ S]))，以 1 − α 的概率成立。
5. **Bonferroni** 校正覆盖全部审计对；ε_lb > ε3 才判越界。审计只能否定隐私声明，ε_lb ≤ ε3 不是隐私成立的证据。

```bash
python scripts/run_sensitivity_audit.py --provider mock --select 20 --eval 200 --source <复现结果目录> --tag <tag>
```

此前的"代入损失（plug-in）筛查 + 追加采样"和 S3 / S4 选位策略为自拟流程，已删除。`results/audit/sensitivity/` 中的
P1 试点按旧流程计算，只作历史记录。

### degree 越界探针（路线 B，`probe.py` / `probe_client.py` / `scripts/run_degree_probe.py`）

PM 的 degree 任务：GS = 1、ε3 = ε = 2、Lap(0.5)，规则变化恰为 1（余量 0），节点输入只有私有邻居表（无消息、无 d̂max），
所以直接从图构造输入，提示词、规则文本、初始状态 0.0 与解析器都与 `NodeAgent` 逐字相同（`tests/test_probe.py` 核对）。
x 与 x′ 的输出始终相差 ≤ 1 时损失不超过 ε3，越界需要输出相差 > 1。

- **计划**（`init`）：度 > 30 的 18 个节点穷举全部 452 个翻转；度 11–30 抽 30 个、1–10 抽 12 个，每节点约 40 个定向翻转
  （R 随机、P 头中尾、C 连号、S 数字相似）；每个入选节点 1 个固定随机对（`random_ref`，跨模型对比用）；
  构造输入 L（长度跨 9→10 … 199→200）与 X（150–450 个 id）单列。计划带哈希，其他模型用 `--plan-from` 复用。
- **筛查**（`screen`）：x 调用 3 次、x′ 2 次，按观察到的 |Δ| 排序（描述性，不作结论）。
- **确认**（`confirm`）：先冻结 `design.json`（对子、m、α、样本量、噪声盐），再对每侧做全新的 eval 采样（默认 300，筛查有抖动的对 500）；
  筛查样本与新增 select 样本只用于选阈值事件；Bonferroni 覆盖本设计的 m 对；ε_lb > ε3 才算越界。
  越界按 eval 样本严格分为 count（两侧全为 JSON）/ number_fallback / failed，真实节点与构造输入分开报告。
- **迁移**：`--pairs confirmed:<1.7B 的 confirm_main>` 在新模型上逐字重测（新模型没有筛查样本，需 `--select 30`）；
  `--pairs random` 为同一批随机对；`report` 汇总迁移保持率与模型 × 度数区间表。

```bash
python scripts/run_degree_probe.py init --out _probe_mock --provider mock --mock-mode edge   # 负对照：exact / bias / random / edge
python scripts/run_degree_probe.py screen --out _probe_mock
python scripts/run_degree_probe.py confirm --out _probe_mock --name main --pairs top:40
scripts/probe_h20.sh offline | pilot 1.7b | main 1.7b | transfer 8b | rescreen 8b | report 1.7b 8b   # 单卡流程
```

配置在 `configs/vllm_probe_*.toml`（温度 0、关闭思考、max_tokens 4096，与 `../psc/config.vllm.toml` 一致）。
每个阶段可断点续跑；API 失败记入 `errors.jsonl`，重跑时补齐；服务不可达或模型名不符时立即退出。

## 参考文献

- Imola, Murakami, Chaudhuri. *Locally Differentially Private Analysis of Graph Statistics*. USENIX Security 2021.（PSC 的 d̂max 与投影）
- Imola, Murakami, Chaudhuri. *Communication-Efficient Triangle Counting under Local Differential Privacy*. USENIX Security 2022.（edge clipping）
- Jagielski, Ullman, Oprea. *Auditing Differentially Private Machine Learning: How Private is Private SGD?* NeurIPS 2020.
- Nasr, Song, Thakurta, Papernot, Carlini. *Adversary Instantiation: Lower Bounds for Differentially Private Machine Learning*. IEEE S&P 2021.
- Ding, Wang, Wang, Zhang, Kifer. *Detecting Violations of Differential Privacy*. ACM CCS 2018.
- Clopper, Pearson. *The Use of Confidence or Fiducial Limits Illustrated in the Case of the Binomial*. Biometrika 1934.

## 其他研究内容

主线是"先能测、再能管、最后能换"：

| 研究内容（开题报告 §3.3） | 模块 | 脚本 | 结果目录 |
|---|---|---|---|
| 内容一：机制误差与执行误差分离 + curator 置信区间 | `evaluation.py` | `scripts/analyze_errors.py` | `results/evaluation/` |
| 内容二：LLM 节点灵敏度审计（RQ1、RQ2；P1–P3） | `audit.py` | `scripts/run_sensitivity_audit.py` | `results/audit/sensitivity/` |
| 内容三：三元绑定、消息强校验、证书式下发、攻击实验（P5） | `binding.py`、`messages.py`、`attacks.py` | `scripts/run_attacks.py` | `results/attacks/` |
| 内容四：DSL 方法与评估（改进二） | `dsl/` | `scripts/run_dsl_check.py`、`run_execution_compare.py`、`run_dsl_design_eval.py` | `results/dsl/`、`results/execution/`、`results/dsl_eval/` |
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

同噪声下 program 的执行正确率为 1、误差等于同噪声规则值；baseline / bind 的节点正确率约 0.95；
program 的节点 LLM 调用为 0（设计结果跨运行缓存），`send_by_code` 让 triangle 的调用从 2n+3 降到 n+2。
（该目录下的 `guard` 行来自已移除的"改进一"（预过滤 + 代码守卫）：它用代码值覆盖 LLM 的计数，执行正确率同样为 1，
但 LLM 因此变成纯冗余，且仍会读到私有表；该模式已从代码中删除，表格只是历史记录，重跑不会再出现。）

## 目录

```
certicount/
  __init__.py      复现目录定位（$PSC_REPRO_ROOT → ../psc → ../psc-reproduction）、DATA_DIR / RESULTS_DIR
  evaluation.py    内容一：误差分解、curator 置信区间（只覆盖 Laplace 部分）
  audit.py         内容二：黑盒 DP 审计（相邻输入 S1/S2、select/eval 两阶段阈值检验、Clopper–Pearson ε 下界）
  probe.py         路线 B：PM degree 越界探针（从图构造输入、翻转族、筛查排序、确认分析）
  probe_client.py  探针的模型调用（与 PSC 节点同请求；记录 finish_reason / token / 延迟）、mock 负对照、断点续跑
  binding.py       内容三：任务—函数—投影—GS 绑定表、规则/任务/GS/证书检查
  messages.py      内容三：消息强校验
  attacks.py       内容三：四类攻击、服从型执行者、防御代价；框架攻击钩子
  agents.py        TrustedNodeAgent：llm / program 两种执行、通道身份、代码 send
  framework.py     TrustedPSCFramework：在复现的 DP 代码上组合以上选项
  dsl/             DSL 方法：lang、sensitivity、designer、utility、falsifier、library、ground_truth（GT-DSL）、quality、clipping（逐节点度界）
  cost.py          内容五：transcripts 成本统计、各执行方式的调用模型、禁止的优化
  composite.py     内容六：预算账本、复合查询计划、发布结果复用、LLM 分解与校验
  artifacts.py     结果目录、清单与表格
scripts/
  run_dsl_check.py          DSL 验收            run_execution_compare.py   方法 / 执行方式对比（目标一）
  run_dsl_design_eval.py    设计器误差（目标二）  run_attacks.py             攻击实验
  run_composite.py          复合查询            run_sensitivity_audit.py   灵敏度审计
  analyze_errors.py         误差分解            analyze_cost.py            成本统计
  run_degree_probe.py       degree 越界探针     probe_h20.sh               探针单卡流程（vLLM 部署 + 各阶段）
  md_to_pdf.py              docs/ 下 Markdown 转 PDF
tests/             test_dsl / test_dsl_eval / test_fuzz / test_search / test_trust / test_audit / test_eval_cost_composite
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
- ~~改进一的工具调用~~：随"改进一"一并放弃。守卫模式下 LLM 的值最终总被代码值覆盖，再给它加工具只会让 LLM 成为更绕的代码调用者。
- **文献系统检索**（开题报告 R1）与 2-star 机制口径（见复现档案）。
