| Task | Method | CU | Avg. |
|---|---|---|---|
| degree | Naive | 0.9316 | 0.9316 |
| degree | *Naive (paper)* | *1.1020* | *1.1020* |
| 2-star | Naive | 1.9247 | 1.9247 |
| 2-star | *Naive (paper)* | *10.4517* | *10.4517* |
| 3-star | Naive | 7.1093 | 7.1093 |
| 3-star | *Naive (paper)* | *109.3320* | *109.3320* |
| triangle | Naive | 13.3614 | 13.3614 |
| triangle | *Naive (paper)* | *9.1228* | *9.1228* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | degree | 2.0000 | Naive | 10 | 0.9316 | 1.0991 | 0.1675 | -0.1675 | 0.0804 | 0.0000 | 0.2570 | 0.2122 | 7 | 0.0448 | 3 | 1.1438 | 0.8868 | 0.9000 |
| CU | 2-star | 2.0000 | Naive | 10 | 1.9247 | 3.7404 | 1.8157 | -1.8157 | 0.2571 | 0.0000 | 1.8157 | 1.8157 | 10 | 0.0000 | 0 | 3.7404 | 1.9247 | 1.0000 |
| CU | 3-star | 2.0000 | Naive | 10 | 7.1093 | 10.5680 | 3.4587 | -3.4587 | 1.4762 | 0.0000 | 5.4713 | 4.4650 | 8 | 1.0063 | 2 | 11.5743 | 6.1030 | 1.0000 |
| CU | triangle | 2.0000 | Naive | 10 | 13.3614 | 1.5596 | 11.8018 | 11.8018 | 6.3564 | 0.0000 | 12.2544 | 0.2263 | 2 | 12.0281 | 8 | 13.5877 | 1.3333 | 0.9000 |
