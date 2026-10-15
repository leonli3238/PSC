| Task | Method | CU | Avg. |
|---|---|---|---|
| degree | Naive | 1.0430 | 1.0430 |
| degree | *Naive (paper)* | *1.1020* | *1.1020* |
| 2-star | Naive | 3.7173 | 3.7173 |
| 2-star | *Naive (paper)* | *10.4517* | *10.4517* |
| 3-star | Naive | 10.2057 | 10.2057 |
| 3-star | *Naive (paper)* | *109.3320* | *109.3320* |
| triangle | Naive | 1.5175 | 1.5175 |
| triangle | *Naive (paper)* | *9.1228* | *9.1228* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | degree | 2.0000 | Naive | 30 | 1.0430 | 1.0919 | 0.0489 | -0.0489 | 0.0340 | 0.8667 | 0.0908 | 0.0490 | 3 | 0.0001 | 1 | 1.0920 | 1.0429 | 0.8333 |
| CU | 2-star | 2.0000 | Naive | 30 | 3.7173 | 3.7173 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 0 | 3.7173 | 3.7173 | 1.0000 |
| CU | 3-star | 2.0000 | Naive | 30 | 10.2057 | 10.5566 | 0.3509 | -0.3509 | 0.3429 | 0.8667 | 0.4228 | 0.3537 | 3 | 0.0028 | 1 | 10.5594 | 10.2029 | 1.0000 |
| CU | triangle | 2.0000 | Naive | 30 | 1.5175 | 1.5164 | 0.0012 | 0.0012 | 0.0019 | 0.8667 | 0.0035 | 0.0012 | 2 | 0.0023 | 2 | 1.5187 | 1.5152 | 0.9333 |
