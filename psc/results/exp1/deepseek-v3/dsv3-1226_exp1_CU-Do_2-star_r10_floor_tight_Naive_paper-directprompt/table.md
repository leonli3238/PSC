| Task | Method | CU | Do | Avg. |
|---|---|---|---|---|
| 2-star | Naive | 24.8014 | 123.1566 | 73.9790 |
| 2-star | *Naive (paper)* | *10.4517* | *7.9931* | *9.2224* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | Naive | 10 | 24.8014 | 3.7404 | 21.0610 | 21.0610 | 8.1568 | 0.0000 | 21.2620 | 0.1005 | 2 | 21.1615 | 8 | 24.9019 | 3.6399 | 1.0000 |
| Do | 2-star | 2.0000 | Naive | 10 | 123.1566 | 3.1550 | 120.0015 | 120.0015 | 107.7116 | 0.0000 | 120.5480 | 0.2732 | 2 | 120.2748 | 8 | 123.4298 | 2.8818 | 1.0000 |
