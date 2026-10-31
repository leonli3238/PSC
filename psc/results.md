# Exp1 复现结果与论文 Table 2 对比（按模型）

- 指标：平均相对误差 `|f̂ − f| / max(f, 0.001n)`，ε = 2，机制 `floor_tight`（TriTR 为 `tritr_alpha0`），seed = 0。
- 每个模型一张表，每个任务依次列出：本项目复现的 Naive（每种 prompt 一行）、*论文 Naive*、*GT-Naive*、本项目复现的 PSC、*论文 PSC*、*GT-PSC*，以及（若有）TriTR。
- 单元格格式：`均值 ± 标准误 (有效运行次数)`；*斜体* 行为参考值（论文 Table 2 或本实现的纯 Python GT，GT 为 1000 次的均值）；`-` 表示本项目未运行。
- 同一模型、同一方法、同一 prompt 的多次实验（不同目录）合并计算；同一目录内按 `(dataset, task, method, run)` 去重。seed 相同，所以不同目录的第 i 次运行使用相同噪声图，合并后的差异仅来自 LLM 输出。
- 模型调用重试耗尽（`call_failed`）的运行不计入，以 † 标出。
- ‡ 表示部分回复的数被解析器取错（见各小节注释），表中保留存档值。
- Naive 的 prompt：`paper` = 论文原始 prompt（当前默认）；`paper-direct` = paper + “只输出最终数字”；`paper-bidir` = 早期试验过的 paper 变体（当前代码中已移除）；`cot` = curator 系统提示 + 逐步推理/JSON 指令（2026-10-13 之前的默认）。
- 数据来源：`results/exp1/` 下各目录的 `runs.jsonl`；GT 来自 `results/ground_truth/gt_all_r1000_floor_tight_20260930`。本文件由 `scripts/build_results_md.py` 生成。

## 0. 参考：纯 Python GT（与模型无关，1000 次）

GT-Naive 是“在噪声图上精确计数”的误差，即 Naive 在 LLM 不出错时的下限；GT-PSC 是 PSC 在节点和 curator 都不出错时的误差。各模型表格中的 GT 行即取自此表的“本实现”行。

| Task | Method | CU | Do | ML | CS | EE | PM |
|---|---|---|---|---|---|---|---|
| degree | GT-Naive（本实现） | 1.07 | 1.18 | 1.13 | 3.27 | 1.70 | 5.79 |
| degree | *GT-Naive（论文）* | *1.07* | *1.18* | *1.14* | *3.28* | *1.70* | *5.79* |
| degree | GT-PSC（本实现） | 0.0182 | 0.0140 | 0.0096 | 0.0208 | 0.0053 | 0.0030 |
| degree | *GT-PSC（论文）* | *0.0187* | *0.0143* | *0.0098* | *0.0202* | *0.0052* | *0.0030* |
| 2-star | GT-Naive（本实现） | 3.60 | 3.19 | 1.92 | 13.07 | 4.46 | 9.97 |
| 2-star | *GT-Naive（论文）* | *3.60* | *3.19* | *1.92* | *13.04* | *4.48* | *9.95* |
| 2-star | GT-PSC（本实现） | 0.1545 | 0.0947 | 0.0823 | 0.1991 | 0.0479 | 0.0448 |
| 2-star | *GT-PSC（论文）* | *0.1062* | *0.0585* | *0.0444* | *0.1210* | *0.0295* | *0.0284* |
| 3-star | GT-Naive（本实现） | 10.07 | 6.74 | 2.00 | 29.82 | 7.48 | 5.00 |
| 3-star | *GT-Naive（论文）* | *10.12* | *6.75* | *2.01* | *29.88* | *7.48* | *5.01* |
| 3-star | GT-PSC（本实现） | 0.6954 | 0.3472 | 0.2596 | 0.6475 | 0.1797 | 0.1239 |
| 3-star | *GT-PSC（论文）* | *0.8035* | *0.3434* | *0.2077* | *0.5410* | *0.1647* | *0.1290* |
| triangle | GT-Naive（本实现） | 1.44 | 1.87 | 0.5647 | 7.00 | 2.00 | 12.06 |
| triangle | *GT-Naive（论文）* | *1.45* | *1.88* | *0.5655* | *7.02* | *1.99* | *12.06* |
| triangle | GT-PSC（本实现） | 1.00 | 0.8431 | 0.3949 | 1.61 | 0.4059 | 1.05 |
| triangle | *GT-PSC（论文）* | *0.9612* | *0.8162* | *0.3877* | *1.71* | *0.2803* | *1.09* |

## 总览：CU 数据集

单元格为 `均值 (运行次数)`，详细数值、标准误和其他数据集见各模型小节。

