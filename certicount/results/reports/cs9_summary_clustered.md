# CS9 summary (per-node architecture, ε = 2, Qwen3-8B thinking curator, simulated choice, α = 5)

Mean relative error, lower is better; CertiCount = all runs of the accepted designs (100 per design). `GT-Select` / `GT-Naive`: the code references of `results/execution/cs9_gt_select_r1000` on the same run indices; `cc_minus_*` = paired mean of RE(CertiCount) − RE(reference); `se_*` = its standard error over all design-run pairs as if independent, `se_*_cl` = two-way clustered by design and run index (the runs of a design share its program, the designs share the noise of run i; use this one). `vs_*`: `worse` / `better` when the difference is outside ±1.96·se_cl, else `n.s.`. `leaked = yes`: the prompt core shows a program of the task (`prompt_spec.core_leak_check`).

## 1. Prompt-core ablation: v1-alt (shows the rows programs) vs generic (shows none)

Same settings except the core; the v1-alt triangle rows are CS7/CS8 (cs7_node_v1alt_sim, cs7_node_v1alt_sim_cudo, cs8_node_v1alt_sim_mlcsee).

| dataset | task | core | leaked | designs | accept_rate | first_try_rate | mean_llm_calls | distinct_programs | same_as_reference | CertiCount | GT-Select | cc_minus_select | se_select | se_select_cl | vs_select | GT-Naive | cc_minus_naive | se_naive_cl | vs_naive |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | triangle | v1-alt | yes | 20 | 1.0000 | 0.3000 | 3.9000 | 19 | 0.0000 | 0.1967 | 0.1263 | 0.0704 | 0.0069 | 0.0683 | n.s. | 12.0779 | -11.8812 | 0.0755 | better |
| PM | triangle | generic | no | 20 | 0.9500 | 0.4500 | 4.2000 | 19 | 0.0000 | 0.2744 | 0.1263 | 0.1482 | 0.0100 | 0.0986 | n.s. | 12.0779 | -11.8034 | 0.1037 | better |
| CU | triangle | v1-alt | yes | 20 | 1.0000 | 0.1500 | 3.9000 | 19 | 0.0000 | 0.5530 | 0.5233 | 0.0297 | 0.0062 | 0.0265 | n.s. | 1.4711 | -0.9181 | 0.0502 | better |
| CU | triangle | generic | no | 20 | 0.9500 | 0.4000 | 4.4500 | 19 | 0.0000 | 0.8537 | 0.5233 | 0.3304 | 0.0143 | 0.0721 | worse | 1.4711 | -0.6173 | 0.0796 | better |
| Do | triangle | v1-alt | yes | 20 | 1.0000 | 0.4000 | 4.1000 | 19 | 0.0000 | 0.4721 | 0.4185 | 0.0536 | 0.0069 | 0.0266 | worse | 1.8829 | -1.4109 | 0.0473 | better |
| Do | triangle | generic | no | 20 | 0.8000 | 0.2500 | 4.9000 | 15 | 0.0000 | 0.6119 | 0.4185 | 0.1935 | 0.0120 | 0.0506 | worse | 1.8829 | -1.2710 | 0.0588 | better |
| ML | triangle | v1-alt | yes | 20 | 0.9500 | 0.3500 | 4.0000 | 18 | 0.0000 | 0.1808 | 0.1545 | 0.0263 | 0.0029 | 0.0125 | worse | 0.5652 | -0.3844 | 0.0184 | better |
| ML | triangle | generic | no | 20 | 0.9000 | 0.4500 | 4.4000 | 17 | 0.0000 | 0.2296 | 0.1545 | 0.0752 | 0.0050 | 0.0212 | worse | 0.5652 | -0.3356 | 0.0220 | better |
| CS | triangle | v1-alt | yes | 20 | 0.9500 | 0.4500 | 3.9000 | 19 | 0.0000 | 0.9980 | 0.8204 | 0.1776 | 0.0205 | 0.0759 | worse | 7.0262 | -6.0282 | 0.1192 | better |
| CS | triangle | generic | no | 20 | 0.9500 | 0.3500 | 4.7500 | 19 | 0.0000 | 1.3722 | 0.8204 | 0.5518 | 0.0339 | 0.1405 | worse | 7.0262 | -5.6540 | 0.1540 | better |
| EE | triangle | v1-alt | yes | 20 | 1.0000 | 0.4000 | 4.0000 | 20 | 0.0000 | 0.2432 | 0.2625 | -0.0193 | 0.0022 | 0.0112 | n.s. | 2.0110 | -1.7677 | 0.0244 | better |
| EE | triangle | generic | no | 20 | 0.9500 | 0.5500 | 4.2500 | 18 | 0.0000 | 0.2666 | 0.2625 | 0.0040 | 0.0007684 | 0.0028 | n.s. | 2.0110 | -1.7444 | 0.0238 | better |
| PM | open-wedge | v1-alt | yes | 20 | 1.0000 | 0.4500 | 5.1000 | 20 | 0.0000 | 0.0297 | 0.0297 | 0.0000 | 0.0000 | 0.0000 | n.s. | 9.6771 | -9.6474 | 0.0158 | better |
| PM | open-wedge | generic | no | 20 | 1.0000 | 0.6500 | 5.3000 | 20 | 0.0000 | 0.0292 | 0.0297 | -0.0004663 | 6.498e-05 | 0.0003164 | n.s. | 9.6771 | -9.6478 | 0.0158 | better |
| CU | open-wedge | v1-alt | yes | 20 | 1.0000 | 0.6500 | 5.3000 | 20 | 0.0000 | 0.5964 | 0.3755 | 0.2210 | 0.0050 | 0.0261 | worse | 5.1291 | -4.5326 | 0.0744 | better |
| CU | open-wedge | generic | no | 20 | 1.0000 | 0.7000 | 5.1000 | 20 | 0.0000 | 0.7410 | 0.3755 | 0.3655 | 0.0096 | 0.0460 | worse | 5.1291 | -4.3881 | 0.0813 | better |
| Do | open-wedge | v1-alt | yes | 20 | 1.0000 | 0.3500 | 5.1000 | 20 | 0.0000 | 0.3541 | 0.2346 | 0.1195 | 0.0041 | 0.0200 | worse | 3.8197 | -3.4656 | 0.0465 | better |
| Do | open-wedge | generic | no | 20 | 1.0000 | 0.6000 | 5.5000 | 20 | 0.0000 | 0.4184 | 0.2346 | 0.1838 | 0.0058 | 0.0230 | worse | 3.8197 | -3.4013 | 0.0468 | better |
| ML | open-wedge | v1-alt | yes | 20 | 1.0000 | 0.3500 | 5.1000 | 20 | 0.0000 | 0.2665 | 0.1590 | 0.1075 | 0.0038 | 0.0182 | worse | 3.2747 | -3.0082 | 0.0306 | better |
| ML | open-wedge | generic | no | 20 | 1.0000 | 0.3500 | 5.7500 | 20 | 0.0000 | 0.3038 | 0.1590 | 0.1448 | 0.0042 | 0.0155 | worse | 3.2747 | -2.9708 | 0.0289 | better |
| CS | open-wedge | v1-alt | yes | 20 | 1.0000 | 0.4500 | 5.1000 | 20 | 0.0000 | 0.5767 | 0.3791 | 0.1975 | 0.0084 | 0.0392 | worse | 15.3323 | -14.7556 | 0.1067 | better |
| CS | open-wedge | generic | no | 20 | 1.0000 | 0.6500 | 5.5000 | 20 | 0.0000 | 0.7182 | 0.3791 | 0.3390 | 0.0131 | 0.0482 | worse | 15.3323 | -14.6141 | 0.1068 | better |
| EE | open-wedge | v1-alt | yes | 20 | 1.0000 | 0.4000 | 5.2000 | 20 | 0.0000 | 0.1812 | 0.1812 | 0.0000 | 0.0000 | 0.0000 | n.s. | 5.8313 | -5.6500 | 0.0265 | better |
| EE | open-wedge | generic | no | 20 | 1.0000 | 0.6500 | 5.3500 | 20 | 0.0000 | 0.1739 | 0.1812 | -0.0073 | 0.0009758 | 0.0037 | better | 5.8313 | -5.6573 | 0.0260 | better |

