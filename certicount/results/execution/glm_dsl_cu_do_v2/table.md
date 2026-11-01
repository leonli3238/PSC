# P4 methods and execution modes on identical noise

provider = openai, node = glm-5.2, curator = glm-5.2, mock error rate = 0.0, ε = 2.0, 10 runs (noise of run i: seed [0, i]). Out-of-library tasks: 4-star, 5-star, degree-moment2.

## Goal 1: methods

`rule_relative_error`: the paired code value on the same noise (GT-Naive for Naive, GT-PSC for PSC, the program itself for DSL); `llm_error` = relative_error − rule_relative_error (execution error added by the LLM). GT-* rows are the code-only references over 1000 runs; GT-Naive / GT-PSC draw the RR noise in another order than the agents (equal in distribution, not run by run), GT-DSL in the same order as `program`.

| dataset | task | method | runs | relative_error | rule_relative_error | llm_error | llm_calls | node_llm_calls |
|---|---|---|---|---|---|---|---|---|
| CU | degree | GT-DSL | 1000 | 0.0187 | - | - | 0.0000 | 0.0000 |
| CU | degree | DSL | 10 | 0.0286 | 0.0286 | 0.0000 | 0.1000 | 0.0000 |
| CU | 2-star | GT-DSL | 1000 | 0.1508 | - | - | 0.0000 | 0.0000 |
| CU | 2-star | DSL | 10 | 0.1931 | 0.1931 | 0.0000 | 0.1000 | 0.0000 |
| CU | 3-star | GT-DSL | 1000 | 0.6961 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | DSL | 10 | 1.0229 | 1.0229 | 0.0000 | 0.1000 | 0.0000 |
| CU | triangle | GT-DSL | 1000 | 0.9854 | - | - | 0.0000 | 0.0000 |
| CU | triangle | DSL | 10 | 1.9187 | 1.8551 | 0.0636 | 0.2000 | 0.0000 |
| Do | degree | GT-DSL | 1000 | 0.0140 | - | - | 0.0000 | 0.0000 |
| Do | degree | DSL | 10 | 0.0237 | 0.0237 | 0.0000 | 0.1000 | 0.0000 |
| Do | 2-star | GT-DSL | 1000 | 0.0925 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | DSL | 10 | 0.1377 | 0.2753 | -0.1377 | 0.2000 | 0.0000 |
| Do | 3-star | GT-DSL | 1000 | 0.3380 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | DSL | 10 | 0.5467 | 0.5467 | 0.0000 | 0.1000 | 0.0000 |
| Do | triangle | GT-DSL | 1000 | 0.8649 | - | - | 0.0000 | 0.0000 |
| Do | triangle | DSL | 0 | nan | - | - | - | - |

## Goal 2: error added by the DSL designer (paired with GT-DSL on the same noise)

`design_error` = relative_error − gt_dsl_relative_error; `design_exact`: share of runs whose estimate equals GT-DSL; `gs_ratio`: GS of the designed program / GS of the reference program at the run's d̂max.

| dataset | task | runs | rejected | relative_error | gt_dsl_relative_error | design_error | design_error_se | design_exact | gs_ratio | split_match | design_iterations | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | degree | 10 | 0 | 0.0286 | 0.0160 | 0.0126 | 0.0081 | 0.0000 | 1.0000 | 0.0000 | 1 | deg = size(project(P, D)) ; return deg ; aggregate: total / n |
| CU | 2-star | 10 | 0 | 0.1931 | 0.1931 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1 | deg = size(project(P, D)) ; pairs = comb(deg, 2) ; return pairs ; aggregate: total |
| CU | 3-star | 10 | 0 | 1.0229 | 1.0229 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1 | deg = size(project(P, D)) ; return clip(comb(deg, 3), 0, comb(dmax, 3)) ; aggregate: total |
| CU | triangle | 10 | 0 | 1.9187 | 1.1723 | 0.7464 | 0.5136 | 0.5000 | 2.0975 | 1.0000 | 2 | Pclip = project(P, D) ; two_hop = sum(size(Pclip & N(j)) for j in Pclip) ; triangles = two_hop / 2 ; return triangles ; aggregate: total / 3 |
| Do | degree | 10 | 0 | 0.0237 | 0.0139 | 0.0098 | 0.0051 | 0.0000 | 1.0000 | 0.0000 | 1 | Pclip = project(P, D) ; deg = size(Pclip) ; return deg ; aggregate: total / n |
| Do | 2-star | 10 | 0 | 0.1377 | 0.1295 | 0.0082 | 0.0016 | 0.0000 | 2.1313 | 1.0000 | 2 | Pclip = project(P, D) ; deg = size(Pclip) ; return deg * (deg - 1) ; aggregate: total / 2 |
| Do | 3-star | 10 | 0 | 0.5467 | 0.4907 | 0.0560 | 0.0100 | 0.0000 | 1.1409 | 1.0000 | 1 | Pclip = project(P, D) ; deg = size(Pclip) ; return clip(deg * (deg - 1) * (deg - 2) / 6, 0, comb(D, 3)) ; aggregate: total |
| Do | triangle | 0 | 10 | nan | - | - | - | - | - | - | - | - |

## Details

| dataset | task | mode | runs | relative_error | rule_relative_error | exec_exact | node_e2e_acc | aggregate_acc | llm_calls | node_llm_calls | guard_fallbacks | rejected_messages | violations | ci_covers_truth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | degree | gt-dsl | 1000 | 0.0187 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | degree | program | 10 | 0.0286 | 0.0286 | 1.0000 | 1.0000 | 1.0000 | 0.1000 | 0.0000 | 0 | 0 | 0 | 1.0000 |
| CU | 2-star | gt-dsl | 1000 | 0.1508 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | 2-star | program | 10 | 0.1931 | 0.1931 | 1.0000 | 1.0000 | 1.0000 | 0.1000 | 0.0000 | 0 | 0 | 0 | 1.0000 |
| CU | 3-star | gt-dsl | 1000 | 0.6961 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | 3-star | program | 10 | 1.0229 | 1.0229 | 1.0000 | 1.0000 | 1.0000 | 0.1000 | 0.0000 | 0 | 0 | 0 | 1.0000 |
| CU | triangle | gt-dsl | 1000 | 0.9854 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| CU | triangle | program | 10 | 1.9187 | 1.8551 | 0.6000 | 0.3204 | 1.0000 | 0.2000 | 0.0000 | 0 | 0 | 0 | 0.8000 |
| Do | degree | gt-dsl | 1000 | 0.0140 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | degree | program | 10 | 0.0237 | 0.0237 | 1.0000 | 1.0000 | 1.0000 | 0.1000 | 0.0000 | 0 | 0 | 0 | 0.9000 |
| Do | 2-star | gt-dsl | 1000 | 0.0925 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | 2-star | program | 10 | 0.1377 | 0.2753 | 0.0000 | 0.1452 | 0.0000 | 0.2000 | 0.0000 | 0 | 0 | 0 | 0.1000 |
| Do | 3-star | gt-dsl | 1000 | 0.3380 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | 3-star | program | 10 | 0.5467 | 0.5467 | 1.0000 | 1.0000 | 1.0000 | 0.1000 | 0.0000 | 0 | 0 | 0 | 0.9000 |
| Do | triangle | gt-dsl | 1000 | 0.8649 | - | - | - | - | 0.0000 | 0.0000 | - | - | - | - |
| Do | triangle | program | 0 | nan | - | - | - | - | - | - | - | - | - | - |
