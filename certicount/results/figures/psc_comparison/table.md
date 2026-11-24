# CertiCount vs the PSC architecture (ε = 2)

Mean relative error, lower is better. `PSC (Qwen3)`: PSC multi-agent architecture with the CertiCount models (curator Qwen3-8B thinking, nodes Qwen3-1.7B), 10 runs. `GT-PSC (code)`: PSC rules in code, runs 0-99 (CertiCount's noise). `CertiCount`: 20 designs x 100 runs, accepted designs; degree / k-stars from CS7/CS8 (v1-alt core), triangle from CS9 (generic core, no leak). `rule` = GT-PSC on the PSC (Qwen3) runs' own noise; `llm_harm` = error the node agents add by mis-executing it.

## Per cell

| task | dataset | PSC (paper) | PSC (Qwen3) | rule | llm_harm | GT-PSC (code) | CertiCount | CC accept | CC v1-alt (leak) |
|---|---|---|---|---|---|---|---|---|---|
| degree | PM | 0.0666 | 104.16 | 0.0033 | 104.16 | 0.0030 | **0.0055** | 1.00 |  |
| degree | CU | 0.0174 | 5.4178 | 0.0160 | 5.4019 | 0.0216 | **0.0219** | 1.00 |  |
| degree | Do | 0.0162 | 23.41 | 0.0139 | 23.39 | 0.0169 | **0.0181** | 0.95 |  |
| degree | ML | 0.0110 | 2.5344 | 0.0077 | 2.5277 | 0.0116 | **0.0130** | 0.95 |  |
| degree | CS | 0.0259 | 18.43 | 0.0184 | 18.42 | 0.0249 | **0.0253** | 0.95 |  |
| degree | EE | 0.0070 | 30.52 | 0.0059 | 30.51 | 0.0057 | **0.0084** | 0.95 |  |
| 2-star | PM | 0.3508 | 0.8761 | 0.0319 | 0.8443 | 0.0443 | **0.0074** | 0.95 |  |
| 2-star | CU | 0.0929 | 0.5816 | 0.1931 | 0.3885 | 0.1408 | **0.0985** | 1.00 |  |
| 2-star | Do | 0.0679 | 0.4306 | 0.1295 | 0.3029 | 0.0863 | **0.0608** | 1.00 |  |
| 2-star | ML | 0.0563 | 0.3686 | 0.0864 | 0.2838 | 0.0850 | **0.0388** | 0.95 |  |
| 2-star | CS | 0.0800 | 0.5081 | 0.2928 | 0.2184 | 0.2002 | **0.1067** | 0.95 |  |
| 2-star | EE | 0.0349 | 0.4382 | 0.0609 | 0.3799 | 0.0499 | **0.0250** | 0.95 |  |
| 3-star | PM | 0.6904 | 1.1177 | 0.0893 | 1.0284 | 0.1227 | **0.0087** | 1.00 |  |
| 3-star | CU | 0.7325 | 1.1591 | 1.0229 | 0.3573 | 0.6632 | **0.4195** | 1.00 |  |
| 3-star | Do | 0.3816 | 0.6915 | 0.4907 | 0.2008 | 0.3125 | **0.1783** | 1.00 |  |
| 3-star | ML | 0.1703 | 0.7404 | 0.2837 | 0.5084 | 0.2686 | **0.0645** | 0.95 |  |
| 3-star | CS | 0.4711 | 0.8065 | 0.7564 | 0.1996 | 0.6120 | **0.2984** | 1.00 |  |
| 3-star | EE | 0.2445 | 0.8697 | 0.2370 | 0.6327 | 0.1918 | **0.0402** | 1.00 |  |
| triangle | PM | 0.4786 | infeasible | - | - | 0.9738 | **0.2744** | 0.95 | 0.1967 |
| triangle | CU | 0.7939 | 1.1349 | 1.1723 | 0.0540 | 0.9386 | **0.8537** | 0.95 | 0.5530 |
| triangle | Do | 0.8628 | 1.0827 | 0.4875 | 0.5952 | 0.8655 | **0.6119** | 0.80 | 0.4721 |
| triangle | ML | 0.3240 | 0.8857 | 0.4101 | 0.4756 | 0.4137 | **0.2296** | 0.90 | 0.1808 |
| triangle | CS | 2.9922 | 2.4979 | 1.2766 | 1.3745 | 1.6135 | **1.3722** | 0.95 | 0.9980 |
| triangle | EE | 0.2914 | 0.8934 | 0.3239 | 0.5695 | 0.4012 | **0.2666** | 0.95 | 0.2432 |

## Geometric mean over the datasets every method has

| task | datasets | PSC (paper) | PSC (Qwen3) | GT-PSC (code) | CertiCount | PSC (Qwen3) / CC | GT-PSC / CC | PSC (paper) / CC |
|---|---|---|---|---|---|---|---|---|
| degree | PM,CU,Do,ML,CS,EE | 0.0183 | 16.31 | 0.0110 | 0.0135 | 1209.1x | 0.82x | 1.36x |
| 2-star | PM,CU,Do,ML,CS,EE | 0.0839 | 0.5120 | 0.0878 | 0.0408 | 12.5x | 2.15x | 2.05x |
| 3-star | PM,CU,Do,ML,CS,EE | 0.3948 | 0.8802 | 0.3048 | 0.0892 | 9.9x | 3.42x | 4.42x |
| triangle | CU,Do,ML,CS,EE | 0.7200 | 1.1942 | 0.7371 | 0.5351 | 2.2x | 1.38x | 1.35x |

## Cells where CertiCount's mean is lower

| task | versus | CertiCount lower |
|---|---|---|
| degree | PSC (paper) | 2/6 |
| degree | PSC (Qwen3) | 6/6 |
| degree | GT-PSC (code) | 0/6 |
| 2-star | PSC (paper) | 4/6 |
| 2-star | PSC (Qwen3) | 6/6 |
| 2-star | GT-PSC (code) | 6/6 |
| 3-star | PSC (paper) | 6/6 |
| 3-star | PSC (Qwen3) | 6/6 |
| 3-star | GT-PSC (code) | 6/6 |
| triangle | PSC (paper) | 5/6 |
| triangle | PSC (Qwen3) | 5/5 |
| triangle | GT-PSC (code) | 6/6 |

Sources: PSC paper Table 2; dsl_eval/cs7_node_v1alt_sim; dsl_eval/cs8_node_v1alt_sim_cudo_3tasks; dsl_eval/cs8_node_v1alt_sim_mlcsee; dsl_eval/cs8_node_v1alt_sim_pm_deg2star; dsl_eval/cs9_node_generic_sim_tri_ow; execution/cs8_code_all6_r1000 (runs 0-99); psc/results/exp1/cs1_cudo_triangle_8bthink-curator_1.7b-node; psc/results/exp1/cs1_pm_8bthink-curator_1.7b-node; psc/results/exp1/cs8_psc_5ds_kstar_8bthink-curator_1.7b-node; psc/results/exp1/cs8_psc_triangle_8bthink-curator_1.7b-node
