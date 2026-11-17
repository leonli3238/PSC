| Task | Method | CU | Do | Avg. |
|---|---|---|---|---|
| triangle | PSC | 1.1349 | 1.0827 | 1.1088 |
| triangle | *PSC (paper)* | *0.7939* | *0.8628* | *0.8284* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | triangle | 2.0000 | PSC | 10 | 1.1349 | 1.1723 | 0.0373 | -0.0373 | 0.0778 | 0.5000 | 0.2997 | 0.0914 | 2 | 0.0540 | 3 | 1.2263 | 1.0809 | 0.6000 |
| Do | triangle | 2.0000 | PSC | 10 | 1.0827 | 0.4875 | 0.5952 | 0.5952 | 0.1769 | 0.2000 | 0.8497 | 0.0000 | 0 | 0.5952 | 8 | 1.0827 | 0.4875 | 0.2000 |
