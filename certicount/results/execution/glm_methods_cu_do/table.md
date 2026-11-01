# P4 methods and execution modes on identical noise

provider = openai, node = glm-5.2, curator = glm-5.2, mock error rate = 0.0, ε = 2.0, 10 runs (noise of run i: seed [0, i]). Out-of-library tasks: 4-star, 5-star, degree-moment2.

## Goal 1: methods

`rule_relative_error`: the paired code value on the same noise (GT-Naive for Naive, GT-PSC for PSC, the program itself for DSL); `llm_error` = relative_error − rule_relative_error (execution error added by the LLM). GT-* rows are the code-only references over 1000 runs; GT-Naive / GT-PSC draw the RR noise in another order than the agents (equal in distribution, not run by run), GT-DSL in the same order as `program`.

| dataset | task | method | runs | relative_error | rule_relative_error | llm_error | llm_calls | node_llm_calls |
|---|---|---|---|---|---|---|---|---|
| CU | degree | GT-Naive | 1000 | 1.0650 | - | - | 0.0000 | 0.0000 |
| CU | degree | Naive | 10 | 0.9796 | 1.0991 | -0.1195 | 2.0000 | 0.0000 |
| CU | degree | GT-PSC | 1000 | 0.0187 | - | - | 0.0000 | 0.0000 |
| CU | degree | PSC | 10 | 0.0418 | 0.0160 | 0.0258 | 52.0000 | 49.0000 |
| CU | degree | GT-DSL | 1000 | 0.0187 | - | - | 0.0000 | 0.0000 |
| CU | degree | DSL | 10 | 0.0286 | 0.0286 | 0.0000 | 0.1000 | 0.0000 |
| CU | 2-star | GT-Naive | 1000 | 3.5793 | - | - | 0.0000 | 0.0000 |
| CU | 2-star | Naive | 10 | 2.2071 | 3.7404 | -1.5333 | 2.0000 | 0.0000 |
| CU | 2-star | GT-PSC | 1000 | 0.1508 | - | - | 0.0000 | 0.0000 |
| CU | 2-star | PSC | 10 | 0.2199 | 0.1931 | 0.0268 | 52.0000 | 49.0000 |
| CU | 2-star | GT-DSL | 1000 | 0.1508 | - | - | 0.0000 | 0.0000 |
| CU | 2-star | DSL | 10 | 0.1931 | 0.1931 | 0.0000 | 0.3000 | 0.0000 |
| CU | 3-star | GT-Naive | 1000 | 9.9833 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | Naive | 10 | 6.2555 | 10.5680 | -4.3126 | 2.0000 | 0.0000 |
| CU | 3-star | GT-PSC | 1000 | 0.6961 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | PSC | 10 | 1.0218 | 1.0229 | -0.0011 | 52.0000 | 49.0000 |
| CU | 3-star | GT-DSL | 1000 | 0.6961 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | DSL | 10 | 1.0229 | 1.0229 | 0.0000 | 0.3000 | 0.0000 |
| CU | triangle | GT-Naive | 1000 | 1.4339 | - | - | 0.0000 | 0.0000 |
| CU | triangle | Naive | 10 | 10.1632 | 1.5596 | 8.6035 | 2.0000 | 0.0000 |
| CU | triangle | GT-PSC | 1000 | 0.9895 | - | - | 0.0000 | 0.0000 |
| CU | triangle | PSC | 10 | 1.1312 | 1.1723 | -0.0411 | 101.0000 | 98.0000 |
| CU | triangle | GT-DSL | 1000 | 0.9854 | - | - | 0.0000 | 0.0000 |
| CU | triangle | DSL | 0 | nan | - | - | - | - |
| Do | degree | GT-Naive | 1000 | 1.1762 | - | - | 0.0000 | 0.0000 |
| Do | degree | Naive | 10 | 0.7968 | 1.1673 | -0.3705 | 2.0000 | 0.0000 |
| Do | degree | GT-PSC | 1000 | 0.0140 | - | - | 0.0000 | 0.0000 |
| Do | degree | PSC | 10 | 0.0229 | 0.0139 | 0.0090 | 65.0000 | 62.0000 |
| Do | degree | GT-DSL | 1000 | 0.0140 | - | - | 0.0000 | 0.0000 |
| Do | degree | DSL | 10 | 0.0237 | 0.0237 | 0.0000 | 0.1000 | 0.0000 |
| Do | 2-star | GT-Naive | 1000 | 3.1869 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | Naive | 10 | 1.4028 | 3.1550 | -1.7522 | 2.0000 | 0.0000 |
| Do | 2-star | GT-PSC | 1000 | 0.0925 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | PSC | 10 | 0.1326 | 0.1295 | 0.0031 | 65.0000 | 62.0000 |
| Do | 2-star | GT-DSL | 1000 | 0.0925 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | DSL | 10 | 0.1377 | 0.1377 | 0.0000 | 0.1000 | 0.0000 |
| Do | 3-star | GT-Naive | 1000 | 6.7146 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | Naive | 10 | 2.7465 | 6.6387 | -3.8922 | 2.0000 | 0.0000 |
| Do | 3-star | GT-PSC | 1000 | 0.3380 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | PSC | 10 | 0.3945 | 0.4907 | -0.0962 | 65.0000 | 62.0000 |
| Do | 3-star | GT-DSL | 1000 | 0.3380 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | DSL | 10 | 0.4907 | 0.4907 | 0.0000 | 0.2000 | 0.0000 |
| Do | triangle | GT-Naive | 1000 | 1.8557 | - | - | 0.0000 | 0.0000 |
| Do | triangle | Naive | 10 | 3.5674 | 1.8674 | 1.7000 | 2.0000 | 0.0000 |
| Do | triangle | GT-PSC | 1000 | 0.8371 | - | - | 0.0000 | 0.0000 |
| Do | triangle | PSC | 10 | 0.5681 | 0.4875 | 0.0805 | 127.0000 | 124.0000 |
| Do | triangle | GT-DSL | 1000 | 0.8649 | - | - | 0.0000 | 0.0000 |
| Do | triangle | DSL | 10 | 0.7657 | 0.4075 | 0.3582 | 0.2000 | 0.0000 |

