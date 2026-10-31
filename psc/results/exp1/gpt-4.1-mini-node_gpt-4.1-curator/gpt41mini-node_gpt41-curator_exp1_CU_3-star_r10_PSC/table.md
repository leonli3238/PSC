| Task | Method | CU | Avg. |
|---|---|---|---|
| 3-star | PSC | 1.0233 | 1.0233 |
| 3-star | *PSC (paper)* | *0.7325* | *0.7325* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 3-star | 2.0000 | PSC | 10 | 1.0233 | 1.0229 | 0.0004 | 0.0004 | 0.0004 | 0.9000 | 0.0004 | 0.0000 | 0 | 0.0004 | 1 | 1.0233 | 1.0229 | 0.3000 |