| 模型 | 方法 · prompt | degree | 2-star | 3-star | triangle |
|---|---|---|---|---|---|
| GPT-4.1 | Naive · paper | 1.15 (10) | 6.45 (70)‡ | 14.70 (40) | 8.36 (60) |
| GLM-5.2 | Naive · paper | 0.9316 (10) | 1.92 (10) | 7.11 (10) | 13.36 (10) |
| DeepSeek-V3（1226） | Naive · paper | 1.10 (10) | 3.76 (10) | 10.58 (10) | 1.17 (10) |
| DeepSeek-V3（1226） | Naive · paper-direct | 36.10 (30) | 26.54 (40) | 124.85 (40) | 10.26 (30) |
| DeepSeek-V3（1226） | Naive · paper-bidir | - | - | 10.54 (10) | - |
| DeepSeek-V3（1226） | Naive · cot | 1.04 (20) | - | 10.62 (20) | 1.33 (20) |
| hy3-ioa | Naive · paper | 1.07 (60)‡ | 3.72 (60) | 10.10 (60)‡ | 1.52 (60) |
| hy3-ioa | Naive · cot | 1.10 (10) | - | 10.57 (10) | 1.56 (10) |
| curator hy3-ioa + 节点 deepseek-v3 | Naive · paper-direct | 8.85 (20)‡ | 3.77 (20) | 10.75 (20) | 1.57 (20) |
| *论文* | *Naive* | *1.10* | *10.45* | *109.33* | *9.12* |
| *GT（本实现）* | *GT-Naive* | *1.07* | *3.60* | *10.07* | *1.44* |
| DeepSeek-V3（1226） | PSC | 0.0243 (10) | - | 1.09 (10) | 1.15 (10) |
| DeepSeek-V3-0324 | PSC | 0.0225 (100) | - | 0.6987 (100) | - |
| hy3-ioa | PSC | 0.0160 (10) | - | 1.02 (10) | 1.17 (10) |
| curator hy3-ioa + 节点 deepseek-v3 | PSC | 0.0196 (20) | 0.1740 (20) | 0.8239 (20) | 0.9952 (20) |
| curator gpt-4.1 + 节点 gpt-4.1-mini | PSC | - | - | 1.02 (10) | 1.17 (10) |
| *论文* | *PSC* | *0.0174* | *0.0929* | *0.7325* | *0.7939* |
| *GT（本实现）* | *GT-PSC* | *0.0182* | *0.1545* | *0.6954* | *1.00* |
| DeepSeek-V3（1226） | TriTR | 0.0140 (10) | - | 0.5597 (10) | 0.9177 (10) |
| hy3-ioa | TriTR | 0.0160 (10) | - | 0.5597 (10) | 0.9154 (10) |

## 1. GPT-4.1

节点 = curator = gpt-4.1；`gpt41-oaifree_*` 走 hub.oaifree.com 网关，其余走 api.oaipro.com（`.env.gpt41`）。来源目录：`gpt41-oaifree_exp1_CU_degree-2-star-3-star-triangle_r10_floor_tight_Naive`、`openai_gpt-4.1_floor_tight_20261014_153755_281075`、`openai_gpt-4.1_floor_tight_20261014_155709_945010`、`gpt41_exp1_CU_2-star_r30_Naive`、`gpt41-oaifree_exp1_CU_triangle_r20_Naive`

| Task | 方法 · prompt | CU | Do |
|---|---|---|---|
| degree | Naive · paper | 1.15 ± 0.06 (10) | - |
| degree | *Naive（论文）* | *1.10* | *1.39* |
| degree | *GT-Naive（本实现）* | *1.07* | *1.18* |
| degree | PSC | - | - |
| degree | *PSC（论文）* | *0.0174* | *0.0162* |
| degree | *GT-PSC（本实现）* | *0.0182* | *0.0140* |
| 2-star | Naive · paper | 6.45 ± 0.42 (70)‡ | 6.97 ± 0.72 (30)‡ |
| 2-star | *Naive（论文）* | *10.45* | *7.99* |
| 2-star | *GT-Naive（本实现）* | *3.60* | *3.19* |
| 2-star | PSC | - | - |
| 2-star | *PSC（论文）* | *0.0929* | *0.0679* |
| 2-star | *GT-PSC（本实现）* | *0.1545* | *0.0947* |
| 3-star | Naive · paper | 14.70 ± 1.26 (40) | 8.41 ± 1.82 (30)‡ |
| 3-star | *Naive（论文）* | *109.33* | *46.90* |
| 3-star | *GT-Naive（本实现）* | *10.07* | *6.74* |
| 3-star | PSC | - | - |
| 3-star | *PSC（论文）* | *0.7325* | *0.3816* |
| 3-star | *GT-PSC（本实现）* | *0.6954* | *0.3472* |
| triangle | Naive · paper | 8.36 ± 0.61 (60) | - |
| triangle | *Naive（论文）* | *9.12* | *12.97* |
| triangle | *GT-Naive（本实现）* | *1.44* | *1.87* |
| triangle | PSC | - | - |
| triangle | *PSC（论文）* | *0.7939* | *0.8628* |
| triangle | *GT-PSC（本实现）* | *1.00* | *0.8431* |

- ‡ Naive · paper · CU · 2-star：1 次回复的答案写成 LaTeX 千分位（`49{,}705`、`47,\!349`），当前解析器只取到最后三位；按回复中的最终答案重算为 6.58（表中为存档值 6.45）
- ‡ Naive · paper · Do · 2-star：1 次回复的答案写成 LaTeX 千分位（`49{,}705`、`47,\!349`），当前解析器只取到最后三位；按回复中的最终答案重算为 7.30（表中为存档值 6.97）
- ‡ Naive · paper · Do · 3-star：1 次回复的答案写成 LaTeX 千分位（`49{,}705`、`47,\!349`），当前解析器只取到最后三位；按回复中的最终答案重算为 12.56（表中为存档值 8.41）
- GPT-4.1 几乎每次都写 Python 代码再自称“运行结果是 X”，X 是编造的（同一个数如 3142、4952、11094 会跨任务重复出现），所以 Naive 误差主要由“编出来的数有多大”决定。`gpt41_exp1_CU_2-star_r30_Naive` 中 30 次全部与噪声图精确值不符，26 次属于“伪造代码输出”（相对噪声图精确值偏差中位数 +62%），只有 4 次逐节点手算（偏差中位数 7.6%）。
- 有些回复没有给出最终数字，解析器从公式或正文中取到 3、4、-12 等无关数字，`parse_failures` 仍为 0：`…153755` 中 CU 3-star 3 次、Do 3-star 3 次，`…155709` 中 CU triangle 4 次。去掉这些运行后，`…153755` 的 CU 3-star 为 15.70、Do 3-star 为 9.24，`…155709` 的 CU triangle 为 8.39。

