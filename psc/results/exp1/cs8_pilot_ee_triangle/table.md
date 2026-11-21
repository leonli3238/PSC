| Task | Method | EE | Avg. |
|---|---|---|---|
| triangle | PSC | 0.9964 | 0.9964 |
| triangle | *PSC (paper)* | *0.2914* | *0.2914* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EE | triangle | 2.0000 | PSC | 1 | 0.9964 | 0.1616 | 0.8348 | 0.8348 | - | 0.0000 | 1.1580 | 0.0000 | 0 | 0.8348 | 1 | 0.9964 | 0.1616 | 0.0000 |
