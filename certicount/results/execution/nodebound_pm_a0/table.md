# P4 methods and execution modes on identical noise

provider = mock, node = gpt-4.1-mini, curator = gpt-4.1, mock error rate = 0.0, ε = 2.0, runs: LLM 200 / DSL 200 / code 200 (noise of run i: seed [0, i]), r1 = 0.5, r2 = 0.2. Design: exact (3 draft(s) x 1 restart(s)), designer temperature = 0.0. Edge-clipping α = 0. Out-of-library tasks: 4-star, 5-star, degree-moment2.

## Mean relative error by method

Lower is better (|estimate − truth| / truth, averaged over runs).

| dataset | task | eps | GT-PSC | GT-DSL | GT-DSL-node | GT-TriTR |
|---|---|---|---|---|---|---|
| PM | degree | 2.0000 | 0.0028 | 0.0028 | 0.0028 | 0.0028 |
| PM | 2-star | 2.0000 | 0.0478 | 0.0478 | 0.0557 | 0.0558 |
| PM | 3-star | 2.0000 | 0.1321 | 0.1321 | 0.0340 | 0.0339 |
| PM | triangle | 2.0000 | 1.0173 | 1.0266 | 0.2675 | 0.2729 |

## Goal 1: methods

`rule_relative_error`: the paired code value on the same noise (GT-Naive for Naive, GT-PSC for PSC, the program itself for DSL); `llm_error` = relative_error − rule_relative_error (execution error added by the LLM; 0 for DSL by construction). `se`: standard error of the mean. GT-* rows are code-only references over 200 runs; GT-Naive / GT-PSC draw the RR noise in another order than the agents (equal in distribution, not run by run), GT-DSL / GT-Tuned in the same order as `program`. GT-Tuned: the library algorithm with its threshold factor and budget split grid-tuned on public synthetic graphs (same scorer as the DSL search).

| dataset | task | eps | method | runs | rejected | relative_error | se | median_relative_error | rule_relative_error | llm_error | llm_calls | node_llm_calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 2.0000 | GT-PSC | 200 | 0 | 0.0028 | 0.0001691 | 0.0021 | - | - | 0.0000 | 0.0000 |
| PM | degree | 2.0000 | GT-DSL | 200 | 0 | 0.0028 | 0.0001691 | 0.0021 | - | - | 0.0000 | 0.0000 |
| PM | degree | 2.0000 | GT-DSL-node | 200 | 0 | 0.0028 | 0.0001691 | 0.0021 | - | - | 0.0000 | 0.0000 |
| PM | degree | 2.0000 | GT-TriTR | 200 | 0 | 0.0028 | 0.0001691 | 0.0021 | - | - | 0.0000 | 0.0000 |
| PM | 2-star | 2.0000 | GT-PSC | 200 | 0 | 0.0478 | 0.0025 | 0.0440 | - | - | 0.0000 | 0.0000 |
| PM | 2-star | 2.0000 | GT-DSL | 200 | 0 | 0.0478 | 0.0025 | 0.0440 | - | - | 0.0000 | 0.0000 |
| PM | 2-star | 2.0000 | GT-DSL-node | 200 | 0 | 0.0557 | 0.0008526 | 0.0552 | - | - | 0.0000 | 0.0000 |
| PM | 2-star | 2.0000 | GT-TriTR | 200 | 0 | 0.0558 | 0.0008628 | 0.0546 | - | - | 0.0000 | 0.0000 |
| PM | 3-star | 2.0000 | GT-PSC | 200 | 0 | 0.1321 | 0.0070 | 0.1221 | - | - | 0.0000 | 0.0000 |
| PM | 3-star | 2.0000 | GT-DSL | 200 | 0 | 0.1321 | 0.0070 | 0.1221 | - | - | 0.0000 | 0.0000 |
| PM | 3-star | 2.0000 | GT-DSL-node | 200 | 0 | 0.0340 | 0.0017 | 0.0288 | - | - | 0.0000 | 0.0000 |
| PM | 3-star | 2.0000 | GT-TriTR | 200 | 0 | 0.0339 | 0.0017 | 0.0293 | - | - | 0.0000 | 0.0000 |
| PM | triangle | 2.0000 | GT-PSC | 200 | 0 | 1.0173 | 0.0554 | 0.8006 | - | - | 0.0000 | 0.0000 |
| PM | triangle | 2.0000 | GT-DSL | 200 | 0 | 1.0266 | 0.0495 | 0.9532 | - | - | 0.0000 | 0.0000 |
| PM | triangle | 2.0000 | GT-DSL-node | 200 | 0 | 0.2675 | 0.0104 | 0.2663 | - | - | 0.0000 | 0.0000 |
| PM | triangle | 2.0000 | GT-TriTR | 200 | 0 | 0.2729 | 0.0088 | 0.2787 | - | - | 0.0000 | 0.0000 |

## Details

| dataset | task | eps | mode | runs | relative_error | rule_relative_error | exec_exact | node_e2e_acc | aggregate_acc | llm_calls | node_llm_calls | rejected_messages | violations | ci_covers_truth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 2.0000 | gt-psc | 200 | 0.0028 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | degree | 2.0000 | gt-dsl | 200 | 0.0028 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | degree | 2.0000 | gt-dsl-node | 200 | 0.0028 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | degree | 2.0000 | gt-tritr | 200 | 0.0028 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 2-star | 2.0000 | gt-psc | 200 | 0.0478 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 2-star | 2.0000 | gt-dsl | 200 | 0.0478 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 2-star | 2.0000 | gt-dsl-node | 200 | 0.0557 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 2-star | 2.0000 | gt-tritr | 200 | 0.0558 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 3-star | 2.0000 | gt-psc | 200 | 0.1321 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 3-star | 2.0000 | gt-dsl | 200 | 0.1321 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 3-star | 2.0000 | gt-dsl-node | 200 | 0.0340 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | 3-star | 2.0000 | gt-tritr | 200 | 0.0339 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | triangle | 2.0000 | gt-psc | 200 | 1.0173 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | triangle | 2.0000 | gt-dsl | 200 | 1.0266 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | triangle | 2.0000 | gt-dsl-node | 200 | 0.2675 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | triangle | 2.0000 | gt-tritr | 200 | 0.2729 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