<details><summary>合并单元格的分来源结果</summary>

- Naive · paper · CU · 2-star：`gpt41-oaifree_exp1_CU_degree-2-star-3-star-triangle_r10_floor_tight_Naive` 5.07 (10)；`openai_gpt-4.1_floor_tight_20261014_153755_281075` 6.13 (30)；`gpt41_exp1_CU_2-star_r30_Naive` 7.22 (30)
- Naive · paper · CU · 3-star：`gpt41-oaifree_exp1_CU_degree-2-star-3-star-triangle_r10_floor_tight_Naive` 16.12 (10)；`openai_gpt-4.1_floor_tight_20261014_153755_281075` 14.23 (30)
- Naive · paper · CU · triangle：`gpt41-oaifree_exp1_CU_degree-2-star-3-star-triangle_r10_floor_tight_Naive` 9.05 (10)；`openai_gpt-4.1_floor_tight_20261014_155709_945010` 8.47 (30)；`gpt41-oaifree_exp1_CU_triangle_r20_Naive` 7.83 (20)

</details>

## 2. GLM-5.2

节点 = curator = glm-5.2，关闭 thinking（`extra_body.thinking.type = disabled`），未保存 transcripts。来源目录：`glm-5.2_exp1_CU_degree-2-star-3-star-triangle_r10_floor_tight_Naive`

| Task | 方法 · prompt | CU |
|---|---|---|
| degree | Naive · paper | 0.9316 ± 0.0888 (10) |
| degree | *Naive（论文）* | *1.10* |
| degree | *GT-Naive（本实现）* | *1.07* |
| degree | PSC | - |
| degree | *PSC（论文）* | *0.0174* |
| degree | *GT-PSC（本实现）* | *0.0182* |
| 2-star | Naive · paper | 1.92 ± 0.28 (10) |
| 2-star | *Naive（论文）* | *10.45* |
| 2-star | *GT-Naive（本实现）* | *3.60* |
| 2-star | PSC | - |
| 2-star | *PSC（论文）* | *0.0929* |
| 2-star | *GT-PSC（本实现）* | *0.1545* |
| 3-star | Naive · paper | 7.11 ± 1.37 (10) |
| 3-star | *Naive（论文）* | *109.33* |
| 3-star | *GT-Naive（本实现）* | *10.07* |
| 3-star | PSC | - |
| 3-star | *PSC（论文）* | *0.7325* |
| 3-star | *GT-PSC（本实现）* | *0.6954* |
| triangle | Naive · paper | 13.36 ± 6.33 (10) |
| triangle | *Naive（论文）* | *9.12* |
| triangle | *GT-Naive（本实现）* | *1.44* |
| triangle | PSC | - |
| triangle | *PSC（论文）* | *0.7939* |
| triangle | *GT-PSC（本实现）* | *1.00* |

- GLM-5.2 列出的度数系统性偏小（估计值约为噪声图精确值的 0.6 倍），抵消了加噪带来的偏大，所以 2-star、3-star 的误差反而低于 GT-Naive 下限，不代表算得更准。triangle 则会编造大量不存在的三角形（如 CU 第 1 次列出 2579 个，其中只有 103 个真实存在）。

## 3. DeepSeek-V3（1226）

节点 = curator = deepseek-v3。来源目录：`dsv3-1226_exp1_all6_r10_floor_tight_Naive`、`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0`、`dsv3-1226_exp1_all6_r10_floor_tight_Naive_paperprompt`、`dsv3-1226_exp1_CU-Do_2-star_r10_floor_tight_Naive_paperprompt`、`dsv3-1226_exp1_CU-Do_degree-2-star-3-star-triangle_r30_floor_tight_Naive_paper-directprompt`、`dsv3-1226_exp1_CU-Do_2-star_r10_floor_tight_Naive_paper-directprompt`、`dsv3-1226_exp1_CU-Do_3-star_r10_floor_tight_Naive_paper-directprompt`、`dsv3-1226_exp1_CU-Do_3-star_r10_floor_tight_Naive_paper-bidirprompt`

