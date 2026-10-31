| Task | Method | CU | Avg. |
|---|---|---|---|
| 2-star | PSC | 0.2021 | 0.2021 |
| 2-star | *PSC (paper)* | *0.0929* | *0.0929* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | PSC | 10 | 0.2021 | 0.1931 | 0.0090 | 0.0090 | 0.0085 | 0.7000 | 0.0090 | 0.0000 | 0 | 0.0090 | 3 | 0.2021 | 0.1931 | 0.0000 |
