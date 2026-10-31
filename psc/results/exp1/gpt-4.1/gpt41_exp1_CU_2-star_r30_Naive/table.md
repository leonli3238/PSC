| Task | Method | CU | Avg. |
|---|---|---|---|
| 2-star | Naive | 7.2214 | 7.2214 |
| 2-star | *Naive (paper)* | *10.4517* | *10.4517* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | Naive | 30 | 7.2214 | 3.7173 | 3.5040 | 3.5040 | 0.7548 | 0.0000 | 3.5987 | 0.0473 | 3 | 3.5514 | 27 | 7.2687 | 3.6700 | 1.0000 |