| Task | 方法 · prompt | CU | Do | ML | CS | EE | PM |
|---|---|---|---|---|---|---|---|
| degree | Naive · paper | 1.10 ± 0.03 (10) | 1.07 ± 0.08 (10) | 0.9402 ± 0.1426 (10) | 2.81 ± 0.32 (10) | 0.8919 ± 0.2046 (10) | 7.84 ± 4.22 (10) |
| degree | Naive · paper-direct | 36.10 ± 4.85 (30) | 27.16 ± 6.85 (30) | - | - | - | - |
| degree | Naive · paper-bidir | - | - | - | - | - | - |
| degree | Naive · cot | 1.04 ± 0.05 (20) | 0.9519 ± 0.0876 (20) | 1.03 ± 0.06 (20) | 2.57 ± 0.23 (20) | 1.77 ± 0.73 (20)‡ | 4.22 ± 0.49 (10) |
| degree | *Naive（论文）* | *1.10* | *1.39* | *1.89* | *4.14* | *2.56* | *5.35* |
| degree | *GT-Naive（本实现）* | *1.07* | *1.18* | *1.13* | *3.27* | *1.70* | *5.79* |
| degree | PSC | 0.0243 ± 0.0083 (10) | 0.0214 ± 0.0060 (10) | 0.0079 ± 0.0020 (10) | 0.0192 ± 0.0040 (10) | 0.0166 ± 0.0079 (10) | - |
| degree | *PSC（论文）* | *0.0174* | *0.0162* | *0.0110* | *0.0259* | *0.0070* | *0.0666* |
| degree | *GT-PSC（本实现）* | *0.0182* | *0.0140* | *0.0096* | *0.0208* | *0.0053* | *0.0030* |
| degree | TriTR | 0.0140 ± 0.0054 (10) | 0.0139 ± 0.0027 (10) | 0.0189 ± 0.0117 (10) | 0.0192 ± 0.0040 (10) | 0.0107 ± 0.0043 (10) | - |
| 2-star | Naive · paper | 3.76 ± 0.15 (10) | 2.62 ± 0.27 (10) | - | - | - | - |
| 2-star | Naive · paper-direct | 26.54 ± 3.91 (40) | 77.76 ± 43.63 (40) | - | - | - | - |
| 2-star | Naive · paper-bidir | - | - | - | - | - | - |
| 2-star | Naive · cot | - | - | - | - | - | - |
| 2-star | *Naive（论文）* | *10.45* | *7.99* | *7.04* | *48.42* | *24.54* | *14.40* |
| 2-star | *GT-Naive（本实现）* | *3.60* | *3.19* | *1.92* | *13.07* | *4.46* | *9.97* |
| 2-star | PSC | - | - | - | - | - | - |
| 2-star | *PSC（论文）* | *0.0929* | *0.0679* | *0.0563* | *0.0800* | *0.0349* | *0.3508* |
| 2-star | *GT-PSC（本实现）* | *0.1545* | *0.0947* | *0.0823* | *0.1991* | *0.0479* | *0.0448* |
| 2-star | TriTR | - | - | - | - | - | - |
| 3-star | Naive · paper | 10.58 ± 0.55 (10) | 6.58 ± 0.38 (10) | 1.93 ± 0.17 (10) | 27.40 ± 1.91 (10) | 2.33 ± 0.80 (10) | 4.66 ± 3.47 (10) |
| 3-star | Naive · paper-direct | 124.85 ± 69.93 (40) | 186.62 ± 61.11 (40) | - | - | - | - |
| 3-star | Naive · paper-bidir | 10.54 ± 0.54 (10) | 6.64 ± 0.37 (10) | - | - | - | - |
| 3-star | Naive · cot | 10.62 ± 0.38 (20) | 6.09 ± 0.37 (20) | 1.97 ± 0.13 (20) | 25.71 ± 1.74 (20) | 4.22 ± 0.68 (20) | 1.54 ± 0.39 (10) |
| 3-star | *Naive（论文）* | *109.33* | *46.90* | *9.41* | *159.43* | *3.11* | *33.77* |
| 3-star | *GT-Naive（本实现）* | *10.07* | *6.74* | *2.00* | *29.82* | *7.48* | *5.00* |
| 3-star | PSC | 1.09 ± 0.33 (10) | 0.5581 ± 0.1033 (10) | 0.3208 ± 0.0646 (10) | 0.8729 ± 0.1746 (10) | 0.2514 ± 0.0640 (10) | - |
| 3-star | *PSC（论文）* | *0.7325* | *0.3816* | *0.1703* | *0.4711* | *0.2445* | *0.6904* |
| 3-star | *GT-PSC（本实现）* | *0.6954* | *0.3472* | *0.2596* | *0.6475* | *0.1797* | *0.1239* |
| 3-star | TriTR | 0.5597 ± 0.0676 (10) | 0.2922 ± 0.0400 (10) | 0.1470 ± 0.0237 (10) | 0.2974 ± 0.0565 (10) | 0.2167 ± 0.0557 (10) | - |
| triangle | Naive · paper | 1.17 ± 0.19 (10) | 2.70 ± 1.10 (10) | 1.15 ± 0.27 (10) | 12.28 ± 5.57 (10) | 1.04 ± 0.30 (10) | 7.77 ± 3.66 (10) |
| triangle | Naive · paper-direct | 10.26 ± 2.39 (30) | 4.62 ± 1.12 (30) | - | - | - | - |
| triangle | Naive · paper-bidir | - | - | - | - | - | - |
| triangle | Naive · cot | 1.33 ± 0.19 (20) | 2.96 ± 1.36 (20) | 0.7916 ± 0.1436 (20) | 6.00 ± 1.65 (20) | 0.7747 ± 0.1605 (20) | 6.00 ± 3.75 (10) |
| triangle | *Naive（论文）* | *9.12* | *12.97* | *7.42* | *51.19* | *11.42* | *32.77* |
| triangle | *GT-Naive（本实现）* | *1.44* | *1.87* | *0.5647* | *7.00* | *2.00* | *12.06* |
| triangle | PSC | 1.15 ± 0.31 (10) | 0.4846 ± 0.1238 (10) | 0.4096 ± 0.1049 (10) | 1.30 ± 0.40 (10) | 0.4071 ± 0.0965 (10) | - |
| triangle | *PSC（论文）* | *0.7939* | *0.8628* | *0.3240* | *2.99* | *0.2914* | *0.4786* |
| triangle | *GT-PSC（本实现）* | *1.00* | *0.8431* | *0.3949* | *1.61* | *0.4059* | *1.05* |
| triangle | TriTR | 0.9177 ± 0.0821 (10) | 0.7134 ± 0.0726 (10) | 0.4929 ± 0.0709 (10) | 0.7278 ± 0.0814 (10) | 0.4230 ± 0.0520 (10) | - |

