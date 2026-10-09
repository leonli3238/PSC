# PSC — Agent-based Substructure Counting under Local Differential Privacy

基于 **AgentScope 1.0**（`agentscope>=1.0,<2.0`）对论文
*Agent-based Substructure Counting under Local Differential Privacy*（ACL 2026）
的代码复现，包含 Naive 基线、PSC 框架（Algorithm 1–3）、纯 Python 的
GT-Naive / GT-PSC / GT-PSC-B，以及论文 Exp1–Exp4 的实验脚本。

## 当前运行方式：CU / Do，每项 10 次

实验入口现在默认使用 `--mechanism floor_tight`：k-star 最大度先限制到 `[0,n−1]`，
投影阈值取 `floor`，报告灵敏度为 `C(D−1,k−1)`；无优化 PSC-B 为 `C(n−2,k−1)`。
degree 和 triangle 的机制保持原有行为。此配置是按论文公开描述与数学紧界选出的实现解释，
并非已确认的作者代码；2-star 仍存在未消除的数值差距。

```bash
# 预览：不会调用模型，不创建实验目录
.venv/bin/python scripts/run_experiments.py --exp pilot --provider openai --datasets CU,Do --runs 10 --mechanism floor_tight --dry-run

# 正式运行：沿用 config.toml 的 hy3-ioa 与 .env 中的连接配置
.venv/bin/python scripts/run_experiments.py --exp pilot --provider openai --datasets CU,Do --runs 10 --mechanism floor_tight --tag hy3-ioa_cudo_r10_floor_tight --verbose

# 纯 Python 的三种 GT 方法，每个数据集/任务/方法各 10 次
.venv/bin/python scripts/run_ground_truth.py --datasets CU,Do --runs 10 --mechanism floor_tight --trace --tag cudo_gt_r10_floor_tight
```

实验脚本默认任务为 degree、triangle、3-star（`psc.graph.DEFAULT_TASKS`）。2-star 的 GT-PSC
机制尚未与论文对齐，默认不跑，需要时用 `--tasks degree,2-star,3-star,triangle` 显式加回。
pilot 中 PSC、Naive 都跟随 `--runs 10`，三任务共 120 次运行，预计 4740 次逻辑模型调用
（不含重试）。`--naive-runs` 只在有意单独覆盖 Naive 次数时使用。已有 `--tag` 会被拒绝，
避免覆盖历史结果；省略 tag 则自动追加时间戳。每完成一次运行立即写入 `runs.jsonl`，
全部完成后写 `summary.json`、`runs.json` 和 `table.md`。此改动不包含断点续跑。

结果新增 `mechanism`、`se_relative_error`、`median_relative_error`、`p95_relative_error`、
`paper_relative_gap`。`manifest.json` 保存非敏感配置和源码/数据哈希。Agent 的
`extra.mechanism_trace` 保存带噪最大度、投影阈值、实际 GS/scale、原始计数和逐节点噪声，
用于本地审计；它不属于可公开的隐私输出。

可选机制为 `legacy`、`floor_bound`、`continuous_bound`、`floor_tight`、`adaptive_2star`。
`adaptive_2star` 在 floor_tight 基础上只改 2-star：节点 i 用自己已发布的带噪度数 y_i 得到
阈值 `D_i = min(D, floor(y_i + 2/ε2))`，并按 `C(D_i−1,1)` 加噪；预算仍为 ε2+ε3=ε。
余量 2 是为接近论文 Table 2 选出的参数，不是作者实现（见 `results/audit/2026-10-02/`）。
`legacy` 恢复旧计算路径。低层 `gt_psc()` 函数及不传 profile 的库敏感度查询保留 legacy
默认以兼容历史研究脚本；GT CLI/实验运行器与 Agent 会显式传入所选机制，默认 floor_tight。

```bash
# 六图候选比较 + 独立随机流确认；不会自动改默认配置
.venv/bin/python scripts/align_gt_psc.py --runs 5000 --confirm-runs 1000
```

本次比较结果见 `results/alignment/profiles_20260929/`；运行说明和限制见
`docs/RUN_CUDO_10.md`。下面旧结果表均为 `legacy` 历史结果，不代表当前默认配置。

## 目录结构

