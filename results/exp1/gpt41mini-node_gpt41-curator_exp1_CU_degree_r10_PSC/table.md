| Task | Method | CU | Avg. |
|---|---|---|---|
| degree | PSC | 0.0167 | 0.0167 |
| degree | *PSC (paper)* | *0.0174* | *0.0174* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | degree | 2.0000 | PSC | 10 | 0.0167 | 0.0160 | 0.0007 | 0.0007 | 0.0005 | 0.8000 | 0.0011 | 0.0000 | 0 | 0.0008 | 2 | 0.0167 | 0.0160 | 0.0000 |
