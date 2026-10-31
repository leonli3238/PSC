| Task | Method | CU | Do | Avg. |
|---|---|---|---|---|
| 2-star | Naive | 6.1332 | 6.9708 | 6.5520 |
| 2-star | *Naive (paper)* | *10.4517* | *7.9931* | *9.2224* |
| 3-star | Naive | 14.2285 | 8.4123 | 11.3204 |
| 3-star | *Naive (paper)* | *109.3320* | *46.9049* | *78.1184* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | Naive | 30 | 6.1332 | 3.7173 | 2.4158 | 2.4158 | 0.4450 | 0.0000 | 2.6366 | 0.1104 | 4 | 2.5262 | 26 | 6.2435 | 3.6070 | 1.0000 |
| CU | 3-star | 2.0000 | Naive | 30 | 14.2285 | 10.5566 | 3.6719 | 3.6719 | 1.4372 | 0.0000 | 7.2952 | 1.7113 | 10 | 5.3831 | 20 | 15.9397 | 8.8453 | 1.0000 |
| Do | 2-star | 2.0000 | Naive | 30 | 6.9708 | 3.2776 | 3.6932 | 3.6932 | 0.7165 | 0.0000 | 4.2404 | 0.2553 | 6 | 3.9485 | 24 | 7.2261 | 3.0223 | 1.0000 |
| Do | 3-star | 2.0000 | Naive | 30 | 8.4123 | 7.0127 | 1.3996 | 1.3996 | 1.8725 | 0.0000 | 4.6502 | 1.5018 | 15 | 2.9014 | 15 | 9.9141 | 5.5109 | 1.0000 |
