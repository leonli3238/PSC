# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 20 independent design(s), 3 draft(s) x up to 1 restart(s) per release (rows, matrix), selection simulated (public Holme-Kim graphs, average degrees 4,8,16, 8 releases each, never chosen at a score >= 1; run-time choice on Chung-Lu graphs of the published noisy degrees), own-row check on, tighten 1, early stop off, normalisation on, feedback full, prompt generic (core generic, 62a207c03a9c4864), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate off.

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio | mean_candidates | runs_matrix | runs_rows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.6500 | 1.3500 | 1.0000 | 2.8500 | 4 | 0.6000 | 0.7000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0750 | 1.0000 | 0.0000 | 0.0000 |
| PM | 2-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.4500 | 1.5500 | 1.0000 | 3.1500 | 20 | 0.0500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| PM | 3-star | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.2500 | 1.7368 | 1.0000 | 3.5500 | 12 | 0.1053 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9500 | 0.0000 | 0.0000 |
| CU | degree | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.7000 | 1.3500 | 1.0000 | 3.1500 | 5 | 0.6000 | 0.8000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0500 | 1.0000 | 0.0000 | 0.0000 |
| CU | 2-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.5500 | 1.4500 | 1.0000 | 3.0000 | 20 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| CU | 3-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.1500 | 1.9500 | 1.0000 | 3.8500 | 13 | 0.2000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| Do | degree | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.5500 | 1.5000 | 1.0000 | 3.4000 | 4 | 0.5500 | 0.6000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.1000 | 1.0000 | 0.0000 | 0.0000 |
| Do | 2-star | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.2500 | 1.7368 | 1.0000 | 3.5000 | 13 | 0.1053 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9500 | 0.0000 | 0.0000 |
| Do | 3-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.3000 | 1.7500 | 1.0000 | 3.2000 | 18 | 0.0500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| ML | degree | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.8500 | 1.1500 | 1.0000 | 3.2000 | 3 | 0.7000 | 0.8500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0375 | 1.0000 | 0.0000 | 0.0000 |
| ML | 2-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.5000 | 1.5500 | 1.0000 | 3.5500 | 15 | 0.1500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| ML | 3-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.3000 | 1.7000 | 1.0000 | 3.3500 | 14 | 0.1000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| CS | degree | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.6500 | 1.4500 | 1.0000 | 3.3000 | 7 | 0.6000 | 0.7500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0625 | 1.0000 | 0.0000 | 0.0000 |
| CS | 2-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.4000 | 1.6000 | 1.0000 | 3.2500 | 15 | 0.2000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| CS | 3-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.3000 | 1.7000 | 1.0000 | 3.3500 | 17 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| EE | degree | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.6000 | 1.4500 | 1.0000 | 2.9500 | 4 | 0.6000 | 0.6000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.1000 | 1.0000 | 0.0000 | 0.0000 |
| EE | 2-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.5000 | 1.5500 | 1.0000 | 3.3000 | 17 | 0.1000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| EE | 3-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.3000 | 1.7500 | 1.0000 | 3.2000 | 17 | 0.0500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | degree | 0.0045 | 0.0030 | 0.0030 | 0.0015 | 0.0050 | 0.7000 | 0.0000 |
| PM | 2-star | 0.0074 | 0.0074 | 0.0074 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| PM | 3-star | 0.0087 | 0.0087 | 0.0087 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| CU | degree | 0.0217 | 0.0216 | 0.0216 | 0.0001159 | 0.0005797 | 0.8000 | 0.0000 |
| CU | 2-star | 0.0985 | 0.0985 | 0.0985 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| CU | 3-star | 0.4195 | 0.4195 | 0.4195 | 0.0000 | 0.0000 | 1.0000 | 0.0200 |
| Do | degree | 0.0178 | 0.0169 | 0.0169 | 0.0008998 | 0.0022 | 0.6000 | 0.0000 |
| Do | 2-star | 0.0608 | 0.0608 | 0.0608 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| Do | 3-star | 0.1783 | 0.1783 | 0.1783 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| ML | degree | 0.0126 | 0.0116 | 0.0116 | 0.0009973 | 0.0066 | 0.8500 | 0.0000 |
| ML | 2-star | 0.0388 | 0.0388 | 0.0388 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| ML | 3-star | 0.0645 | 0.0645 | 0.0645 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| CS | degree | 0.0252 | 0.0249 | 0.0249 | 0.0003608 | 0.0014 | 0.7500 | 0.0000 |
| CS | 2-star | 0.1067 | 0.1067 | 0.1067 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| CS | 3-star | 0.2984 | 0.2984 | 0.2984 | 0.0000 | 0.0000 | 1.0000 | 0.0100 |
| EE | degree | 0.0086 | 0.0057 | 0.0057 | 0.0030 | 0.0074 | 0.6000 | 0.0000 |
| EE | 2-star | 0.0250 | 0.0250 | 0.0250 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| EE | 3-star | 0.0402 | 0.0402 | 0.0402 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 1 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | return size(project(P, D)) ; aggregate: total / n |
| PM | degree | 2 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 3 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | size_P = size(P) ; return size_P ; aggregate: total / n |
| PM | degree | 5 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | size_projected = size(project(P, D)) ; return size_projected ; aggregate: total / n |
| PM | degree | 6 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 7 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 8 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | return size(project(P, D)) ; aggregate: total / n |
| PM | degree | 9 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | return size(project(P, D)) ; aggregate: total / n |
| PM | degree | 10 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 11 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 12 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 13 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 14 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | return size(project(P, D)) ; aggregate: total / n |
| PM | degree | 15 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | size_P = size(P) ; return size_P ; aggregate: total / n |
| PM | degree | 17 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 18 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 19 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | size_projected = size(project(P, D)) ; return size_projected ; aggregate: total / n |
| PM | 2-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | size_PD = size(project(P, D)) ; return comb(size_PD, 2) ; aggregate: total |
| PM | 2-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | projected_p = project(P, D) ; size_p = size(projected_p) ; return comb(size_p, 2) ; aggregate: total |
| PM | 2-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | size_proj = size(project(P, D)) ; return comb(size_proj, 2) ; aggregate: total |
| PM | 2-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; report = comb(degree, 2) ; return report ; aggregate: total |
| PM | 2-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | degree = size(project(P, D)) ; contribution = comb(degree, 2) ; return contribution ; aggregate: total |
| PM | 2-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | projected = project(P, D) ; k = size(projected) ; return comb(k, 2) ; aggregate: total |
| PM | 2-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; report = comb(degree, 2) ; return report ; aggregate: total |
| PM | 2-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | d = size(P) ; d_proj = min(d, D) ; contribution = comb(d_proj, 2) ; return contribution ; aggregate: total |
| PM | 2-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | projected_P = project(P, D) ; size_projected_P = size(projected_P) ; return comb(size_projected_P, 2) ; aggregate: total |
| PM | 2-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | projected_neighbors = project(P, D) ; size_projected = size(projected_neighbors) ; return comb(size_projected, 2) ; aggregate: total |
| PM | 2-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | d = size(project(P, D)) ; return comb(d, 2) ; aggregate: total |
| PM | 2-star | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | degree = size(project(P, D)) ; stars = comb(degree, 2) ; return stars ; aggregate: total |
| PM | 2-star | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | projected = project(P, D) ; size_proj = size(projected) ; count = comb(size_proj, 2) ; return count ; aggregate: total |
| PM | 2-star | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; count = comb(degree, 2) ; return count ; aggregate: total |
| PM | 2-star | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | size_P = size(project(P, D)) ; comb_size = comb(size_P, 2) ; return comb_size ; aggregate: total |
| PM | 2-star | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | project_P = project(P, D) ; size_projected = size(project_P) ; return comb(size_projected, 2) ; aggregate: total |
| PM | 2-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 2) ; aggregate: total |
| PM | 2-star | 17 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| PM | 2-star | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| PM | 2-star | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; count = comb(degree, 2) ; return count ; aggregate: total |
| PM | 3-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| PM | 3-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| PM | 3-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; count = comb(degree, 3) ; return count ; aggregate: total |
| PM | 3-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | proj = project(P, D) ; d = size(proj) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| PM | 3-star | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_P = project(P, D) ; size_P = size(projected_P) ; stars = comb(size_P, 3) ; return stars ; aggregate: total |
| PM | 3-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | bounded_degree = size(project(P, D)) ; return comb(bounded_degree, 3) ; aggregate: total |
| PM | 3-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| PM | 3-star | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected = project(P, D) ; d = size(projected) ; return d * (d - 1) * (d - 2) / 6 ; aggregate: total |
| PM | 3-star | 11 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| PM | 3-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | k = size(project(P, D)) ; return comb(k, 3) ; aggregate: total |
| PM | 3-star | 13 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| PM | 3-star | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | d = size(project(P, D)) ; term = d * (d - 1) * (d - 2) ; return term / 6 ; aggregate: total |
| PM | 3-star | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| CU | degree | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 1 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 2 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0083 | - | 0.0222 | 0.0005797 | return size(project(P, D)) ; aggregate: total / n |
| CU | degree | 3 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | size_P = size(P) ; return size_P ; aggregate: total / n |
| CU | degree | 5 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 6 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | degree = size(P) ; return degree ; aggregate: total / n |
| CU | degree | 8 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0083 | - | 0.0222 | 0.0005797 | return size(project(P, D)) ; aggregate: total / n |
| CU | degree | 9 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 10 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 11 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 12 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 13 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 14 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0083 | - | 0.0222 | 0.0005797 | return size(project(P, D)) ; aggregate: total / n |
| CU | degree | 15 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | degree | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | report = size(P) ; return report ; aggregate: total / n |
| CU | degree | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | size_P = size(P) ; return size_P ; aggregate: total / n |
| CU | degree | 18 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0083 | - | 0.0222 | 0.0005797 | return size(project(P, D)) ; aggregate: total / n |
| CU | degree | 19 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0216 | 0.0000 | return size(P) ; aggregate: total / n |
| CU | 2-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; count = comb(degree, 2) ; return count ; aggregate: total |
| CU | 2-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| CU | 2-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | size_P = size(project(P, D)) ; count = comb(size_P, 2) ; return count ; aggregate: total |
| CU | 2-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; stars = comb(degree, 2) ; return stars ; aggregate: total |
| CU | 2-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return comb(degree, 2) ; aggregate: total |
| CU | 2-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| CU | 2-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 2) ; aggregate: total |
| CU | 2-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | projected_P = project(P, D) ; size_P = size(projected_P) ; return comb(size_P, 2) ; aggregate: total |
| CU | 2-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; contribution = comb(degree, 2) ; return contribution ; aggregate: total |
| CU | 2-star | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | projected = project(P, D) ; count = comb(size(projected), 2) ; return count ; aggregate: total |
| CU | 2-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | size_n = size(project(P, D)) ; return comb(size_n, 2) ; aggregate: total |
| CU | 2-star | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 2) ; aggregate: total |
| CU | 2-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | projected_neighbors = project(P, D) ; projected_degree = size(projected_neighbors) ; report = comb(projected_degree, 2) ; return report ; aggregate: total |
| CU | 2-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 2) ; aggregate: total |
| CU | 2-star | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | projected = project(P, D) ; size_projected = size(projected) ; count = comb(size_projected, 2) ; return count ; aggregate: total |
| CU | 2-star | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | d = size(project(P, D)) ; return comb(d, 2) ; aggregate: total |
| CU | 2-star | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | size_p = size(project(P, D)) ; count = comb(size_p, 2) ; return count ; aggregate: total |
| CU | 2-star | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; two_stars = comb(degree, 2) ; return two_stars ; aggregate: total |
| CU | 2-star | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 2) ; aggregate: total |
| CU | 2-star | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0141 | - | 0.0985 | 0.0000 | degree = size(project(P, D)) ; count = (degree * (degree - 1)) / 2 ; return count ; aggregate: total |
| CU | 3-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 3) ; aggregate: total |
| CU | 3-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | projected_p = project(P, D) ; size_p = size(projected_p) ; return comb(size_p, 3) ; aggregate: total |
| CU | 3-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| CU | 3-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| CU | 3-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 3) ; aggregate: total |
| CU | 3-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| CU | 3-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | size_P = size(project(P, D)) ; return (size_P * (size_P - 1) * (size_P - 2)) / 6 ; aggregate: total |
| CU | 3-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | stars = comb(size(project(P, D)), 3) ; return stars ; aggregate: total |
| CU | 3-star | 8 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| CU | 3-star | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 3) ; aggregate: total |
| CU | 3-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 3) ; aggregate: total |
| CU | 3-star | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| CU | 3-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| CU | 3-star | 13 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| CU | 3-star | 14 | True | 1 | 3 | True | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| CU | 3-star | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | size_projected = size(project(P, D)) ; contrib = comb(size_projected, 3) ; return contrib ; aggregate: total |
| CU | 3-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| CU | 3-star | 17 | True | 1 | 3 | True | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| CU | 3-star | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | d = size(project(P, D)) ; term = d * (d - 1) * (d - 2) / 6 ; return term ; aggregate: total |
| CU | 3-star | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0133 | - | 0.4195 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; term = (degree * (degree - 1) * (degree - 2)) / 6 ; return term ; aggregate: total |
| Do | degree | 0 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 1 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | return size(project(P, D)) ; aggregate: total / n |
| Do | degree | 2 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | size_projected = size(project(P, D)) ; return size_projected ; aggregate: total / n |
| Do | degree | 3 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | return size(project(P, D)) ; aggregate: total / n |
| Do | degree | 4 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | return size(project(P, D)) ; aggregate: total / n |
| Do | degree | 5 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 6 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 7 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | return size(project(P, D)) ; aggregate: total / n |
| Do | degree | 8 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | return size(project(P, D)) ; aggregate: total / n |
| Do | degree | 9 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | degree = size(P) ; return degree ; aggregate: total / n |
| Do | degree | 11 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 12 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 13 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | return size(project(P, D)) ; aggregate: total / n |
| Do | degree | 14 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0097 | - | 0.0192 | 0.0022 | size_projected = size(project(P, D)) ; return size_projected ; aggregate: total / n |
| Do | degree | 15 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 16 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 17 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 18 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | degree | 19 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0169 | 0.0000 | return size(P) ; aggregate: total / n |
| Do | 2-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| Do | 2-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | projected_P = project(P, D) ; num_2stars = comb(size(projected_P), 2) ; return num_2stars ; aggregate: total |
| Do | 2-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| Do | 2-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| Do | 2-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return comb(degree, 2) ; aggregate: total |
| Do | 2-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; stars = comb(degree, 2) ; return stars ; aggregate: total |
| Do | 2-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| Do | 2-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | p_proj = project(P, D) ; s = size(p_proj) ; return comb(s, 2) ; aggregate: total |
| Do | 2-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 2) ; aggregate: total |
| Do | 2-star | 9 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| Do | 2-star | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 2) ; aggregate: total |
| Do | 2-star | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | projected_P = project(P, D) ; size_projected_P = size(projected_P) ; return comb(size_projected_P, 2) ; aggregate: total |
| Do | 2-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | size_proj = size(project(P, D)) ; return comb(size_proj, 2) ; aggregate: total |
| Do | 2-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; stars = comb(degree, 2) ; return stars ; aggregate: total |
| Do | 2-star | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return comb(degree, 2) ; aggregate: total |
| Do | 2-star | 15 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| Do | 2-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | projected_P = project(P, D) ; d = size(projected_P) ; return comb(d, 2) ; aggregate: total |
| Do | 2-star | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | d = size(project(P, D)) ; return comb(d, 2) ; aggregate: total |
| Do | 2-star | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | 2-star | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0608 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1)) / 2 ; aggregate: total |
| Do | 3-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| Do | 3-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | projected = project(P, D) ; size_projected = size(projected) ; term = comb(size_projected, 3) ; return term ; aggregate: total |
| Do | 3-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | degree = size(project(P, D)) ; stars = (degree * (degree - 1) * (degree - 2)) / 6 ; return stars ; aggregate: total |
| Do | 3-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| Do | 3-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; count = comb(degree, 3) ; return count ; aggregate: total |
| Do | 3-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 3) ; aggregate: total |
| Do | 3-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | size_P = size(project(P, D)) ; return size_P * (size_P - 1) * (size_P - 2) / 6 ; aggregate: total |
| Do | 3-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | proj = project(P, D) ; degree = size(proj) ; count = degree * (degree - 1) * (degree - 2) / 6 ; return count ; aggregate: total |
| Do | 3-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | proj = project(P, D) ; degree = size(proj) ; count = comb(degree, 3) ; return count ; aggregate: total |
| Do | 3-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| Do | 3-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | degree = size(project(P, D)) ; num_3stars = degree * (degree - 1) * (degree - 2) / 6 ; return num_3stars ; aggregate: total |
| Do | 3-star | 11 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | return comb( size(project(P, D)), 3 ) ; aggregate: total |
| Do | 3-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | projected_p = project(P, D) ; size_projected_p = size(projected_p) ; return comb(size_projected_p, 3) ; aggregate: total |
| Do | 3-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | projected_P = project(P, D) ; size_projected = size(projected_P) ; return comb(size_projected, 3) ; aggregate: total |
| Do | 3-star | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| Do | 3-star | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| Do | 3-star | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; count = (degree * (degree - 1) * (degree - 2)) / 6 ; return count ; aggregate: total |
| Do | 3-star | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| Do | 3-star | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| Do | 3-star | 19 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0176 | - | 0.1783 | 0.0000 | q = project(P, D) ; d = size(q) ; count = comb(d, 3) ; return count ; aggregate: total |
| ML | degree | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 1 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 2 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | size_P = size(P) ; return size_P ; aggregate: total / n |
| ML | degree | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | size_P = size(P) ; return size_P ; aggregate: total / n |
| ML | degree | 5 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 6 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 7 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 8 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | size_P = size(P) ; return size_P ; aggregate: total / n |
| ML | degree | 10 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 11 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 12 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0120 | - | 0.0183 | 0.0066 | return size(project(P, D)) ; aggregate: total / n |
| ML | degree | 13 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 14 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 15 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0120 | - | 0.0183 | 0.0066 | return size(project(P, D)) ; aggregate: total / n |
| ML | degree | 16 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 17 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 18 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0120 | - | 0.0183 | 0.0066 | return size(project(P, D)) ; aggregate: total / n |
| ML | degree | 19 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | 2-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| ML | 2-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | k = size(project(P, D)) ; return comb(k, 2) ; aggregate: total |
| ML | 2-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| ML | 2-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 2) ; aggregate: total |
| ML | 2-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | d = size(project(P, D)) ; return comb(d, 2) ; aggregate: total |
| ML | 2-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 2) ; aggregate: total |
| ML | 2-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | projected_P = project(P, D) ; size_projected_P = size(projected_P) ; return comb(size_projected_P, 2) ; aggregate: total |
| ML | 2-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | projected_P = project(P, D) ; size_P = size(projected_P) ; report = comb(size_P, 2) ; return report ; aggregate: total |
| ML | 2-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 2) ; aggregate: total |
| ML | 2-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| ML | 2-star | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | k = size(project(P, D)) ; return comb(k, 2) ; aggregate: total |
| ML | 2-star | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | projected_neighbors = project(P, D) ; degree = size(projected_neighbors) ; return comb(degree, 2) ; aggregate: total |
| ML | 2-star | 12 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| ML | 2-star | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; stars = comb(degree, 2) ; return stars ; aggregate: total |
| ML | 2-star | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; stars = comb(degree, 2) ; return stars ; aggregate: total |
| ML | 2-star | 15 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| ML | 2-star | 16 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 2) ; aggregate: total |
| ML | 2-star | 17 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| ML | 2-star | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| ML | 2-star | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | projected_p = project(P, D) ; size_p = size(projected_p) ; return comb(size_p, 2) ; aggregate: total |
| ML | 3-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; count = comb(degree, 3) ; return count ; aggregate: total |
| ML | 3-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | projected = project(P, D) ; size_p = size(projected) ; return comb(size_p, 3) ; aggregate: total |
| ML | 3-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| ML | 3-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| ML | 3-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| ML | 3-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| ML | 3-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| ML | 3-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| ML | 3-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | q = project(P, D) ; deg = size(q) ; return comb(deg, 3) ; aggregate: total |
| ML | 3-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 3) ; aggregate: total |
| ML | 3-star | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; count = comb(degree, 3) ; return count ; aggregate: total |
| ML | 3-star | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| ML | 3-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| ML | 3-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 3) ; aggregate: total |
| ML | 3-star | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| ML | 3-star | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | projected_P = project(P, D) ; size_P = size(projected_P) ; return comb(size_P, 3) ; aggregate: total |
| ML | 3-star | 16 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | return comb( size( project( P, D ) ), 3 ) ; aggregate: total |
| ML | 3-star | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; count = comb(degree, 3) ; return count ; aggregate: total |
| ML | 3-star | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| ML | 3-star | 19 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| CS | degree | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 1 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 2 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0084 | - | 0.0263 | 0.0014 | size_projected = size(project(P, D)) ; return size_projected ; aggregate: total / n |
| CS | degree | 3 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 4 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | size_P = size(P) ; return size_P ; aggregate: total / n |
| CS | degree | 6 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0084 | - | 0.0263 | 0.0014 | projected_P = project(P, D) ; return size(projected_P) ; aggregate: total / n |
| CS | degree | 7 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 8 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 9 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 10 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0084 | - | 0.0263 | 0.0014 | return size(project(P, D)) ; aggregate: total / n |
| CS | degree | 11 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | size_p = size(P) ; return size_p ; aggregate: total / n |
| CS | degree | 13 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | sum_size = size(P) ; return sum_size ; aggregate: total / n |
| CS | degree | 15 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0084 | - | 0.0263 | 0.0014 | return size(project(P, D)) ; aggregate: total / n |
| CS | degree | 16 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 17 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 18 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 19 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0084 | - | 0.0263 | 0.0014 | return size(project(P, D)) ; aggregate: total / n |
| CS | 2-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 2) ; aggregate: total |
| CS | 2-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | d = size(project(P, D)) ; return comb(d, 2) ; aggregate: total |
| CS | 2-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; count = comb(degree, 2) ; return count ; aggregate: total |
| CS | 2-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | size_p = size(project(P, D)) ; count = comb(size_p, 2) ; return count ; aggregate: total |
| CS | 2-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | projected_P = project(P, D) ; size_projected = size(projected_P) ; count = comb(size_projected, 2) ; return count ; aggregate: total |
| CS | 2-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| CS | 2-star | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | projected_P = project(P, D) ; size_P = size(projected_P) ; return comb(size_P, 2) ; aggregate: total |
| CS | 2-star | 7 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| CS | 2-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 2) ; aggregate: total |
| CS | 2-star | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | projected = project(P, D) ; size_proj = size(projected) ; count = comb(size_proj, 2) ; return count ; aggregate: total |
| CS | 2-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | size_projected = size(project(P, D)) ; count = comb(size_projected, 2) ; return count ; aggregate: total |
| CS | 2-star | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | projected_p = project(P, D) ; k = size(projected_p) ; count = comb(k, 2) ; return count ; aggregate: total |
| CS | 2-star | 12 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| CS | 2-star | 13 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| CS | 2-star | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| CS | 2-star | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | size_deg = size(project(P, D)) ; two_stars = comb(size_deg, 2) ; return two_stars ; aggregate: total |
| CS | 2-star | 16 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| CS | 2-star | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| CS | 2-star | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | size_P_proj = size(project(P, D)) ; return comb(size_P_proj, 2) ; aggregate: total |
| CS | 2-star | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | neighbors = project(P, D) ; num_neighbors = size(neighbors) ; return comb(num_neighbors, 2) ; aggregate: total |
| CS | 3-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 3) ; aggregate: total |
| CS | 3-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 3) ; aggregate: total |
| CS | 3-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | d = size(project(P, D)) ; stars = comb(d, 3) ; return stars ; aggregate: total |
| CS | 3-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| CS | 3-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | d = size(project(P, D)) ; count = comb(d, 3) ; return count ; aggregate: total |
| CS | 3-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | degree = size(project(P, D)) ; count = degree * (degree - 1) * (degree - 2) / 6 ; return count ; aggregate: total |
| CS | 3-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| CS | 3-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | d_proj = size(project(P, D)) ; return comb(d_proj, 3) ; aggregate: total |
| CS | 3-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 3) ; aggregate: total |
| CS | 3-star | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | proj_p = project(P, D) ; d = size(proj_p) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| CS | 3-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | projected = project(P, D) ; size_deg = size(projected) ; return size_deg * (size_deg - 1) * (size_deg - 2) / 6 ; aggregate: total |
| CS | 3-star | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | degree = size(project(P, D)) ; count = comb(degree, 3) ; return count ; aggregate: total |
| CS | 3-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | degree_projected = size(project(P, D)) ; return comb(degree_projected, 3) ; aggregate: total |
| CS | 3-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | size_projected = size(project(P, D)) ; term = size_projected * (size_projected - 1) * (size_projected - 2) ; return term / 6 ; aggregate: total |
| CS | 3-star | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 3) ; aggregate: total |
| CS | 3-star | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 3) ; aggregate: total |
| CS | 3-star | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| CS | 3-star | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 3) ; aggregate: total |
| CS | 3-star | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | projected_P = project(P, D) ; size_P = size(projected_P) ; return comb(size_P, 3) ; aggregate: total |
| CS | 3-star | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | projected = project(P, D) ; size_projected = size(projected) ; return (size_projected * (size_projected - 1) * (size_projected - 2)) / 6 ; aggregate: total |
| EE | degree | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 1 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 2 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 3 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0094 | - | 0.0131 | 0.0074 | return size(project(P, D)) ; aggregate: total / n |
| EE | degree | 4 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 5 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0094 | - | 0.0131 | 0.0074 | size_projected = size(project(P, D)) ; return size_projected ; aggregate: total / n |
| EE | degree | 6 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 7 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 8 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0094 | - | 0.0131 | 0.0074 | return size(project(P, D)) ; aggregate: total / n |
| EE | degree | 9 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0094 | - | 0.0131 | 0.0074 | projected_P = project(P, D) ; return size(projected_P) ; aggregate: total / n |
| EE | degree | 10 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0094 | - | 0.0131 | 0.0074 | return size(project(P, D)) ; aggregate: total / n |
| EE | degree | 11 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 12 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0094 | - | 0.0131 | 0.0074 | return size(project(P, D)) ; aggregate: total / n |
| EE | degree | 13 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 14 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 15 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0094 | - | 0.0131 | 0.0074 | return size(project(P, D)) ; aggregate: total / n |
| EE | degree | 16 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 17 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 18 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0094 | - | 0.0131 | 0.0074 | size_projected = size(project(P, D)) ; return size_projected ; aggregate: total / n |
| EE | degree | 19 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | 2-star | 0 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | proj = project(P, D) ; d = size(proj) ; return comb(d, 2) ; aggregate: total |
| EE | 2-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | size_P = size(project(P, D)) ; count = comb(size_P, 2) ; return count ; aggregate: total |
| EE | 2-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 2) ; aggregate: total |
| EE | 2-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | projected_P = project(P, D) ; size_projected = size(projected_P) ; return comb(size_projected, 2) ; aggregate: total |
| EE | 2-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 2) ; aggregate: total |
| EE | 2-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| EE | 2-star | 6 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | return comb( size( project(P, D) ), 2 ) ; aggregate: total |
| EE | 2-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | projected_P = project(P, D) ; count = comb(size(projected_P), 2) ; return count ; aggregate: total |
| EE | 2-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 2) ; aggregate: total |
| EE | 2-star | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | proj = project(P, D) ; k = size(proj) ; return comb(k, 2) ; aggregate: total |
| EE | 2-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | projected_neighbors = project(P, D) ; size_deg = size(projected_neighbors) ; return comb(size_deg, 2) ; aggregate: total |
| EE | 2-star | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| EE | 2-star | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | projected_P = project(P, D) ; size_projected_P = size(projected_P) ; return comb(size_projected_P, 2) ; aggregate: total |
| EE | 2-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| EE | 2-star | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 2) ; aggregate: total |
| EE | 2-star | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | d = size(project(P, D)) ; return comb(d, 2) ; aggregate: total |
| EE | 2-star | 16 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| EE | 2-star | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | count = comb(size(project(P, D)), 2) ; return count ; aggregate: total |
| EE | 2-star | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| EE | 2-star | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | degree = size(project(P, D)) ; stars = (degree * (degree - 1)) / 2 ; return stars ; aggregate: total |
| EE | 3-star | 0 | True | 1 | 3 | True | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| EE | 3-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | size_proj = size(project(P, D)) ; return comb(size_proj, 3) ; aggregate: total |
| EE | 3-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | size_p = size(project(P, D)) ; value = comb(size_p, 3) ; return value ; aggregate: total |
| EE | 3-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | projected_P = project(P, D) ; size_p = size(projected_P) ; c = comb(size_p, 3) ; return c ; aggregate: total |
| EE | 3-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | s = size(project(P, D)) ; c = s * (s - 1) * (s - 2) / 6 ; return c ; aggregate: total |
| EE | 3-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| EE | 3-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| EE | 3-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 3) ; aggregate: total |
| EE | 3-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | d = size(project(P, D)) ; return d * (d - 1) * (d - 2) / 6 ; aggregate: total |
| EE | 3-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| EE | 3-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; count = comb(degree, 3) ; return count ; aggregate: total |
| EE | 3-star | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| EE | 3-star | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return comb(degree, 3) ; aggregate: total |
| EE | 3-star | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| EE | 3-star | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; count = (degree * (degree - 1) * (degree - 2)) / 6 ; return count ; aggregate: total |
| EE | 3-star | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| EE | 3-star | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; count = comb(degree, 3) ; return count ; aggregate: total |
| EE | 3-star | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | size_p = size(project(P, D)) ; count = comb(size_p, 3) ; return count ; aggregate: total |
| EE | 3-star | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | degree_proj = size(project(P, D)) ; return comb(degree_proj, 3) ; aggregate: total |
| EE | 3-star | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return comb(degree, 3) ; aggregate: total |
