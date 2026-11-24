# GT-Select: the release choice with reference programs (code only)

ε = 2.0, α = 5.0, floor_tight, seed 0, 1000 runs per method (run i: noise [seed, i]). Mean relative error, lower is better.

* `GT-Naive`: the whole budget on the RR noisy graph, exact count on it (no correction).
* `GT-Rows` / `GT-DSL-node`: rows program / per-node reference program (the matrix program of a pair) alone; `GT-Oracle`: the better of the two per dataset in hindsight (not a method).
* `GT-Select-design`: design-time choice on public Holme-Kim graphs only; `GT-Select`: + run-time choice from the published noisy degrees (the CertiCount procedure). `select_rows_share`: runs of GT-Select that ran rows. `design_choice = refused`: the simulated choice releases nothing (no GT-Select value).
* `CertiCount`: all runs of the accepted LLM designs (cs9_node_generic_sim_tri_ow); `cc_rows_share`: their runs that read the rows.

| dataset | task | n | truth | runs | releases | GT-Naive | GT-Rows | GT-DSL-node | GT-Oracle | GT-Select-design | GT-Select | select_rows_share | design_choice | CertiCount | cc_rows_share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | triangle | 453 | 3284.0000 | 1000 | rows/matrix | 12.0618 | 1.5385 | 0.1591 | 0.1591 | 0.1591 | 0.1591 | 0.0000 | matrix | 0.2744 | 0.1053 |
| PM | open-wedge | 453 | 6.932e+04 | 1000 | rows/matrix | 9.6668 | 0.2497 | 0.0354 | 0.0354 | 0.0354 | 0.0354 | 0.0000 | matrix | 0.0292 | 0.0000 |
| CU | triangle | 49 | 57.0000 | 1000 | rows/matrix | 1.4339 | 0.5557 | 1.0574 | 0.5557 | 0.5557 | 0.5554 | 1.0000 | rows | 0.8537 | 0.3684 |
| CU | open-wedge | 49 | 250.0000 | 1000 | rows/matrix | 5.0468 | 0.4065 | 1.0631 | 0.4065 | 1.0631 | 0.4052 | 1.0000 | matrix | 0.7410 | 0.7435 |
| Do | triangle | 62 | 95.0000 | 1000 | rows/matrix | 1.8557 | 0.4764 | 0.7930 | 0.4764 | 0.7930 | 0.4748 | 1.0000 | matrix | 0.6119 | 0.3750 |
| Do | open-wedge | 62 | 638.0000 | 1000 | rows/matrix | 3.7815 | 0.2626 | 0.5749 | 0.2626 | 0.5749 | 0.2650 | 1.0000 | matrix | 0.4184 | 0.7680 |
| ML | triangle | 77 | 467.0000 | 1000 | rows/matrix | 0.5624 | 0.1486 | 0.2887 | 0.1486 | 0.2887 | 0.1497 | 0.9920 | matrix | 0.2296 | 0.3889 |
| ML | open-wedge | 77 | 1407.0000 | 1000 | rows/matrix | 3.2650 | 0.1391 | 0.3822 | 0.1391 | 0.3822 | 0.1591 | 0.9160 | matrix | 0.3038 | 0.7055 |
| CS | triangle | 86 | 42.0000 | 1000 | rows/matrix | 7.0034 | 0.8896 | 1.4772 | 0.8896 | 1.4772 | 0.8732 | 0.9960 | matrix | 1.3722 | 0.1563 |
| CS | open-wedge | 86 | 337.0000 | 1000 | rows/matrix | 15.3111 | 0.3891 | 0.9222 | 0.3891 | 0.9222 | 0.3915 | 0.9930 | matrix | 0.7182 | 0.4805 |
| EE | triangle | 143 | 889.0000 | 1000 | rows/matrix | 2.0047 | 0.1235 | 0.2395 | 0.1235 | 0.2395 | 0.2388 | 0.0150 | matrix | 0.2666 | 0.0053 |
| EE | open-wedge | 143 | 4760.0000 | 1000 | rows/matrix | 5.8493 | 0.1261 | 0.1762 | 0.1261 | 0.1762 | 0.1764 | 0.0020 | matrix | 0.1739 | 0.0500 |

