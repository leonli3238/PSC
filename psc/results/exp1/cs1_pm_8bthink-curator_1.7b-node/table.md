| Task | Method | PM | Avg. |
|---|---|---|---|
| degree | PSC | 104.1606 | 104.1606 |
| degree | *PSC (paper)* | *0.0666* | *0.0666* |
| 2-star | PSC | 0.8761 | 0.8761 |
| 2-star | *PSC (paper)* | *0.3508* | *0.3508* |
| 3-star | PSC | 1.1177 | 1.1177 |
| 3-star | *PSC (paper)* | *0.6904* | *0.6904* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 2.0000 | PSC | 10 | 104.1606 | 0.0033 | 104.1573 | 104.1573 | 55.4284 | 0.0000 | 104.1589 | 0.0000 | 0 | 104.1573 | 10 | 104.1606 | 0.0033 | 0.0000 |
| PM | 2-star | 2.0000 | PSC | 10 | 0.8761 | 0.0319 | 0.8443 | 0.8443 | 0.0432 | 0.0000 | 0.8644 | 0.0000 | 0 | 0.8443 | 10 | 0.8761 | 0.0319 | 0.0000 |
| PM | 3-star | 2.0000 | PSC | 10 | 1.1177 | 0.0893 | 1.0284 | 1.0284 | 0.2849 | 0.0000 | 1.0858 | 0.0000 | 0 | 1.0284 | 10 | 1.1177 | 0.0893 | 0.0000 |
