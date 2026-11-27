# P4 methods and execution modes on identical noise

provider = mock, node = gpt-4.1-mini, curator = gpt-4.1, mock error rate = 0.0, ε = 2.0, runs: LLM 100 / DSL 100 / code 100 (noise of run i: seed [0, i]), r1 = 0.5, r2 = 0.2. Design: exact (3 draft(s) x 1 restart(s)), designer temperature = 0.0. Edge-clipping α = 20. Out-of-library tasks: 4-star, 5-star, degree-moment2, open-wedge, degree-ge3, triangle-node, triangle-edge, 4-cycle.

## Mean relative error by method

Lower is better (|estimate − truth| / truth, averaged over runs).

| dataset | task | eps | GT-DSL-node |
|---|---|---|---|
| CU | 2-star | 2.0000 | 0.2556 |
| CU | 3-star | 2.0000 | 1.8081 |
| CU | triangle | 2.0000 | 1.8211 |
| Do | 2-star | 2.0000 | 0.1372 |
| Do | 3-star | 2.0000 | 0.7600 |
| Do | triangle | 2.0000 | 1.2742 |
| ML | 2-star | 2.0000 | 0.0576 |
| ML | 3-star | 2.0000 | 0.1601 |
| ML | triangle | 2.0000 | 0.4556 |
| CS | 2-star | 2.0000 | 0.3100 |
| CS | 3-star | 2.0000 | 1.2854 |
| CS | triangle | 2.0000 | 3.3294 |
| EE | 2-star | 2.0000 | 0.0307 |
| EE | 3-star | 2.0000 | 0.0877 |
| EE | triangle | 2.0000 | 0.3622 |
| PM | 2-star | 2.0000 | 0.0060 |
| PM | 3-star | 2.0000 | 0.0064 |
| PM | triangle | 2.0000 | 0.2479 |

## Goal 1: methods

`rule_relative_error`: the paired code value on the same noise (GT-Naive for Naive, GT-PSC for PSC, the program itself for DSL); `llm_error` = relative_error − rule_relative_error (execution error added by the LLM; 0 for DSL by construction). `se`: standard error of the mean. GT-* rows are code-only references over 100 runs; GT-Naive / GT-PSC draw the RR noise in another order than the agents (equal in distribution, not run by run), GT-DSL / GT-Tuned in the same order as `program`. GT-Tuned: the library algorithm with its threshold factor and budget split grid-tuned on public synthetic graphs (same scorer as the DSL search).

| dataset | task | eps | method | runs | rejected | relative_error | se | median_relative_error | rule_relative_error | llm_error | llm_calls | node_llm_calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.2556 | 0.0187 | 0.2132 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 1.8081 | 0.1677 | 1.0000 | - | - | 0.0000 | 0.0000 |
| CU | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 1.8211 | 0.1608 | 1.0000 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.1372 | 0.0105 | 0.1267 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.7600 | 0.0565 | 0.6846 | - | - | 0.0000 | 0.0000 |
| Do | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 1.2742 | 0.1089 | 1.0000 | - | - | 0.0000 | 0.0000 |
| ML | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0576 | 0.0042 | 0.0453 | - | - | 0.0000 | 0.0000 |
| ML | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.1601 | 0.0116 | 0.1278 | - | - | 0.0000 | 0.0000 |
| ML | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.4556 | 0.0366 | 0.3652 | - | - | 0.0000 | 0.0000 |
| CS | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.3100 | 0.0242 | 0.2569 | - | - | 0.0000 | 0.0000 |
| CS | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 1.2854 | 0.1039 | 1.0000 | - | - | 0.0000 | 0.0000 |
| CS | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 3.3294 | 0.3424 | 1.2593 | - | - | 0.0000 | 0.0000 |
| EE | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0307 | 0.0025 | 0.0248 | - | - | 0.0000 | 0.0000 |
| EE | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0877 | 0.0066 | 0.0773 | - | - | 0.0000 | 0.0000 |
| EE | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.3622 | 0.0286 | 0.2946 | - | - | 0.0000 | 0.0000 |
| PM | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0060 | 0.0004294 | 0.0055 | - | - | 0.0000 | 0.0000 |
| PM | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0064 | 0.0004721 | 0.0055 | - | - | 0.0000 | 0.0000 |
| PM | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.2479 | 0.0233 | 0.1581 | - | - | 0.0000 | 0.0000 |

## Details

| dataset | task | eps | mode | runs | relative_error | rule_relative_error | exec_exact | node_e2e_acc | aggregate_acc | llm_calls | node_llm_calls | rejected_messages | violations | ci_covers_truth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | gt-dsl-node | 100 | 0.2556 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | 3-star | 2.0000 | gt-dsl-node | 100 | 1.8081 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | triangle | 2.0000 | gt-dsl-node | 100 | 1.8211 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 2-star | 2.0000 | gt-dsl-node | 100 | 0.1372 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 3-star | 2.0000 | gt-dsl-node | 100 | 0.7600 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | triangle | 2.0000 | gt-dsl-node | 100 | 1.2742 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| ML | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0576 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| ML | 3-star | 2.0000 | gt-dsl-node | 100 | 0.1601 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| ML | triangle | 2.0000 | gt-dsl-node | 100 | 0.4556 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CS | 2-star | 2.0000 | gt-dsl-node | 100 | 0.3100 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CS | 3-star | 2.0000 | gt-dsl-node | 100 | 1.2854 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CS | triangle | 2.0000 | gt-dsl-node | 100 | 3.3294 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| EE | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0307 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| EE | 3-star | 2.0000 | gt-dsl-node | 100 | 0.0877 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| EE | triangle | 2.0000 | gt-dsl-node | 100 | 0.3622 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0060 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 3-star | 2.0000 | gt-dsl-node | 100 | 0.0064 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | triangle | 2.0000 | gt-dsl-node | 100 | 0.2479 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
