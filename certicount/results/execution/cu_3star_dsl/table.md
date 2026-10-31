# P4 execution modes on identical noise

provider = mock, node = gpt-4.1-mini, curator = gpt-4.1, mock error rate = 0.0, ε = 2.0, 10 runs (noise of run i: seed [0, i]). Out-of-library tasks: 4-star, 5-star, degree-moment2.

| dataset | task | mode | runs | relative_error | rule_relative_error | exec_exact | node_e2e_acc | aggregate_acc | llm_calls | node_llm_calls | guard_fallbacks | rejected_messages | violations | ci_covers_truth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 3-star | program | 10 | 1.0229 | 1.0229 | 1.0000 | 1.0000 | 1.0000 | 0.1000 | 0.0000 | 0 | 0 | 0 | 1.0000 |
