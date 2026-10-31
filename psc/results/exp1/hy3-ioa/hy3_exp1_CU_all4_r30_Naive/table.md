| Task | Method | CU | Avg. |
|---|---|---|---|
| degree | Naive | 1.0916 | 1.0916 |
| degree | *Naive (paper)* | *1.1020* | *1.1020* |
| 2-star | Naive | 3.7158 | 3.7158 |
| 2-star | *Naive (paper)* | *10.4517* | *10.4517* |
| 3-star | Naive | 9.9874 | 9.9874 |
| 3-star | *Naive (paper)* | *109.3320* | *109.3320* |
| triangle | Naive | 1.5175 | 1.5175 |
| triangle | *Naive (paper)* | *9.1228* | *9.1228* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | degree | 2.0000 | Naive | 30 | 1.0916 | 1.0919 | 0.0003 | -0.0003 | 0.0003 | 0.8667 | 0.0005 | 0.0004 | 3 | 0.0001 | 1 | 1.0920 | 1.0915 | 0.8333 |
| CU | 2-star | 2.0000 | Naive | 30 | 3.7158 | 3.7173 | 0.0016 | -0.0016 | 0.0016 | 0.9667 | 0.0016 | 0.0016 | 1 | 0.0000 | 0 | 3.7173 | 3.7158 | 1.0000 |
| CU | 3-star | 2.0000 | Naive | 30 | 9.9874 | 10.5566 | 0.5692 | -0.5692 | 0.3955 | 0.9000 | 0.7018 | 0.5692 | 3 | 0.0000 | 0 | 10.5566 | 9.9874 | 1.0000 |
| CU | triangle | 2.0000 | Naive | 30 | 1.5175 | 1.5164 | 0.0012 | 0.0012 | 0.0012 | 0.9667 | 0.0012 | 0.0000 | 0 | 0.0012 | 1 | 1.5175 | 1.5164 | 0.9333 |
