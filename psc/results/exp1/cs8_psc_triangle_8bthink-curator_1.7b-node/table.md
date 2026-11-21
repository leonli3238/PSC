| Task | Method | ML | CS | EE | Avg. |
|---|---|---|---|---|---|
| triangle | PSC | 0.8857 | 2.4979 | 0.8934 | 1.4256 |
| triangle | *PSC (paper)* | *0.3240* | *2.9922* | *0.2914* | *1.2025* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ML | triangle | 2.0000 | PSC | 10 | 0.8857 | 0.4101 | 0.4756 | 0.4756 | 0.0912 | 0.0000 | 0.5690 | 0.0000 | 0 | 0.4756 | 10 | 0.8857 | 0.4101 | 0.0000 |
| CS | triangle | 2.0000 | PSC | 10 | 2.4979 | 1.2766 | 1.2213 | 1.2213 | 0.9649 | 0.2000 | 1.7277 | 0.1532 | 4 | 1.3745 | 4 | 2.6511 | 1.1234 | 0.7000 |
| EE | triangle | 2.0000 | PSC | 10 | 0.8934 | 0.3239 | 0.5695 | 0.5695 | 0.0714 | 0.0000 | 0.5746 | 0.0000 | 0 | 0.5695 | 10 | 0.8934 | 0.3239 | 0.0000 |
