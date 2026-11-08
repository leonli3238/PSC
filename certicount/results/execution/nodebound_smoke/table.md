# P4 methods and execution modes on identical noise

provider = mock, node = gpt-4.1-mini, curator = gpt-4.1, mock error rate = 0.0, ε = 2.0, runs: LLM 200 / DSL 200 / code 200 (noise of run i: seed [0, i]), r1 = 0.5, r2 = 0.2. Design: exact (3 draft(s) x 1 restart(s)), designer temperature = 0.0. Edge-clipping α = 0. Out-of-library tasks: 4-star, 5-star, degree-moment2.

## Mean relative error by method

Lower is better (|estimate − truth| / truth, averaged over runs).

| dataset | task | eps | GT-PSC | GT-DSL | GT-DSL-node |
|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | 0.1487 | 0.1487 | 0.3516 |
| CU | 3-star | 2.0000 | 0.7089 | 0.7089 | 0.4234 |
| CU | 4-star | 2.0000 | - | 2.8841 | 0.7434 |
| CU | triangle | 2.0000 | 0.9492 | 1.0097 | 1.0033 |
| Do | 2-star | 2.0000 | 0.0855 | 0.0855 | 0.2869 |
| Do | 3-star | 2.0000 | 0.3137 | 0.3137 | 0.3325 |
| Do | 4-star | 2.0000 | - | 0.8459 | 0.3880 |
| Do | triangle | 2.0000 | 0.8122 | 0.8523 | 0.7795 |

## Goal 1: methods

`rule_relative_error`: the paired code value on the same noise (GT-Naive for Naive, GT-PSC for PSC, the program itself for DSL); `llm_error` = relative_error − rule_relative_error (execution error added by the LLM; 0 for DSL by construction). `se`: standard error of the mean. GT-* rows are code-only references over 200 runs; GT-Naive / GT-PSC draw the RR noise in another order than the agents (equal in distribution, not run by run), GT-DSL / GT-Tuned in the same order as `program`. GT-Tuned: the library algorithm with its threshold factor and budget split grid-tuned on public synthetic graphs (same scorer as the DSL search).

| dataset | task | eps | method | runs | rejected | relative_error | se | median_relative_error | rule_relative_error | llm_error | llm_calls | node_llm_calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | GT-PSC | 200 | 0 | 0.1487 | 0.0086 | 0.1147 | - | - | 0.0000 | 0.0000 |
| CU | 2-star | 2.0000 | GT-DSL | 200 | 0 | 0.1487 | 0.0086 | 0.1147 | - | - | 0.0000 | 0.0000 |
| CU | 2-star | 2.0000 | GT-DSL-node | 200 | 0 | 0.3516 | 0.0063 | 0.3514 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | 2.0000 | GT-PSC | 200 | 0 | 0.7089 | 0.0473 | 0.5516 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | 2.0000 | GT-DSL | 200 | 0 | 0.7089 | 0.0473 | 0.5516 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | 2.0000 | GT-DSL-node | 200 | 0 | 0.4234 | 0.0147 | 0.4160 | - | - | 0.0000 | 0.0000 |
| CU | 4-star | 2.0000 | GT-DSL | 200 | 0 | 2.8841 | 0.3504 | 1.0000 | - | - | 0.0000 | 0.0000 |
| CU | 4-star | 2.0000 | GT-DSL-node | 200 | 0 | 0.7434 | 0.0526 | 0.6441 | - | - | 0.0000 | 0.0000 |
| CU | triangle | 2.0000 | GT-PSC | 200 | 0 | 0.9492 | 0.0569 | 0.9392 | - | - | 0.0000 | 0.0000 |
| CU | triangle | 2.0000 | GT-DSL | 200 | 0 | 1.0097 | 0.0626 | 1.0000 | - | - | 0.0000 | 0.0000 |
| CU | triangle | 2.0000 | GT-DSL-node | 200 | 0 | 1.0033 | 0.0669 | 1.0000 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | 2.0000 | GT-PSC | 200 | 0 | 0.0855 | 0.0048 | 0.0729 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | 2.0000 | GT-DSL | 200 | 0 | 0.0855 | 0.0048 | 0.0729 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | 2.0000 | GT-DSL-node | 200 | 0 | 0.2869 | 0.0053 | 0.2862 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | 2.0000 | GT-PSC | 200 | 0 | 0.3137 | 0.0196 | 0.2341 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | 2.0000 | GT-DSL | 200 | 0 | 0.3137 | 0.0196 | 0.2341 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | 2.0000 | GT-DSL-node | 200 | 0 | 0.3325 | 0.0093 | 0.3258 | - | - | 0.0000 | 0.0000 |
| Do | 4-star | 2.0000 | GT-DSL | 200 | 0 | 0.8459 | 0.0652 | 0.6562 | - | - | 0.0000 | 0.0000 |
| Do | 4-star | 2.0000 | GT-DSL-node | 200 | 0 | 0.3880 | 0.0169 | 0.3483 | - | - | 0.0000 | 0.0000 |
| Do | triangle | 2.0000 | GT-PSC | 200 | 0 | 0.8122 | 0.0438 | 0.7722 | - | - | 0.0000 | 0.0000 |
| Do | triangle | 2.0000 | GT-DSL | 200 | 0 | 0.8523 | 0.0433 | 0.8302 | - | - | 0.0000 | 0.0000 |
| Do | triangle | 2.0000 | GT-DSL-node | 200 | 0 | 0.7795 | 0.0416 | 0.7478 | - | - | 0.0000 | 0.0000 |

## Details

| dataset | task | eps | mode | runs | relative_error | rule_relative_error | exec_exact | node_e2e_acc | aggregate_acc | llm_calls | node_llm_calls | rejected_messages | violations | ci_covers_truth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | gt-psc | 200 | 0.1487 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | 2-star | 2.0000 | gt-dsl | 200 | 0.1487 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | 2-star | 2.0000 | gt-dsl-node | 200 | 0.3516 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | 3-star | 2.0000 | gt-psc | 200 | 0.7089 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | 3-star | 2.0000 | gt-dsl | 200 | 0.7089 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | 3-star | 2.0000 | gt-dsl-node | 200 | 0.4234 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | 4-star | 2.0000 | gt-dsl | 200 | 2.8841 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | 4-star | 2.0000 | gt-dsl-node | 200 | 0.7434 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | triangle | 2.0000 | gt-psc | 200 | 0.9492 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | triangle | 2.0000 | gt-dsl | 200 | 1.0097 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | triangle | 2.0000 | gt-dsl-node | 200 | 1.0033 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 2-star | 2.0000 | gt-psc | 200 | 0.0855 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 2-star | 2.0000 | gt-dsl | 200 | 0.0855 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 2-star | 2.0000 | gt-dsl-node | 200 | 0.2869 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 3-star | 2.0000 | gt-psc | 200 | 0.3137 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 3-star | 2.0000 | gt-dsl | 200 | 0.3137 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 3-star | 2.0000 | gt-dsl-node | 200 | 0.3325 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 4-star | 2.0000 | gt-dsl | 200 | 0.8459 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 4-star | 2.0000 | gt-dsl-node | 200 | 0.3880 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | triangle | 2.0000 | gt-psc | 200 | 0.8122 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | triangle | 2.0000 | gt-dsl | 200 | 0.8523 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | triangle | 2.0000 | gt-dsl-node | 200 | 0.7795 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
