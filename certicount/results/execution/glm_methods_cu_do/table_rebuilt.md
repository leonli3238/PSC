# P4 methods and execution modes on identical noise

Rebuilt from `glm_methods_cu_do` with the fixed metrics (72 run(s) changed; see `runs_rebuilt.jsonl`, field `rebuilt`). Settings: provider = openai, node_model = glm-5.2, curator_model = glm-5.2, eps = 2.0, runs = 10, seed = 0.

## Mean relative error by method

Lower is better (|estimate − truth| / truth, averaged over runs).

| dataset | task | eps | GT-Naive | Naive | GT-PSC | PSC | GT-DSL | PSC[program] |
|---|---|---|---|---|---|---|---|---|
| CU | degree | 2.0000 | 1.0650 | 0.8861 | 0.0187 | 0.0418 | 0.0187 | 0.0286 |
| CU | 2-star | 2.0000 | 3.5793 | 2.2071 | 0.1508 | 0.2199 | 0.1508 | 0.1931 |
| CU | 3-star | 2.0000 | 9.9833 | 6.2555 | 0.6961 | 1.0218 | 0.6961 | 1.0229 |
| CU | triangle | 2.0000 | 1.4339 | 10.1632 | 0.9895 | 1.1312 | 0.9854 | - |
| Do | degree | 2.0000 | 1.1762 | 0.7968 | 0.0140 | 0.0229 | 0.0140 | 0.0237 |
| Do | 2-star | 2.0000 | 3.1869 | 1.4028 | 0.0925 | 0.1326 | 0.0925 | 0.1377 |
| Do | 3-star | 2.0000 | 6.7146 | 2.7465 | 0.3380 | 0.3945 | 0.3380 | 0.4907 |
| Do | triangle | 2.0000 | 1.8557 | 3.5674 | 0.8371 | 0.5681 | 0.8649 | 0.7657 |

## Goal 1: methods

`rule_relative_error`: the paired code value on the same noise (GT-Naive for Naive, GT-PSC for PSC, the program itself for DSL); `llm_error` = relative_error − rule_relative_error (execution error added by the LLM; 0 for DSL by construction). `se`: standard error of the mean. GT-* rows are code-only references over 1000 runs; GT-Naive / GT-PSC draw the RR noise in another order than the agents (equal in distribution, not run by run), GT-DSL / GT-Tuned in the same order as `program`. GT-Tuned: the library algorithm with its threshold factor and budget split grid-tuned on public synthetic graphs (same scorer as the DSL search).

