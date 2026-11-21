# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 20 independent design(s), 3 draft(s) x up to 1 restart(s) per release (rows, matrix), selection simulated (public Holme-Kim graphs, average degrees 4,8,16, 8 releases each, never chosen at a score >= 1; run-time choice on Chung-Lu graphs of the published noisy degrees), own-row check on, tighten 1, early stop off, normalisation on, prompt v1-alt (core v1-alt, b3ea0cb2b6add266), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate off.

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio | mean_candidates | runs_matrix | runs_rows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | degree | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.5500 | 1.4500 | 1.0000 | 3.7000 | 4 | 0.5500 | 0.6000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.1000 | 1.0000 | 0.0000 | 0.0000 |
| CU | 2-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.2500 | 1.8500 | 1.0000 | 3.6500 | 13 | 0.3000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| CU | 3-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.4500 | 1.5500 | 1.0000 | 3.3000 | 15 | 0.1000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| Do | degree | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.4500 | 1.5263 | 1.0000 | 3.8500 | 4 | 0.4737 | 0.4737 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.1316 | 0.9500 | 0.0000 | 0.0000 |
| Do | 2-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.2000 | 1.8500 | 1.0000 | 4.1500 | 10 | 0.2000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| Do | 3-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.2500 | 1.8000 | 1.0000 | 3.5000 | 13 | 0.2500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| CU | degree | 0.0219 | 0.0216 | 0.0216 | 0.0002319 | 0.0005797 | 0.6000 | 0.0000 |
| CU | 2-star | 0.0985 | 0.0985 | 0.0985 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| CU | 3-star | 0.4195 | 0.4195 | 0.4195 | 0.0000 | 0.0000 | 1.0000 | 0.0200 |
| Do | degree | 0.0181 | 0.0192 | 0.0169 | 0.0012 | 0.0022 | 0.4737 | 0.0000 |
| Do | 2-star | 0.0608 | 0.0608 | 0.0608 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| Do | 3-star | 0.1783 | 0.1783 | 0.1783 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | degree | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 1 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 2 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 3 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0083 | - | 0.0222 | 0.0005797 | size_projected = size(project(P, D)) ; return size_projected ; aggregate: total / n |
| CU | degree | 4 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0083 | - | 0.0222 | 0.0005797 | return size(project(P, D)) ; aggregate: total / n |
| CU | degree | 5 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0083 | - | 0.0222 | 0.0005797 | return size(project(P, D)) ; aggregate: total / n |
| CU | degree | 6 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0083 | - | 0.0222 | 0.0005797 | return size(project(P, D)) ; aggregate: total / n |
| CU | degree | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | size_P = size(P) ; return size_P ; aggregate: total / n |
| CU | degree | 8 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0083 | - | 0.0222 | 0.0005797 | return size(project(P, D)) ; aggregate: total / n |
| CU | degree | 9 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 10 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 11 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 12 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0083 | - | 0.0222 | 0.0005797 | return size(project(P, D)) ; aggregate: total / n |
| CU | degree | 13 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 14 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0083 | - | 0.0222 | 0.0005797 | return size(project(P, D)) ; aggregate: total / n |
| CU | degree | 15 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 16 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 17 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0083 | - | 0.0222 | 0.0005797 | return size(project(P, D)) ; aggregate: total / n |
| CU | degree | 18 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 19 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | 2-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | projected = project(P, D) ; return 0.5 * size(projected) * (size(projected) - 1) ; aggregate: total |
| CU | 2-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | return (size(project(P, D)) * (size(project(P, D)) - 1)) / 2 ; aggregate: total |
| CU | 2-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | size_p = size(project(P, D)) ; return (size_p * (size_p - 1)) / 2 ; aggregate: total |
| CU | 2-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| CU | 2-star | 4 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| CU | 2-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| CU | 2-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| CU | 2-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 2) ; aggregate: total |
| CU | 2-star | 8 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| CU | 2-star | 9 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| CU | 2-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | size_proj = size(project(P, D)) ; return (size_proj * (size_proj - 1)) / 2 ; aggregate: total |
| CU | 2-star | 11 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| CU | 2-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| CU | 2-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 2) ; aggregate: total |
| CU | 2-star | 14 | True | 1 | 3 | True | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| CU | 2-star | 15 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| CU | 2-star | 16 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | s = size(project(P, D)) ; return (s * (s - 1)) / 2 ; aggregate: total |
| CU | 2-star | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 2) ; aggregate: total |
| CU | 2-star | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 2) ; aggregate: total |
| CU | 2-star | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | degree = size(project(P, D)) ; stars = (degree * (degree - 1)) / 2 ; return stars ; aggregate: total |
| CU | 3-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | k = size(project(P, D)) ; return k * (k - 1) * (k - 2) / 6 ; aggregate: total |
| CU | 3-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return comb(degree, 3) ; aggregate: total |
| CU | 3-star | 2 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| CU | 3-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | projected_degree = size(project(P, D)) ; return comb(projected_degree, 3) ; aggregate: total |
| CU | 3-star | 4 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| CU | 3-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | k = size(project(P, D)) ; return comb(k, 3) ; aggregate: total |
| CU | 3-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | size_S = size(project(P, D)) ; return comb(size_S, 3) ; aggregate: total |
| CU | 3-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| CU | 3-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | d = size(project(P, D)) ; stars = (pow(d, 3) - 3 * pow(d, 2) + 2 * d) / 6 ; return stars ; aggregate: total |
| CU | 3-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | k = size(project(P, D)) ; return comb(k, 3) ; aggregate: total |
| CU | 3-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| CU | 3-star | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | S = project(P, D) ; degree = size(S) ; return comb(degree, 3) ; aggregate: total |
| CU | 3-star | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | S = project(P, D) ; d = size(S) ; return comb(d, 3) ; aggregate: total |
| CU | 3-star | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return (degree * (degree - 1) * (degree - 2)) / 6 ; aggregate: total |
| CU | 3-star | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| CU | 3-star | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| CU | 3-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| CU | 3-star | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | projected_p = project(P, D) ; size_p = size(projected_p) ; stars = comb(size_p, 3) ; return stars ; aggregate: total |
| CU | 3-star | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| CU | 3-star | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return (degree * (degree - 1) * (degree - 2)) / 6 ; aggregate: total |
| Do | degree | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 1 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | return size(project(P, D)) ; aggregate: total / n |
| Do | degree | 2 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | return size(project(P, D)) ; aggregate: total / n |
| Do | degree | 3 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | return size(project(P, D)) ; aggregate: total / n |
| Do | degree | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | degree | 5 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 6 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | line1 = size(project(P, D)) ; return line1 ; aggregate: total / n |
| Do | degree | 7 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | size_projected = size(project(P, D)) ; return size_projected ; aggregate: total / n |
| Do | degree | 8 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 9 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | return size(project(P, D)) ; aggregate: total / n |
| Do | degree | 10 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 11 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | return size(project(P, D)) ; aggregate: total / n |
| Do | degree | 12 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | return size(project(P, D)) ; aggregate: total / n |
| Do | degree | 13 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 14 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 15 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 16 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | return size(project(P, D)) ; aggregate: total / n |
| Do | degree | 17 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | return size(project(P, D)) ; aggregate: total / n |
| Do | degree | 18 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 19 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | 2-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 2) ; aggregate: total |
| Do | 2-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| Do | 2-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | neighbors = project(P, D) ; degree = size(neighbors) ; return comb(degree, 2) ; aggregate: total |
| Do | 2-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | size_P = size(project(P, D)) ; return (size_P * (size_P - 1)) / 2 ; aggregate: total |
| Do | 2-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 2) ; aggregate: total |
| Do | 2-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| Do | 2-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| Do | 2-star | 7 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| Do | 2-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | size_S = size(project(P, D)) ; return comb(size_S, 2) ; aggregate: total |
| Do | 2-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| Do | 2-star | 10 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | d = size(project(P, D)) ; return d * (d - 1) / 2 ; aggregate: total |
| Do | 2-star | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| Do | 2-star | 12 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| Do | 2-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| Do | 2-star | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | projected_P = project(P, D) ; return comb(size(projected_P), 2) ; aggregate: total |
| Do | 2-star | 15 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| Do | 2-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| Do | 2-star | 17 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| Do | 2-star | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 2) ; aggregate: total |
| Do | 2-star | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | projected_P = project(P, D) ; return comb(size(projected_P), 2) ; aggregate: total |
| Do | 3-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | proj = project(P, D) ; k = size(proj) ; return comb(k, 3) ; aggregate: total |
| Do | 3-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| Do | 3-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| Do | 3-star | 3 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| Do | 3-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | proj = project(P, D) ; s = size(proj) ; return (s * (s - 1) * (s - 2)) / 6 ; aggregate: total |
| Do | 3-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| Do | 3-star | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| Do | 3-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | size_P_projected = size(project(P, D)) ; return comb(size_P_projected, 3) ; aggregate: total |
| Do | 3-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 3) ; aggregate: total |
| Do | 3-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| Do | 3-star | 10 | True | 1 | 3 | True | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| Do | 3-star | 11 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| Do | 3-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| Do | 3-star | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | projected = project(P, D) ; d = size(projected) ; return comb(d, 3) ; aggregate: total |
| Do | 3-star | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | s = size(project(P, D)) ; return (s * (s - 1) * (s - 2)) / 6 ; aggregate: total |
| Do | 3-star | 15 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | return comb( size( project(P, D) ), 3 ) ; aggregate: total |
| Do | 3-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | projected_P = project(P, D) ; return comb(size(projected_P), 3) ; aggregate: total |
| Do | 3-star | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | size_proj = size(project(P, D)) ; return comb(size_proj, 3) ; aggregate: total |
| Do | 3-star | 18 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| Do | 3-star | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
