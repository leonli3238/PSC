# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 20 independent design(s), 3 draft(s) x up to 1 restart(s) per release (rows, matrix), selection simulated (public Holme-Kim graphs, average degrees 4,8,16, 8 releases each, never chosen at a score >= 1; run-time choice on Chung-Lu graphs of the published noisy degrees), own-row check on, tighten 1, early stop off, normalisation on, prompt v1-alt (core v1-alt, b3ea0cb2b6add266), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate off.

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio | mean_candidates | runs_matrix | runs_rows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.5000 | 1.5500 | 1.0000 | 3.6500 | 4 | 0.4500 | 0.5000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.1250 | 1.0000 | 0.0000 | 0.0000 |
| PM | 2-star | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.3000 | 1.6842 | 1.0000 | 3.8500 | 13 | 0.2105 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9500 | 0.0000 | 0.0000 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | degree | 0.0055 | 0.0055 | 0.0030 | 0.0025 | 0.0050 | 0.5000 | 0.0000 |
| PM | 2-star | 0.0074 | 0.0074 | 0.0074 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 0 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | return size(project(P, D)) ; aggregate: total / n |
| PM | degree | 1 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | return size(project(P, D)) ; aggregate: total / n |
| PM | degree | 2 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 3 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 4 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | return size(project(P, D)) ; aggregate: total / n |
| PM | degree | 5 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | return size(project(P, D)) ; aggregate: total / n |
| PM | degree | 6 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 7 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 8 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 9 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | size_projected = size(project(P, D)) ; return size_projected ; aggregate: total / n |
| PM | degree | 10 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | return size(project(P, D)) ; aggregate: total / n |
| PM | degree | 11 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 12 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | size_P = size(P) ; return size_P ; aggregate: total / n |
| PM | degree | 14 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 15 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | size_projected = size(project(P, D)) ; return size_projected ; aggregate: total / n |
| PM | degree | 16 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | return size(project(P, D)) ; aggregate: total / n |
| PM | degree | 17 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | return size(project(P, D)) ; aggregate: total / n |
| PM | degree | 18 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | return size(project(P, D)) ; aggregate: total / n |
| PM | degree | 19 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | 2-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| PM | 2-star | 1 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| PM | 2-star | 2 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| PM | 2-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | size_proj = size(project(P, D)) ; stars = comb(size_proj, 2) ; return stars ; aggregate: total |
| PM | 2-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | size_projected = size(project(P, D)) ; return (size_projected * (size_projected - 1)) / 2 ; aggregate: total |
| PM | 2-star | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 2-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| PM | 2-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | S = project(P, D) ; k = size(S) ; return comb(k, 2) ; aggregate: total |
| PM | 2-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 2) ; aggregate: total |
| PM | 2-star | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | return (size(project(P, D)) * (size(project(P, D)) - 1)) / 2 ; aggregate: total |
| PM | 2-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 2) ; aggregate: total |
| PM | 2-star | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 2) ; aggregate: total |
| PM | 2-star | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 2) ; aggregate: total |
| PM | 2-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | size_projected = size(project(P, D)) ; num_pairs = size_projected * (size_projected - 1) / 2 ; return num_pairs ; aggregate: total |
| PM | 2-star | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | size_S = size(project(P, D)) ; return 0.5 * size_S * (size_S - 1) ; aggregate: total |
| PM | 2-star | 15 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| PM | 2-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return (degree * (degree - 1)) / 2 ; aggregate: total |
| PM | 2-star | 17 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| PM | 2-star | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | degree = size(project(P, D)) ; return (degree * (degree - 1)) / 2 ; aggregate: total |
| PM | 2-star | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 2) ; aggregate: total |
