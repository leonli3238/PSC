# P4 methods and execution modes on identical noise

provider = mock, node = gpt-4.1-mini, curator = gpt-4.1, mock error rate = 0.0, ε = 2.0, runs: LLM 100 / DSL 100 / code 100 (noise of run i: seed [0, i]), r1 = 0.5, r2 = 0.2. Design: exact (3 draft(s) x 1 restart(s)), designer temperature = 0.0. Edge-clipping α = 5. Out-of-library tasks: 4-star, 5-star, degree-moment2, open-wedge, degree-ge3, triangle-node, triangle-edge, 4-cycle.

## Mean relative error by method

Lower is better (|estimate − truth| / truth, averaged over runs).

| dataset | task | eps | GT-DSL-node |
|---|---|---|---|
| CU | 2-star | 2.0000 | 0.0985 |
| CU | 3-star | 2.0000 | 0.4195 |
| CU | triangle | 2.0000 | 1.0465 |
| Do | 2-star | 2.0000 | 0.0608 |
| Do | 3-star | 2.0000 | 0.1783 |
| Do | triangle | 2.0000 | 0.7280 |
| ML | 2-star | 2.0000 | 0.0388 |
| ML | 3-star | 2.0000 | 0.0645 |
| ML | triangle | 2.0000 | 0.2795 |
| CS | 2-star | 2.0000 | 0.1067 |
| CS | 3-star | 2.0000 | 0.2984 |
| CS | triangle | 2.0000 | 1.4757 |
| EE | 2-star | 2.0000 | 0.0250 |
| EE | 3-star | 2.0000 | 0.0402 |
| EE | triangle | 2.0000 | 0.2680 |
| PM | 2-star | 2.0000 | 0.0074 |
| PM | 3-star | 2.0000 | 0.0087 |
| PM | triangle | 2.0000 | 0.1263 |

## Goal 1: methods

`rule_relative_error`: the paired code value on the same noise (GT-Naive for Naive, GT-PSC for PSC, the program itself for DSL); `llm_error` = relative_error − rule_relative_error (execution error added by the LLM; 0 for DSL by construction). `se`: standard error of the mean. GT-* rows are code-only references over 100 runs; GT-Naive / GT-PSC draw the RR noise in another order than the agents (equal in distribution, not run by run), GT-DSL / GT-Tuned in the same order as `program`. GT-Tuned: the library algorithm with its threshold factor and budget split grid-tuned on public synthetic graphs (same scorer as the DSL search).

| dataset | task | eps | method | runs | rejected | relative_error | se | median_relative_error | rule_relative_error | llm_error | llm_calls | node_llm_calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0985 | 0.0071 | 0.0844 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.4195 | 0.0313 | 0.3762 | - | - | 0.0000 | 0.0000 |
| CU | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 1.0465 | 0.0677 | 1.0000 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0608 | 0.0045 | 0.0512 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.1783 | 0.0138 | 0.1447 | - | - | 0.0000 | 0.0000 |
| Do | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.7280 | 0.0489 | 0.7163 | - | - | 0.0000 | 0.0000 |
| ML | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0388 | 0.0031 | 0.0299 | - | - | 0.0000 | 0.0000 |
| ML | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0645 | 0.0055 | 0.0512 | - | - | 0.0000 | 0.0000 |
| ML | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.2795 | 0.0220 | 0.2148 | - | - | 0.0000 | 0.0000 |
| CS | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.1067 | 0.0086 | 0.0924 | - | - | 0.0000 | 0.0000 |
| CS | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.2984 | 0.0251 | 0.2542 | - | - | 0.0000 | 0.0000 |
| CS | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 1.4757 | 0.1485 | 1.0000 | - | - | 0.0000 | 0.0000 |
| EE | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0250 | 0.0020 | 0.0233 | - | - | 0.0000 | 0.0000 |
| EE | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0402 | 0.0037 | 0.0277 | - | - | 0.0000 | 0.0000 |
| EE | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.2680 | 0.0187 | 0.2340 | - | - | 0.0000 | 0.0000 |
| PM | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0074 | 0.0006441 | 0.0062 | - | - | 0.0000 | 0.0000 |
| PM | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0087 | 0.0013 | 0.0058 | - | - | 0.0000 | 0.0000 |
| PM | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.1263 | 0.0101 | 0.1087 | - | - | 0.0000 | 0.0000 |

## Details

| dataset | task | eps | mode | runs | relative_error | rule_relative_error | exec_exact | node_e2e_acc | aggregate_acc | llm_calls | node_llm_calls | rejected_messages | violations | ci_covers_truth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0985 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | 3-star | 2.0000 | gt-dsl-node | 100 | 0.4195 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | triangle | 2.0000 | gt-dsl-node | 100 | 1.0465 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0608 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 3-star | 2.0000 | gt-dsl-node | 100 | 0.1783 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | triangle | 2.0000 | gt-dsl-node | 100 | 0.7280 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| ML | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0388 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| ML | 3-star | 2.0000 | gt-dsl-node | 100 | 0.0645 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| ML | triangle | 2.0000 | gt-dsl-node | 100 | 0.2795 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CS | 2-star | 2.0000 | gt-dsl-node | 100 | 0.1067 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CS | 3-star | 2.0000 | gt-dsl-node | 100 | 0.2984 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CS | triangle | 2.0000 | gt-dsl-node | 100 | 1.4757 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| EE | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0250 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| EE | 3-star | 2.0000 | gt-dsl-node | 100 | 0.0402 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| EE | triangle | 2.0000 | gt-dsl-node | 100 | 0.2680 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0074 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 3-star | 2.0000 | gt-dsl-node | 100 | 0.0087 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | triangle | 2.0000 | gt-dsl-node | 100 | 0.1263 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