## CertiCount against GT-Select and GT-Naive on the same runs

`cc_minus_select` / `cc_minus_naive`: mean over all (design, run) pairs of RE(CertiCount) − RE(GT-Select) / RE(GT-Naive) on run index i (negative: the LLM design is better); `identical_estimate`: share of pairs with the same estimate as GT-Select (the design behaves as the reference pair).

| dataset | task | designs | pairs | CertiCount | GT-Select (same runs) | GT-DSL-node (same runs) | GT-Naive (same runs) | cc_minus_select | se | cc_minus_naive | se_naive | identical_estimate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | triangle | 19 | 1900 | 0.2744 | 0.1263 | 0.1263 | 12.0779 | 0.1482 | 0.0100 | -11.8034 | 0.0125 | 0.8947 |
| PM | open-wedge | 20 | 2000 | 0.0292 | 0.0297 | 0.0297 | 9.6771 | -0.0004663 | 6.498e-05 | -9.6478 | 0.0036 | 0.9000 |
| CU | triangle | 19 | 1900 | 0.8537 | 0.5233 | 1.0465 | 1.4711 | 0.3304 | 0.0143 | -0.6173 | 0.0163 | 0.3874 |
| CU | open-wedge | 20 | 2000 | 0.7410 | 0.3755 | 1.0528 | 5.1291 | 0.3655 | 0.0096 | -4.3881 | 0.0181 | 0.0665 |
| Do | triangle | 16 | 1600 | 0.6119 | 0.4185 | 0.7280 | 1.8829 | 0.1935 | 0.0120 | -1.2710 | 0.0143 | 0.3750 |
| Do | open-wedge | 20 | 2000 | 0.4184 | 0.2346 | 0.5561 | 3.8197 | 0.1838 | 0.0058 | -3.4013 | 0.0110 | 0.0000 |
| ML | triangle | 18 | 1800 | 0.2296 | 0.1545 | 0.2795 | 0.5652 | 0.0752 | 0.0050 | -0.3356 | 0.0052 | 0.3333 |
| ML | open-wedge | 20 | 2000 | 0.3038 | 0.1590 | 0.3829 | 3.2747 | 0.1448 | 0.0042 | -2.9708 | 0.0070 | 0.0600 |
| CS | triangle | 19 | 1900 | 1.3722 | 0.8204 | 1.4757 | 7.0262 | 0.5518 | 0.0339 | -5.6540 | 0.0370 | 0.2084 |
| CS | open-wedge | 20 | 2000 | 0.7182 | 0.3791 | 0.8966 | 15.3323 | 0.3390 | 0.0131 | -14.6141 | 0.0255 | 0.0140 |
| EE | triangle | 19 | 1900 | 0.2666 | 0.2625 | 0.2680 | 2.0110 | 0.0040 | 0.0007684 | -1.7444 | 0.0056 | 0.9853 |
| EE | open-wedge | 20 | 2000 | 0.1739 | 0.1812 | 0.1812 | 5.8313 | -0.0073 | 0.0009758 | -5.6573 | 0.0060 | 0.8000 |

## Details

`bias`: mean signed error / truth; `rmse`: of the signed relative error; `zero_share`: estimates clamped to 0.

