# CertiCount 表格的 Naive (LLM) 行

模型：本地 vLLM 服务的 Qwen3-8B（非 thinking），ε = 2，每格 20 次，seed 0。
机制：论文 2.4 节 Naive —— 全部预算用于 Algorithm 1 的 RR 噪声图 G'，curator 模型只收到
`(V(G), Q)` 加 G' 的边表，单轮直接作答（`scripts/run_naive_llm.py`）。
prompt：论文 prompt + "把最终数字放进 \boxed{}"（`boxed` 风格；没有 \boxed{} 的回复按未作答处理，
≥ 1e11 的数字按退化输出丢弃）。指标：平均相对误差 `|f_hat − f| / max(f, 0.001n)`，越小越好，
与 GT / CertiCount 行同口径。

数据：`results/execution/naive_qwen3-8b_all5_r20_eps2_v5/`（CU–CS）、
`results/execution/naive_qwen3-8b_ee_r20_v5/`（EE，其 prompt 14.2k token，服务按 32k 上下文启动）、
`results/execution/naive_qwen3-8b_fill_deg_r20/`（degree-ge3 用 8192 token 回复预算重跑，
3072 会在列举邻接表时被截断）。

| Task | Method | CU | Do | ML | CS | EE | PM | Avg. |
|---|---|---|---|---|---|---|---|
| open-wedge | Naive (Qwen3-8B) | 3.4800 | 0.7810 | 0.2011 | 2.4926 | 1.1708 | - | 1.6251 |
| open-wedge | GT-Naive | 5.1291 | 3.8197 | 3.2747 | 15.3323 | 5.8313 | 9.6771 | 7.1774 |
| open-wedge | GT-Select | 0.3755 | 0.2346 | 0.1590 | 0.3791 | 0.1812 | 0.0297 | 0.2265 |
| open-wedge | CertiCOUNT | 0.7410 | 0.4184 | 0.3038 | 0.7182 | 0.1739 | 0.0292 | 0.3974 |
| degree-ge3 | Naive (Qwen3-8B) | 0.0988 | 0.1781 | 0.4675 | 1.4381 | 0.1818 | - | 0.4729 |
| degree-ge3 | GT-Naive | 0.1370 | 0.3187 | 0.5392 | 1.4566 | 0.1818 | 0.0486 | 0.4470 |
| degree-ge3 | GT-Select | 0.1077 | 0.1143 | 0.1179 | 0.1763 | 0.0585 | 0.0281 | 0.1005 |
| degree-ge3 | CertiCOUNT | 0.1075 | 0.1139 | 0.1175 | 0.1766 | 0.0602 | 0.0292 | 0.1008 |
| triangle-edge | Naive (Qwen3-8B) | 0.0807 | 0.3601 | 0.5172 | 0.2961 | 1.1153 | - | 0.4739 |
| triangle-edge | GT-Naive | 0.8628 | 1.5600 | 1.1836 | 4.2415 | 1.8475 | 5.8524 | 2.5913 |
| triangle-edge | GT-Select | 0.4892 | 0.4833 | 0.4079 | 0.6340 | 0.2258 | 0.1821 | 0.4037 |
| triangle-edge | CertiCOUNT | 0.4986 | 0.5648 | 0.3739 | 0.7128 | 0.2739 | 0.1912 | 0.4359 |
| triangle-node | Naive (Qwen3-8B) | 0.0938 | 0.1250 | 0.1919 | 0.3877 | 0.1000 | - | 0.1797 |
| triangle-node | GT-Naive | 0.0144 | 0.3354 | 0.3451 | 0.5833 | 0.1000 | 0.0203 | 0.2331 |
| triangle-node | GT-Select | 0.2017 | 0.2203 | 0.2322 | 0.2411 | 0.1173 | 0.0756 | 0.1814 |
| triangle-node | CertiCOUNT | 0.2167 | 0.2408 | 0.2085 | 0.2692 | 0.1336 | 0.0743 | 0.1905 |

每格可解析作答数（共 20 次）。其余三行取自 `results/reports/cs9_summary.md`。

| Task | CU | Do | ML | CS | EE | PM |
|---|---|---|---|---|---|---|
| open-wedge | 19/20 | 7/20 | 2/20 | 10/20 | 6/20 | 0/0 |
| degree-ge3 | 20/20 | 19/20 | 8/20 | 9/20 | 1/20 | 0/0 |
| triangle-edge | 18/20 | 14/20 | 9/20 | 13/20 | 15/20 | 0/0 |
| triangle-node | 18/20 | 4/20 | 16/20 | 16/20 | 18/20 | 0/0 |

说明：

* PM 未跑：其 RR 噪声图的 prompt 远超本部署的 32k 上下文（复现 README 记录 PM 的 Naive prompt
  约 15 万 token）。
* Naive 的 Avg. 只对 CU–EE 有值的格子平均。作答数少的格子（EE / ML degree-ge3、Do triangle-node、
  ML/EE open-wedge）只是弱估计；Qwen3-8B 经常在列举邻居时耗尽回复预算而给不出最终答案，这本身是
  Naive 的一种失败模式。
* 多个格子 Naive 的误差低于 GT-Naive（CU triangle-edge 0.0807 对 0.8865、ML open-wedge 0.2011 对
  3.2846、triangle-node 的整体偏低）：RR 噪声图上的计数系统性偏大，猜得靠近真值属于"凑巧降幅"，
  不等于执行更准；判断执行质量应看 `Naive − GT-Naive` 与作答率，见项目 README 的误差分解。