| dataset | task | eps | method | runs | rejected | relative_error | se | median_relative_error | rule_relative_error | llm_error | llm_calls | node_llm_calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | degree | 2.0000 | GT-Naive | 1000 | 0 | 1.0650 | 0.0033 | 1.0654 | - | - | 0.0000 | 0.0000 |
| CU | degree | 2.0000 | Naive | 10 | 0 | 0.8861 | 0.1193 | 0.8131 | 1.0991 | -0.2129 | 2.0000 | 0.0000 |
| CU | degree | 2.0000 | GT-PSC | 1000 | 0 | 0.0187 | 0.0004594 | 0.0159 | - | - | 0.0000 | 0.0000 |
| CU | degree | 2.0000 | PSC | 10 | 0 | 0.0418 | 0.0116 | 0.0378 | 0.0160 | 0.0258 | 52.0000 | 49.0000 |
| CU | degree | 2.0000 | GT-DSL | 1000 | 0 | 0.0187 | 0.0004594 | 0.0159 | - | - | 0.0000 | 0.0000 |
| CU | degree | 2.0000 | PSC[program] | 10 | 0 | 0.0286 | 0.0053 | 0.0329 | 0.0286 | 0.0000 | 0.1000 | 0.0000 |
| CU | 2-star | 2.0000 | GT-Naive | 1000 | 0 | 3.5793 | 0.0150 | 3.5701 | - | - | 0.0000 | 0.0000 |
| CU | 2-star | 2.0000 | Naive | 10 | 0 | 2.2071 | 0.1520 | 2.2518 | 3.7404 | -1.5333 | 2.0000 | 0.0000 |
| CU | 2-star | 2.0000 | GT-PSC | 1000 | 0 | 0.1508 | 0.0040 | 0.1213 | - | - | 0.0000 | 0.0000 |
| CU | 2-star | 2.0000 | PSC | 10 | 0 | 0.2199 | 0.0575 | 0.1840 | 0.1931 | 0.0268 | 52.0000 | 49.0000 |
| CU | 2-star | 2.0000 | GT-DSL | 1000 | 0 | 0.1508 | 0.0040 | 0.1213 | - | - | 0.0000 | 0.0000 |
| CU | 2-star | 2.0000 | PSC[program] | 10 | 0 | 0.1931 | 0.0465 | 0.1913 | 0.1931 | 0.0000 | 0.3000 | 0.0000 |
| CU | 3-star | 2.0000 | GT-Naive | 1000 | 0 | 9.9833 | 0.0560 | 9.8937 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | 2.0000 | Naive | 10 | 0 | 6.2555 | 1.0118 | 6.1174 | 10.5680 | -4.3126 | 2.0000 | 0.0000 |
| CU | 3-star | 2.0000 | GT-PSC | 1000 | 0 | 0.6961 | 0.0220 | 0.5634 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | 2.0000 | PSC | 10 | 0 | 1.0218 | 0.3370 | 0.7526 | 1.0229 | -0.0011 | 52.0000 | 49.0000 |
| CU | 3-star | 2.0000 | GT-DSL | 1000 | 0 | 0.6961 | 0.0220 | 0.5634 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | 2.0000 | PSC[program] | 10 | 0 | 1.0229 | 0.3367 | 0.7547 | 1.0229 | 0.0000 | 0.3000 | 0.0000 |
| CU | triangle | 2.0000 | GT-Naive | 1000 | 0 | 1.4339 | 0.0113 | 1.4211 | - | - | 0.0000 | 0.0000 |
| CU | triangle | 2.0000 | Naive | 10 | 0 | 10.1632 | 5.5343 | 2.4474 | 1.5596 | 8.6035 | 2.0000 | 0.0000 |
| CU | triangle | 2.0000 | GT-PSC | 1000 | 0 | 0.9895 | 0.0253 | 1.0000 | - | - | 0.0000 | 0.0000 |
| CU | triangle | 2.0000 | PSC | 10 | 0 | 1.1312 | 0.2331 | 1.0000 | 1.1723 | -0.0411 | 101.0000 | 98.0000 |
| CU | triangle | 2.0000 | GT-DSL | 1000 | 0 | 0.9854 | 0.0241 | 1.0000 | - | - | 0.0000 | 0.0000 |
| CU | triangle | 2.0000 | PSC[program] | 0 | 10 | nan | - | nan | - | - | 0.3000 | - |
| Do | degree | 2.0000 | GT-Naive | 1000 | 0 | 1.1762 | 0.0027 | 1.1761 | - | - | 0.0000 | 0.0000 |
| Do | degree | 2.0000 | Naive | 10 | 0 | 0.7968 | 0.1261 | 0.8425 | 1.1673 | -0.3705 | 2.0000 | 0.0000 |
| Do | degree | 2.0000 | GT-PSC | 1000 | 0 | 0.0140 | 0.0003537 | 0.0111 | - | - | 0.0000 | 0.0000 |
| Do | degree | 2.0000 | PSC | 10 | 0 | 0.0229 | 0.0064 | 0.0154 | 0.0139 | 0.0090 | 65.0000 | 62.0000 |
| Do | degree | 2.0000 | GT-DSL | 1000 | 0 | 0.0140 | 0.0003537 | 0.0111 | - | - | 0.0000 | 0.0000 |
| Do | degree | 2.0000 | PSC[program] | 10 | 0 | 0.0237 | 0.0045 | 0.0188 | 0.0237 | 0.0000 | 0.1000 | 0.0000 |
| Do | 2-star | 2.0000 | GT-Naive | 1000 | 0 | 3.1869 | 0.0105 | 3.1804 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | 2.0000 | Naive | 10 | 0 | 1.4028 | 0.1946 | 1.4296 | 3.1550 | -1.7522 | 2.0000 | 0.0000 |
| Do | 2-star | 2.0000 | GT-PSC | 1000 | 0 | 0.0925 | 0.0023 | 0.0775 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | 2.0000 | PSC | 10 | 0 | 0.1326 | 0.0195 | 0.1160 | 0.1295 | 0.0031 | 65.0000 | 62.0000 |
| Do | 2-star | 2.0000 | GT-DSL | 1000 | 0 | 0.0925 | 0.0023 | 0.0775 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | 2.0000 | PSC[program] | 10 | 0 | 0.1377 | 0.0250 | 0.1175 | 0.1377 | 0.0000 | 0.1000 | 0.0000 |
| Do | 3-star | 2.0000 | GT-Naive | 1000 | 0 | 6.7146 | 0.0300 | 6.7042 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | 2.0000 | Naive | 10 | 0 | 2.7465 | 0.6461 | 2.9581 | 6.6387 | -3.8922 | 2.0000 | 0.0000 |
| Do | 3-star | 2.0000 | GT-PSC | 1000 | 0 | 0.3380 | 0.0090 | 0.2657 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | 2.0000 | PSC | 10 | 0 | 0.3945 | 0.0917 | 0.3167 | 0.4907 | -0.0962 | 65.0000 | 62.0000 |
| Do | 3-star | 2.0000 | GT-DSL | 1000 | 0 | 0.3380 | 0.0090 | 0.2657 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | 2.0000 | PSC[program] | 10 | 0 | 0.4907 | 0.0927 | 0.4669 | 0.4907 | 0.0000 | 0.2000 | 0.0000 |
| Do | triangle | 2.0000 | GT-Naive | 1000 | 0 | 1.8557 | 0.0105 | 1.8421 | - | - | 0.0000 | 0.0000 |
| Do | triangle | 2.0000 | Naive | 10 | 0 | 3.5674 | 1.3476 | 1.8000 | 1.8674 | 1.7000 | 2.0000 | 0.0000 |
| Do | triangle | 2.0000 | GT-PSC | 1000 | 0 | 0.8371 | 0.0218 | 0.7951 | - | - | 0.0000 | 0.0000 |
| Do | triangle | 2.0000 | PSC | 10 | 0 | 0.5681 | 0.1067 | 0.6026 | 0.4875 | 0.0805 | 127.0000 | 124.0000 |
| Do | triangle | 2.0000 | GT-DSL | 1000 | 0 | 0.8649 | 0.0209 | 0.8592 | - | - | 0.0000 | 0.0000 |
| Do | triangle | 2.0000 | PSC[program] | 10 | 0 | 0.7657 | 0.1828 | 0.7542 | 0.7657 | 0.0000 | 0.2000 | 0.0000 |

