| Task | Method | CU | Avg. |
|---|---|---|---|
| triangle | Naive | 8.4743 | 8.4743 |
| triangle | *Naive (paper)* | *9.1228* | *9.1228* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | triangle | 2.0000 | Naive | 30 | 8.4743 | 1.5164 | 6.9579 | 6.9579 | 1.1206 | 0.0000 | 7.3439 | 0.1234 | 3 | 7.0813 | 27 | 8.5977 | 1.3930 | 0.9333 |
