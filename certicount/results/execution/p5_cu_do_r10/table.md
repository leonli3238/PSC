# P4 methods and execution modes on identical noise

provider = mock, node = gpt-4.1-mini, curator = gpt-4.1, mock error rate = 0.0, ε = 2.0, runs: LLM 10 / DSL 10 / code 1000 (noise of run i: seed [0, i]), r1 = 0.5, r2 = 0.2. Design: exact (3 draft(s) x 1 restart(s)), designer temperature = 0.0. Out-of-library tasks: 4-star, 5-star, degree-moment2.

## Mean relative error by method

Lower is better (|estimate − truth| / truth, averaged over runs).

| dataset | task | eps | PSC[program+adaptive] |
|---|---|---|---|
| CU | 2-star | 2.0000 | 0.2075 |
| CU | 3-star | 2.0000 | 0.4771 |
| CU | 4-star | 2.0000 | 0.6737 |
| CU | triangle | 2.0000 | 0.6444 |
| Do | 2-star | 2.0000 | 0.1098 |
| Do | 3-star | 2.0000 | 0.3126 |
| Do | 4-star | 2.0000 | 0.6286 |
| Do | triangle | 2.0000 | 1.2408 |

## Goal 1: methods

`rule_relative_error`: the paired code value on the same noise (GT-Naive for Naive, GT-PSC for PSC, the program itself for DSL); `llm_error` = relative_error − rule_relative_error (execution error added by the LLM; 0 for DSL by construction). `se`: standard error of the mean. GT-* rows are code-only references over 1000 runs; GT-Naive / GT-PSC draw the RR noise in another order than the agents (equal in distribution, not run by run), GT-DSL / GT-Tuned in the same order as `program`. GT-Tuned: the library algorithm with its threshold factor and budget split grid-tuned on public synthetic graphs (same scorer as the DSL search).

| dataset | task | eps | method | runs | rejected | relative_error | se | median_relative_error | rule_relative_error | llm_error | llm_calls | node_llm_calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | PSC[program+adaptive] | 10 | 0 | 0.2075 | 0.0401 | 0.2117 | 0.2075 | 0.0000 | 0.0000 | 0.0000 |
| CU | 3-star | 2.0000 | PSC[program+adaptive] | 10 | 0 | 0.4771 | 0.1667 | 0.3111 | 0.4771 | 0.0000 | 0.0000 | 0.0000 |
| CU | 4-star | 2.0000 | PSC[program+adaptive] | 10 | 0 | 0.6737 | 0.1531 | 0.6331 | 0.6737 | 0.0000 | 0.0000 | 0.0000 |
| CU | triangle | 2.0000 | PSC[program+adaptive] | 10 | 0 | 0.6444 | 0.2039 | 0.5324 | 0.6444 | 0.0000 | 0.0000 | 0.0000 |
| Do | 2-star | 2.0000 | PSC[program+adaptive] | 10 | 0 | 0.1098 | 0.0211 | 0.0906 | 0.1098 | 0.0000 | 0.0000 | 0.0000 |
| Do | 3-star | 2.0000 | PSC[program+adaptive] | 10 | 0 | 0.3126 | 0.0633 | 0.2504 | 0.3126 | 0.0000 | 0.0000 | 0.0000 |
| Do | 4-star | 2.0000 | PSC[program+adaptive] | 10 | 0 | 0.6286 | 0.1206 | 0.5194 | 0.6286 | 0.0000 | 0.0000 | 0.0000 |
| Do | triangle | 2.0000 | PSC[program+adaptive] | 10 | 0 | 1.2408 | 0.2696 | 1.0707 | 1.2408 | 0.0000 | 0.0000 | 0.0000 |

## Details

| dataset | task | eps | mode | runs | relative_error | rule_relative_error | exec_exact | node_e2e_acc | aggregate_acc | llm_calls | node_llm_calls | guard_fallbacks | rejected_messages | violations | ci_covers_truth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 2.0000 | adaptive | 10 | 0.2075 | 0.2075 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0 | 0 | 0 | 0.7000 |
| CU | 3-star | 2.0000 | adaptive | 10 | 0.4771 | 0.4771 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0 | 0 | 0 | 0.6000 |
| CU | 4-star | 2.0000 | adaptive | 10 | 0.6737 | 0.6737 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0 | 0 | 0 | 0.6000 |
| CU | triangle | 2.0000 | adaptive | 10 | 0.6444 | 0.6444 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0 | 0 | 0 | 0.8000 |
| Do | 2-star | 2.0000 | adaptive | 10 | 0.1098 | 0.1098 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0 | 0 | 0 | 0.9000 |
| Do | 3-star | 2.0000 | adaptive | 10 | 0.3126 | 0.3126 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0 | 0 | 0 | 0.8000 |
| Do | 4-star | 2.0000 | adaptive | 10 | 0.6286 | 0.6286 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0 | 0 | 0 | 0.7000 |
| Do | triangle | 2.0000 | adaptive | 10 | 1.2408 | 1.2408 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0 | 0 | 0 | 0.5000 |
