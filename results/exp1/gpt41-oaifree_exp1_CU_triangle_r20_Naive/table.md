| Task | Method | CU | Avg. |
|---|---|---|---|
| triangle | Naive | 7.8316 | 7.8316 |
| triangle | *Naive (paper)* | *9.1228* | *9.1228* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | triangle | 2.0000 | Naive | 20 | 7.8316 | 1.5728 | 6.2588 | 6.2588 | 0.6306 | 0.0000 | 6.2588 | 0.0000 | 0 | 6.2588 | 20 | 7.8316 | 1.5728 | 0.9500 |
