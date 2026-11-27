# P4 methods and execution modes on identical noise

provider = mock, node = gpt-4.1-mini, curator = gpt-4.1, mock error rate = 0.0, ε = 2.0, runs: LLM 100 / DSL 100 / code 100 (noise of run i: seed [0, i]), r1 = 0.5, r2 = 0.2. Design: exact (3 draft(s) x 1 restart(s)), designer temperature = 0.0. Edge-clipping α = 10. Out-of-library tasks: 4-star, 5-star, degree-moment2, open-wedge, degree-ge3, triangle-node, triangle-edge, 4-cycle.

## Mean relative error by method

Lower is better (|estimate − truth| / truth, averaged over runs).

| dataset | task | eps | GT-DSL-node |
|---|---|---|---|
| CU | 2-star | 2.0000 | 0.1472 |
| CU | 3-star | 2.0000 | 0.7935 |
| CU | triangle | 2.0000 | 1.2466 |
| Do | 2-star | 2.0000 | 0.0815 |
| Do | 3-star | 2.0000 | 0.3180 |
| Do | triangle | 2.0000 | 0.8993 |
| ML | 2-star | 2.0000 | 0.0367 |
| ML | 3-star | 2.0000 | 0.0769 |
| ML | triangle | 2.0000 | 0.2889 |
| CS | 2-star | 2.0000 | 0.1757 |
| CS | 3-star | 2.0000 | 0.6158 |
| CS | triangle | 2.0000 | 1.9885 |
| EE | 2-star | 2.0000 | 0.0200 |
| EE | 3-star | 2.0000 | 0.0433 |
| EE | triangle | 2.0000 | 0.2664 |
| PM | 2-star | 2.0000 | 0.0051 |
| PM | 3-star | 2.0000 | 0.0064 |
| PM | triangle | 2.0000 | 0.1908 |

## Goal 1: methods

`rule_relative_error`: the paired code value on the same noise (GT-Naive for Naive, GT-PSC for PSC, the program itself for DSL); `llm_error` = relative_error − rule_relative_error (execution error added by the LLM; 0 for DSL by construction). `se`: standard error of the mean. GT-* rows are code-only references over 100 runs; GT-Naive / GT-PSC draw the RR noise in another order than the agents (equal in distribution, not run by run), GT-DSL / GT-Tuned in the same order as `program`. GT-Tuned: the library algorithm with its threshold factor and budget split grid-tuned on public synthetic graphs (same scorer as the DSL search).

| dataset | task | eps | method | runs | rejected | relative_error | se | median_relative_error | rule_relative_error | llm_error | llm_calls | node_llm_calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.1472 | 0.0106 | 0.1343 | - | - | 0.0000 | 0.0000 |
| CU | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.7935 | 0.0544 | 0.7699 | - | - | 0.0000 | 0.0000 |
| CU | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 1.2466 | 0.0864 | 1.0000 | - | - | 0.0000 | 0.0000 |
| Do | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0815 | 0.0065 | 0.0663 | - | - | 0.0000 | 0.0000 |
| Do | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.3180 | 0.0256 | 0.2296 | - | - | 0.0000 | 0.0000 |
| Do | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.8993 | 0.0692 | 0.9307 | - | - | 0.0000 | 0.0000 |
| ML | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0367 | 0.0026 | 0.0308 | - | - | 0.0000 | 0.0000 |
| ML | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0769 | 0.0060 | 0.0653 | - | - | 0.0000 | 0.0000 |
| ML | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.2889 | 0.0249 | 0.2185 | - | - | 0.0000 | 0.0000 |
| CS | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.1757 | 0.0141 | 0.1493 | - | - | 0.0000 | 0.0000 |
| CS | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.6158 | 0.0382 | 0.5605 | - | - | 0.0000 | 0.0000 |
| CS | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 1.9885 | 0.1905 | 1.0000 | - | - | 0.0000 | 0.0000 |
| EE | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0200 | 0.0016 | 0.0169 | - | - | 0.0000 | 0.0000 |
| EE | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0433 | 0.0033 | 0.0393 | - | - | 0.0000 | 0.0000 |
| EE | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.2664 | 0.0200 | 0.2256 | - | - | 0.0000 | 0.0000 |
| PM | 2-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0051 | 0.0003828 | 0.0043 | - | - | 0.0000 | 0.0000 |
| PM | 3-star | 2.0000 | GT-DSL-node | 100 | 0 | 0.0064 | 0.0006478 | 0.0047 | - | - | 0.0000 | 0.0000 |
| PM | triangle | 2.0000 | GT-DSL-node | 100 | 0 | 0.1908 | 0.0144 | 0.1560 | - | - | 0.0000 | 0.0000 |

## Details

| dataset | task | eps | mode | runs | relative_error | rule_relative_error | exec_exact | node_e2e_acc | aggregate_acc | llm_calls | node_llm_calls | rejected_messages | violations | ci_covers_truth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | gt-dsl-node | 100 | 0.1472 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | 3-star | 2.0000 | gt-dsl-node | 100 | 0.7935 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CU | triangle | 2.0000 | gt-dsl-node | 100 | 1.2466 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0815 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | 3-star | 2.0000 | gt-dsl-node | 100 | 0.3180 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| Do | triangle | 2.0000 | gt-dsl-node | 100 | 0.8993 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| ML | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0367 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| ML | 3-star | 2.0000 | gt-dsl-node | 100 | 0.0769 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| ML | triangle | 2.0000 | gt-dsl-node | 100 | 0.2889 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CS | 2-star | 2.0000 | gt-dsl-node | 100 | 0.1757 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CS | 3-star | 2.0000 | gt-dsl-node | 100 | 0.6158 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| CS | triangle | 2.0000 | gt-dsl-node | 100 | 1.9885 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| EE | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0200 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| EE | 3-star | 2.0000 | gt-dsl-node | 100 | 0.0433 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| EE | triangle | 2.0000 | gt-dsl-node | 100 | 0.2664 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 2-star | 2.0000 | gt-dsl-node | 100 | 0.0051 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 3-star | 2.0000 | gt-dsl-node | 100 | 0.0064 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | triangle | 2.0000 | gt-dsl-node | 100 | 0.1908 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
