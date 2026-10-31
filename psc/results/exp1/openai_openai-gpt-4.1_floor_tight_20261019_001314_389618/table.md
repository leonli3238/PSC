| Task | Method | Do | Avg. |
|---|---|---|---|
| 2-star | Naive | 7.4234 | 7.4234 |
| 2-star | *Naive (paper)* | *7.9931* | *7.9931* |
| 3-star | Naive | 11.9324 | 11.9324 |
| 3-star | *Naive (paper)* | *46.9049* | *46.9049* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Do | 2-star | 2.0000 | Naive | 10 | 7.4234 | 3.1550 | 4.2684 | 4.2684 | 0.9571 | 0.0000 | 4.4625 | 0.0971 | 1 | 4.3654 | 9 | 7.5205 | 3.0580 | 1.0000 |
| Do | 3-star | 2.0000 | Naive | 10 | 11.9324 | 6.6387 | 5.2937 | 5.2937 | 5.1568 | 0.0000 | 7.0521 | 0.8792 | 7 | 6.1729 | 3 | 12.8116 | 5.7595 | 1.0000 |