- ‡ Naive · cot · EE · degree：1 次回复被当时的解析器取错数（当前解析器已能正确解析）；按回复中的最终答案重算为 1.01（表中为存档值 1.77）
- `paper-direct` 禁止推理后模型只能猜数，误差比其他 prompt 高一个数量级。

<details><summary>合并单元格的分来源结果</summary>

- Naive · cot · CU · degree：`dsv3-1226_exp1_all6_r10_floor_tight_Naive` 1.10 (10)；`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0` 0.9893 (10)
- Naive · cot · Do · degree：`dsv3-1226_exp1_all6_r10_floor_tight_Naive` 0.8497 (10)；`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0` 1.05 (10)
- Naive · cot · ML · degree：`dsv3-1226_exp1_all6_r10_floor_tight_Naive` 1.00 (10)；`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0` 1.05 (10)
- Naive · cot · CS · degree：`dsv3-1226_exp1_all6_r10_floor_tight_Naive` 2.70 (10)；`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0` 2.44 (10)
- Naive · cot · EE · degree：`dsv3-1226_exp1_all6_r10_floor_tight_Naive` 1.21 (10)；`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0` 2.33 (10)
- Naive · paper-direct · CU · 2-star：`dsv3-1226_exp1_CU-Do_degree-2-star-3-star-triangle_r30_floor_tight_Naive_paper-directprompt` 27.12 (30)；`dsv3-1226_exp1_CU-Do_2-star_r10_floor_tight_Naive_paper-directprompt` 24.80 (10)
- Naive · paper-direct · Do · 2-star：`dsv3-1226_exp1_CU-Do_degree-2-star-3-star-triangle_r30_floor_tight_Naive_paper-directprompt` 62.62 (30)；`dsv3-1226_exp1_CU-Do_2-star_r10_floor_tight_Naive_paper-directprompt` 123.16 (10)
- Naive · paper-direct · CU · 3-star：`dsv3-1226_exp1_CU-Do_degree-2-star-3-star-triangle_r30_floor_tight_Naive_paper-directprompt` 65.52 (30)；`dsv3-1226_exp1_CU-Do_3-star_r10_floor_tight_Naive_paper-directprompt` 302.86 (10)
- Naive · paper-direct · Do · 3-star：`dsv3-1226_exp1_CU-Do_degree-2-star-3-star-triangle_r30_floor_tight_Naive_paper-directprompt` 139.54 (30)；`dsv3-1226_exp1_CU-Do_3-star_r10_floor_tight_Naive_paper-directprompt` 327.87 (10)
- Naive · cot · CU · 3-star：`dsv3-1226_exp1_all6_r10_floor_tight_Naive` 10.59 (10)；`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0` 10.65 (10)
- Naive · cot · Do · 3-star：`dsv3-1226_exp1_all6_r10_floor_tight_Naive` 5.99 (10)；`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0` 6.19 (10)
- Naive · cot · ML · 3-star：`dsv3-1226_exp1_all6_r10_floor_tight_Naive` 1.98 (10)；`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0` 1.96 (10)
- Naive · cot · CS · 3-star：`dsv3-1226_exp1_all6_r10_floor_tight_Naive` 24.28 (10)；`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0` 27.15 (10)
- Naive · cot · EE · 3-star：`dsv3-1226_exp1_all6_r10_floor_tight_Naive` 4.10 (10)；`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0` 4.35 (10)
- Naive · cot · CU · triangle：`dsv3-1226_exp1_all6_r10_floor_tight_Naive` 1.18 (10)；`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0` 1.49 (10)
- Naive · cot · Do · triangle：`dsv3-1226_exp1_all6_r10_floor_tight_Naive` 1.37 (10)；`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0` 4.55 (10)
- Naive · cot · ML · triangle：`dsv3-1226_exp1_all6_r10_floor_tight_Naive` 0.5859 (10)；`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0` 0.9974 (10)
- Naive · cot · CS · triangle：`dsv3-1226_exp1_all6_r10_floor_tight_Naive` 8.49 (10)；`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0` 3.50 (10)
- Naive · cot · EE · triangle：`dsv3-1226_exp1_all6_r10_floor_tight_Naive` 0.5432 (10)；`dsv3-1226_exp1_CU-Do-ML-CS-EE_r10_floor_tight_tritr-a0` 1.01 (10)

</details>

## 4. DeepSeek-V3-0324

节点 = curator = deepseek-v3-0324。来源目录：`dsv3-0324_exp1_CU_degree-3star_r100_floor_tight_PSC`