## Goal 2: the DSL design (paired with GT-DSL on the same noise)

`design_error` = relative_error − gt_dsl_relative_error (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs (both clamped to 0); `noise_ratio`: final noise |c|·GS/ε3 of the design over the reference (c: aggregate slope); `search_score`: simulated error on public synthetic graphs (search mode).

| dataset | task | eps | runs | rejected | relative_error | gt_dsl_relative_error | design_error | design_error_se | design_exact | both_zero | noise_ratio | split_match | design_mode | design_restarts | design_iterations | llm_calls_total | search_score | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | degree | 2.0000 | 10 | 0 | 0.0286 | 0.0160 | 0.0126 | 0.0081 | 0.0000 | 0.0000 | 1.2500 | 0.0000 | exact | 1 | 1 | 1 | - | Pd = project(P, D) ; deg = size(Pd) ; return deg ; aggregate: total / n |
| CU | 2-star | 2.0000 | 10 | 0 | 0.1931 | 0.1931 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | exact | 1 | 3 | 3 | - | Pd = project(P, D) ; deg = size(Pd) ; pairs = comb(deg, 2) ; return pairs ; aggregate: total |
| CU | 3-star | 2.0000 | 10 | 0 | 1.0229 | 1.0229 | 0.0000 | 0.0000 | 1.0000 | 0.1000 | 1.0000 | 1.0000 | exact | 1 | 3 | 3 | - | P_clip = project(P, D) ; deg = size(P_clip) ; return comb(deg, 3) ; aggregate: total |
| CU | triangle | 2.0000 | 0 | 10 | nan | - | - | - | - | - | - | - | exact | 1 | 3 | 3 | - | - |
| Do | degree | 2.0000 | 10 | 0 | 0.0237 | 0.0139 | 0.0098 | 0.0051 | 0.0000 | 0.0000 | 1.2500 | 0.0000 | exact | 1 | 1 | 1 | - | Pd = project(P, D) ; deg = size(Pd) ; return deg ; aggregate: total / n |
| Do | 2-star | 2.0000 | 10 | 0 | 0.1377 | 0.1295 | 0.0082 | 0.0016 | 0.0000 | 0.0000 | 1.0656 | 1.0000 | exact | 1 | 1 | 1 | - | Pclip = project(P, D) ; deg = size(Pclip) ; twostars = deg * (deg - 1) / 2 ; return twostars ; aggregate: total |
| Do | 3-star | 2.0000 | 10 | 0 | 0.4907 | 0.4907 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | exact | 1 | 2 | 2 | - | Pd = project(P, D) ; deg = size(Pd) ; return comb(deg, 3) ; aggregate: total |
| Do | triangle | 2.0000 | 10 | 0 | 0.7657 | 0.4875 | 0.2782 | 0.1390 | 0.0000 | 0.2000 | 2.0860 | 1.0000 | exact | 1 | 2 | 2 | - | Pd = project(P, D) ; tri = sum(size(Pd & N(j)) for j in Pd) ; count = tri / 6 ; return count ; aggregate: total |

## Details

| dataset | task | eps | mode | runs | relative_error | rule_relative_error | exec_exact | node_e2e_acc | aggregate_acc | llm_calls | node_llm_calls | guard_fallbacks | rejected_messages | violations | ci_covers_truth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | degree | 2.0000 | gt-naive | 1000 | 1.0650 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | degree | 2.0000 | naive | 10 | 0.8861 | 1.0991 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| CU | degree | 2.0000 | gt-psc | 1000 | 0.0187 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | degree | 2.0000 | baseline | 10 | 0.0418 | 0.0160 | 0.5000 | 1.0000 | 0.5000 | 52.0000 | 49.0000 | 0 | 0 | 0 | 1.0000 |
| CU | degree | 2.0000 | gt-dsl | 1000 | 0.0187 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | degree | 2.0000 | program | 10 | 0.0286 | 0.0286 | 1.0000 | 1.0000 | 1.0000 | 0.1000 | 0.0000 | 0 | 0 | 0 | 1.0000 |
| CU | 2-star | 2.0000 | gt-naive | 1000 | 3.5793 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | 2-star | 2.0000 | naive | 10 | 2.2071 | 3.7404 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| CU | 2-star | 2.0000 | gt-psc | 1000 | 0.1508 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | 2-star | 2.0000 | baseline | 10 | 0.2199 | 0.1931 | 0.5000 | 1.0000 | 0.5000 | 52.0000 | 49.0000 | 0 | 0 | 0 | 1.0000 |
| CU | 2-star | 2.0000 | gt-dsl | 1000 | 0.1508 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | 2-star | 2.0000 | program | 10 | 0.1931 | 0.1931 | 1.0000 | 1.0000 | 1.0000 | 0.3000 | 0.0000 | 0 | 0 | 0 | 1.0000 |
| CU | 3-star | 2.0000 | gt-naive | 1000 | 9.9833 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | 3-star | 2.0000 | naive | 10 | 6.2555 | 10.5680 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| CU | 3-star | 2.0000 | gt-psc | 1000 | 0.6961 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | 3-star | 2.0000 | baseline | 10 | 1.0218 | 1.0229 | 0.8000 | 1.0000 | 0.8000 | 52.0000 | 49.0000 | 0 | 0 | 0 | 1.0000 |
| CU | 3-star | 2.0000 | gt-dsl | 1000 | 0.6961 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | 3-star | 2.0000 | program | 10 | 1.0229 | 1.0229 | 1.0000 | 1.0000 | 1.0000 | 0.3000 | 0.0000 | 0 | 0 | 0 | 1.0000 |
| CU | triangle | 2.0000 | gt-naive | 1000 | 1.4339 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | triangle | 2.0000 | naive | 10 | 10.1632 | 1.5596 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| CU | triangle | 2.0000 | gt-psc | 1000 | 0.9895 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | triangle | 2.0000 | baseline | 10 | 1.1312 | 1.1723 | 0.4000 | 0.9735 | 0.6000 | 101.0000 | 98.0000 | 0 | 0 | 0 | 0.8000 |
| CU | triangle | 2.0000 | gt-dsl | 1000 | 0.9854 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | triangle | 2.0000 | program | 0 | nan | - | - | - | - | 0.3000 | - | - | - | - | - |
| Do | degree | 2.0000 | gt-naive | 1000 | 1.1762 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | degree | 2.0000 | naive | 10 | 0.7968 | 1.1673 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| Do | degree | 2.0000 | gt-psc | 1000 | 0.0140 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | degree | 2.0000 | baseline | 10 | 0.0229 | 0.0139 | 0.4000 | 1.0000 | 0.4000 | 65.0000 | 62.0000 | 0 | 0 | 0 | 1.0000 |
| Do | degree | 2.0000 | gt-dsl | 1000 | 0.0140 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | degree | 2.0000 | program | 10 | 0.0237 | 0.0237 | 1.0000 | 1.0000 | 1.0000 | 0.1000 | 0.0000 | 0 | 0 | 0 | 0.9000 |
| Do | 2-star | 2.0000 | gt-naive | 1000 | 3.1869 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | 2-star | 2.0000 | naive | 10 | 1.4028 | 3.1550 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| Do | 2-star | 2.0000 | gt-psc | 1000 | 0.0925 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | 2-star | 2.0000 | baseline | 10 | 0.1326 | 0.1295 | 0.5000 | 1.0000 | 0.4000 | 65.0000 | 62.0000 | 0 | 0 | 0 | 0.9000 |
| Do | 2-star | 2.0000 | gt-dsl | 1000 | 0.0925 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | 2-star | 2.0000 | program | 10 | 0.1377 | 0.1377 | 1.0000 | 1.0000 | 1.0000 | 0.1000 | 0.0000 | 0 | 0 | 0 | 0.9000 |
| Do | 3-star | 2.0000 | gt-naive | 1000 | 6.7146 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | 3-star | 2.0000 | naive | 10 | 2.7465 | 6.6387 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| Do | 3-star | 2.0000 | gt-psc | 1000 | 0.3380 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | 3-star | 2.0000 | baseline | 10 | 0.3945 | 0.4907 | 0.5000 | 0.9984 | 0.6000 | 65.0000 | 62.0000 | 0 | 0 | 0 | 0.9000 |
| Do | 3-star | 2.0000 | gt-dsl | 1000 | 0.3380 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | 3-star | 2.0000 | program | 10 | 0.4907 | 0.4907 | 1.0000 | 1.0000 | 1.0000 | 0.2000 | 0.0000 | 0 | 0 | 0 | 0.9000 |
| Do | triangle | 2.0000 | gt-naive | 1000 | 1.8557 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | triangle | 2.0000 | naive | 10 | 3.5674 | 1.8674 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| Do | triangle | 2.0000 | gt-psc | 1000 | 0.8371 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | triangle | 2.0000 | baseline | 10 | 0.5681 | 0.4875 | 0.1000 | 0.9468 | 0.6000 | 127.0000 | 124.0000 | 0 | 0 | 0 | 1.0000 |
| Do | triangle | 2.0000 | gt-dsl | 1000 | 0.8649 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | triangle | 2.0000 | program | 10 | 0.7657 | 0.7657 | 1.0000 | 1.0000 | 1.0000 | 0.2000 | 0.0000 | 0 | 0 | 0 | 1.0000 |
