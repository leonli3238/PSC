# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 10 independent design(s), 3 draft(s) x up to 1 restart(s) per release (rows, matrix), selection simulated (public Holme-Kim graphs, average degrees 4,8,16, 8 releases each, never chosen at a score >= 1; run-time choice on Chung-Lu graphs of the published noisy degrees), own-row check on, tighten 1, early stop off, normalisation on, prompt generic (core generic, 62a207c03a9c4864), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate off.

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio | mean_candidates | runs_matrix | runs_rows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 4-cycle | 10 | 0.0000 | [0.00, 0.28] | 0.0000 | 0.0000 | - | 1.0000 | 6.0000 | 0 | - | - | - | - | - | - | - | - | 0.0000 | - | - |
| ML | 4-cycle | 10 | 0.0000 | [0.00, 0.28] | 0.0000 | 0.0000 | - | 1.0000 | 6.0000 | 0 | - | - | - | - | - | - | - | - | 0.0000 | - | - |
| EE | 4-cycle | 10 | 0.0000 | [0.00, 0.28] | 0.0000 | 0.0000 | - | 1.0000 | 5.9000 | 0 | - | - | - | - | - | - | - | - | 0.1000 | - | - |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| CU | 4-cycle | - | - | 7.6522 | - | - | - | - |
| ML | 4-cycle | - | - | 0.9830 | - | - | - | - |
| EE | 4-cycle | - | - | 2.0378 | - | - | - | - |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 4-cycle | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | 4-cycle | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | 4-cycle | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | 4-cycle | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | 4-cycle | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | 4-cycle | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | 4-cycle | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | 4-cycle | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | 4-cycle | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | 4-cycle | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | 4-cycle | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | 4-cycle | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | 4-cycle | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | 4-cycle | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | 4-cycle | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | 4-cycle | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | 4-cycle | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | 4-cycle | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | 4-cycle | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | 4-cycle | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | 4-cycle | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | 4-cycle | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | 4-cycle | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | 4-cycle | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | 4-cycle | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | 4-cycle | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | 4-cycle | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | 4-cycle | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | 4-cycle | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | 4-cycle | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
