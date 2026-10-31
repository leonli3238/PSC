| Task | Method | CU | Do | Avg. |
|---|---|---|---|---|
| 2-star | Naive | 3.7603 | 2.6185 | 3.1894 |
| 2-star | *Naive (paper)* | *10.4517* | *7.9931* | *9.2224* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | Naive | 10 | 3.7603 | 3.7404 | 0.0200 | 0.0200 | 0.0145 | 0.4000 | 0.0271 | 0.0036 | 2 | 0.0235 | 4 | 3.7639 | 3.7368 | 1.0000 |
| Do | 2-star | 2.0000 | Naive | 10 | 2.6185 | 3.1550 | 0.5365 | -0.5365 | 0.3548 | 0.2000 | 0.5504 | 0.5434 | 6 | 0.0069 | 2 | 3.1620 | 2.6116 | 1.0000 |
