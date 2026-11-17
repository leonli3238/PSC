| Task | Method | PM | Avg. |
|---|---|---|---|
| 2-star | TriTR | 0.9272 | 0.9272 |
| 3-star | TriTR | 0.9882 | 0.9882 |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 2-star | 2.0000 | TriTR | 10 | 0.9272 | 0.0079 | 0.9192 | 0.9192 | 0.0414 | 0.0000 | 0.9195 | 0.0000 | 0 | 0.9192 | 10 | 0.9272 | 0.0079 | 0.0000 |
| PM | 3-star | 2.0000 | TriTR | 10 | 0.9882 | 0.0060 | 0.9822 | 0.9822 | 0.0125 | 0.0000 | 0.9867 | 0.0000 | 0 | 0.9822 | 10 | 0.9882 | 0.0060 | 0.0000 |
