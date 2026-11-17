| Task | Method | PM | Avg. |
|---|---|---|---|
| 2-star | PSC | 0.8888 | 0.8888 |
| 2-star | *PSC (paper)* | *0.3508* | *0.3508* |
| 3-star | PSC | 0.8039 | 0.8039 |
| 3-star | *PSC (paper)* | *0.6904* | *0.6904* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 2-star | 2.0000 | PSC | 5 | 0.8888 | 0.0242 | 0.8646 | 0.8646 | 0.1032 | 0.0000 | 0.8907 | 0.0000 | 0 | 0.8646 | 5 | 0.8888 | 0.0242 | 0.0000 |
| PM | 3-star | 2.0000 | PSC | 5 | 0.8039 | 0.0669 | 0.7370 | 0.7370 | 0.2026 | 0.0000 | 0.7971 | 0.0134 | 1 | 0.7503 | 4 | 0.8172 | 0.0535 | 0.0000 |
