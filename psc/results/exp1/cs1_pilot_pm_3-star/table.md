| Task | Method | PM | Avg. |
|---|---|---|---|
| 3-star | PSC | 0.9841 | 0.9841 |
| 3-star | *PSC (paper)* | *0.6904* | *0.6904* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 2.0000 | PSC | 1 | 0.9841 | 0.0061 | 0.9780 | 0.9780 | - | 0.0000 | 0.9780 | 0.0000 | 0 | 0.9780 | 1 | 0.9841 | 0.0061 | 0.0000 |
