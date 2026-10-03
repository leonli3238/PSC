CU / Do 每项运行 10 次

默认机制已选为 `floor_tight`。选择依据是六图的四个候选配置、每格 5000 次、Table 2/3
唯一单元格的平均绝对 log 比例差；再以独立随机流每格 1000 次确认。评分从 legacy 的
约 .2993 降到 .2308，确认流为 .2925 对 .2308。此配置总体更接近论文，不能保证每一格
都改善，也不能保证只跑十次的均值比此前更低。2-star 仍有明显差距。

在仓库根目录运行，沿用原来 config.toml 中的 hy3-ioa 和 .env：

```bash
cd /data/workspace/PSC
.venv/bin/python scripts/run_experiments.py --exp pilot --provider openai --datasets CU,Do --runs 10 --mechanism floor_tight --dry-run
.venv/bin/python scripts/run_experiments.py --exp pilot --provider openai --datasets CU,Do --runs 10 --mechanism floor_tight --tag hy3-ioa_cudo_r10_floor_tight --verbose
```

这是四项任务（degree、2-star、3-star、triangle），PSC 和 Naive 每格各 10 次：
2 数据集 × 4 任务 × 2 方法 × 10 次 = 160 次完整实验，预计 5950 次模型调用，不含重试。
默认并发继续来自 config.toml。命令启动时会打印真实解析出的模型和机制。

结果在 `results/pilot/hy3-ioa_cudo_r10_floor_tight/`。若目录已存在，使用另一个 tag；也可以
省略 `--tag` 自动生成含时间戳的目录。日志追加逐次结果不等于支持断点续跑，当前尚无 resume。

| 文件 | 含义 |
|---|---|
| summary.json / table.md | 每格十次平均 RE、RE 标准误、同噪声规则 RE、节点/聚合正确率 |
| runs.json | 全部完成后的逐次结果与机制 trace |
| runs.jsonl | 每完成一次立即写入，异常中断后仍可检查已完成记录 |
| manifest.json | 机制配置、数据/源码哈希、实际模型和运行设置 |
| errors.jsonl / run.log | API 重试和解析失败等日志 |

如只跑两个 k-star 任务，在正式命令加：

```bash
--tasks 2-star,3-star
```

此时是 80 次实验，预计 2420 次调用。若同时保留两种范围的结果，使用不同 tag。

纯 Python GT 的十次平均也可单独执行：

```bash
.venv/bin/python scripts/run_ground_truth.py --datasets CU,Do --runs 10 --mechanism floor_tight --trace --tag cudo_gt_r10_floor_tight
```

默认包含 GT-Naive、GT-PSC、GT-PSC-B，每格各 10 次，共 240 次纯代码实验。
只需要 GT-PSC 则加 `--methods GT-PSC`。结果在 `results/ground_truth/cudo_gt_r10_floor_tight/`。
这个命令用每格连续 RNG 流，Agent 用每次独立 RNG 流，两者相同 seed 不表示逐次噪声相同；
评价模型执行差异时，应读取 pilot 的 `rule_relative_error`，它才是同实际噪声的 GT 回算。

旧版对照使用同样命令加 `--mechanism legacy` 和新 tag。不要将新旧版本的 runs 混在一起平均。

如需稳定的纯代码机制参照，可将 GT 的 `--runs` 单独设为 1000；这不会改变 Agent 每格 10 次的设置。

修改内容：新增四种可选机制；GT 与 Agent 共享参数计算；默认 k-star 用 floor 和紧敏感度；
PSC-B 同样采用一致的紧上界；degree/triangle 保留旧行为；修正 pilot Naive 默认次数；
添加中间量、标准误、逐次落盘与防覆盖。低层 gt_psc() 保留 legacy 默认，实验入口显式传入 profile。

离线验证产物：

- `results/alignment/profiles_20260929/`：六图候选比较和独立确认。
- `results/pilot/mock_cudo_r10_20260929/`：160 次 mock 流程，5950 次本地模型调用，解析失败 0。
- `results/ground_truth/gt_cudo_r10_20260929/`：240 次 GT 流程和 trace。

真实模型实验由上述命令启动，本次代码修改没有代为调用付费模型。

测试结果：`python -m pytest tests -q` 全部 40 项通过（包含本地流式 API 协议桩服务器）；
有一项依赖库 DashScope 的弃用警告，不影响这些测试。
