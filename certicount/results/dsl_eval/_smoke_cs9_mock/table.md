# DSL design evaluation (goal 2: error added by the LLM designer)

designer = mock, temperature = 0.0, 2 independent design(s), 3 draft(s) x up to 1 restart(s) per release (rows, matrix), selection simulated (public Holme-Kim graphs, average degrees 4,8,16, 8 releases each, never chosen at a score >= 1; run-time choice on Chung-Lu graphs of the published noisy degrees), own-row check on, tighten 1, early stop off, normalisation on, prompt generic (core generic, 62a207c03a9c4864), ε = 2.0, 5 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate off.

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio | mean_candidates | runs_matrix | runs_rows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ML | degree-ge3 | 2 | 1.0000 | [0.34, 1.00] | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 2.0000 | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| ML | triangle-node | 2 | 1.0000 | [0.34, 1.00] | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 2.0000 | 1 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| ML | triangle-edge | 2 | 1.0000 | [0.34, 1.00] | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 3.0000 | 1 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9113 | 1.0000 | 0.0000 | 1.0000 |
| ML | 4-cycle | 2 | 0.0000 | [0.00, 0.66] | 0.0000 | 0.0000 | - | 1.0000 | 5.0000 | 0 | - | - | - | - | - | - | - | - | 1.0000 | - | - |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| ML | degree-ge3 | 0.1184 | 0.1184 | 0.1184 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| ML | triangle-node | 0.2548 | 0.2548 | 0.2156 | 0.0392 | 0.0392 | 0.0000 | 0.0000 |
| ML | triangle-edge | 0.3342 | 0.3342 | 0.3777 | -0.0435 | -0.0435 | 0.0000 | 0.0000 |
| ML | 4-cycle | - | - | 0.7428 | - | - | - | - |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ML | degree-ge3 | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.1184 | 0.0000 | return clip(size(P) - 2, 0, 1) ; aggregate: total |
| ML | degree-ge3 | 1 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.1184 | 0.0000 | return clip(size(P) - 2, 0, 1) ; aggregate: total |
| ML | triangle-node | 0 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2548 | 0.0392 | Q = project(P, D) ; return clip(sum(size(Q & N(v)) for v in Q), 0, 1) ; aggregate: total |
| ML | triangle-node | 1 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2548 | 0.0392 | Q = project(P, D) ; return clip(sum(size(Q & N(v)) for v in Q), 0, 1) ; aggregate: total |
| ML | triangle-edge | 0 | True | 1 | 1 | False | False | 0.9113 | True | True | 0.0380 | - | 0.3342 | -0.0435 | Q = project(P, D) ; return 0.5 * sum(clip(size(Q & N(v)), 0, 1) for v in Q) ; aggregate: total |
| ML | triangle-edge | 1 | True | 1 | 1 | False | False | 0.9113 | True | True | 0.0380 | - | 0.3342 | -0.0435 | Q = project(P, D) ; return 0.5 * sum(clip(size(Q & N(v)), 0, 1) for v in Q) ; aggregate: total |
| ML | 4-cycle | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | 4-cycle | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