| Task | 方法 · prompt | CU |
|---|---|---|
| degree | Naive | - |
| degree | *Naive（论文）* | *1.10* |
| degree | *GT-Naive（本实现）* | *1.07* |
| degree | PSC | 0.0225 ± 0.0019 (100) |
| degree | *PSC（论文）* | *0.0174* |
| degree | *GT-PSC（本实现）* | *0.0182* |
| 3-star | Naive | - |
| 3-star | *Naive（论文）* | *109.33* |
| 3-star | *GT-Naive（本实现）* | *10.07* |
| 3-star | PSC | 0.6987 ± 0.0661 (100) |
| 3-star | *PSC（论文）* | *0.7325* |
| 3-star | *GT-PSC（本实现）* | *0.6954* |

- 节点更新 9800 次中 9799 次与规则一致；curator 汇总 degree 97/100、3-star 92/100 正确。3-star 的 8 次错误里有 7 次是不做计算直接输出 `{"result": 0}`（10 到 13 个输出 token），而带噪计数之和实际为 99 到 460。

## 5. hy3-ioa

节点 = curator = hy3-ioa。来源目录：`hy3_exp1_r10`+`hy3_exp1_pm_rest`、`hy3_exp1_CU_all4_r30_Naive`、`hy3_exp1_CU_all4_r30_Naive_transcripts`、`hy3-ioa_exp1_CU-Do_r10_floor_tight_TriTR-a0`

| Task | 方法 · prompt | CU | Do | ML | CS | EE | PM |
|---|---|---|---|---|---|---|---|
| degree | Naive · paper | 1.07 ± 0.02 (60)‡ | - | - | - | - | - |
| degree | Naive · cot | 1.10 ± 0.03 (10) | 1.17 ± 0.03 (10) | 1.16 ± 0.02 (10) | 3.27 ± 0.04 (10) | 1.71 ± 0.02 (10) | 7.19 ± 1.14 (8)† |
| degree | *Naive（论文）* | *1.10* | *1.39* | *1.89* | *4.14* | *2.56* | *5.35* |
| degree | *GT-Naive（本实现）* | *1.07* | *1.18* | *1.13* | *3.27* | *1.70* | *5.79* |
| degree | PSC | 0.0160 ± 0.0053 (10) | 0.0139 ± 0.0027 (10) | 0.0077 ± 0.0023 (10) | 0.0180 ± 0.0039 (10) | 0.0060 ± 0.0015 (10) | 0.0038 ± 0.0006 (10) |
| degree | *PSC（论文）* | *0.0174* | *0.0162* | *0.0110* | *0.0259* | *0.0070* | *0.0666* |
| degree | *GT-PSC（本实现）* | *0.0182* | *0.0140* | *0.0096* | *0.0208* | *0.0053* | *0.0030* |
| degree | TriTR | 0.0160 ± 0.0053 (10) | 0.0152 ± 0.0026 (10) | - | - | - | - |
| 2-star | Naive · paper | 3.72 ± 0.06 (60) | - | - | - | - | - |
| 2-star | Naive · cot | - | - | - | - | - | - |
| 2-star | *Naive（论文）* | *10.45* | *7.99* | *7.04* | *48.42* | *24.54* | *14.40* |
| 2-star | *GT-Naive（本实现）* | *3.60* | *3.19* | *1.92* | *13.07* | *4.46* | *9.97* |
| 2-star | PSC | - | - | - | - | - | - |
| 2-star | *PSC（论文）* | *0.0929* | *0.0679* | *0.0563* | *0.0800* | *0.0349* | *0.3508* |
| 2-star | *GT-PSC（本实现）* | *0.1545* | *0.0947* | *0.0823* | *0.1991* | *0.0479* | *0.0448* |
| 2-star | TriTR | - | - | - | - | - | - |
| 3-star | Naive · paper | 10.10 ± 0.36 (60)‡ | - | - | - | - | - |
| 3-star | Naive · cot | 10.57 ± 0.54 (10) | 6.62 ± 0.36 (10) | 2.13 ± 0.08 (10) | 29.22 ± 0.88 (10) | 7.57 ± 0.18 (8)† | -† |
| 3-star | *Naive（论文）* | *109.33* | *46.90* | *9.41* | *159.43* | *3.11* | *33.77* |
| 3-star | *GT-Naive（本实现）* | *10.07* | *6.74* | *2.00* | *29.82* | *7.48* | *5.00* |
| 3-star | PSC | 1.02 ± 0.34 (10) | 0.4907 ± 0.0927 (10) | 0.2837 ± 0.0689 (10) | 0.7564 ± 0.1832 (10) | 0.2370 ± 0.0404 (10) | - |
| 3-star | *PSC（论文）* | *0.7325* | *0.3816* | *0.1703* | *0.4711* | *0.2445* | *0.6904* |
| 3-star | *GT-PSC（本实现）* | *0.6954* | *0.3472* | *0.2596* | *0.6475* | *0.1797* | *0.1239* |
| 3-star | TriTR | 0.5597 ± 0.0676 (10) | 0.2922 ± 0.0400 (10) | - | - | - | - |
| triangle | Naive · paper | 1.52 ± 0.05 (60) | - | - | - | - | - |
| triangle | Naive · cot | 1.56 ± 0.12 (10) | 1.87 ± 0.11 (10) | 0.6120 ± 0.0902 (5)† | 6.30 ± 0.18 (6)† | 2.23 ± 0.24 (10) | 81.15 ± 37.89 (10) |
| triangle | *Naive（论文）* | *9.12* | *12.97* | *7.42* | *51.19* | *11.42* | *32.77* |
| triangle | *GT-Naive（本实现）* | *1.44* | *1.87* | *0.5647* | *7.00* | *2.00* | *12.06* |
| triangle | PSC | 1.17 ± 0.29 (10) | 0.4877 ± 0.1189 (10) | 0.4097 ± 0.1032 (10) | 1.28 ± 0.38 (10) | 0.3238 ± 0.0821 (10) | -† |
| triangle | *PSC（论文）* | *0.7939* | *0.8628* | *0.3240* | *2.99* | *0.2914* | *0.4786* |
| triangle | *GT-PSC（本实现）* | *1.00* | *0.8431* | *0.3949* | *1.61* | *0.4059* | *1.05* |
| triangle | TriTR | 0.9154 ± 0.0846 (10) | 0.7176 ± 0.0718 (10) | - | - | - | - |

