| Task | Method | CU | Avg. |
|---|---|---|---|
| triangle | PSC | 1.1732 | 1.1732 |
| triangle | *PSC (paper)* | *0.7939* | *0.7939* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | triangle | 2.0000 | PSC | 10 | 1.1732 | 1.1723 | 0.0009 | 0.0009 | 0.0013 | 0.6000 | 0.0020 | 0.0006 | 2 | 0.0015 | 2 | 1.1737 | 1.1717 | 0.6000 |
