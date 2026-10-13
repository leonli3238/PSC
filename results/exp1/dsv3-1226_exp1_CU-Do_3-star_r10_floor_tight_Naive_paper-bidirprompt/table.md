| Task | Method | CU | Do | Avg. |
|---|---|---|---|---|
| 3-star | Naive | 10.5437 | 6.6387 | 8.5912 |
| 3-star | *Naive (paper)* | *109.3320* | *46.9049* | *78.1184* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 3-star | 2.0000 | Naive | 10 | 10.5437 | 10.5680 | 0.0243 | -0.0243 | 0.0243 | 0.9000 | 0.0243 | 0.0243 | 1 | 0.0000 | 0 | 10.5680 | 10.5437 | 1.0000 |
| Do | 3-star | 2.0000 | Naive | 10 | 6.6387 | 6.6387 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 0 | 6.6387 | 6.6387 | 1.0000 |
