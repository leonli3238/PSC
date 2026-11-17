# Mechanism vs execution error

relative_error = rule_relative_error + delta_signed; delta_signed = llm_harm - lucky_gain (paired, same noise).

| source | dataset | task | method | runs | relative_error | rule_relative_error | delta_signed | se_delta_signed | exec_exact | lucky_gain | llm_harm | node_e2e_acc | aggregate_acc | ci_covers_truth | ci_covers_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ../psc/results/exp1/cs1_pm_8bthink-curator_1.7b-node | PM | 2-star | PSC | 10 | 0.8761 | 0.0319 | 0.8443 | 0.0432 | 0.0000 | 0.0000 | 0.8443 | 0.9336 | 0.0000 | 0.0000 | 0.0000 |
| ../psc/results/exp1/cs1_pm_8bthink-curator_1.7b-node | PM | 3-star | PSC | 10 | 1.1177 | 0.0893 | 1.0284 | 0.2849 | 0.0000 | 0.0000 | 1.0284 | 0.9095 | 0.0000 | 0.0000 | 0.3000 |
| ../psc/results/exp1/cs1_pm_8bthink-curator_1.7b-node | PM | degree | PSC | 10 | 104.1606 | 0.0033 | 104.1573 | 55.4284 | 0.0000 | 0.0000 | 104.1573 | 0.9333 | 0.0000 | 0.0000 | 0.0000 |
| ../psc/results/exp1/cs1_cudo_triangle_8bthink-curator_1.7b-node | CU | triangle | PSC | 10 | 1.1349 | 1.1723 | -0.0373 | 0.0778 | 0.5000 | 0.0914 | 0.0540 | 0.0918 | 0.8000 | 0.6000 | 0.8000 |
| ../psc/results/exp1/cs1_cudo_triangle_8bthink-curator_1.7b-node | Do | triangle | PSC | 10 | 1.0827 | 0.4875 | 0.5952 | 0.1769 | 0.2000 | 0.0000 | 0.5952 | 0.0468 | 0.4000 | 1.0000 | 1.0000 |
