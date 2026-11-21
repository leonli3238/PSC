# Mechanism vs execution error

relative_error = rule_relative_error + delta_signed; delta_signed = llm_harm - lucky_gain (paired, same noise).

| source | dataset | task | method | runs | relative_error | rule_relative_error | delta_signed | se_delta_signed | exec_exact | lucky_gain | llm_harm | node_e2e_acc | aggregate_acc | ci_covers_truth | ci_covers_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ../psc/results/exp1/cs1_pm_8bthink-curator_1.7b-node | PM | 2-star | PSC | 10 | 0.8761 | 0.0319 | 0.8443 | 0.0432 | 0.0000 | 0.0000 | 0.8443 | 0.9336 | 0.0000 | 0.0000 | 0.0000 |
| ../psc/results/exp1/cs1_pm_8bthink-curator_1.7b-node | PM | 3-star | PSC | 10 | 1.1177 | 0.0893 | 1.0284 | 0.2849 | 0.0000 | 0.0000 | 1.0284 | 0.9095 | 0.0000 | 0.0000 | 0.3000 |
| ../psc/results/exp1/cs1_pm_8bthink-curator_1.7b-node | PM | degree | PSC | 10 | 104.1606 | 0.0033 | 104.1573 | 55.4284 | 0.0000 | 0.0000 | 104.1573 | 0.9333 | 0.0000 | 0.0000 | 0.0000 |
| ../psc/results/exp1/cs1_cudo_triangle_8bthink-curator_1.7b-node | CU | triangle | PSC | 10 | 1.1349 | 1.1723 | -0.0373 | 0.0778 | 0.5000 | 0.0914 | 0.0540 | 0.0918 | 0.8000 | 0.6000 | 0.8000 |
| ../psc/results/exp1/cs1_cudo_triangle_8bthink-curator_1.7b-node | Do | triangle | PSC | 10 | 1.0827 | 0.4875 | 0.5952 | 0.1769 | 0.2000 | 0.0000 | 0.5952 | 0.0468 | 0.4000 | 1.0000 | 1.0000 |
| ../psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node | CS | 2-star | PSC | 10 | 0.5081 | 0.2928 | 0.2153 | 0.1092 | 0.0000 | 0.0032 | 0.2184 | 0.9488 | 0.5000 | 0.9000 | 0.2000 |
| ../psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node | CS | 3-star | PSC | 10 | 0.8065 | 0.7564 | 0.0501 | 0.1743 | 0.3000 | 0.1494 | 0.1996 | 0.9884 | 0.4000 | 0.9000 | 0.6000 |
| ../psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node | CS | degree | PSC | 10 | 18.4318 | 0.0184 | 18.4134 | 10.8597 | 0.1000 | 0.0018 | 18.4152 | 1.0000 | 0.1000 | 1.0000 | 0.0000 |
| ../psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node | CU | 2-star | PSC | 10 | 0.5816 | 0.1931 | 0.3885 | 0.1331 | 0.4000 | 7.544e-08 | 0.3885 | 1.0000 | 0.4000 | 1.0000 | 0.0000 |
| ../psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node | CU | 3-star | PSC | 10 | 1.1591 | 1.0229 | 0.1362 | 0.3003 | 0.0000 | 0.2211 | 0.3573 | 0.9694 | 0.0000 | 1.0000 | 0.6000 |
| ../psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node | CU | degree | PSC | 10 | 5.4178 | 0.0160 | 5.4019 | 4.0914 | 0.4000 | 6.855e-07 | 5.4019 | 1.0000 | 0.4000 | 1.0000 | 0.0000 |
| ../psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node | Do | 2-star | PSC | 10 | 0.4306 | 0.1295 | 0.3011 | 0.1412 | 0.0000 | 0.0019 | 0.3029 | 0.9694 | 0.5000 | 0.8000 | 0.0000 |
| ../psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node | Do | 3-star | PSC | 10 | 0.6915 | 0.4907 | 0.2008 | 0.0990 | 0.4000 | 1.023e-07 | 0.2008 | 0.9984 | 0.4000 | 0.9000 | 0.4000 |
| ../psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node | Do | degree | PSC | 10 | 23.4054 | 0.0139 | 23.3915 | 11.4061 | 0.1000 | 6.32e-05 | 23.3915 | 1.0000 | 0.1000 | 1.0000 | 0.0000 |
| ../psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node | EE | 2-star | PSC | 10 | 0.4382 | 0.0609 | 0.3773 | 0.1527 | 0.1000 | 0.0026 | 0.3799 | 0.8741 | 0.4000 | 1.0000 | 0.0000 |
| ../psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node | EE | 3-star | PSC | 10 | 0.8697 | 0.2370 | 0.6327 | 0.0793 | 0.0000 | 0.0000 | 0.6327 | 0.9098 | 0.1000 | 0.2000 | 0.0000 |
| ../psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node | EE | degree | PSC | 10 | 30.5186 | 0.0059 | 30.5128 | 18.0125 | 0.0000 | 0.0000 | 30.5128 | 0.8559 | 0.0000 | 0.1000 | 0.0000 |
| ../psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node | ML | 2-star | PSC | 10 | 0.3686 | 0.0864 | 0.2823 | 0.1417 | 0.0000 | 0.0016 | 0.2838 | 0.9403 | 0.7000 | 1.0000 | 0.0000 |
| ../psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node | ML | 3-star | PSC | 10 | 0.7404 | 0.2837 | 0.4566 | 0.1428 | 0.0000 | 0.0517 | 0.5084 | 0.9753 | 0.7000 | 0.5000 | 0.0000 |
| ../psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node | ML | degree | PSC | 10 | 2.5344 | 0.0077 | 2.5267 | 1.3630 | 0.0000 | 0.0009846 | 2.5277 | 0.9468 | 0.2000 | 1.0000 | 0.0000 |
| ../psc/results/exp1/cs8_psc_triangle_8bthink-curator_1.7b-node | CS | triangle | PSC | 10 | 2.4979 | 1.2766 | 1.2213 | 0.9649 | 0.2000 | 0.1532 | 1.3745 | 0.1209 | 0.7000 | 1.0000 | 1.0000 |
| ../psc/results/exp1/cs8_psc_triangle_8bthink-curator_1.7b-node | EE | triangle | PSC | 10 | 0.8934 | 0.3239 | 0.5695 | 0.0714 | 0.0000 | 0.0000 | 0.5695 | 0.0524 | 0.5000 | 0.3000 | 1.0000 |
| ../psc/results/exp1/cs8_psc_triangle_8bthink-curator_1.7b-node | ML | triangle | PSC | 10 | 0.8857 | 0.4101 | 0.4756 | 0.0912 | 0.0000 | 0.0000 | 0.4756 | 0.0455 | 0.5000 | 0.4000 | 1.0000 |
