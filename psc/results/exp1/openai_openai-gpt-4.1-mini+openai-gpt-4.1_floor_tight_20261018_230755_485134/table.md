| Task | Method | Do | Avg. |
|---|---|---|---|
| degree | PSC | 0.0333 | 0.0333 |
| degree | *PSC (paper)* | *0.0162* | *0.0162* |
| 2-star | PSC | 0.1316 | 0.1316 |
| 2-star | *PSC (paper)* | *0.0679* | *0.0679* |
| 3-star | PSC | 0.5984 | 0.5984 |
| 3-star | *PSC (paper)* | *0.3816* | *0.3816* |
| triangle | PSC | 0.5724 | 0.5724 |
| triangle | *PSC (paper)* | *0.8628* | *0.8628* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Do | degree | 2.0000 | PSC | 10 | 0.0333 | 0.0139 | 0.0194 | 0.0194 | 0.0191 | 0.8000 | 0.0196 | 0.0000 | 0 | 0.0194 | 2 | 0.0333 | 0.0139 | 0.0000 |
| Do | 2-star | 2.0000 | PSC | 10 | 0.1316 | 0.1295 | 0.0021 | 0.0021 | 0.0069 | 0.6000 | 0.0132 | 0.0038 | 1 | 0.0059 | 3 | 0.1354 | 0.1257 | 0.0000 |
| Do | 3-star | 2.0000 | PSC | 10 | 0.5984 | 0.4907 | 0.1078 | 0.1078 | 0.0557 | 0.5000 | 0.1078 | 0.0000 | 0 | 0.1078 | 5 | 0.5984 | 0.4907 | 0.0000 |
| Do | triangle | 2.0000 | PSC | 10 | 0.5724 | 0.4875 | 0.0848 | 0.0848 | 0.0923 | 0.2000 | 0.1023 | 0.0087 | 3 | 0.0936 | 5 | 0.5811 | 0.4788 | 0.2000 |