```
psc/
  graph.py              图结构、任务定义（degree / 2-star / 3-star / triangle）、附录 A 统一数据格式
  dp.py                 DP 原语：RR 噪声图(Alg.1)、Laplace 机制、噪声最大度 + 图投影(Alg.2)、预算分配
  mechanism.py          GT / Agent 共享的取整与灵敏度配置，legacy 和三个对齐候选
  alignment.py          k-star 候选机制的配对比较与论文逐格评分
  artifacts.py          防覆盖目录、逐次落盘与非敏感实验清单
  library.py            算法库（send/update/aggregate 规则文本，附录 E）与 DP 框架库
  rules.py              规则的代码语义（GT 算法与 Mock 模型共用）
  ground_truth.py       GT-Naive / GT-PSC / GT-PSC-B 纯 Python 实现 + 相对误差指标
  baselines.py          附录 B 单 LLM 基线：RAW / REFINED（含 10 节点 few-shot 示例生成）
  prompts.py            各阶段 prompt 模板（自然语言 + <structured_input> 机器可读块，后者仅发给 mock）
  mock_model.py         离线 ChatModelBase：严格按规则推理的“完美 LLM”，用于无 API 的端到端验证
  models.py             OpenAI / DashScope / Ollama / Mock 模型与 Formatter 工厂
  agents/
    node_agent.py       NodeAgent：私有真实邻居 + 噪声邻居记忆；send/update 由 LLM 执行
    curator_agent.py    CuratorAgent：算法设计（查算法库）、结果聚合、Naive 直接作答
    privacy_controller.py  PrivacyController：选 DP 框架、拆分 ε、RR/GSOptimize/Laplace 全部代码执行
  framework.py          PSCFramework(Alg.3) 与 NaiveFramework(Alg.1+curator) 编排（fanout_pipeline / observe）
  experiments.py        实验运行器、论文 Table 2/3 参考值、表格输出
scripts/
  prepare_datasets.py   下载并预处理 6 个真实数据集 -> data/*.json
  run_ground_truth.py   GT 实验（默认 1000 次）
  align_gt_psc.py       纯代码候选比较及独立随机流确认
  run_experiments.py    智能体实验 exp1–exp4（默认每算法 10 次）
tests/                  单元/集成测试（含机制差分、同噪声回放和本地协议桩服务器）
data/                   预处理后的数据集（附录 A 格式）
results/                实验输出：<实验>/<标签>/{summary.json, runs.json, table.md}
```

## 安装与运行

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scripts/prepare_datasets.py            # 下载 + 预处理 6 个数据集
python -m pytest tests -q                      # 单元测试
python scripts/run_ground_truth.py --runs 1000 # Table 2 的 GT 列
python scripts/run_experiments.py --exp exp1 --runs 10                 # 离线 mock 模型
python scripts/run_experiments.py --exp exp2 --runs 10                 # 变化 ε
python scripts/run_experiments.py --exp exp3 --runs 10                 # PSC vs PSC-B
python scripts/run_experiments.py --exp exp4 --runs 10                 # 预算分配
python scripts/run_experiments.py --exp exp5 --runs 1                  # 附录 B: RAW / REFINED / PSC-noDP
python scripts/run_experiments.py --exp exp6 --runs 10                 # 附录 B: Naive+RAW vs Naive+REFINED
```

### 使用真实 LLM（论文设置：node = GPT-4.1-mini，curator = GPT-4.1，temperature 0）

密钥与端点写在 `.env`（已加入 `.gitignore`，模板见 `.env.example`），模型写在 `config.toml`：

| 文件 | 内容 |
|---|---|
| `.env` | `OPENAI_API_KEY`、`OPENAI_BASE_URL`（留空即官方 API）、`DASHSCOPE_API_KEY`、`OLLAMA_HOST` |
| `config.toml` | 默认 `provider`、`temperature`、`max_concurrency`、`parallel_runs`、`stream`、`max_retries`、`retry_backoff`，以及每个 provider 的 `node_model` / `curator_model`（隐私控制器复用 curator 模型）；只接受流式请求的网关需设 `stream = true`；`[<provider>.extra]` 为附加请求参数，`[<provider>.node_extra]` / `[<provider>.curator_extra]` 按角色覆盖其中的顶层键（示例见 `config.vllm-think.toml`） |

优先级：命令行参数 > 环境变量（`PSC_PROVIDER`、`OLLAMA_MODEL`；已设置的环境变量也优先于 `.env`）> `config.toml` > 内置默认值。
`--config path/to/other.toml`（或 `PSC_CONFIG`）可切换配置文件。

```bash
python scripts/run_experiments.py --exp exp1 --provider openai --datasets CU,Do --runs 10

