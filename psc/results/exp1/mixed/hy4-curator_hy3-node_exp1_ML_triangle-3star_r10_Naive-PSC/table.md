| Task | Method | ML | Avg. |
|---|---|---|---|
| 3-star | Naive | 1.5867 | 1.5867 |
| 3-star | *Naive (paper)* | *9.4129* | *9.4129* |
| 3-star | PSC | 0.2837 | 0.2837 |
| 3-star | *PSC (paper)* | *0.1703* | *0.1703* |
| triangle | Naive | 0.6400 | 0.6400 |
| triangle | *Naive (paper)* | *7.4197* | *7.4197* |
| triangle | PSC | 0.4100 | 0.4100 |
| triangle | *PSC (paper)* | *0.3240* | *0.3240* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ML | triangle | 2.0000 | Naive | 10 | 0.6400 | 0.6218 | 0.0182 | 0.0182 | 0.0187 | 0.7000 | 0.1818 | 0.0004 | 2 | 0.0186 | 1 | 0.6405 | 0.6214 | 0.0000 |
| ML | triangle | 2.0000 | PSC | 10 | 0.4100 | 0.4101 | 0.0000 | -0.0000 | 0.0001 | 1.0000 | 0.0001 | 0.0001 | 0 | 0.0000 | 0 | 0.4101 | 0.4100 | 0.0000 |
| ML | 3-star | 2.0000 | Naive | 10 | 1.5867 | 2.1431 | 0.5563 | -0.5563 | 0.1931 | 0.4000 | 1.5236 | 0.5563 | 6 | 0.0000 | 0 | 2.1431 | 1.5867 | 1.0000 |
| ML | 3-star | 2.0000 | PSC | 10 | 0.2837 | 0.2837 | 0.0000 | -0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 0 | 0.2837 | 0.2837 | 0.0000 |
