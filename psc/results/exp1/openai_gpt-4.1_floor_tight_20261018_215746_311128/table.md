| Task | Method | Do | Avg. |
|---|---|---|---|
| degree | Naive | 1.1599 | 1.1599 |
| degree | *Naive (paper)* | *1.3935* | *1.3935* |
| triangle | Naive | 5.1179 | 5.1179 |
| triangle | *Naive (paper)* | *12.9684* | *12.9684* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Do | degree | 2.0000 | Naive | 10 | 1.1599 | 1.1673 | 0.0074 | -0.0074 | 0.1060 | 0.2000 | 0.2281 | 0.1178 | 3 | 0.1103 | 5 | 1.2776 | 1.0495 | 1.0000 |
| Do | triangle | 2.0000 | Naive | 10 | 5.1179 | 1.8674 | 3.2505 | 3.2505 | 0.6186 | 0.0000 | 3.2505 | 0.0000 | 0 | 3.2505 | 10 | 5.1179 | 1.8674 | 1.0000 |