## 2. Extension tasks (generic core, PSC has no rule for them)

`truth_per_n` close to 1: the statistic is saturated (almost every node counts), an easy target for GT-Naive.

| dataset | task | n | truth | truth_per_n | designs | accept_rate | first_try_rate | CertiCount | GT-Naive | cc_minus_naive | se_naive | se_naive_cl | vs_naive | GT-DSL-node | GT-Select | cc_minus_select | se_select | se_select_cl | vs_select | design_choice |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree-ge3 | 453 | 432.0000 | 0.9536 | 20 | 1.0000 | 0.7000 | 0.0292 | 0.0486 | -0.0194 | 0.000528 | 0.0017 | better | 0.0277 | 0.0281 | 0.0011 | 0.000414 | 0.0009274 | n.s. | node |
| CU | degree-ge3 | 49 | 43.0000 | 0.8776 | 20 | 0.9500 | 0.7500 | 0.1075 | 0.1370 | -0.0294 | 0.0019 | 0.0068 | better | 0.0929 | 0.1077 | -0.0001175 | 0.0010 | 0.0015 | n.s. | node |
| Do | degree-ge3 | 62 | 47.0000 | 0.7581 | 20 | 0.9000 | 0.7500 | 0.1139 | 0.3187 | -0.2048 | 0.0020 | 0.0072 | better | 0.0947 | 0.1143 | -0.0004575 | 0.000956 | 0.0010 | n.s. | node |
| ML | degree-ge3 | 77 | 50.0000 | 0.6494 | 20 | 1.0000 | 0.7500 | 0.1175 | 0.5392 | -0.4217 | 0.0020 | 0.0080 | better | 0.0991 | 0.1179 | -0.0004278 | 0.0008812 | 0.0009257 | n.s. | node |
| CS | degree-ge3 | 86 | 35.0000 | 0.4070 | 20 | 1.0000 | 0.7500 | 0.1766 | 1.4566 | -1.2800 | 0.0028 | 0.0099 | better | 0.1484 | 0.1763 | 0.0003065 | 0.0019 | 0.0033 | n.s. | node |
| EE | degree-ge3 | 143 | 121.0000 | 0.8462 | 20 | 1.0000 | 0.8000 | 0.0602 | 0.1818 | -0.1216 | 0.0010 | 0.0035 | better | 0.0558 | 0.0585 | 0.0017 | 0.0006903 | 0.0015 | n.s. | node |
| PM | triangle-edge | 453 | 2007.0000 | 4.4305 | 20 | 0.5000 | 0.1000 | 0.1912 | 5.8524 | -5.6612 | 0.0043 | 0.0106 | better | 0.2599 | 0.1821 | 0.0090 | 0.0056 | 0.0153 | n.s. | rows |
| CU | triangle-edge | 49 | 104.0000 | 2.1224 | 20 | 0.4500 | 0.0500 | 0.4986 | 0.8628 | -0.3642 | 0.0126 | 0.0303 | better | 0.5495 | 0.4892 | 0.0094 | 0.0141 | 0.0354 | n.s. | matrix |
| Do | triangle-edge | 62 | 121.0000 | 1.9516 | 20 | 0.5500 | 0.1500 | 0.5648 | 1.5600 | -0.9952 | 0.0139 | 0.0363 | better | 0.5404 | 0.4833 | 0.0815 | 0.0166 | 0.0463 | n.s. | matrix |
| ML | triangle-edge | 77 | 232.0000 | 3.0130 | 20 | 0.4000 | 0.1000 | 0.3739 | 1.1836 | -0.8097 | 0.0097 | 0.0176 | better | 0.3889 | 0.4079 | -0.0340 | 0.0130 | 0.0290 | n.s. | rows |
| CS | triangle-edge | 86 | 86.0000 | 1.0000 | 20 | 0.4000 | 0.1000 | 0.7128 | 4.2415 | -3.5287 | 0.0214 | 0.0489 | better | 0.6841 | 0.6340 | 0.0788 | 0.0221 | 0.0509 | n.s. | rows |
| EE | triangle-edge | 143 | 579.0000 | 4.0490 | 20 | 0.3500 | 0.0500 | 0.2739 | 1.8475 | -1.5735 | 0.0073 | 0.0174 | better | 0.2871 | 0.2258 | 0.0481 | 0.0095 | 0.0229 | worse | rows |
| PM | triangle-node | 453 | 444.0000 | 0.9801 | 20 | 1.0000 | 0.4500 | 0.0743 | 0.0203 | 0.0540 | 0.0013 | 0.0045 | worse | 0.0728 | 0.0756 | -0.0014 | 0.0012 | 0.0038 | n.s. | rows |
| CU | triangle-node | 49 | 48.0000 | 0.9796 | 20 | 1.0000 | 0.3500 | 0.2167 | 0.0144 | 0.2024 | 0.0039 | 0.0132 | worse | 0.2249 | 0.2017 | 0.0151 | 0.0050 | 0.0194 | n.s. | matrix |
| Do | triangle-node | 62 | 46.0000 | 0.7419 | 20 | 1.0000 | 0.5500 | 0.2408 | 0.3354 | -0.0946 | 0.0040 | 0.0108 | better | 0.2488 | 0.2203 | 0.0205 | 0.0052 | 0.0179 | n.s. | matrix |
| ML | triangle-node | 77 | 57.0000 | 0.7403 | 20 | 1.0000 | 0.6000 | 0.2085 | 0.3451 | -0.1366 | 0.0034 | 0.0113 | better | 0.2265 | 0.2322 | -0.0237 | 0.0040 | 0.0145 | n.s. | rows |
| CS | triangle-node | 86 | 54.0000 | 0.6279 | 20 | 1.0000 | 0.7500 | 0.2692 | 0.5833 | -0.3142 | 0.0047 | 0.0123 | better | 0.2790 | 0.2411 | 0.0281 | 0.0052 | 0.0158 | n.s. | rows |
| EE | triangle-node | 143 | 130.0000 | 0.9091 | 20 | 1.0000 | 0.5500 | 0.1336 | 0.1000 | 0.0336 | 0.0021 | 0.0067 | worse | 0.1391 | 0.1173 | 0.0163 | 0.0028 | 0.0103 | n.s. | rows |