- ‡ Naive · paper · CU · degree：2 次回复被当前解析器的 `###` 规则取成标题序号（如 `### 3.` 中的 3）；按回复中的最终答案重算为 1.09（表中为存档值 1.07）
- † Naive · cot · PM · degree：2 次运行模型调用重试耗尽，未计入
- ‡ Naive · paper · CU · 3-star：2 次回复被当前解析器的 `###` 规则取成标题序号（如 `### 3.` 中的 3）；按回复中的最终答案重算为 10.39（表中为存档值 10.10）
- † Naive · cot · EE · 3-star：2 次运行模型调用重试耗尽，未计入
- † Naive · cot · PM · 3-star：全部 10 次运行模型调用重试耗尽，未计入
- † Naive · cot · ML · triangle：5 次运行模型调用重试耗尽，未计入
- † Naive · cot · CS · triangle：4 次运行模型调用重试耗尽，未计入
- † PSC · PM · triangle：全部 7 次运行模型调用重试耗尽，未计入
- hy3-ioa 带隐藏推理（`hy3_exp1_CU_all4_r30_Naive_transcripts` 中每次约 0.8 万到 6.5 万输出 token，可见回复很短），Naive 结果基本等于 GT-Naive 下限：该目录 120 次中 110 次与噪声图精确值一致（容许四舍五入）。
- TriTR 的 degree 与 PSC 机制相同，所以数值一样。

<details><summary>合并单元格的分来源结果</summary>

- Naive · paper · CU · degree：`hy3_exp1_CU_all4_r30_Naive` 1.09 (30)；`hy3_exp1_CU_all4_r30_Naive_transcripts` 1.04 (30)
- Naive · paper · CU · 2-star：`hy3_exp1_CU_all4_r30_Naive` 3.72 (30)；`hy3_exp1_CU_all4_r30_Naive_transcripts` 3.72 (30)
- Naive · paper · CU · 3-star：`hy3_exp1_CU_all4_r30_Naive` 9.99 (30)；`hy3_exp1_CU_all4_r30_Naive_transcripts` 10.21 (30)
- Naive · paper · CU · triangle：`hy3_exp1_CU_all4_r30_Naive` 1.52 (30)；`hy3_exp1_CU_all4_r30_Naive_transcripts` 1.52 (30)

</details>

## 6. curator hy3-ioa + 节点 deepseek-v3

Naive 只调用 curator，等同 hy3-ioa 的 Naive。来源目录：`hy3-dsv3-1226_exp1_CU-Do_degree-2-star-3-star-triangle_r20_floor_tight_Naive-PSC_paper-directprompt`

| Task | 方法 · prompt | CU | Do |
|---|---|---|---|
| degree | Naive · paper-direct | 8.85 ± 0.75 (20)‡ | 2.74 ± 0.43 (20)‡ |
| degree | *Naive（论文）* | *1.10* | *1.39* |
| degree | *GT-Naive（本实现）* | *1.07* | *1.18* |
| degree | PSC | 0.0196 ± 0.0035 (20) | 0.0147 ± 0.0021 (20) |
| degree | *PSC（论文）* | *0.0174* | *0.0162* |
| degree | *GT-PSC（本实现）* | *0.0182* | *0.0140* |
| 2-star | Naive · paper-direct | 3.77 ± 0.11 (20) | 3.27 ± 0.08 (20) |
| 2-star | *Naive（论文）* | *10.45* | *7.99* |
| 2-star | *GT-Naive（本实现）* | *3.60* | *3.19* |
| 2-star | PSC | 0.1740 ± 0.0289 (20) | 0.0987 ± 0.0158 (20) |
| 2-star | *PSC（论文）* | *0.0929* | *0.0679* |
| 2-star | *GT-PSC（本实现）* | *0.1545* | *0.0947* |
| 3-star | Naive · paper-direct | 10.75 ± 0.44 (20) | 6.99 ± 0.24 (20) |
| 3-star | *Naive（论文）* | *109.33* | *46.90* |
| 3-star | *GT-Naive（本实现）* | *10.07* | *6.74* |
| 3-star | PSC | 0.8239 ± 0.1745 (20) | 0.3655 ± 0.0636 (20) |
| 3-star | *PSC（论文）* | *0.7325* | *0.3816* |
| 3-star | *GT-PSC（本实现）* | *0.6954* | *0.3472* |
| triangle | Naive · paper-direct | 1.57 ± 0.09 (20) | 2.01 ± 0.08 (20) |
| triangle | *Naive（论文）* | *9.12* | *12.97* |
| triangle | *GT-Naive（本实现）* | *1.44* | *1.87* |
| triangle | PSC | 0.9952 ± 0.1976 (20) | 0.6735 ± 0.1224 (20) |
| triangle | *PSC（论文）* | *0.7939* | *0.8628* |
| triangle | *GT-PSC（本实现）* | *1.00* | *0.8431* |

