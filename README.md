# PSC — Agent-based Substructure Counting under Local Differential Privacy

基于 **AgentScope 1.0**（`agentscope>=1.0,<2.0`）对论文
*Agent-based Substructure Counting under Local Differential Privacy*（ACL 2026）
的代码复现，包含 Naive 基线、PSC 框架（Algorithm 1–3）、纯 Python 的
GT-Naive / GT-PSC / GT-PSC-B，以及论文 Exp1–Exp6 的实验脚本。

- [快速开始](#快速开始)
- [使用真实 LLM](#使用真实-llm)
- [DP 机制配置](#dp-机制配置)
- [实现说明](#实现说明)
- [复现结果](#复现结果ε--2floor_tight)：[Exp1（Table 2）](#exp1论文-table-2)、[LLM 误差分解](#llm-误差分解)、[CU 上 100 次](#cu-上-100-次-psc)、[Naive 提示词对照](#naive-提示词对照)、[TriTR 对照](#tritr-对照)
- 全部结果目录的说明见 [`results/README.md`](results/README.md)

## 快速开始

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scripts/prepare_datasets.py            # 下载 + 预处理 6 个数据集 -> data/*.json
python -m pytest tests -q                      # 单元测试

# 纯 Python GT（Table 2 的 GT 行），默认 1000 次
python scripts/run_ground_truth.py --runs 1000
python scripts/run_ground_truth.py --tasks degree,2-star,3-star,triangle --methods GT-PSC,GT-TriTR  # 对照 TriTR

# 离线 mock 模型（严格按规则推理的“完美 LLM”，不调用 API）
python scripts/run_experiments.py --exp exp1 --runs 10                 # Table 2
python scripts/run_experiments.py --exp exp2 --runs 10                 # 变化 ε
python scripts/run_experiments.py --exp exp3 --runs 10                 # PSC vs PSC-B
python scripts/run_experiments.py --exp exp4 --runs 10                 # 预算分配
python scripts/run_experiments.py --exp exp5 --runs 1                  # 附录 B: RAW / REFINED / PSC-noDP
python scripts/run_experiments.py --exp exp6 --runs 10                 # 附录 B: Naive+RAW vs Naive+REFINED
```

实验脚本默认任务为 degree、triangle、3-star（`psc.graph.DEFAULT_TASKS`）。2-star 的 GT-PSC
机制尚未与论文对齐，默认不跑，需要时用 `--tasks degree,2-star,3-star,triangle` 显式加回。

mock 模型在统计上等价于 GT（`tests/test_psc.py::test_agent_pipeline_matches_ground_truth_distribution`），
只用于验证流水线；`--mock-error-rate` 可给节点注入对称的 ±1 计数错误。

## 使用真实 LLM

### 配置

论文设置为 node = GPT-4.1-mini、curator = GPT-4.1、temperature 0。密钥与端点写在 `.env`
（已加入 `.gitignore`，模板见 `.env.example`），模型写在 `config.toml`：

| 文件 | 内容 |
|---|---|
| `.env` | `OPENAI_API_KEY`、`OPENAI_BASE_URL`（留空即官方 API）、`DASHSCOPE_API_KEY`、`OLLAMA_HOST` |
| `config.toml` | 默认 `provider`、`temperature`、`max_concurrency`、`parallel_runs`、`stream`、`max_retries`、`retry_backoff`，以及每个 provider 的 `node_model` / `curator_model`（隐私控制器复用 curator 模型）；只接受流式请求的网关需设 `stream = true`；`[<provider>.extra]` 为附加请求参数，`[<provider>.node_extra]` / `[<provider>.curator_extra]` 按角色覆盖其中的顶层键（示例见 `config.vllm-think.toml`） |

优先级：命令行参数 > 环境变量（`PSC_PROVIDER`、`OLLAMA_MODEL`；已设置的环境变量也优先于 `.env`）> `--profile` 选中的 `[profiles.<name>]` > provider 分节 > 共享键 > 内置默认值。
非 vLLM 的模型共用 `config.toml`：模型用 `--node-model` / `--curator-model` 在命令行指定；不同网关的密钥文件
（`env_file`，替代 `.env`）、`stream`、并发与重试写在 `[profiles.<name>]` 中，用 `--profile` 选择：

| profile | 网关 / 密钥文件 | 用过的模型 |
|---|---|---|
| （不指定） | `.env`，`stream = true` | hy3-ioa、hy4-preview-ioa、deepseek-v3、deepseek-v3-0324 |
| `gpt41` | elysia.h-e.top，`.env.gpt41` | gpt-4.1、gpt-4.1-mini |
| `oaifree` / `oaifree2` | hub.oaifree.com，`.env.oaifree` / `.env.oaifree2`，低并发、长退避 | gpt-4.1、gpt-4.1-mini、gpt-4o、gpt-4o-mini |
| `glm` | `.env`，关闭 thinking | glm-5.2 |

```bash
# 论文设置：node = gpt-4.1-mini、curator = gpt-4.1
.venv/bin/python scripts/run_experiments.py --exp exp1 --provider openai --profile gpt41 \
  --node-model gpt-4.1-mini --curator-model gpt-4.1 --datasets CU --tasks degree --methods PSC --runs 10
```

`--config path/to/other.toml`（或 `PSC_CONFIG`）可切换配置文件；本地 vLLM 用 `config.vllm.toml` / `config.vllm-think.toml`。

真实模型只收到自然语言 prompt：`<structured_input>` 块只在 `provider=mock` 时保留
（`ModelConfig.structured_input` 可强制开关）。节点 send 回复无法解析时不用规则结果兜底，
而是不发送消息并计入 `parse_failures`。

### 常用命令

```bash
# 预览：不会调用模型，不创建实验目录
.venv/bin/python scripts/run_experiments.py --exp pilot --provider openai --datasets CU,Do --runs 10 --dry-run

# CU/Do 上 PSC、Naive 各 10 次，沿用 config.toml 与 .env
.venv/bin/python scripts/run_experiments.py --exp pilot --provider openai --datasets CU,Do --runs 10 --tag hy3-ioa_cudo_r10_floor_tight --verbose

# 单独跑论文的某一个实验（exp1 … exp6，见脚本头部说明）；默认 hy3-ioa，NODE_MODEL= / CURATOR_MODEL= / PROFILE= 可换；
# exp1–exp3 默认加跑智能体版 TriTR，并附 1000 次的 GT-PSC / GT-TriTR（WITH_TRITR=0、GT_RUNS=0 关闭）
bash scripts/run_hy3.sh exp3 --datasets CU,Do --verbose

# Naive 提示词：默认 paper，只发送论文中的 (V(G), Q) + 边列表，不带 system prompt 和作答要求；
# --naive-prompt cot 加上 curator system prompt 和 "Think step by step … JSON" 作答要求（2026-10-13 之前的默认，
# 当时的目录名不带提示词后缀），目录名加 _cotprompt；runs.jsonl 的 extra.reply 保存原始回复
NODE_MODEL=deepseek-v3-0324 GT_RUNS=0 bash scripts/run_hy3.sh exp1 -d CU,Do -m Naive --naive-prompt cot --verbose

# 通义千问（论文 Exp7：node=qwen3-8b, curator=qwen-plus），模型取 config.toml 的 [dashscope]
python scripts/run_experiments.py --exp exp1 --provider dashscope --datasets CU --runs 3

# 本地 Ollama
OLLAMA_MODEL=qwen3:8b python scripts/run_experiments.py --exp exp1 --provider ollama --datasets CU --runs 1

# 中断后补跑的运行与原目录合并，并重建 summary/table（同 seed 的第 i 次运行噪声相同）
python scripts/merge_runs.py results/exp1/<原目录> results/exp1/<补跑目录> --out results/exp1/<新目录>

# 从各结果目录重新生成 Exp1 汇总表 results/exp1/table2.{md,json}
python scripts/build_exp1_table.py
```

已有 `--tag` 会被拒绝，避免覆盖历史结果；省略 tag 则自动追加时间戳。每完成一次运行立即写入
`runs.jsonl`，全部完成后写 `summary.json`、`runs.json` 和 `table.md`；没有断点续跑，中断后用
`merge_runs.py` 合并。

### 调用量

每次 PSC 运行的 LLM 调用数为 `2n + 3`（triangle）或 `n + 3`（degree / k-star），n 为节点数；
Naive 每次 2 次。CU/Do 三任务的 pilot（PSC、Naive 各 10 次，共 120 次运行）预计 4740 次逻辑调用（不含重试）。
PM（453 节点）triangle 的 Naive 提示词约 15 万 token，PSC 每次 909 次调用，请注意成本。

### 并发

`parallel_runs`（或 `--parallel-runs`）控制同时执行的运行数，跨所有数据集 / 任务 / 方法调度；
节点调用共用 `max_concurrency` 的上限，curator 调用（含 Naive 的回答）不受其限制。
第 i 次运行的全部 DP 噪声来自 `np.random.default_rng([seed, i])`，结果与并发度、完成顺序无关。

### 重试与错误日志

每次模型调用遇到 429 / 5xx / 连接或超时错误、或返回空文本时，按 `retry_backoff × 2^k` 秒
（服务端给了 `Retry-After` 则取较大者）重试，最多 `max_retries` 次；openai 客户端自身的重试已关闭，
保证每次限流都被记录。全部重试失败时该调用返回空文本并按解析失败处理，实验不中断；
400 / 鉴权等不可重试的错误直接抛出。

> 重试耗尽的 Naive 作答会被记成 0。Naive 的同噪声规则值大多大于 1，答 0 反而让误差变小，
> 所以汇总这类格子前要先剔除 `failed_calls > 0` 的运行（`scripts/build_exp1_table.py` 已这样做）。

| 文件 | 内容 |
|---|---|
| `errors.jsonl` | 每条错误一行，**运行中实时追加**：`kind`（`api_error` / `empty_reply` / `call_failed` / `parse_failure` / `key_fallback`）、数据集 / 任务 / 方法 / 第几次运行、agent 与阶段、耗时、HTTP 状态码、模型原始回复（最长 20000 字符，保留首尾） |
| `run.log` | 全部 warning 日志，回复最长显示 4000 字符 |
| `runs.json` | 每次运行的 `extra.errors` 为该次的错误记录 |
| `summary.json` / `table.md` | `api_retries`（重试次数）、`failed_calls`（重试耗尽的调用数） |

### 输出与校验字段

`manifest.json` 保存非敏感配置和源码/数据哈希。汇总行除平均相对误差外还有 `se_relative_error`、
`median_relative_error`、`p95_relative_error`、`paper_relative_gap`。Agent 的 `extra.mechanism_trace`
保存带噪最大度、投影阈值、实际 GS/scale、原始计数和逐节点噪声，用于本地审计，不属于可公开的隐私输出。

每次运行都会在同一份输入、同一份噪声上用代码重算各步骤（`RunResult.extra["validation"]`），
得到“完美执行”时的结果 `rule_estimate`。汇总列：

| 列 | 含义 |
|---|---|
| `node_update_acc` | 节点 update 输出与“对实际收到的消息执行规则”一致的比例 |
| `node_e2e_acc` | 节点计数与完美流水线一致的比例（send + update 误差合计） |
| `send_acc` | triangle 的 send 消息与规则一致的比例 |
| `aggregate_acc` | curator 聚合结果与规则聚合一致的比例 |
| `rule_relative_error` | 同噪声下完美流水线的平均相对误差，即算法本身的误差 |
| `delta` | 论文 Table 6 的 \|mean RE_LLM − mean RE_rule\|。先平均再相减，正负会抵消，**只是 LLM 影响的下界** |
| `delta_signed`、`se_delta_signed` | 逐次差值 RE_LLM − RE_rule 的均值及配对标准误；负数表示 LLM 的错误让误差变小 |
| `exec_exact`、`exec_deviation` | LLM 结果与规则结果一致（容差为真值的 0.1%）的运行占比；两者距离的平均，单位同相对误差 |
| `lucky_gain`、`llm_harm` | 凑巧降幅 / 错误增幅：平均相对误差 = 规则值 − 凑巧降幅 + 错误增幅 |
| `conservative_relative_error`、`optimistic_relative_error` | 逐次取两者较大 / 较小值的平均，即去掉 / 给足 LLM 出错带来的运气 |
| `rule_not_better_than_zero` | 完美执行也不比“直接答 0”好的运行占比；这些运行里少算只会让误差变小 |

`delta ≤ mean|RE_LLM − RE_rule| ≤ exec_deviation`。`table.md` 末尾附有这些列的分解表。

## DP 机制配置

实验入口默认 `--mechanism floor_tight`：k-star 最大度先限制到 `[0,n−1]`，投影阈值取 `floor`，
报告灵敏度为 `C(D−1,k−1)`；无优化 PSC-B 为 `C(n−2,k−1)`。degree 和 triangle 的机制保持原有行为。
此配置是按论文公开描述与数学紧界选出的实现解释，并非已确认的作者代码；2-star 仍存在未消除的数值差距。

可选机制为 `legacy`、`floor_bound`、`continuous_bound`、`floor_tight`、`adaptive_2star`。
`adaptive_2star` 在 floor_tight 基础上只改 2-star：节点 i 用自己已发布的带噪度数 y_i 得到
阈值 `D_i = min(D, floor(y_i + 2/ε2))`，并按 `C(D_i−1,1)` 加噪；预算仍为 ε2+ε3=ε。
余量 2 是为接近论文 Table 2 选出的参数，不是作者实现（见 `results/audit/2026-10-02/`）。
`legacy` 恢复旧计算路径。低层 `gt_psc()` 函数及不传 profile 的库敏感度查询保留 legacy
默认以兼容历史研究脚本；GT CLI/实验运行器与 Agent 会显式传入所选机制。

```bash
# 六图候选比较 + 独立随机流确认；不会自动改默认配置
.venv/bin/python scripts/align_gt_psc.py --runs 5000 --confirm-runs 1000
```

比较结果见 `results/alignment/profiles_20260929/`，运行说明、k-star 差距诊断和工作计划见
`docs/PSC_REPRODUCTION_REPORT.md`。

## 实现说明

### 目录结构

```
psc/
  graph.py              图结构、任务定义（degree / 2-star / 3-star / triangle）、附录 A 统一数据格式
  dp.py                 DP 原语：RR 噪声图(Alg.1)、Laplace 机制、噪声最大度 + 图投影(Alg.2)、预算分配
  mechanism.py          GT / Agent 共享的取整与灵敏度配置，legacy 和三个对齐候选
  alignment.py          k-star 候选机制的配对比较与论文逐格评分
  artifacts.py          防覆盖目录、逐次落盘与非敏感实验清单
  library.py            算法库（send/update/aggregate 规则文本，附录 E）与 DP 框架库
  rules.py              规则的代码语义（GT 算法与 Mock 模型共用）
  ground_truth.py       GT-Naive / GT-PSC / GT-PSC-B / GT-TriTR 纯 Python 实现 + 相对误差指标
  baselines.py          附录 B 单 LLM 基线：RAW / REFINED（含 10 节点 few-shot 示例生成）
  prompts.py            各阶段 prompt 模板（自然语言 + <structured_input> 机器可读块，后者仅发给 mock）
  mock_model.py         离线 ChatModelBase：严格按规则推理的“完美 LLM”，用于无 API 的端到端验证
  models.py             OpenAI / DashScope / Ollama / vLLM / Mock 模型与 Formatter 工厂
  agents/
    node_agent.py       NodeAgent：私有真实邻居 + 噪声邻居记忆；send/update 由 LLM 执行
    curator_agent.py    CuratorAgent：算法设计（查算法库）、结果聚合、Naive 直接作答
    privacy_controller.py  PrivacyController：选 DP 框架、拆分 ε、RR/GSOptimize/Laplace 全部代码执行
  framework.py          PSCFramework(Alg.3) 与 NaiveFramework(Alg.1+curator) 编排（fanout_pipeline / observe）
  experiments.py        实验运行器、论文 Table 2/3 参考值、LLM 误差分解、表格输出
scripts/
  prepare_datasets.py   下载并预处理 6 个真实数据集 -> data/*.json
  run_ground_truth.py   GT 实验（默认 1000 次）
  align_gt_psc.py       纯代码候选比较及独立随机流确认
  run_experiments.py    智能体实验 exp1–exp6 与 pilot（默认每算法 10 次）
  run_hy3.sh            按配置文件跑单个实验的封装
  serve_node.sh、serve_curator.sh、run_all_vllm.sh  本地 vLLM 部署与批量运行
  merge_runs.py         合并中断与补跑的 runs.jsonl 并重建表格
  build_exp1_table.py   从结果目录生成 Exp1（Table 2）汇总表
tests/                  单元/集成测试（含机制差分、同噪声回放和本地协议桩服务器）
data/                   预处理后的数据集（附录 A 格式）
docs/                   审计、诊断与方法分析记录
results/                实验输出：<实验>/<标签>/，索引见 results/README.md
```

### 与论文的对应

| 论文 | 实现 |
|---|---|
| Algorithm 1 BuildNoisyGraph | `NodeAgent.release_noisy_edges`（只扰动 j<i 的下三角）+ `PrivacyController.build_noisy_graph` |
| Algorithm 2 GSOptimize | `NodeAgent.report_noisy_degree`（deg + Lap(1/ε2)）→ d̂max → `graph_projection` |
| Algorithm 3 PSC | `PSCFramework.run`：select DP framework → split ε → noisy graph → GS opt → design algorithm → send（`fanout_pipeline` + `observe` 定向投递）→ update → Lap(GS/ε3) → aggregate |
| Naive（2.4 节） | `NaiveFramework.run`：ε 全部用于 RR，噪声边表拼入 prompt 由 curator 直接作答 |
| 预算分配（4.1 节） | `split_budget`：ε1=0.5ε，ε2=0.2(ε−ε1)，ε3=其余；不需要的步骤置 0 并按比例保留 |
| 灵敏度 | degree 1；k-star 依机制配置：默认 floor_tight 为 C(D−1,k−1)，legacy 为 C(D,k−1)；triangle **d̂max−1**（无优化时 n−2） |
| 附录 E 规则/库 | `library.py`；三角形 send/update/aggregate 规则与附录 E 示例逐字对应（含 0.5 计数与 /3、截断负数） |
| 附录 A 数据格式 / 提示词 | `graph.task_prompt`：2-star 提示词与附录 A 逐字一致；Naive 按 RAW 格式把边表插在 `Q: The nodes are numbered from 0 to n−1.` 之后 |
| 附录 B RAW / REFINED / 无 DP 的 PSC | `baselines.py`（含 10 节点 few-shot 示例生成）、`PSCFramework(dp=False)`、`NaiveFramework(prompt_style="refined")` → `exp5` / `exp6` |
| 相对误差 | `|f̂−f| / max(f, 0.001n)`，每次运行算一次再对运行取平均（与论文数值一致） |

### 论文未明确、由本实现补充的细节

| 细节 | 本实现的选择 |
|---|---|
| d̂max 取整 | 默认 k-star 用 `floor`；legacy 和 triangle 用原有 `ceil`；连续最大值和实际阈值分别记录 |
| k-star 任务的投影对象 | 没有噪声图，故对每个节点**本地真实邻居表**投影到 d̂max 个（与 Imola et al. 2021 的 k-star 算法一致） |
| 图投影的对称性 | 删边时对称删除，保证 G′ 仍是无向简单图，且满足 `degree-1` 灵敏度的推导 |
| 隐私控制器使用的 LLM | 复用 curator 模型（论文未指定），且只用于“选 DP 框架”这一步 |
| 附录 B 的 10 节点示例图 | 论文只给了部分示例；本实现用固定种子生成 10 节点 38 边图并程序化写出四步推理 |
| 未实现 | 附录 C 的 token 统计（Exp8）与附录 D 的节点采样扩展（Exp9，Facebook / Bible 大图） |

隐私机制（RR、Laplace、图投影、ε 拆分）全部由 `PrivacyController` 以代码执行，
LLM 只负责算法设计、节点级推理与聚合（对应论文的 Challenge 1）。

### TriTR 对照实现

`GT-TriTR`（`psc.ground_truth.gt_tritr`）的 triangle 部分是 NAM-DPRD 的 TriTR：每个用户发布
d̃ᵢ = max(dᵢ + Lap(1/ε₂), 0) + α，并把自己的邻居表投影到 ⌊d̃ᵢ⌋；随后对投影后邻居表的上三角位做 RR，
得到无偏矩阵 Â；用户 i 上报 Σ_{j,k∈N′(i)} clip(Â_jk, ±κ) + Lap(2κ·d̃ᵢ/ε₃)，总和除以 6。
上游代码在原始邻居表上求和，当 dᵢ > d̃ᵢ 时 2κ·d̃ᵢ 的灵敏度不成立，所以本实现改在投影后的表上求和。
degree / 2-star / 3-star 是同一框架的**扩展，并非原论文算法**：k-star 上报
C(min(dᵢ, ⌊d̃ᵢ⌋), k) + Lap(C(⌊d̃ᵢ⌋−1, k−1)/ε₃)；degree 不投影，与 GT-PSC 逐位相同。
默认参数为 PSC 的预算拆分、α = 0，输出端与 PSC 一样把负数截断为 0。可用 `--tritr-alpha` 调整 α
（上游取 150），`--tritr-budget nam` 改用 TriTR 的 0.1 / 0.45 / 0.45 拆分。

智能体版 `TriTR`（`run_experiments.py --with-tritr`，用于 exp1–exp3）只替换隐私控制器中的 DP 框架
（`PrivacyController.tritr_prepare`）：curator 和节点仍执行 PSC 的 send / update / aggregate 规则。
triangle 节点基于投影后的真实邻居表，读取这些邻居在公开带噪图中的行，按附录 E 规则数出邻居之间的带噪边数 m。
随后本地服务器把 m 换算为无偏值 a·m − b·C(d′, 2)，即 Σ Â_jk / 2，加 Lap(κ·d̃ᵢ/ε₃) 噪声，
因此聚合规则仍是"总和除以 3"。mock 下与 GT-TriTR 分布一致，节点、发送、聚合正确率均为 1。
`--gt-runs N` 在同一张表中附上 N 次纯代码 GT-PSC（exp3 另加 GT-PSC-B）和 GT-TriTR。

## 复现结果（ε = 2，floor_tight）

全部运行 seed = 0、temperature 0，经 OpenAI 兼容网关调用。第 i 次运行的 DP 噪声只由 `(seed, i)`
决定，所以不同模型面对的是同一批噪声图和 Laplace 噪声。论文行取自 Table 2（node = GPT-4.1-mini，
curator = GPT-4.1，每格 10 次）。

### Exp1：论文 Table 2

平均相对误差，越小越好。GT 行是本实现 1000 次纯代码结果（`results/ground_truth/gt_all_r1000_floor_tight_20260930/`）；
LLM 行每格 10 次，node 与 curator 用同一模型：DeepSeek-V3 来自
`results/exp1/dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0/`，hy3-ioa 来自 `results/exp1/hy3_exp1_r10_5ds/`
（PM 行另取自 `hy3_exp1_r10/`、`hy3_exp1_pm_rest/`）。PM 的智能体运行不完整，所以 Avg. 一律取 CU–EE
五个数据集，论文行也按同样五个数据集重新平均。本表由 `scripts/build_exp1_table.py` 生成，原文件为
`results/exp1/table2.md`。

| Task | Method | CU | Do | ML | CS | EE | PM | Avg. (CU–EE) |
|---|---|---|---|---|---|---|---|---|
| degree | GT-Naive（本实现，1000 次） | 1.0684 | 1.1766 | 1.1339 | 3.2738 | 1.7038 | 5.7901 | 1.6713 |
| degree | *GT-Naive（论文）* | *1.0707* | *1.1791* | *1.1351* | *3.2757* | *1.7026* | *5.7853* | *1.6726* |
| degree | Naive · DeepSeek-V3 | 0.9893 | 1.0541 | 1.0549 | 2.4359 | 2.3291 | - | 1.5726 |
| degree | Naive · hy3-ioa | 1.0991 | 1.1673 | 1.1583 | 3.2726 | 1.7093 | 7.1925† | 1.6813 |
| degree | *Naive（论文）* | *1.1020* | *1.3935* | *1.8939* | *4.1415* | *2.5564* | *5.3465* | *2.2175* |
| degree | GT-PSC（本实现，1000 次） | 0.0182 | 0.0140 | 0.0096 | 0.0208 | 0.0053 | 0.0030 | 0.0136 |
| degree | *GT-PSC（论文）* | *0.0187* | *0.0143* | *0.0098* | *0.0202* | *0.0052* | *0.0030* | *0.0136* |
| degree | PSC · DeepSeek-V3 | 0.0243 | 0.0214 | 0.0079 | 0.0192 | 0.0166 | - | 0.0179 |
| degree | PSC · hy3-ioa | 0.0160 | 0.0139 | 0.0077 | 0.0180 | 0.0060 | 0.0038 | 0.0123 |
| degree | *PSC（论文）* | *0.0174* | *0.0162* | *0.0110* | *0.0259* | *0.0070* | *0.0666* | *0.0155* |
| 2-star | GT-Naive（本实现，1000 次） | 3.5982 | 3.1935 | 1.9210 | 13.0671 | 4.4642 | 9.9656 | 5.2488 |
| 2-star | *GT-Naive（论文）* | *3.6030* | *3.1858* | *1.9165* | *13.0441* | *4.4800* | *9.9490* | *5.2459* |
| 2-star | *Naive（论文）* | *10.4517* | *7.9931* | *7.0450* | *48.4216* | *24.5390* | *14.3962* | *19.6901* |
| 2-star | GT-PSC（本实现，1000 次） | 0.1545 | 0.0947 | 0.0823 | 0.1991 | 0.0479 | 0.0448 | 0.1157 |
| 2-star | *GT-PSC（论文）* | *0.1062* | *0.0585* | *0.0444* | *0.1210* | *0.0295* | *0.0284* | *0.0719* |
| 2-star | *PSC（论文）* | *0.0929* | *0.0679* | *0.0563* | *0.0800* | *0.0349* | *0.3508* | *0.0664* |
| 3-star | GT-Naive（本实现，1000 次） | 10.0666 | 6.7418 | 1.9979 | 29.8181 | 7.4814 | 5.0049 | 11.2212 |
| 3-star | *GT-Naive（论文）* | *10.1186* | *6.7480* | *2.0073* | *29.8754* | *7.4755* | *5.0099* | *11.2450* |
| 3-star | Naive · DeepSeek-V3 | 10.6460 | 6.1865 | 1.9605 | 27.1507 | 4.3452 | - | 10.0578 |
| 3-star | Naive · hy3-ioa | 10.5680 | 6.6208 | 2.1267 | 29.2204 | 7.5672† | - | 11.2206 |
| 3-star | *Naive（论文）* | *109.3320* | *46.9049* | *9.4129* | *159.4328* | *3.1083* | *33.7694* | *65.6382* |
| 3-star | GT-PSC（本实现，1000 次） | 0.6954 | 0.3472 | 0.2596 | 0.6475 | 0.1797 | 0.1239 | 0.4259 |
| 3-star | *GT-PSC（论文）* | *0.8035* | *0.3434* | *0.2077* | *0.5410* | *0.1647* | *0.1290* | *0.4121* |
| 3-star | PSC · DeepSeek-V3 | 1.0875 | 0.5581 | 0.3208 | 0.8729 | 0.2514 | - | 0.6181 |
| 3-star | PSC · hy3-ioa | 1.0229 | 0.4907 | 0.2837 | 0.7564 | 0.2370 | - | 0.5581 |
| 3-star | *PSC（论文）* | *0.7325* | *0.3816* | *0.1703* | *0.4711* | *0.2445* | *0.6904* | *0.4000* |
| triangle | GT-Naive（本实现，1000 次） | 1.4433 | 1.8661 | 0.5647 | 6.9952 | 1.9952 | 12.0601 | 2.5729 |
| triangle | *GT-Naive（论文）* | *1.4545* | *1.8761* | *0.5655* | *7.0165* | *1.9941* | *12.0592* | *2.5813* |
| triangle | Naive · DeepSeek-V3 | 1.4860 | 4.5474 | 0.9974 | 3.5024 | 1.0063 | - | 2.3079 |
| triangle | Naive · hy3-ioa | 1.5561 | 1.8653 | 0.6120† | 6.3016† | 2.2253 | 81.1538 | 2.5121 |
| triangle | *Naive（论文）* | *9.1228* | *12.9684* | *7.4197* | *51.1905* | *11.4162* | *32.7652* | *18.4235* |
| triangle | GT-PSC（本实现，1000 次） | 1.0028 | 0.8431 | 0.3949 | 1.6068 | 0.4059 | 1.0462 | 0.8507 |
| triangle | *GT-PSC（论文）* | *0.9612* | *0.8162* | *0.3877* | *1.7108* | *0.2803* | *1.0863* | *0.8312* |
| triangle | PSC · DeepSeek-V3 | 1.1506 | 0.4846 | 0.4096 | 1.3031 | 0.4071 | - | 0.7510 |
| triangle | PSC · hy3-ioa | 1.1723 | 0.4877 | 0.4097 | 1.2766 | 0.3238 | - | 0.7340 |
| triangle | *PSC（论文）* | *0.7939* | *0.8628* | *0.3240* | *2.9922* | *0.2914* | *0.4786* | *1.0529* |

- † 剔除了模型调用重试耗尽的运行（它们的估计值被记成 0），按其余运行计算：hy3 Naive 的 ML triangle 剩 5 次、
  CS triangle 剩 6 次、EE 3-star 剩 8 次、PM degree 剩 8 次；PM 3-star 10 次全部失败，未列入。
  旧版 README 把失败运行算了进去，所以 hy3 Naive 的 ML/CS triangle 和 EE 3-star 当时写的是 0.8060、4.1810、6.2537。
- hy3 的 PM triangle Naive（81.15）每次都拿到了回复，但 15 万 token 的提示词下答案基本是猜的（例如两次都答 123456）。
- 2-star 机制未对齐，智能体 2-star 只在 CU/Do 的 pilot 里跑过，见[其他运行](#其他运行)。

**GT 行**：GT-Naive 24 格与论文偏差均 < 1%；GT-PSC 的 degree 与论文一致，triangle 除 EE（0.41 对 0.28）外接近，
3-star 的 Avg. 接近（0.426 对 0.412）但 CU、CS 有差距；2-star 的 GT-PSC 仍高于论文约 60%。

### Exp1 想说明什么、本实现复现了哪些

论文 Exp1 的主结论是“PSC 在所有数据集和任务上比 Naive 低 1–2 个数量级”，附带结论是“PSC 比 Naive 更接近各自的 GT，
所以多智能体比单个 LLM 算得更准”。Table 2 的四行可以把 PSC 对 Naive 的差距拆成两部分：GT-Naive 对 GT-PSC
是算法本身（不含 LLM）的差距；Naive 对 GT-Naive、PSC 对 GT-PSC 是 LLM 执行带来的变化。

Naive / PSC 平均相对误差之比（CU–EE 平均）：

| Task | 本实现 GT（1000 次） | 论文 GT | DeepSeek-V3 | hy3-ioa | 论文 LLM |
|---|---|---|---|---|---|
| degree | 123.1× | 122.6× | 87.9× | 136.4× | 143.1× |
| 2-star | 45.4× | 72.9× | - | - | 296.5× |
| 3-star | 26.3× | 27.3× | 16.3× | 20.1× | 164.1× |
| triangle | 3.0× | 3.1× | 3.1× | 3.4× | 17.5× |

- **算法层面复现了**：本实现与论文的 GT 比值几乎相同。degree 约两个数量级，3-star 一个多数量级，
  但 triangle 只有约 3 倍，到不了“1–2 个数量级”。
- **LLM 层面没有复现论文的放大**：论文 3-star、triangle 的比值是 164×、17.5×，主要因为 GPT-4.1 的 Naive 比它自己的
  GT-Naive 高 5–6 倍（往多了数）。本实现两个模型的 Naive 都接近或低于 GT-Naive，所以比值与算法层面基本一致。
- 两个模型在全部 15 个格子里 PSC 都优于 Naive，但 triangle 在 CU 上差距很小：按保守口径（PSC 去掉运气、Naive 给足运气）
  只有 1.1–1.3 倍。

### LLM 误差分解

“同噪声规则值”是用代码在同一批噪声上执行算法的结果，不含 LLM 误差。执行正确率是 LLM 结果与规则结果一致的运行占比；
凑巧降幅 / 错误增幅是 LLM 出错让误差变小 / 变大的量，满足 平均相对误差 = 规则值 − 凑巧降幅 + 错误增幅。
“去掉运气”“给足运气”是逐次取两者较大 / 较小值的平均。CU–EE 平均：

| Task | Method | 模型 | 平均相对误差 | 同噪声规则值 | 执行正确率 | 凑巧降幅 | 错误增幅 | 去掉运气 | 给足运气 |
|---|---|---|---|---|---|---|---|---|---|
| degree | Naive | DeepSeek-V3 | 1.5726 | 1.6816 | 60% | 0.3858 | 0.2769 | 1.9585 | 1.2957 |
| degree | Naive | hy3-ioa | 1.6813 | 1.6816 | 94% | 0.0003 | 0.0000 | 1.6816 | 1.6813 |
| degree | PSC | DeepSeek-V3 | 0.0179 | 0.0124 | 82% | 0.0000 | 0.0055 | 0.0179 | 0.0123 |
| degree | PSC | hy3-ioa | 0.0123 | 0.0124 | 92% | 0.0004 | 0.0004 | 0.0127 | 0.0120 |
| 3-star | Naive | DeepSeek-V3 | 10.0578 | 11.2621 | 8% | 1.2461 | 0.0418 | 11.3039 | 10.0160 |
| 3-star | Naive | hy3-ioa | 11.2206 | 11.2812 | 44% | 0.0632 | 0.0027 | 11.2839 | 11.2180 |
| 3-star | PSC | DeepSeek-V3 | 0.6181 | 0.5581 | 86% | 0.0030 | 0.0630 | 0.6211 | 0.5551 |
| 3-star | PSC | hy3-ioa | 0.5581 | 0.5581 | 100% | 0.0000 | 0.0000 | 0.5581 | 0.5581 |
| triangle | Naive | DeepSeek-V3 | 2.3079 | 2.5674 | 0% | 1.1666 | 0.9071 | 3.4744 | 1.4008 |
| triangle | Naive | hy3-ioa | 2.5121 | 2.4894 | 33% | 0.0492 | 0.0719 | 2.5613 | 2.4402 |
| triangle | PSC | DeepSeek-V3 | 0.7510 | 0.7341 | 24% | 0.0260 | 0.0429 | 0.7770 | 0.7081 |
| triangle | PSC | hy3-ioa | 0.7340 | 0.7341 | 96% | 0.0001 | 0.0000 | 0.7341 | 0.7340 |

PSC 各步骤与规则一致的比例（CU–EE 平均，取自各目录的 `summary.json`）：

| Task | 模型 | 节点正确率 | send 正确率 | 聚合正确率 |
|---|---|---|---|---|
| degree | hy3-ioa | 0.998 | - | 1.00 |
| degree | DeepSeek-V3 | 0.998 | - | 0.88 |
| 3-star | hy3-ioa | 1.000 | - | 1.00 |
| 3-star | DeepSeek-V3 | 1.000 | - | 0.86 |
| triangle | hy3-ioa | 0.998 | 1.000 | 1.00 |
| triangle | DeepSeek-V3 | 0.765 | 1.000 | 0.94 |

- **PSC 的误差小是算法的功劳**：hy3-ioa 几乎每一步都与规则一致，误差与同噪声规则值相同，全部来自 DP 噪声。
  DeepSeek-V3 的 LLM 错误净效果是让误差变大：degree、3-star 的节点几乎全部正确，误差来自 curator 聚合（12–14% 的运行
  聚合结果不对）；triangle 节点正确率只有 0.77，执行正确率 24%，凑巧降幅 0.026 与错误增幅 0.043 部分抵消，
  所以均值接近规则值并不代表算对了。
- **Naive 的数字被 LLM 少数美化了**：RR 噪声图上的子结构本来就偏多，Naive 的规则误差几乎都大于 1，
  这时 LLM 少数任何量都只会让误差变小。DeepSeek-V3 与噪声图精确计数一致的比例只有 60% / 8% / 0%，
  3-star、triangle 的凑巧降幅超过 1。hy3-ioa 剔除失败调用后凑巧降幅不超过 0.06。
- **均值相近不等于算对**：`delta` 先平均再相减，正负会抵消。例如 DeepSeek Naive triangle 在 CU 上
  `delta` 只有 0.07，但 LLM 结果平均偏离精确计数 0.64 个真值。判断 LLM 是否算对应看执行正确率和 `exec_deviation`。
- **“直接答 0”的相对误差恒为 1**。CU、CS 的 triangle 上，正确执行 PSC 也有一半以上的运行不比答 0 好
  （1000 次 GT-PSC 中 CU 有 31% 被截断为 0、另 22% 误差大于 1；CS 为 42% 和 32%），这两格的误差小不能算作任何方法的功劳。

解读时还要注意运行次数：PSC 单次相对误差的变异系数为 0.65–1.03 且重尾，10 次均值的 95% 范围约为 ±40–75%，
100 次约为 ±13–21%；Naive 的波动小得多，10 次为 ±2–15%。论文的 LLM 行也只有 10 次。

### CU 上 100 次 PSC

node、curator 均为 DeepSeek-V3-0324，degree / 3-star，带 `--save-transcripts`，共 10400 次模型调用，无失败调用。
目录：`results/exp1/dsv3-0324_exp1_CU_degree-3star_r100_floor_tight_PSC/`。

| Task | PSC（100 次） | 95% CI | 同噪声规则值 | GT-PSC（1000 次） | *PSC (paper)* | *GT-PSC (paper)* |
|---|---|---|---|---|---|---|
| degree | 0.0225 | [0.0189, 0.0262] | 0.0216 | 0.0182 | *0.0174* | *0.0187* |
| 3-star | 0.6987 | [0.5692, 0.8281] | 0.6632 | 0.6954 | *0.7325* | *0.8035* |

运行次数越多，3-star 越接近论文：前 10 / 30 / 50 / 100 次的平均误差为 1.1315 / 0.9276 / 0.8343 / 0.6987
（同噪声规则值 1.0229 / 0.8603 / 0.7822 / 0.6632）。10 次的结果主要取决于抽到了哪些噪声，不足以和论文比较。

- **3-star**：论文的 0.7325 落在 95% CI 内，与 1000 次 GT-PSC 也一致。
- **degree**：0.0225 略高于论文的 0.0174，其中 LLM 只贡献 0.0009；同噪声规则值 0.0216 比
  1000 次 GT-PSC 高约 2 个标准误，主要是这 100 组噪声偏大。
- **LLM 误差来源**：节点 9800 次 update 只错 1 次（3-star 一个节点在 run 86 报了 0，应为 10）。
  其余误差都来自 curator 聚合，全部 100 次中 degree 错 3 次、3-star 错 8 次：
  - 3-star 有 7 次 curator 只输出 10–13 个 token，不做求和直接回答 0，此时那一次的相对误差变成 1。
    这些运行的 49 个带噪计数里有 16–23 个负数，但总和都是正的（99–460，都低于真值 494）；
  - degree 的 3 次也是 15 个 token 左右的直接作答（如 4.0、3.997），没有计算；
  - 写出逐项求和过程的回复中只有 1 次算错（3-star run 58：286.30，应为 234.01），这一次凑巧让误差从 0.526 降到 0.420。

  curator 一旦跳过逐步计算就会出错。3-star 的 LLM 误差 0.0355 几乎全部来自这 7 次直接回答 0；
  9 次与规则不一致的运行中 8 次让误差变大。不要只挑算对的运行来算误差：只用 91 次算对的运行，规则误差是 0.684，全部 100 次是 0.663。
- 64 条 `errors.jsonl` 记录都是可重试的 API 错误（63 条网关 500），重试后都成功，没有解析失败。

### Naive 提示词对照

DeepSeek-V3，6 个数据集，每格 10 次，无失败调用。这组运行在 2026-10-13 之前，“默认 prompt”即现在的
`--naive-prompt cot`；论文 prompt（现在的默认）只发送论文附录中的 (V(G), Q) 和噪声边表，
不带 curator system prompt 和 "Think step by step … JSON" 作答要求：

| Task | Method | CU | Do | ML | CS | EE | PM | Avg. |
|---|---|---|---|---|---|---|---|---|
| degree | 默认 prompt | 1.0991 | 0.8497 | 1.0045 | 2.6988 | 1.2061 | 4.2234 | 1.8469 |
| degree | 论文 prompt | 1.0997 | 1.0730 | 0.9402 | 2.8149 | 0.8919 | 7.8369 | 2.4428 |
| degree | 同噪声规则值 | 1.0991 | 1.1673 | 1.1583 | 3.2734 | 1.7098 | 5.8081 | 2.3693 |
| degree | *Naive (paper)* | *1.1020* | *1.3935* | *1.8939* | *4.1415* | *2.5564* | *5.3465* | *2.7390* |
| 3-star | 默认 prompt | 10.5929 | 5.9941 | 1.9762 | 24.2786 | 4.0976 | 1.5382 | 8.0796 |
| 3-star | 论文 prompt | 10.5763 | 6.5848 | 1.9317 | 27.4017 | 2.3341 | 4.6591 | 8.9146 |
| 3-star | 同噪声规则值 | 10.5680 | 6.6387 | 2.1431 | 29.4321 | 7.5284 | 5.0659 | 10.2294 |
| 3-star | *Naive (paper)* | *109.3320* | *46.9049* | *9.4129* | *159.4328* | *3.1083* | *33.7694* | *60.3267* |
| triangle | 默认 prompt | 1.1789 | 1.3716 | 0.5859 | 8.4881 | 0.5432 | 6.0047 | 3.0287 |
| triangle | 论文 prompt | 1.1667 | 2.6989 | 1.1544 | 12.2833 | 1.0391 | 7.7746 | 4.3529 |
| triangle | 同噪声规则值 | 1.5596 | 1.8674 | 0.6218 | 6.7833 | 2.0046 | 12.1645 | 4.1669 |
| triangle | *Naive (paper)* | *9.1228* | *12.9684* | *7.4197* | *51.1905* | *11.4162* | *32.7652* | *20.8138* |

换成论文 prompt 后结果没有向论文 Naive 靠拢，Avg. 仍比论文低一个数量级，论文 Naive 偏高更可能来自
GPT-4.1 本身，而不是提示词。两种 prompt 的多数格子都低于同噪声规则值，同样是少数造成的。
数据见 `results/exp1/dsv3-1226_exp1_all6_r10_floor_tight_Naive{,_paperprompt}/`。
这组默认 prompt 的运行与 Exp1 表中的 DeepSeek-V3 Naive 是两次独立调用，同噪声下结果也不完全相同。

### TriTR 对照

智能体版 TriTR（α = 0，DeepSeek-V3，CU–EE 平均）：degree 0.0153、3-star 0.3026、triangle 0.6550，
与 1000 次 GT-TriTR（0.0136 / 0.2897 / 0.6033）接近，3-star、triangle 低于 PSC。
数据在 Exp1 的 DeepSeek-V3 目录里，逐格数值和误差分解见该目录的 `table.md`；
hy3-ioa 的 CU/Do 版本见 `results/exp1/hy3-ioa_exp1_CU-Do_r10_floor_tight_TriTR-a0/`；
纯代码对照见 `results/ground_truth/all6_r1000_psc_vs_tritr_a0_20261009/` 与 `all6_r1000_tritr_*_20261009/`。

### 其他运行

- `results/pilot/hy3-ioa_cudo_r10_floor_tight/`、`results/pilot/hy4-preview-ioa_cudo_r10_floor_tight/`：
  CU、Do 上含 2-star 的四任务 pilot。两个模型的 2-star PSC 都与同噪声规则值完全一致，为 CU 0.1931 / Do 0.1295
  （论文 0.0929 / 0.0679），差距来自 2-star 机制尚未对齐，不是 LLM 误差。hy3-ioa 的 Do triangle Naive 有 1 次调用重试耗尽。
- 已归档（`results/archive/`）：curator = hy3-ioa、node = DeepSeek-V3-0324 的单次调试运行，用于定位节点 prompt 的
  状态变量名问题（修复前 degree 节点 17/49 正确，修复后 49/49）；Qwen3-8B 节点 + Qwen3-32B curator 的 exp1–exp6，
  跑在解析器和状态变量名修复之前，Naive 答案多为与图无关的占位数，不宜与论文对比；`legacy` 机制下的 mock 与 GT 结果。
  归档原因逐项见 [`results/README.md`](results/README.md)。
- legacy mock 的 exp2–exp4（`results/archive/exp2…exp4/mock/`）复现了论文的几个趋势：ε = 3.0 时 triangle 的 GT-Naive
  反超 GT-PSC；CU 的误差随 ε1 单调上升、ML 先降后升；ε2 过大或过小都使误差上升。这些趋势尚未在 floor_tight 和真实 LLM 下重跑。