# 通义千问（论文 Exp7：node=qwen3-8b, curator=qwen-plus），模型取 config.toml 的 [dashscope]
python scripts/run_experiments.py --exp exp1 --provider dashscope --datasets CU --runs 3

# 本地 Ollama
OLLAMA_MODEL=qwen3:8b python scripts/run_experiments.py --exp exp1 --provider ollama --datasets CU --runs 1
```

每次 PSC 运行的 LLM 调用数为 `2n + 3`（triangle）或 `n + 3`（degree / k-star），
n 为节点数；PM（453 节点）triangle 的 Naive 提示词约 15 万 token，请注意成本。

真实模型只收到自然语言 prompt：`<structured_input>` 块只在 `provider=mock` 时保留
（`ModelConfig.structured_input` 可强制开关）。节点 send 回复无法解析时不再用规则结果兜底，
而是不发送消息并计入 `parse_failures`。

### 并发运行

`parallel_runs`（或 `--parallel-runs`）控制同时执行的运行数，跨所有数据集 / 任务 / 方法调度；
节点调用仍共用 `max_concurrency` 的上限，curator 调用（含 Naive 的回答）不受其限制。
第 i 次运行的全部 DP 噪声来自 `np.random.default_rng([seed, i])`，结果与并发度、完成顺序无关。

### 错误日志与重试

每次模型调用遇到 429 / 5xx / 连接或超时错误、或返回空文本时，会按 `retry_backoff × 2^k` 秒
（服务端给了 `Retry-After` 则取较大者）重试，最多 `max_retries` 次；openai 客户端自身的重试已关闭，
保证每次限流都被记录。全部重试失败时该调用返回空文本并按解析失败处理，实验不中断；
400 / 鉴权等不可重试的错误仍直接抛出。

所有问题写入 `results/<实验>/<标签>/` 下：

| 文件 | 内容 |
|---|---|
| `errors.jsonl` | 每条错误一行，**运行中实时追加**（实验中途崩溃也保留）：`kind`（`api_error` / `empty_reply` / `call_failed` / `parse_failure`）、数据集 / 任务 / 方法 / 第几次运行、agent 与阶段、耗时、HTTP 状态码、模型原始回复（最长 20000 字符，保留首尾） |
| `run.log` | 全部 warning 日志，回复最长显示 4000 字符 |
| `runs.json` | 每次运行的 `extra.errors` 为该次的错误记录 |
| `summary.json` / `table.md` | `api_retries`（重试次数）、`failed_calls`（重试耗尽的调用数） |

### 真实 API 初期验证（pilot）

`--exp pilot` 在 CU、Do 的 3 个默认任务上跑 PSC ×10、Naive ×10（ε = 2），共 4740 次 LLM 调用，
启动时会打印预计调用数。每次运行都会在同一份输入、同一份 Laplace 噪声上用代码重算各步骤，
记录在 `RunResult.extra["validation"]`，汇总列含义：

| 列 | 含义 |
|---|---|
| `node_update_acc` | 节点 update 输出与"对实际收到的消息执行规则"一致的比例 |
| `node_e2e_acc` | 节点计数与完美流水线一致的比例（send + update 误差合计） |
| `send_acc` | triangle 的 send 消息与规则一致的比例 |
| `aggregate_acc` | curator 聚合结果与规则聚合一致的比例 |
| `rule_relative_error` / `delta` | 同噪声下完美流水线的相对误差，及 \|RE_LLM − RE_rule\|（论文 Table 6 的 Δ） |

```bash
python scripts/run_experiments.py --exp pilot --provider mock --runs 10   # 自动生成新标签
python scripts/run_experiments.py --exp pilot --provider openai --runs 10 --verbose
```

## 与论文的对应关系

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
| 相对误差 | `|f̂−f| / max(f, 0.001n)` |

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

## 复现结果（ε = 2）

### 历史 legacy GT 列（纯 Python，1000 次）vs 论文 Table 2

| Task | Method | CU | Do | ML | CS | EE | PM | Avg. |
|---|---|---|---|---|---|---|---|---|
| degree | GT-Naive | 1.0684 | 1.1766 | 1.1339 | 3.2738 | 1.7038 | 5.7901 | 2.3578 |
| degree | *paper* | *1.0707* | *1.1791* | *1.1351* | *3.2757* | *1.7026* | *5.7853* | *2.3581* |
| degree | GT-PSC | 0.0182 | 0.0140 | 0.0096 | 0.0208 | 0.0053 | 0.0030 | 0.0118 |
| degree | *paper* | *0.0187* | *0.0143* | *0.0098* | *0.0202* | *0.0052* | *0.0030* | *0.0119* |
| 2-star | GT-Naive | 3.5982 | 3.1935 | 1.9210 | 13.0671 | 4.4642 | 9.9656 | 6.0349 |
| 2-star | *paper* | *3.6030* | *3.1858* | *1.9165* | *13.0441* | *4.4800* | *9.9490* | *6.0297* |
| 2-star | GT-PSC | 0.1787 | 0.1064 | 0.0797 | 0.2277 | 0.0492 | 0.0435 | 0.1142 |
| 2-star | *paper* | *0.1062* | *0.0585* | *0.0444* | *0.1210* | *0.0295* | *0.0284* | *0.0647* |
| 3-star | GT-Naive | 10.0666 | 6.7418 | 1.9979 | 29.8181 | 7.4814 | 5.0049 | 10.1851 |
| 3-star | *paper* | *10.1186* | *6.7480* | *2.0073* | *29.8754* | *7.4755* | *5.0099* | *10.2058* |
| 3-star | GT-PSC | 0.8730 | 0.4326 | 0.2627 | 0.8010 | 0.1933 | 0.1213 | 0.4473 |
| 3-star | *paper* | *0.8035* | *0.3434* | *0.2077* | *0.5410* | *0.1647* | *0.1290* | *0.3649* |
| triangle | GT-Naive | 1.4433 | 1.8661 | 0.5647 | 6.9952 | 1.9952 | 12.0601 | 4.1541 |
| triangle | *paper* | *1.4545* | *1.8761* | *0.5655* | *7.0165* | *1.9941* | *12.0592* | *4.1610* |
| triangle | GT-PSC | 1.0028 | 0.8431 | 0.3949 | 1.6068 | 0.4059 | 1.0462 | 0.8833 |
| triangle | *paper* | *0.9612* | *0.8162* | *0.3877* | *1.7108* | *0.2803* | *1.0863* | *0.8737* |

GT-Naive 24 个单元格与论文偏差均 < 1%，GT-PSC 的 degree / triangle 与论文基本一致
（triangle 采用附录 E 的 `degree-1` 灵敏度后 Avg 0.8833 vs 论文 0.8737）；
k-star 的历史 GT-PSC 存在持续差距，特别是 2-star；仅用 ceil 更保守不能解释全部差距。
当前候选比较和确认结果保存在 `results/alignment/`。历史 GT-PSC-B、Exp2、Exp3、Exp4 见 `results/`。

### 智能体版（AgentScope，mock 模型，10 次）

完整表见 `results/exp1/mock/table.md`。PSC 平均相对误差：degree 0.0142，2-star 0.1237，
3-star 0.4562，triangle 0.8928（论文 PSC 列：0.0240 / 0.1138 / 0.4484 / 0.9572），
Naive 比 PSC 高 1–2 个数量级，与论文结论一致。Exp2 复现了“ε=3.0 时三角形任务
GT-Naive 反超 GT-PSC”的现象；Exp4 复现了 CU 误差随 ε1 单调上升、ML 先降后升，以及
ε2 过大/过小均使误差上升的现象。Exp5 / Exp6（附录 B）的流水线在 mock 下可完整运行，
但它们度量的是**提示词质量对真实 LLM 的影响**，只有接入真实模型才能得到有意义的数值。

> 说明：mock 模型是严格按规则推理的“完美 LLM”，因此智能体版结果在统计上等价于
> GT 版（`tests/test_psc.py::test_agent_pipeline_matches_ground_truth_distribution`）。
> 论文中 Naive 列远高于 GT-Naive、PSC 与 GT-PSC 的偏差，来源于真实 LLM 的推理误差，
> 需接入真实模型复现；`--mock-error-rate` 可注入节点智能体的 ±1 计数错误做敏感性分析。