- ‡ Naive · paper-direct · CU · degree：17 次回复被当时的解析器取错数（当前解析器已能正确解析）；按回复中的最终答案重算为 1.10（表中为存档值 8.85）
- ‡ Naive · paper-direct · Do · degree：8 次回复被当时的解析器取错数（当前解析器已能正确解析）；按回复中的最终答案重算为 1.20（表中为存档值 2.74）
- hy3 在 `paper-direct` 下仍会隐藏推理，degree 回答为 `454/49` 这样的分数，旧解析器取了分母 49。

## 7. curator hy4-preview-ioa + 节点 hy3-ioa

Naive 只调用 curator，等同 hy4-preview-ioa 的 Naive。来源目录：`hy4-curator_hy3-node_exp1_ML_triangle-3star_r10_Naive-PSC`

| Task | 方法 · prompt | ML |
|---|---|---|
| 3-star | Naive · paper | 1.59 ± 0.21 (10)‡ |
| 3-star | *Naive（论文）* | *9.41* |
| 3-star | *GT-Naive（本实现）* | *2.00* |
| 3-star | PSC | 0.2837 ± 0.0689 (10) |
| 3-star | *PSC（论文）* | *0.1703* |
| 3-star | *GT-PSC（本实现）* | *0.2596* |
| triangle | Naive · paper | 0.6000 ± 0.0425 (9)† |
| triangle | *Naive（论文）* | *7.42* |
| triangle | *GT-Naive（本实现）* | *0.5647* |
| triangle | PSC | 0.4100 ± 0.1032 (10) |
| triangle | *PSC（论文）* | *0.3240* |
| triangle | *GT-PSC（本实现）* | *0.3949* |

- ‡ Naive · paper · ML · 3-star：5 次回复的答案写成 LaTeX 千分位（`49{,}705`、`47,\!349`），当前解析器只取到最后三位；按回复中的最终答案重算为 2.14（表中为存档值 1.59）
- † Naive · paper · ML · triangle：1 次运行模型调用重试耗尽，未计入
- PSC 节点更新 3-star 770/770、triangle 767/770 与规则一致，curator 汇总 20/20 正确，误差与同噪声下精确执行（3-star 0.2837、triangle 0.4101）几乎相同。Naive 修正解析后 3-star 2.14、triangle 0.6000，也与同噪声的精确计数（2.14、0.6005）一致。

## 8. curator gpt-4.1 + 节点 gpt-4.1-mini

本组只跑了 PSC，走 api.oaipro.com。Naive 只调用 curator，等同 GPT-4.1 的 Naive，表中 Naive 行取自第 1 节。来源目录：`gpt41mini-node_gpt41-curator_exp1_CU_3-star_r10_PSC`、`gpt41mini-node_gpt41-curator_exp1_CU_triangle_r10_PSC`

| Task | 方法 · prompt | CU |
|---|---|---|
| 3-star | Naive · paper（= GPT-4.1） | 14.70 ± 1.26 (40) |
| 3-star | *Naive（论文）* | *109.33* |
| 3-star | *GT-Naive（本实现）* | *10.07* |
| 3-star | PSC | 1.02 ± 0.34 (10) |
| 3-star | *PSC（论文）* | *0.7325* |
| 3-star | *GT-PSC（本实现）* | *0.6954* |
| triangle | Naive · paper（= GPT-4.1） | 8.36 ± 0.61 (60) |
| triangle | *Naive（论文）* | *9.12* |
| triangle | *GT-Naive（本实现）* | *1.44* |
| triangle | PSC | 1.17 ± 0.29 (10) |
| triangle | *PSC（论文）* | *0.7939* |
| triangle | *GT-PSC（本实现）* | *1.00* |

- 节点更新 3-star 490/490、triangle 481/490 与规则一致，curator 汇总 19/20 正确（3-star 第 4 次 548.54，应为 546.54）。误差与同噪声下精确执行（3-star 1.0229、triangle 1.1723）几乎相同，所以和 hy3-ioa 的 PSC 数值一样。
- 这 10 次比 1000 次的 GT-PSC 高（3-star 0.6954、triangle 1.00），是前 10 个噪声样本本身偏大，不是模型误差。
- 同一个 curator 下，PSC 把 3-star 误差从 Naive 的 14.70 降到 1.02、triangle 从 8.36 降到 1.17。GPT-4.1 的 Naive 远差于 GT-Naive（10.07、1.44），主要是编造数字（见第 1 节）；PSC 把计数拆给节点后，gpt-4.1-mini 也几乎不出错。

## 未纳入的目录

- `hy3_exp1_r10_5ds`：`hy3_exp1_r10` 前五个数据集的合并副本，避免重复计数。
- `gpt41-oaifree_exp1_CU-Do_2-star_r30_Naive`：第 1 次运行就被 429 限流中断，只有空的 transcripts，没有 `runs.jsonl`。
- `_smoke_hy3-dsv3-1226`：冒烟测试，没有运行结果。
- `table2.md` / `table2.json`：此前由 `scripts/build_exp1_table.py` 生成的 DeepSeek-V3 与 hy3-ioa 汇总表，本文件已包含其中的数据。
