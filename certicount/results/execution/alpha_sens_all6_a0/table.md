# P4 methods and execution modes on identical noise

provider = mock, node = gpt-4.1-mini, curator = gpt-4.1, mock error rate = 0.0, ε = 2.0, runs: LLM 100 / DSL 100 / code 100 (noise of run i: seed [0, i]), r1 = 0.5, r2 = 0.2. Design: exact (3 draft(s) x 1 restart(s)), designer temperature = 0.0. Edge-clipping α = 0. Out-of-library tasks: 4-star, 5-star, degree-moment2, open-wedge, degree-ge3, triangle-node, triangle-edge, 4-cycle.

## Mean relative error by method

Lower is better (|estimate − truth| / truth, averaged over runs).

| dataset | task | eps | GT-DSL-node |
|---|---|---|---|
| CU | 2-star | 2.0000 | 0.3510 |
| CU | 3-star | 2.0000 | 0.4161 |
| CU | triangle | 2.0000 | 0.7590 |
| Do | 2-star | 2.0000 | 0.2824 |
| Do | 3-star | 2.0000 | 0.3197 |
| Do | triangle | 2.0000 | 0.6502 |
| ML | 2-star | 2.0000 | 0.1697 |
| ML | 3-star | 2.0000 | 0.1566 |
| ML | triangle | 2.0000 | 0.4371 |
| CS | 2-star | 2.0000 | 0.2994 |
| CS | 3-star | 2.0000 | 0.3116 |
| CS | triangle | 2.0000 | 0.9834 |
| EE | 2-star | 2.0000 | 0.1771 |
| EE | 3-star | 2.0000 | 0.1849 |
| EE | triangle | 2.0000 | 0.4064 |
| PM | 2-star | 2.0000 | 0.0567 |
| PM | 3-star | 2.0000 | 0.0350 |
| PM | triangle | 2.0000 | 0.2659 |

## Goal 1: methods

`rule_relative_error`: the paired code value on the same noise (GT-Naive for Naive, GT-PSC for PSC, the program itself for DSL); `llm_error` = relative_error − rule_relative_error (execution error added by the LLM; 0 for DSL by construction). `se`: standard error of the mean. GT-* rows are code-only references over 100 runs; GT-Naive / GT-PSC draw the RR noise in another order than the agents (equal in distribution, not run by run), GT-DSL / GT-Tuned in the same order as `program`. GT-Tuned: the library algorithm with its threshold factor and budget split grid-tuned on public synthetic graphs (same scorer as the DSL search).

| dataset | task | eps | method | runs | rejected | relative_error | se | median_relative_error | rule_relative_error | llm_error | llm_calls | node_llm_calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.3510 | 0.0091 | 0.3482 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.4161 | 0.0209 | 0.4126 | - | - | 0.0000 | 0.0000 |
| CU | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.7590 | 0.0369 | 0.9200 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.2824 | 0.0076 | 0.2781 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.3197 | 0.0125 | 0.3130 | - | - | 0.0000 | 0.0000 |
| Do | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.6502 | 0.0348 | 0.6814 | - | - | 0.0000 | 0.0000 |
| ML | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.1697 | 0.0055 | 0.1648 | - | - | 0.0000 | 0.0000 |
| ML | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.1566 | 0.0090 | 0.1370 | - | - | 0.0000 | 0.0000 |
| ML | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.4371 | 0.0254 | 0.4236 | - | - | 0.0000 | 0.0000 |
| CS | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.2994 | 0.0107 | 0.2877 | - | - | 0.0000 | 0.0000 |
| CS | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.3116 | 0.0187 | 0.2871 | - | - | 0.0000 | 0.0000 |
| CS | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.9834 | 0.0755 | 0.9810 | - | - | 0.0000 | 0.0000 |
| EE | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.1771 | 0.0032 | 0.1743 | - | - | 0.0000 | 0.0000 |
| EE | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.1849 | 0.0062 | 0.1722 | - | - | 0.0000 | 0.0000 |
| EE | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.4064 | 0.0192 | 0.3896 | - | - | 0.0000 | 0.0000 |
| PM | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0567 | 0.0012 | 0.0554 | - | - | 0.0000 | 0.0000 |
| PM | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0350 | 0.0025 | 0.0295 | - | - | 0.0000 | 0.0000 |
| PM | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.2659 | 0.0132 | 0.2808 | - | - | 0.0000 | 0.0000 |

## Details

| dataset | task | eps | mode | runs | relative_error | rule_relative_error | exec_exact | node_e2e_acc | aggregate_acc | llm_calls | node_llm_calls | rejected_messages | violations | ci_covers_truth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | gt-dsl-node | 100 | 0.3510 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | 3-star | 2.0000 | gt-dsl-node | 100 | 0.4161 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | triangle | 2.0000 | gt-dsl-node | 100 | 0.7590 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 2-star | 2.0000 | gt-dsl-node | 100 | 0.2824 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 3-star | 2.0000 | gt-dsl-node | 100 | 0.3197 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | triangle | 2.0000 | gt-dsl-node | 100 | 0.6502 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| ML | 2-star | 2.0000 | gt-dsl-node | 100 | 0.1697 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| ML | 3-star | 2.0000 | gt-dsl-node | 100 | 0.1566 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| ML | triangle | 2.0000 | gt-dsl-node | 100 | 0.4371 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CS | 2-star | 2.0000 | gt-dsl-node | 100 | 0.2994 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CS | 3-star | 2.0000 | gt-dsl-node | 100 | 0.3116 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CS | triangle | 2.0000 | gt-dsl-node | 100 | 0.9834 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| EE | 2-star | 2.0000 | gt-dsl-node | 100 | 0.1771 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| EE | 3-star | 2.0000 | gt-dsl-node | 100 | 0.1849 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| EE | triangle | 2.0000 | gt-dsl-node | 100 | 0.4064 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0567 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 3-star | 2.0000 | gt-dsl-node | 100 | 0.0350 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | triangle | 2.0000 | gt-dsl-node | 100 | 0.2659 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