## Goal 2: error added by the DSL designer (paired with GT-DSL on the same noise)

`design_error` = relative_error − gt_dsl_relative_error; `design_exact`: share of runs whose estimate equals GT-DSL; `gs_ratio`: GS of the designed program / GS of the reference program at the run's d̂max.

| dataset | task | runs | rejected | relative_error | gt_dsl_relative_error | design_error | design_error_se | design_exact | gs_ratio | split_match | design_iterations | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | degree | 10 | 0 | 0.0286 | 0.0160 | 0.0126 | 0.0081 | 0.0000 | 1.0000 | 0.0000 | 1 | Pd = project(P, D) ; deg = size(Pd) ; return deg ; aggregate: total / n |
| CU | 2-star | 10 | 0 | 0.1931 | 0.1931 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 3 | Pd = project(P, D) ; deg = size(Pd) ; pairs = comb(deg, 2) ; return pairs ; aggregate: total |
| CU | 3-star | 10 | 0 | 1.0229 | 1.0229 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 3 | P_clip = project(P, D) ; deg = size(P_clip) ; return comb(deg, 3) ; aggregate: total |
| CU | triangle | 0 | 10 | nan | - | - | - | - | - | - | - | - |
| Do | degree | 10 | 0 | 0.0237 | 0.0139 | 0.0098 | 0.0051 | 0.0000 | 1.0000 | 0.0000 | 1 | Pd = project(P, D) ; deg = size(Pd) ; return deg ; aggregate: total / n |
| Do | 2-star | 10 | 0 | 0.1377 | 0.1295 | 0.0082 | 0.0016 | 0.0000 | 1.0656 | 1.0000 | 1 | Pclip = project(P, D) ; deg = size(Pclip) ; twostars = deg * (deg - 1) / 2 ; return twostars ; aggregate: total |
| Do | 3-star | 10 | 0 | 0.4907 | 0.4907 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 2 | Pd = project(P, D) ; deg = size(Pd) ; return comb(deg, 3) ; aggregate: total |
| Do | triangle | 10 | 0 | 0.7657 | 0.4875 | 0.2782 | 0.1390 | 0.2000 | 0.6953 | 1.0000 | 2 | Pd = project(P, D) ; tri = sum(size(Pd & N(j)) for j in Pd) ; count = tri / 6 ; return count ; aggregate: total |

## Details

