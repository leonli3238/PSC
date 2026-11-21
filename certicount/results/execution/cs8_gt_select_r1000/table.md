# GT-Select: the release choice with reference programs (code only)

ε = 2.0, α = 5.0, floor_tight, seed 0, 1000 runs per method (run i: noise [seed, i]). Mean relative error, lower is better.

* `GT-Rows` / `GT-DSL-node`: rows / matrix reference program alone; `GT-Oracle`: the better of the two per dataset in hindsight (not a method).
* `GT-Select-design`: design-time choice on public Holme-Kim graphs only; `GT-Select`: + run-time choice from the published noisy degrees (the CertiCount procedure). `select_rows_share`: runs of GT-Select that ran rows.
* `CertiCount`: all runs of the accepted LLM designs (cs7_node_v1alt_sim, cs7_node_v1alt_sim_cudo, cs8_node_v1alt_sim_mlcsee); `cc_rows_share`: their runs that read the rows.

| dataset | task | n | truth | runs | GT-Rows | GT-DSL-node | GT-Oracle | GT-Select-design | GT-Select | select_rows_share | design_choice | CertiCount | cc_rows_share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | triangle | 453 | 3284.0000 | 1000 | 1.5385 | 0.1591 | 0.1591 | 0.1591 | 0.1591 | 0.0000 | matrix | 0.1967 | 0.0500 |
| CU | triangle | 49 | 57.0000 | 1000 | 0.5557 | 1.0574 | 0.5557 | 0.5557 | 0.5554 | 1.0000 | rows | 0.5530 | 0.9500 |
| Do | triangle | 62 | 95.0000 | 1000 | 0.4764 | 0.7930 | 0.4764 | 0.7930 | 0.4748 | 1.0000 | matrix | 0.4721 | 0.8500 |
| ML | triangle | 77 | 467.0000 | 1000 | 0.1486 | 0.2887 | 0.1486 | 0.2887 | 0.1497 | 0.9920 | matrix | 0.1808 | 0.7895 |
| CS | triangle | 86 | 42.0000 | 1000 | 0.8896 | 1.4772 | 0.8896 | 1.4772 | 0.8732 | 0.9960 | matrix | 0.9980 | 0.7300 |
| EE | triangle | 143 | 889.0000 | 1000 | 0.1235 | 0.2395 | 0.1235 | 0.2395 | 0.2388 | 0.0150 | matrix | 0.2432 | 0.1630 |

## CertiCount against GT-Select on the same runs

`cc_minus_select`: mean over all (design, run) pairs of RE(CertiCount) − RE(GT-Select) on run index i (negative: the LLM design beats the reference selection); `identical_estimate`: share of pairs with the same estimate (the design behaves as the reference pair).

| dataset | task | designs | pairs | CertiCount | GT-Select (same runs) | GT-DSL-node (same runs) | cc_minus_select | se | identical_estimate |
|---|---|---|---|---|---|---|---|---|---|
| PM | triangle | 20 | 2000 | 0.1967 | 0.1263 | 0.1263 | 0.0704 | 0.0069 | 0.9500 |
| CU | triangle | 20 | 2000 | 0.5530 | 0.5233 | 1.0465 | 0.0297 | 0.0062 | 0.8045 |
| Do | triangle | 20 | 2000 | 0.4721 | 0.4185 | 0.7280 | 0.0536 | 0.0069 | 0.7000 |
| ML | triangle | 19 | 1900 | 0.1808 | 0.1545 | 0.2795 | 0.0263 | 0.0029 | 0.7895 |
| CS | triangle | 19 | 1900 | 0.9980 | 0.8204 | 1.4757 | 0.1776 | 0.0205 | 0.7011 |
| EE | triangle | 20 | 2000 | 0.2432 | 0.2625 | 0.2680 | -0.0193 | 0.0022 | 0.8460 |

## Details

`bias`: mean signed error / truth; `rmse`: of the signed relative error; `zero_share`: estimates clamped to 0.

