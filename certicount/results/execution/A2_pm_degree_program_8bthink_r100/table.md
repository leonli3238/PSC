# P4 methods and execution modes on identical noise

provider = vllm, node = Qwen3-8B, curator = Qwen3-8B, mock error rate = 0.0, ε = 2.0, runs: LLM 100 / DSL 100 / code 100 (noise of run i: seed [0, i]), r1 = 0.5, r2 = 0.2. Design: exact (3 draft(s) x 1 restart(s)), designer temperature = 0.0. Edge-clipping α = 0. Out-of-library tasks: 4-star, 5-star, degree-moment2.

## Mean relative error by method

Lower is better (|estimate − truth| / truth, averaged over runs).

| dataset | task | eps | DSL | GT-DSL | GT-PSC |
|---|---|---|---|---|---|
| PM | degree | 2.0000 | 0.0030 | 0.0030 | 0.0030 |

## Goal 1: methods

`rule_relative_error`: the paired code value on the same noise (GT-Naive for Naive, GT-PSC for PSC, the program itself for DSL); `llm_error` = relative_error − rule_relative_error (execution error added by the LLM; 0 for DSL by construction). `se`: standard error of the mean. GT-* rows are code-only references over 100 runs; GT-Naive / GT-PSC draw the RR noise in another order than the agents (equal in distribution, not run by run), GT-DSL / GT-Tuned in the same order as `program`. GT-Tuned: the library algorithm with its threshold factor and budget split grid-tuned on public synthetic graphs (same scorer as the DSL search).

| dataset | task | eps | method | runs | rejected | relative_error | se | median_relative_error | rule_relative_error | llm_error | llm_calls | node_llm_calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 2.0000 | DSL | 100 | 0 | 0.0030 | 0.0002386 | 0.0024 | 0.0030 | 0.0000 | 0.0100 | 0.0000 |
| PM | degree | 2.0000 | GT-DSL | 100 | 0 | 0.0030 | 0.0002386 | 0.0024 | - | - | 0.0000 | 0.0000 |
| PM | degree | 2.0000 | GT-PSC | 100 | 0 | 0.0030 | 0.0002386 | 0.0024 | - | - | 0.0000 | 0.0000 |

## Goal 2: the DSL design (paired with GT-DSL on the same noise)

`design_error` = relative_error − gt_dsl_relative_error (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs (both clamped to 0); `noise_ratio`: final noise |c|·GS/ε3 of the design over the reference (c: aggregate slope); `search_score`: simulated error on public synthetic graphs (search mode).

| dataset | task | eps | runs | rejected | relative_error | gt_dsl_relative_error | design_error | design_error_se | design_exact | both_zero | noise_ratio | split_match | design_mode | design_restarts | design_iterations | llm_calls_total | search_score | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 2.0000 | 100 | 0 | 0.0030 | 0.0030 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | exact | 1 | 1 | 1 | - | size_p = size(P) ; return size_p ; aggregate: total / n |

## Details

| dataset | task | eps | mode | runs | relative_error | rule_relative_error | exec_exact | node_e2e_acc | aggregate_acc | llm_calls | node_llm_calls | rejected_messages | violations | ci_covers_truth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 2.0000 | program | 100 | 0.0030 | 0.0030 | 1.0000 | 1.0000 | 1.0000 | 0.0100 | 0.0000 | 0 | 0 | 0.9400 |
| PM | degree | 2.0000 | gt-dsl | 100 | 0.0030 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
| PM | degree | 2.0000 | gt-psc | 100 | 0.0030 | - | - | - | - | 0.0000 | 0.0000 | - | - | - |