| dataset | task | mode | runs | relative_error | rule_relative_error | exec_exact | node_e2e_acc | aggregate_acc | llm_calls | node_llm_calls | guard_fallbacks | rejected_messages | violations | ci_covers_truth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | degree | gt-naive | 1000 | 1.0650 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | degree | naive | 10 | 0.9796 | 1.0991 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| CU | degree | gt-psc | 1000 | 0.0187 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | degree | baseline | 10 | 0.0418 | 0.0160 | 0.5000 | 1.0000 | 0.5000 | 52.0000 | 49.0000 | 0 | 0 | 0 | 1.0000 |
| CU | degree | gt-dsl | 1000 | 0.0187 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | degree | program | 10 | 0.0286 | 0.0286 | 1.0000 | 1.0000 | 1.0000 | 0.1000 | 0.0000 | 0 | 0 | 0 | 1.0000 |
| CU | 2-star | gt-naive | 1000 | 3.5793 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | 2-star | naive | 10 | 2.2071 | 3.7404 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| CU | 2-star | gt-psc | 1000 | 0.1508 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | 2-star | baseline | 10 | 0.2199 | 0.1931 | 0.5000 | 1.0000 | 0.5000 | 52.0000 | 49.0000 | 0 | 0 | 0 | 1.0000 |
| CU | 2-star | gt-dsl | 1000 | 0.1508 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | 2-star | program | 10 | 0.1931 | 0.1931 | 1.0000 | 1.0000 | 1.0000 | 0.3000 | 0.0000 | 0 | 0 | 0 | 1.0000 |
| CU | 3-star | gt-naive | 1000 | 9.9833 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | 3-star | naive | 10 | 6.2555 | 10.5680 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| CU | 3-star | gt-psc | 1000 | 0.6961 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | 3-star | baseline | 10 | 1.0218 | 1.0229 | 0.8000 | 1.0000 | 0.8000 | 52.0000 | 49.0000 | 0 | 0 | 0 | 1.0000 |
| CU | 3-star | gt-dsl | 1000 | 0.6961 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | 3-star | program | 10 | 1.0229 | 1.0229 | 1.0000 | 1.0000 | 1.0000 | 0.3000 | 0.0000 | 0 | 0 | 0 | 1.0000 |
| CU | triangle | gt-naive | 1000 | 1.4339 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | triangle | naive | 10 | 10.1632 | 1.5596 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| CU | triangle | gt-psc | 1000 | 0.9895 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | triangle | baseline | 10 | 1.1312 | 1.1723 | 0.4000 | 0.9735 | 0.6000 | 101.0000 | 98.0000 | 0 | 0 | 0 | 0.8000 |
| CU | triangle | gt-dsl | 1000 | 0.9854 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | triangle | program | 0 | nan | - | - | - | - | - | - | - | - | - | - |
| Do | degree | gt-naive | 1000 | 1.1762 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | degree | naive | 10 | 0.7968 | 1.1673 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| Do | degree | gt-psc | 1000 | 0.0140 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | degree | baseline | 10 | 0.0229 | 0.0139 | 0.4000 | 1.0000 | 0.4000 | 65.0000 | 62.0000 | 0 | 0 | 0 | 1.0000 |
| Do | degree | gt-dsl | 1000 | 0.0140 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | degree | program | 10 | 0.0237 | 0.0237 | 1.0000 | 1.0000 | 1.0000 | 0.1000 | 0.0000 | 0 | 0 | 0 | 0.9000 |
| Do | 2-star | gt-naive | 1000 | 3.1869 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | 2-star | naive | 10 | 1.4028 | 3.1550 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| Do | 2-star | gt-psc | 1000 | 0.0925 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | 2-star | baseline | 10 | 0.1326 | 0.1295 | 0.5000 | 1.0000 | 0.4000 | 65.0000 | 62.0000 | 0 | 0 | 0 | 0.9000 |
| Do | 2-star | gt-dsl | 1000 | 0.0925 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | 2-star | program | 10 | 0.1377 | 0.1377 | 1.0000 | 1.0000 | 1.0000 | 0.1000 | 0.0000 | 0 | 0 | 0 | 0.9000 |
| Do | 3-star | gt-naive | 1000 | 6.7146 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | 3-star | naive | 10 | 2.7465 | 6.6387 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| Do | 3-star | gt-psc | 1000 | 0.3380 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | 3-star | baseline | 10 | 0.3945 | 0.4907 | 0.5000 | 0.9984 | 0.6000 | 65.0000 | 62.0000 | 0 | 0 | 0 | 0.9000 |
| Do | 3-star | gt-dsl | 1000 | 0.3380 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | 3-star | program | 10 | 0.4907 | 0.4907 | 1.0000 | 1.0000 | 1.0000 | 0.2000 | 0.0000 | 0 | 0 | 0 | 0.9000 |
| Do | triangle | gt-naive | 1000 | 1.8557 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | triangle | naive | 10 | 3.5674 | 1.8674 | 0.0000 | - | - | 2.0000 | 0.0000 | - | - | - | - |
| Do | triangle | gt-psc | 1000 | 0.8371 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | triangle | baseline | 10 | 0.5681 | 0.4875 | 0.1000 | 0.9468 | 0.6000 | 127.0000 | 124.0000 | 0 | 0 | 0 | 1.0000 |
| Do | triangle | gt-dsl | 1000 | 0.8649 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | triangle | program | 10 | 0.7657 | 0.4075 | 0.0000 | 0.2306 | 0.2000 | 0.2000 | 0.0000 | 0 | 0 | 0 | 1.0000 |
