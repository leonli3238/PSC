# P4 methods and execution modes on identical noise

provider = mock, node = gpt-4.1-mini, curator = gpt-4.1, mock error rate = 0.0, ε = 2.0, runs: LLM 200 / DSL 200 / code 200 (noise of run i: seed [0, i]), r1 = 0.5, r2 = 0.2. Design: exact (3 draft(s) x 1 restart(s)), designer temperature = 0.0. Edge-clipping α = 2. Out-of-library tasks: 4-star, 5-star, degree-moment2.

## Mean relative error by method

Lower is better (|estimate − truth| / truth, averaged over runs).

| dataset | task | eps | GT-DSL-node |
|---|---|---|---|
| CU | 2-star | 2.0000 | 0.1505 |
| CU | 3-star | 2.0000 | 0.3119 |
| CU | 4-star | 2.0000 | 1.0547 |
| Do | 2-star | 2.0000 | 0.1284 |
| Do | 3-star | 2.0000 | 0.1776 |
| Do | 4-star | 2.0000 | 0.3366 |

## Goal 1: methods

`rule_relative_error`: the paired code value on the same noise (GT-Naive for Naive, GT-PSC for PSC, the program itself for DSL); `llm_error` = relative_error − rule_relative_error (execution error added by the LLM; 0 for DSL by construction). `se`: standard error of the mean. GT-* rows are code-only references over 200 runs; GT-Naive / GT-PSC draw the RR noise in another order than the agents (equal in distribution, not run by run), GT-DSL / GT-Tuned in the same order as `program`. GT-Tuned: the library algorithm with its threshold factor and budget split grid-tuned on public synthetic graphs (same scorer as the DSL search).

| dataset | task | eps | method | runs | rejected | relative_error | se | median_relative_error | rule_relative_error | llm_error | llm_calls | node_llm_calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | GT-DSL-node | 200 | 0 | 0.1505 | 0.0063 | 0.1369 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | 2.0000 | GT-DSL-node | 200 | 0 | 0.3119 | 0.0176 | 0.2408 | - | - | 0.0000 | 0.0000 |
| CU | 4-star | 2.0000 | GT-DSL-node | 200 | 0 | 1.0547 | 0.0959 | 0.9279 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | 2.0000 | GT-DSL-node | 200 | 0 | 0.1284 | 0.0047 | 0.1235 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | 2.0000 | GT-DSL-node | 200 | 0 | 0.1776 | 0.0091 | 0.1550 | - | - | 0.0000 | 0.0000 |
| Do | 4-star | 2.0000 | GT-DSL-node | 200 | 0 | 0.3366 | 0.0175 | 0.2772 | - | - | 0.0000 | 0.0000 |

## Details

| dataset | task | eps | mode | runs | relative_error | rule_relative_error | exec_exact | node_e2e_acc | aggregate_acc | llm_calls | node_llm_calls | rejected_messages | violations | ci_covers_truth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | gt-dsl-node | 200 | 0.1505 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | 3-star | 2.0000 | gt-dsl-node | 200 | 0.3119 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | 4-star | 2.0000 | gt-dsl-node | 200 | 1.0547 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 2-star | 2.0000 | gt-dsl-node | 200 | 0.1284 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 3-star | 2.0000 | gt-dsl-node | 200 | 0.1776 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 4-star | 2.0000 | gt-dsl-node | 200 | 0.3366 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