| dataset | task | method | runs | relative_error | se | median | p90 | bias | rmse | zero_share |
|---|---|---|---|---|---|---|---|---|---|---|
| PM | triangle | GT-Naive | 1000 | 12.0618 | 0.0092 | 12.0652 | 12.4431 | 12.0618 | 12.0653 | 0.0000 |
| PM | triangle | GT-Rows | 1000 | 1.5385 | 0.0030 | 1.5398 | 1.6570 | 1.5385 | 1.5414 | 0.0000 |
| PM | triangle | GT-DSL-node | 1000 | 0.1591 | 0.0039 | 0.1324 | 0.3300 | -0.0718 | 0.2017 | 0.0000 |
| PM | triangle | GT-Select-design | 1000 | 0.1591 | 0.0039 | 0.1324 | 0.3300 | -0.0718 | 0.2017 | 0.0000 |
| PM | triangle | GT-Select | 1000 | 0.1591 | 0.0039 | 0.1324 | 0.3300 | -0.0718 | 0.2017 | 0.0000 |
| PM | triangle | CertiCount | 1900 | 0.2744 | 0.0102 | 0.1184 | 1.3554 | 0.1353 | 0.5215 | 0.0000 |
| PM | open-wedge | GT-Naive | 1000 | 9.6668 | 0.0047 | 9.6652 | 9.8540 | 9.6668 | 9.6679 | 0.0000 |
| PM | open-wedge | GT-Rows | 1000 | 0.2497 | 0.0005069 | 0.2496 | 0.2695 | -0.2497 | 0.2502 | 0.0000 |
| PM | open-wedge | GT-DSL-node | 1000 | 0.0354 | 0.0008882 | 0.0283 | 0.0734 | -0.0207 | 0.0452 | 0.0000 |
| PM | open-wedge | GT-Select-design | 1000 | 0.0354 | 0.0008882 | 0.0283 | 0.0734 | -0.0207 | 0.0452 | 0.0000 |
| PM | open-wedge | GT-Select | 1000 | 0.0354 | 0.0008882 | 0.0283 | 0.0734 | -0.0207 | 0.0452 | 0.0000 |
| PM | open-wedge | CertiCount | 2000 | 0.0292 | 0.0005162 | 0.0244 | 0.0545 | -0.0163 | 0.0372 | 0.0000 |
| CU | triangle | GT-Naive | 1000 | 1.4339 | 0.0113 | 1.4211 | 1.8772 | 1.4339 | 1.4777 | 0.0000 |
| CU | triangle | GT-Rows | 1000 | 0.5557 | 0.0131 | 0.4850 | 1.0000 | 0.0803 | 0.6930 | 0.0750 |
| CU | triangle | GT-DSL-node | 1000 | 1.0574 | 0.0246 | 1.0000 | 2.0611 | 0.2382 | 1.3134 | 0.2960 |
| CU | triangle | GT-Select-design | 1000 | 0.5557 | 0.0131 | 0.4850 | 1.0000 | 0.0803 | 0.6930 | 0.0750 |
| CU | triangle | GT-Select | 1000 | 0.5554 | 0.0128 | 0.4880 | 1.0000 | 0.0667 | 0.6878 | 0.0820 |
| CU | triangle | CertiCount | 1900 | 0.8537 | 0.0143 | 0.8394 | 1.5277 | 0.0854 | 1.0580 | 0.2353 |
| CU | open-wedge | GT-Naive | 1000 | 5.0468 | 0.0184 | 5.0280 | 5.7888 | 5.0468 | 5.0803 | 0.0000 |
| CU | open-wedge | GT-Rows | 1000 | 0.4065 | 0.0095 | 0.3565 | 0.8905 | -0.1069 | 0.5062 | 0.0450 |
| CU | open-wedge | GT-DSL-node | 1000 | 1.0631 | 0.0248 | 1.0000 | 2.1117 | 0.2467 | 1.3216 | 0.2890 |
| CU | open-wedge | GT-Select-design | 1000 | 1.0631 | 0.0248 | 1.0000 | 2.1117 | 0.2467 | 1.3216 | 0.2890 |
| CU | open-wedge | GT-Select | 1000 | 0.4052 | 0.0093 | 0.3467 | 0.8929 | -0.1172 | 0.5014 | 0.0510 |
| CU | open-wedge | CertiCount | 2000 | 0.7410 | 0.0111 | 0.7342 | 1.2245 | -0.0051 | 0.8913 | 0.2085 |
| Do | triangle | GT-Naive | 1000 | 1.8557 | 0.0105 | 1.8421 | 2.2842 | 1.8557 | 1.8850 | 0.0000 |
| Do | triangle | GT-Rows | 1000 | 0.4764 | 0.0111 | 0.4080 | 0.9391 | 0.1843 | 0.5916 | 0.0190 |
| Do | triangle | GT-DSL-node | 1000 | 0.7930 | 0.0167 | 0.8019 | 1.3442 | -0.0051 | 0.9531 | 0.2480 |
| Do | triangle | GT-Select-design | 1000 | 0.7930 | 0.0167 | 0.8019 | 1.3442 | -0.0051 | 0.9531 | 0.2480 |
| Do | triangle | GT-Select | 1000 | 0.4748 | 0.0116 | 0.4033 | 1.0000 | 0.1974 | 0.6002 | 0.0200 |
| Do | triangle | CertiCount | 1600 | 0.6119 | 0.0115 | 0.5168 | 1.1019 | 0.0544 | 0.7654 | 0.1688 |
| Do | open-wedge | GT-Naive | 1000 | 3.7815 | 0.0110 | 3.7751 | 4.2335 | 3.7815 | 3.7976 | 0.0000 |
| Do | open-wedge | GT-Rows | 1000 | 0.2626 | 0.0062 | 0.2305 | 0.5227 | -0.2001 | 0.3275 | 0.0020 |
| Do | open-wedge | GT-DSL-node | 1000 | 0.5749 | 0.0123 | 0.5347 | 1.0000 | -0.0619 | 0.6948 | 0.1310 |
| Do | open-wedge | GT-Select-design | 1000 | 0.5749 | 0.0123 | 0.5347 | 1.0000 | -0.0619 | 0.6948 | 0.1310 |
| Do | open-wedge | GT-Select | 1000 | 0.2650 | 0.0060 | 0.2325 | 0.5288 | -0.1938 | 0.3262 | 0.0010 |
| Do | open-wedge | CertiCount | 2000 | 0.4184 | 0.0068 | 0.3597 | 0.9370 | -0.1346 | 0.5177 | 0.0480 |
| ML | triangle | GT-Naive | 1000 | 0.5624 | 0.0042 | 0.5610 | 0.7238 | 0.5624 | 0.5781 | 0.0000 |
| ML | triangle | GT-Rows | 1000 | 0.1486 | 0.0035 | 0.1225 | 0.3054 | -0.0956 | 0.1848 | 0.0000 |
| ML | triangle | GT-DSL-node | 1000 | 0.2887 | 0.0070 | 0.2375 | 0.5995 | -0.1304 | 0.3644 | 0.0080 |
| ML | triangle | GT-Select-design | 1000 | 0.2887 | 0.0070 | 0.2375 | 0.5995 | -0.1304 | 0.3644 | 0.0080 |
| ML | triangle | GT-Select | 1000 | 0.1497 | 0.0037 | 0.1247 | 0.3075 | -0.0877 | 0.1903 | 0.0000 |
| ML | triangle | CertiCount | 1800 | 0.2296 | 0.0046 | 0.1705 | 0.5343 | -0.1274 | 0.3012 | 0.0000 |
| ML | open-wedge | GT-Naive | 1000 | 3.2650 | 0.0081 | 3.2655 | 3.5772 | 3.2650 | 3.2750 | 0.0000 |
| ML | open-wedge | GT-Rows | 1000 | 0.1391 | 0.0034 | 0.1204 | 0.2938 | -0.0711 | 0.1757 | 0.0000 |
| ML | open-wedge | GT-DSL-node | 1000 | 0.3822 | 0.0091 | 0.3215 | 0.8112 | -0.0206 | 0.4774 | 0.0240 |
| ML | open-wedge | GT-Select-design | 1000 | 0.3822 | 0.0091 | 0.3215 | 0.8112 | -0.0206 | 0.4774 | 0.0240 |
| ML | open-wedge | GT-Select | 1000 | 0.1591 | 0.0046 | 0.1248 | 0.3216 | -0.0647 | 0.2157 | 0.0020 |
| ML | open-wedge | CertiCount | 2000 | 0.3038 | 0.0051 | 0.2596 | 0.5938 | -0.1029 | 0.3812 | 0.0015 |
| CS | triangle | GT-Naive | 1000 | 7.0034 | 0.0304 | 6.9524 | 8.2619 | 7.0034 | 7.0688 | 0.0000 |
| CS | triangle | GT-Rows | 1000 | 0.8896 | 0.0222 | 0.7930 | 1.7746 | 0.3242 | 1.1326 | 0.1550 |
| CS | triangle | GT-DSL-node | 1000 | 1.4772 | 0.0433 | 1.0000 | 3.4033 | 0.6262 | 2.0134 | 0.3500 |
| CS | triangle | GT-Select-design | 1000 | 1.4772 | 0.0433 | 1.0000 | 3.4033 | 0.6262 | 2.0134 | 0.3500 |
| CS | triangle | GT-Select | 1000 | 0.8732 | 0.0216 | 0.8646 | 1.7626 | 0.2787 | 1.1076 | 0.1720 |
| CS | triangle | CertiCount | 1900 | 1.3722 | 0.0322 | 1.0000 | 2.7615 | 0.7284 | 1.9630 | 0.2505 |
| CS | open-wedge | GT-Naive | 1000 | 15.3111 | 0.0354 | 15.2908 | 16.8080 | 15.3111 | 15.3518 | 0.0000 |
| CS | open-wedge | GT-Rows | 1000 | 0.3891 | 0.0089 | 0.3267 | 0.8471 | -0.1418 | 0.4811 | 0.0400 |
| CS | open-wedge | GT-DSL-node | 1000 | 0.9222 | 0.0225 | 0.9536 | 1.7729 | 0.1744 | 1.1637 | 0.2590 |
| CS | open-wedge | GT-Select-design | 1000 | 0.9222 | 0.0225 | 0.9536 | 1.7729 | 0.1744 | 1.1637 | 0.2590 |
| CS | open-wedge | GT-Select | 1000 | 0.3915 | 0.0090 | 0.3428 | 0.8192 | -0.1644 | 0.4834 | 0.0420 |
| CS | open-wedge | CertiCount | 2000 | 0.7182 | 0.0130 | 0.6535 | 1.0930 | 0.0630 | 0.9234 | 0.2125 |
| EE | triangle | GT-Naive | 1000 | 2.0047 | 0.0050 | 1.9978 | 2.2127 | 2.0047 | 2.0110 | 0.0000 |
| EE | triangle | GT-Rows | 1000 | 0.1235 | 0.0031 | 0.1030 | 0.2526 | -0.0178 | 0.1571 | 0.0000 |
| EE | triangle | GT-DSL-node | 1000 | 0.2395 | 0.0056 | 0.2052 | 0.4791 | -0.1268 | 0.2970 | 0.0000 |
| EE | triangle | GT-Select-design | 1000 | 0.2395 | 0.0056 | 0.2052 | 0.4791 | -0.1268 | 0.2970 | 0.0000 |
| EE | triangle | GT-Select | 1000 | 0.2388 | 0.0055 | 0.2044 | 0.4757 | -0.1283 | 0.2963 | 0.0000 |
| EE | triangle | CertiCount | 1900 | 0.2666 | 0.0043 | 0.2327 | 0.5102 | -0.1811 | 0.3250 | 0.0000 |
| EE | open-wedge | GT-Naive | 1000 | 5.8493 | 0.0076 | 5.8463 | 6.1635 | 5.8493 | 5.8542 | 0.0000 |
| EE | open-wedge | GT-Rows | 1000 | 0.1261 | 0.0024 | 0.1251 | 0.2285 | -0.1196 | 0.1476 | 0.0000 |
| EE | open-wedge | GT-DSL-node | 1000 | 0.1762 | 0.0041 | 0.1505 | 0.3659 | -0.0465 | 0.2186 | 0.0000 |
| EE | open-wedge | GT-Select-design | 1000 | 0.1762 | 0.0041 | 0.1505 | 0.3659 | -0.0465 | 0.2186 | 0.0000 |
| EE | open-wedge | GT-Select | 1000 | 0.1764 | 0.0041 | 0.1507 | 0.3652 | -0.0474 | 0.2186 | 0.0000 |
| EE | open-wedge | CertiCount | 2000 | 0.1739 | 0.0028 | 0.1485 | 0.3599 | -0.0863 | 0.2150 | 0.0000 |
