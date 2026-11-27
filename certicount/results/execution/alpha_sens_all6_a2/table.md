# P4 methods and execution modes on identical noise

provider = mock, node = gpt-4.1-mini, curator = gpt-4.1, mock error rate = 0.0, ε = 2.0, runs: LLM 100 / DSL 100 / code 100 (noise of run i: seed [0, i]), r1 = 0.5, r2 = 0.2. Design: exact (3 draft(s) x 1 restart(s)), designer temperature = 0.0. Edge-clipping α = 2. Out-of-library tasks: 4-star, 5-star, degree-moment2, open-wedge, degree-ge3, triangle-node, triangle-edge, 4-cycle.

## Mean relative error by method

Lower is better (|estimate − truth| / truth, averaged over runs).

| dataset | task | eps | GT-DSL-node |
|---|---|---|---|
| CU | 2-star | 2.0000 | 0.1507 |
| CU | 3-star | 2.0000 | 0.3114 |
| CU | triangle | 2.0000 | 0.8060 |
| Do | 2-star | 2.0000 | 0.1308 |
| Do | 3-star | 2.0000 | 0.1780 |
| Do | triangle | 2.0000 | 0.6495 |
| ML | 2-star | 2.0000 | 0.0832 |
| ML | 3-star | 2.0000 | 0.0932 |
| ML | triangle | 2.0000 | 0.3596 |
| CS | 2-star | 2.0000 | 0.1395 |
| CS | 3-star | 2.0000 | 0.2432 |
| CS | triangle | 2.0000 | 1.1294 |
| EE | 2-star | 2.0000 | 0.0797 |
| EE | 3-star | 2.0000 | 0.0842 |
| EE | triangle | 2.0000 | 0.3236 |
| PM | 2-star | 2.0000 | 0.0253 |
| PM | 3-star | 2.0000 | 0.0183 |
| PM | triangle | 2.0000 | 0.2212 |

## Goal 1: methods

`rule_relative_error`: the paired code value on the same noise (GT-Naive for Naive, GT-PSC for PSC, the program itself for DSL); `llm_error` = relative_error − rule_relative_error (execution error added by the LLM; 0 for DSL by construction). `se`: standard error of the mean. GT-* rows are code-only references over 100 runs; GT-Naive / GT-PSC draw the RR noise in another order than the agents (equal in distribution, not run by run), GT-DSL / GT-Tuned in the same order as `program`. GT-Tuned: the library algorithm with its threshold factor and budget split grid-tuned on public synthetic graphs (same scorer as the DSL search).

| dataset | task | eps | method | runs | rejected | relative_error | se | median_relative_error | rule_relative_error | llm_error | llm_calls | node_llm_calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.1507 | 0.0095 | 0.1335 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.3114 | 0.0242 | 0.2514 | - | - | 0.0000 | 0.0000 |
| CU | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.8060 | 0.0569 | 0.7641 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.1308 | 0.0065 | 0.1267 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.1780 | 0.0128 | 0.1556 | - | - | 0.0000 | 0.0000 |
| Do | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.6495 | 0.0364 | 0.6726 | - | - | 0.0000 | 0.0000 |
| ML | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0832 | 0.0045 | 0.0775 | - | - | 0.0000 | 0.0000 |
| ML | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0932 | 0.0077 | 0.0790 | - | - | 0.0000 | 0.0000 |
| ML | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.3596 | 0.0226 | 0.3113 | - | - | 0.0000 | 0.0000 |
| CS | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.1395 | 0.0086 | 0.1331 | - | - | 0.0000 | 0.0000 |
| CS | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.2432 | 0.0181 | 0.2110 | - | - | 0.0000 | 0.0000 |
| CS | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 1.1294 | 0.0858 | 1.0000 | - | - | 0.0000 | 0.0000 |
| EE | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0797 | 0.0026 | 0.0773 | - | - | 0.0000 | 0.0000 |
| EE | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0842 | 0.0054 | 0.0759 | - | - | 0.0000 | 0.0000 |
| EE | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.3236 | 0.0194 | 0.3096 | - | - | 0.0000 | 0.0000 |
| PM | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0253 | 0.0010 | 0.0243 | - | - | 0.0000 | 0.0000 |
| PM | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0183 | 0.0018 | 0.0140 | - | - | 0.0000 | 0.0000 |
| PM | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.2212 | 0.0138 | 0.2068 | - | - | 0.0000 | 0.0000 |

## Details

| dataset | task | eps | mode | runs | relative_error | rule_relative_error | exec_exact | node_e2e_acc | aggregate_acc | llm_calls | node_llm_calls | rejected_messages | violations | ci_covers_truth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | gt-dsl-node | 100 | 0.1507 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | 3-star | 2.0000 | gt-dsl-node | 100 | 0.3114 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | triangle | 2.0000 | gt-dsl-node | 100 | 0.8060 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 2-star | 2.0000 | gt-dsl-node | 100 | 0.1308 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 3-star | 2.0000 | gt-dsl-node | 100 | 0.1780 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | triangle | 2.0000 | gt-dsl-node | 100 | 0.6495 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| ML | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0832 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| ML | 3-star | 2.0000 | gt-dsl-node | 100 | 0.0932 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| ML | triangle | 2.0000 | gt-dsl-node | 100 | 0.3596 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CS | 2-star | 2.0000 | gt-dsl-node | 100 | 0.1395 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CS | 3-star | 2.0000 | gt-dsl-node | 100 | 0.2432 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CS | triangle | 2.0000 | gt-dsl-node | 100 | 1.1294 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| EE | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0797 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| EE | 3-star | 2.0000 | gt-dsl-node | 100 | 0.0842 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| EE | triangle | 2.0000 | gt-dsl-node | 100 | 0.3236 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0253 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 3-star | 2.0000 | gt-dsl-node | 100 | 0.0183 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | triangle | 2.0000 | gt-dsl-node | 100 | 0.2212 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
