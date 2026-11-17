| Task | Method | CU | Do | Avg. |
|---|---|---|---|---|
| triangle | TriTR | 1.0437 | 0.9934 | 1.0185 |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | triangle | 2.0000 | TriTR | 10 | 1.0437 | 0.8227 | 0.2209 | 0.2209 | 0.2380 | 0.1000 | 1.1341 | 0.1768 | 3 | 0.3977 | 6 | 1.2205 | 0.6459 | 0.5000 |
| Do | triangle | 2.0000 | TriTR | 10 | 0.9934 | 0.5959 | 0.3975 | 0.3975 | 0.1162 | 0.2000 | 0.9004 | 0.0077 | 1 | 0.4052 | 7 | 1.0011 | 0.5882 | 0.3000 |