### Paired comparison over all generic-core cells (sections 1 and 2, clustered se)

| reference | cells | worse | n.s. | better | no_data |
|---|---|---|---|---|---|
| GT-Select | 30 | 9 | 20 | 1 | 0 |
| GT-Naive | 30 | 3 | 0 | 27 | 0 |

## 3. Boundary case: 4-cycle (certified, GS about D·dmax)

`usable_candidates`: certified programs whose simulated score is below the release threshold; `gt_choice = refused`: the reference program itself is not released. `stages`: design-loop outcomes of all drafts.

| dataset | task | designs | accepted | candidates | usable_candidates | median_sim_score | gt_choice | GT-Naive | GT-DSL-node | stages |
|---|---|---|---|---|---|---|---|---|---|---|
| CU | 4-cycle | 10 | 0 | 0 | 0 | - | refused | 9.9244 | 7.6044 | semantic=26, parse=25, gs_loose=4, duplicate=3, own_row=2 |
| ML | 4-cycle | 10 | 0 | 0 | 0 | - | refused | 1.6695 | 1.0122 | semantic=26, parse=18, gs_loose=6, own_row=5, duplicate=4, release=1 |
| EE | 4-cycle | 10 | 0 | 1 | 0 | 9.0880 | refused | 6.7145 | 2.1015 | semantic=26, parse=22, gs_loose=4, own_row=4, accepted=1, not_tighter=1 |

## 4. Certification and model errors

`certificate_unsound` must be 0 (run_cs9.sh stops otherwise); `api_errors`: lines of errors.jsonl (timeouts are retried, a design whose calls all fail counts as not accepted).

| tag | core | drafts | accepted | certificate_unsound | uncertified_violations | api_errors | ablation |
|---|---|---|---|---|---|---|---|
| cs9_node_generic_sim_tri_ow | generic | 302 | 142 | 0 | 107 | 72 | yes |
| cs9_node_generic_sim_ext | generic | 1551 | 586 | 0 | 360 | 19 | yes |
| cs9_node_generic_sim_4cycle | generic | 179 | 1 | 0 | 33 | 0 | yes |
| cs9_node_v1alt_sim_ow | v1-alt | 618 | 398 | 0 | 285 | 68 | yes |