| dataset | task | method | runs | relative_error | se | median | p90 | bias | rmse | zero_share |
|---|---|---|---|---|---|---|---|---|---|---|
| PM | triangle | GT-Rows | 1000 | 1.5385 | 0.0030 | 1.5398 | 1.6570 | 1.5385 | 1.5414 | 0.0000 |
| PM | triangle | GT-DSL-node | 1000 | 0.1591 | 0.0039 | 0.1324 | 0.3300 | -0.0718 | 0.2017 | 0.0000 |
| PM | triangle | GT-Select-design | 1000 | 0.1591 | 0.0039 | 0.1324 | 0.3300 | -0.0718 | 0.2017 | 0.0000 |
| PM | triangle | GT-Select | 1000 | 0.1591 | 0.0039 | 0.1324 | 0.3300 | -0.0718 | 0.2017 | 0.0000 |
| PM | triangle | CertiCount | 2000 | 0.1967 | 0.0072 | 0.1155 | 0.3385 | 0.0489 | 0.3779 | 0.0000 |
| CU | triangle | GT-Rows | 1000 | 0.5557 | 0.0131 | 0.4850 | 1.0000 | 0.0803 | 0.6930 | 0.0750 |
| CU | triangle | GT-DSL-node | 1000 | 1.0574 | 0.0246 | 1.0000 | 2.0611 | 0.2382 | 1.3134 | 0.2960 |
| CU | triangle | GT-Select-design | 1000 | 0.5557 | 0.0131 | 0.4850 | 1.0000 | 0.0803 | 0.6930 | 0.0750 |
| CU | triangle | GT-Select | 1000 | 0.5554 | 0.0128 | 0.4880 | 1.0000 | 0.0667 | 0.6878 | 0.0820 |
| CU | triangle | CertiCount | 2000 | 0.5530 | 0.0086 | 0.5308 | 1.0000 | 0.0371 | 0.6724 | 0.1000 |
| Do | triangle | GT-Rows | 1000 | 0.4764 | 0.0111 | 0.4080 | 0.9391 | 0.1843 | 0.5916 | 0.0190 |
| Do | triangle | GT-DSL-node | 1000 | 0.7930 | 0.0167 | 0.8019 | 1.3442 | -0.0051 | 0.9531 | 0.2480 |
| Do | triangle | GT-Select-design | 1000 | 0.7930 | 0.0167 | 0.8019 | 1.3442 | -0.0051 | 0.9531 | 0.2480 |
| Do | triangle | GT-Select | 1000 | 0.4748 | 0.0116 | 0.4033 | 1.0000 | 0.1974 | 0.6002 | 0.0200 |
| Do | triangle | CertiCount | 2000 | 0.4721 | 0.0085 | 0.3913 | 1.0000 | 0.1662 | 0.6062 | 0.0420 |
| ML | triangle | GT-Rows | 1000 | 0.1486 | 0.0035 | 0.1225 | 0.3054 | -0.0956 | 0.1848 | 0.0000 |
| ML | triangle | GT-DSL-node | 1000 | 0.2887 | 0.0070 | 0.2375 | 0.5995 | -0.1304 | 0.3644 | 0.0080 |
| ML | triangle | GT-Select-design | 1000 | 0.2887 | 0.0070 | 0.2375 | 0.5995 | -0.1304 | 0.3644 | 0.0080 |
| ML | triangle | GT-Select | 1000 | 0.1497 | 0.0037 | 0.1247 | 0.3075 | -0.0877 | 0.1903 | 0.0000 |
| ML | triangle | CertiCount | 1900 | 0.1808 | 0.0034 | 0.1395 | 0.3751 | -0.1032 | 0.2350 | 0.0000 |
| CS | triangle | GT-Rows | 1000 | 0.8896 | 0.0222 | 0.7930 | 1.7746 | 0.3242 | 1.1326 | 0.1550 |
| CS | triangle | GT-DSL-node | 1000 | 1.4772 | 0.0433 | 1.0000 | 3.4033 | 0.6262 | 2.0134 | 0.3500 |
| CS | triangle | GT-Select-design | 1000 | 1.4772 | 0.0433 | 1.0000 | 3.4033 | 0.6262 | 2.0134 | 0.3500 |
| CS | triangle | GT-Select | 1000 | 0.8732 | 0.0216 | 0.8646 | 1.7626 | 0.2787 | 1.1076 | 0.1720 |
| CS | triangle | CertiCount | 1900 | 0.9980 | 0.0230 | 0.8368 | 1.8854 | 0.3565 | 1.4149 | 0.2132 |
| EE | triangle | GT-Rows | 1000 | 0.1235 | 0.0031 | 0.1030 | 0.2526 | -0.0178 | 0.1571 | 0.0000 |
| EE | triangle | GT-DSL-node | 1000 | 0.2395 | 0.0056 | 0.2052 | 0.4791 | -0.1268 | 0.2970 | 0.0000 |
| EE | triangle | GT-Select-design | 1000 | 0.2395 | 0.0056 | 0.2052 | 0.4791 | -0.1268 | 0.2970 | 0.0000 |
| EE | triangle | GT-Select | 1000 | 0.2388 | 0.0055 | 0.2044 | 0.4757 | -0.1283 | 0.2963 | 0.0000 |
| EE | triangle | CertiCount | 2000 | 0.2432 | 0.0041 | 0.2152 | 0.4879 | -0.1579 | 0.3038 | 0.0000 |
