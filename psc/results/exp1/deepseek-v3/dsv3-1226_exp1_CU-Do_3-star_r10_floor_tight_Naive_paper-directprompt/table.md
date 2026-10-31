| Task | Method | CU | Do | Avg. |
|---|---|---|---|---|
| 3-star | Naive | 302.8563 | 327.8679 | 315.3621 |
| 3-star | *Naive (paper)* | *109.3320* | *46.9049* | *78.1184* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 3-star | 2.0000 | Naive | 10 | 302.8563 | 10.5680 | 292.2883 | 292.2883 | 275.6093 | 0.0000 | 296.9980 | 2.2917 | 3 | 294.5800 | 7 | 305.1480 | 8.2763 | 1.0000 |
| Do | 3-star | 2.0000 | Naive | 10 | 327.8679 | 6.6387 | 321.2292 | 321.2292 | 195.2630 | 0.0000 | 324.3920 | 1.5814 | 4 | 322.8106 | 6 | 329.4493 | 5.0573 | 1.0000 |
