# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 20 independent design(s), 3 draft(s) x up to 1 restart(s) per release (rows, matrix), selection simulated (public Holme-Kim graphs, average degrees 4,8,16, 8 releases each, never chosen at a score >= 1; run-time choice on Chung-Lu graphs of the published noisy degrees), own-row check on, tighten 1, early stop off, normalisation on, prompt v1-alt (core v1-alt, b3ea0cb2b6add266), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate off.

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio | mean_candidates | runs_matrix | runs_rows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ML | degree | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.7000 | 1.3684 | 1.0000 | 4.0000 | 4 | 0.7368 | 0.7895 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0526 | 0.9500 | 0.0000 | 0.0000 |
| ML | 2-star | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.2000 | 1.8421 | 1.0000 | 4.1500 | 12 | 0.2632 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9500 | 0.0000 | 0.0000 |
| ML | 3-star | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.3500 | 1.6316 | 1.0000 | 3.4500 | 13 | 0.2105 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9500 | 0.0000 | 0.0000 |
| ML | triangle | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.3500 | 1.7895 | 1.0000 | 4.0000 | 18 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.5619 | 1.7000 | 0.2105 | 0.7895 |
| CS | degree | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.6500 | 1.3158 | 1.0000 | 3.8000 | 5 | 0.6316 | 0.6842 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0789 | 0.9500 | 0.0000 | 0.0000 |
| CS | 2-star | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.2500 | 1.7368 | 1.0000 | 3.9500 | 12 | 0.2105 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9500 | 0.0000 | 0.0000 |
| CS | 3-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.2500 | 1.8000 | 1.0000 | 3.6000 | 11 | 0.3000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| CS | triangle | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.4500 | 1.6842 | 1.0000 | 3.9000 | 19 | 0.0000 | 0.9474 | 1.0000 | 1.0000 | 1.0000 | 0.9717 | 1.0000 | 0.5894 | 1.6000 | 0.2700 | 0.7300 |
| EE | degree | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.6000 | 1.4737 | 1.0000 | 4.0000 | 4 | 0.5789 | 0.6316 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0921 | 0.9500 | 0.0000 | 0.0000 |
| EE | 2-star | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.2000 | 1.7895 | 1.0000 | 4.2500 | 16 | 0.1579 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9500 | 0.0000 | 0.0000 |
| EE | 3-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.2000 | 1.9000 | 1.0000 | 3.6500 | 16 | 0.1000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| EE | triangle | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.4000 | 1.6500 | 1.0000 | 4.0000 | 20 | 0.0000 | 0.8500 | 1.0000 | 1.0000 | 1.0000 | 0.9193 | 1.0000 | 0.9101 | 1.6500 | 0.8370 | 0.1630 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| ML | degree | 0.0130 | 0.0116 | 0.0116 | 0.0014 | 0.0066 | 0.7895 | 0.0000 |
| ML | 2-star | 0.0388 | 0.0388 | 0.0388 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| ML | 3-star | 0.0645 | 0.0645 | 0.0645 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| ML | triangle | 0.1808 | 0.1545 | 0.2795 | -0.0987 | 0.0000 | 0.2105 | 0.0000 |
| CS | degree | 0.0253 | 0.0249 | 0.0249 | 0.0004557 | 0.0014 | 0.6842 | 0.0000 |
| CS | 2-star | 0.1067 | 0.1067 | 0.1067 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| CS | 3-star | 0.2984 | 0.2984 | 0.2984 | 0.0000 | 0.0000 | 1.0000 | 0.0100 |
| CS | triangle | 0.9980 | 0.8204 | 1.4757 | -0.4777 | 0.0000 | 0.2704 | 0.1053 |
| EE | degree | 0.0084 | 0.0057 | 0.0057 | 0.0027 | 0.0074 | 0.6316 | 0.0000 |
| EE | 2-star | 0.0250 | 0.0250 | 0.0250 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| EE | 3-star | 0.0402 | 0.0402 | 0.0402 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| EE | triangle | 0.2432 | 0.2625 | 0.2680 | -0.0248 | 0.0000 | 0.8370 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ML | degree | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 1 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0120 | - | 0.0183 | 0.0066 | return size(project(P, D)) ; aggregate: total / n |
| ML | degree | 2 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 3 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 4 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 5 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 6 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 7 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0120 | - | 0.0183 | 0.0066 | return size(project(P, D)) ; aggregate: total / n |
| ML | degree | 8 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0120 | - | 0.0183 | 0.0066 | return size(project(P, D)) ; aggregate: total / n |
| ML | degree | 9 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 10 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 11 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 12 | True | 1 | 3 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 13 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0120 | - | 0.0183 | 0.0066 | size_projected = size(project(P, D)) ; return size_projected ; aggregate: total / n |
| ML | degree | 14 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | degree | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | size_P = size(P) ; return size_P ; aggregate: total / n |
| ML | degree | 17 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 18 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | degree | 19 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0116 | 0.0000 | return size(P) ; aggregate: total / n |
| ML | 2-star | 0 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| ML | 2-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return comb(degree, 2) ; aggregate: total |
| ML | 2-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| ML | 2-star | 3 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| ML | 2-star | 4 | True | 1 | 3 | True | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| ML | 2-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | k = size(project(P, D)) ; return (k * (k - 1)) / 2 ; aggregate: total |
| ML | 2-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| ML | 2-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | size_S = size(project(P, D)) ; return comb(size_S, 2) ; aggregate: total |
| ML | 2-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| ML | 2-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | s = size(project(P, D)) ; return comb(s, 2) ; aggregate: total |
| ML | 2-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| ML | 2-star | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | 2-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | degree = size(project(P, D)) ; return (degree * (degree - 1)) / 2 ; aggregate: total |
| ML | 2-star | 13 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| ML | 2-star | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; stars = degree * (degree - 1) / 2 ; return stars ; aggregate: total |
| ML | 2-star | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | return 0.5 * size(project(P, D)) * (size(project(P, D)) - 1) ; aggregate: total |
| ML | 2-star | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 2) ; aggregate: total |
| ML | 2-star | 17 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| ML | 2-star | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 2) ; aggregate: total |
| ML | 2-star | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0156 | - | 0.0388 | 0.0000 | projected_P = project(P, D) ; size_P = size(projected_P) ; count = comb(size_P, 2) ; return count ; aggregate: total |
| ML | 3-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| ML | 3-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| ML | 3-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | proj = project(P, D) ; d = size(proj) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| ML | 3-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| ML | 3-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 3) ; aggregate: total |
| ML | 3-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| ML | 3-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | k = size(project(P, D)) ; return comb(k, 3) ; aggregate: total |
| ML | 3-star | 7 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| ML | 3-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | degree = size(project(P, D)) ; count = degree * (degree - 1) * (degree - 2) / 6 ; return count ; aggregate: total |
| ML | 3-star | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return comb(degree, 3) ; aggregate: total |
| ML | 3-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| ML | 3-star | 11 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | return comb( size(project(P, D)), 3 ) ; aggregate: total |
| ML | 3-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | s = size(project(P, D)) ; return (s * (s - 1) * (s - 2)) / 6 ; aggregate: total |
| ML | 3-star | 13 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | 3-star | 14 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| ML | 3-star | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| ML | 3-star | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| ML | 3-star | 17 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| ML | 3-star | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | projected = project(P, D) ; size_proj = size(projected) ; return comb(size_proj, 3) ; aggregate: total |
| ML | 3-star | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0112 | - | 0.0645 | 0.0000 | size_N_self = size(project(P, D)) ; return comb(size_N_self, 3) ; aggregate: total |
| ML | triangle | 0 | True | 1 | 3 | False | True | 0.4451 | True | True | 0.1836 | - | 0.1545 | -0.1250 | return sum(sum(A(u, w) for w in project(P, D)) for u in project(P, D)) / 2 ; aggregate: total / 3 |
| ML | triangle | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1836 | - | 0.2795 | 0.0000 | proj = project(P, D) ; total_pairs = sum( sum( A(v, w) for w in proj ) for v in proj ) ; return total_pairs / 2 ; aggregate: total / 3 |
| ML | triangle | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1836 | - | 0.2795 | 0.0000 | contribution = sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) ; return contribution ; aggregate: total / 6 |
| ML | triangle | 3 | True | 1 | 3 | False | True | 0.4451 | True | True | 0.1836 | - | 0.1545 | -0.1250 | contribution = 0.5 * sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return contribution ; aggregate: total / 3 |
| ML | triangle | 4 | True | 1 | 1 | False | True | 0.4451 | True | True | 0.1836 | - | 0.1545 | -0.1250 | return sum( sum( A(u, v) for v in project(P, D) ) for u in project(P, D) ) / 2 ; aggregate: total / 3 |
| ML | triangle | 5 | True | 1 | 3 | False | True | 0.4451 | True | True | 0.1836 | - | 0.1545 | -0.1250 | S = project(P, D) ; sum_total = sum( sum( A(v, w) for w in S ) for v in S ) ; edges_between_neighbors = sum_total / 2 ; return edges_between_neighbors ; aggregate: total / 3 |
| ML | triangle | 6 | True | 1 | 1 | False | True | 0.4451 | True | True | 0.1836 | - | 0.1545 | -0.1250 | S = project(P, D) ; return sum( sum( A(v, w) for w in S ) for v in S ) / 2 ; aggregate: total / 3 |
| ML | triangle | 7 | True | 1 | 1 | False | True | 0.4451 | True | True | 0.1836 | - | 0.1545 | -0.1250 | S = project(P, D) ; sum_ordered = sum( sum( A(v, w) for w in S ) for v in S ) ; return 0.5 * sum_ordered ; aggregate: total / 3 |
| ML | triangle | 8 | True | 1 | 1 | False | True | 0.4451 | True | True | 0.1836 | - | 0.1545 | -0.1250 | S = project(P, D) ; edges_between_neighbors = 0.5 * sum(sum(A(u, v) for u in S) for v in S) ; return edges_between_neighbors ; aggregate: total / 3 |
| ML | triangle | 9 | True | 1 | 2 | False | True | 0.4451 | True | True | 0.1836 | - | 0.1545 | -0.1250 | return 0.5 * sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; aggregate: total / 3 |
| ML | triangle | 10 | True | 1 | 2 | False | True | 0.4451 | True | True | 0.1836 | - | 0.1545 | -0.1250 | projected_P = project(P, D) ; total_pairs = sum( sum( A(v, w) for w in projected_P ) for v in projected_P ) ; return total_pairs / 2 ; aggregate: total / 3 |
| ML | triangle | 11 | True | 1 | 2 | False | True | 0.4451 | True | True | 0.1836 | - | 0.1545 | -0.1250 | return 0.5 * sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; aggregate: total / 3 |
| ML | triangle | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1836 | - | 0.2795 | 0.0000 | sum_uw = sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) ; contribution = sum_uw / 2 ; return contribution ; aggregate: total / 3 |
| ML | triangle | 13 | True | 1 | 1 | False | True | 0.4451 | True | True | 0.1836 | - | 0.1545 | -0.1250 | total_pairs = sum( sum( A(u, v) for v in project(P, D) ) for u in project(P, D) ) ; return total_pairs / 2 ; aggregate: total / 3 |
| ML | triangle | 14 | True | 1 | 2 | False | True | 0.4451 | True | True | 0.1836 | - | 0.1545 | -0.1250 | s = sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) ; return s / 2 ; aggregate: total / 3 |
| ML | triangle | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1836 | - | 0.2795 | 0.0000 | a = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return a / 2 ; aggregate: total / 3 |
| ML | triangle | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle | 17 | True | 1 | 1 | False | True | 0.4451 | True | True | 0.1836 | - | 0.1545 | -0.1250 | neighbors = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in neighbors ) for u in neighbors ) ; contribution = 0.5 * sum_uv ; return contribution ; aggregate: total / 3 |
| ML | triangle | 18 | True | 1 | 2 | False | True | 0.4451 | True | True | 0.1836 | - | 0.1545 | -0.1250 | S = project(P, D) ; sum_vw = sum( sum( A(v, w) for w in S ) for v in S ) ; return sum_vw / 2 ; aggregate: total / 3 |
| ML | triangle | 19 | True | 1 | 2 | False | True | 0.4451 | True | True | 0.1836 | - | 0.1545 | -0.1250 | sum_pairs = sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) ; return sum_pairs / 2 ; aggregate: total / 3 |
| CS | degree | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 1 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 2 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 3 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0084 | - | 0.0263 | 0.0014 | return size(project(P, D)) ; aggregate: total / n |
| CS | degree | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | degree | 5 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0084 | - | 0.0263 | 0.0014 | size_projected = size(project(P, D)) ; return size_projected ; aggregate: total / n |
| CS | degree | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | degree = size(P) ; return degree ; aggregate: total / n |
| CS | degree | 7 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0084 | - | 0.0263 | 0.0014 | return size(project(P, D)) ; aggregate: total / n |
| CS | degree | 8 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 9 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 10 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 11 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 12 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0084 | - | 0.0263 | 0.0014 | result = size(project(P, D)) ; return result ; aggregate: total / n |
| CS | degree | 13 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 14 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 15 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 16 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | degree | 17 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0084 | - | 0.0263 | 0.0014 | return size(project(P, D)) ; aggregate: total / n |
| CS | degree | 18 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0084 | - | 0.0263 | 0.0014 | return size(project(P, D)) ; aggregate: total / n |
| CS | degree | 19 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0249 | 0.0000 | return size(P) ; aggregate: total / n |
| CS | 2-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 2) ; aggregate: total |
| CS | 2-star | 1 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| CS | 2-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| CS | 2-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; stars = (degree * (degree - 1)) / 2 ; return stars ; aggregate: total |
| CS | 2-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | size_projected = size(project(P, D)) ; return (size_projected * (size_projected - 1)) / 2 ; aggregate: total |
| CS | 2-star | 5 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | return comb( size( project(P, D) ), 2 ) ; aggregate: total |
| CS | 2-star | 6 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | return comb( size( project(P, D) ), 2 ) ; aggregate: total |
| CS | 2-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | d = size(project(P, D)) ; return comb(d, 2) ; aggregate: total |
| CS | 2-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | stars = comb(size(project(P, D)), 2) ; return stars ; aggregate: total |
| CS | 2-star | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | k = size(project(P, D)) ; return comb(k, 2) ; aggregate: total |
| CS | 2-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| CS | 2-star | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | 2-star | 12 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| CS | 2-star | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 2) ; aggregate: total |
| CS | 2-star | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | return 0.5 * size(project(P, D)) * (size(project(P, D)) - 1) ; aggregate: total |
| CS | 2-star | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 2) ; aggregate: total |
| CS | 2-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| CS | 2-star | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 2) ; aggregate: total |
| CS | 2-star | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 2) ; aggregate: total |
| CS | 2-star | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0153 | - | 0.1067 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| CS | 3-star | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| CS | 3-star | 1 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | return comb( size(project(P, D)), 3 ) ; aggregate: total |
| CS | 3-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| CS | 3-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| CS | 3-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| CS | 3-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | size_projected = size(project(P, D)) ; return (size_projected * (size_projected - 1) * (size_projected - 2)) / 6 ; aggregate: total |
| CS | 3-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | s = size(project(P, D)) ; return (s * (s - 1) * (s - 2)) / 6 ; aggregate: total |
| CS | 3-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| CS | 3-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | k = size(project(P, D)) ; return comb(k, 3) ; aggregate: total |
| CS | 3-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| CS | 3-star | 10 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| CS | 3-star | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | degree = size(project(P, D)) ; return (degree * (degree - 1) * (degree - 2)) / 6 ; aggregate: total |
| CS | 3-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| CS | 3-star | 13 | True | 1 | 3 | True | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| CS | 3-star | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | projected_P = project(P, D) ; return comb( size(projected_P), 3 ) ; aggregate: total |
| CS | 3-star | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| CS | 3-star | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | degree = size(project(P, D)) ; return (degree * (degree - 1) * (degree - 2)) / 6 ; aggregate: total |
| CS | 3-star | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | k = size(project(P, D)) ; return comb(k, 3) ; aggregate: total |
| CS | 3-star | 18 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| CS | 3-star | 19 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0109 | - | 0.2984 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| CS | triangle | 0 | True | 1 | 2 | False | True | 0.4424 | True | True | 0.1016 | - | 0.8204 | -0.6553 | S = project(P, D) ; sum_vw = sum( sum( A(v, w) for w in S ) for v in S ) ; return sum_vw / 2 ; aggregate: total / 3 |
| CS | triangle | 1 | True | 1 | 1 | False | True | 0.4424 | True | True | 0.1016 | - | 0.8204 | -0.6553 | S = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in S ) for u in S ) ; contribution = sum_uv / 2 ; return contribution ; aggregate: total / 3 |
| CS | triangle | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1016 | - | 1.4757 | 0.0000 | s = 0.5 * sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return s ; aggregate: total / 3 |
| CS | triangle | 3 | True | 1 | 1 | False | True | 0.4424 | True | True | 0.1016 | - | 0.8204 | -0.6553 | S = project(P, D) ; sum_A = sum(sum(A(u, v) for v in S) for u in S) ; count = 0.5 * sum_A ; return count ; aggregate: total / 3 |
| CS | triangle | 4 | True | 1 | 2 | False | True | 0.4424 | True | True | 0.1016 | - | 0.8204 | -0.6553 | s = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return 0.5 * s ; aggregate: total / 3 |
| CS | triangle | 5 | True | 1 | 1 | False | True | 0.4424 | True | True | 0.1016 | - | 0.8204 | -0.6553 | S = project(P, D) ; total_pairs = sum( sum( A(v, w) for w in S ) for v in S ) ; return total_pairs / 2 ; aggregate: total / 3 |
| CS | triangle | 6 | True | 1 | 1 | False | True | 0.4424 | True | True | 0.1016 | - | 0.8204 | -0.6553 | S = project(P, D) ; sum_A = sum( sum( A(v, w) for w in S ) for v in S ) ; return 0.5 * sum_A ; aggregate: total / 3 |
| CS | triangle | 7 | True | 1 | 2 | False | True | 0.4424 | True | True | 0.1016 | - | 0.8204 | -0.6553 | neighbors = project(P, D) ; sum_edges = sum(sum(A(v, w) for w in neighbors) for v in neighbors) ; contribution = sum_edges / 2 ; return contribution ; aggregate: total / 3 |
| CS | triangle | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.4757 | 0.0000 | s = sum( sum( A(u, v) for v in project(P, D) ) for u in project(P, D) ) ; return s / 2 ; aggregate: total / 3 |
| CS | triangle | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1016 | - | 1.4757 | 0.0000 | return sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; aggregate: total / 6 |
| CS | triangle | 10 | True | 1 | 1 | False | True | 0.4424 | True | True | 0.1016 | - | 0.8204 | -0.6553 | S = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in S ) for u in S ) ; return sum_uv / 2 ; aggregate: total / 3 |
| CS | triangle | 11 | True | 1 | 3 | False | True | 0.4424 | True | True | 0.1016 | - | 0.8204 | -0.6553 | projected_P = project(P, D) ; sum_over_pairs = sum( sum( A(v, w) for w in projected_P ) for v in projected_P ) ; return sum_over_pairs / 2 ; aggregate: total / 3 |
| CS | triangle | 12 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 13 | True | 1 | 1 | False | True | 0.4424 | True | True | 0.1016 | - | 0.8204 | -0.6553 | S = project(P, D) ; sum_pairs = sum( sum( A(u, w) for w in S ) for u in S ) ; return sum_pairs / 2 ; aggregate: total / 3 |
| CS | triangle | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1016 | - | 1.4757 | 0.0000 | S = project(P, D) ; sum_edges = sum( sum( A(u, w) for w in S ) for u in S ) ; edges_count = 0.5 * sum_edges ; return edges_count ; aggregate: total / 3 |
| CS | triangle | 15 | True | 1 | 2 | False | False | 0.4472 | True | True | 0.7722 | - | 0.9178 | -0.5579 | sum_v = sum(size(project(P, D) & N(u)) for u in project(P, D)) ; count_v = 0.5 * sum_v ; return count_v ; aggregate: total / 3 |
| CS | triangle | 16 | True | 1 | 1 | False | True | 0.4424 | True | True | 0.1016 | - | 0.8204 | -0.6553 | return sum( sum( A(u, v) for v in project(P, D) ) for u in project(P, D) ) / 2 ; aggregate: total / 3 |
| CS | triangle | 17 | True | 1 | 3 | False | True | 0.4424 | True | True | 0.1016 | - | 0.8204 | -0.6553 | projected_neighbors = project(P, D) ; sum_edges = sum(sum(A(v, w) for w in projected_neighbors) for v in projected_neighbors) ; count = sum_edges / 2 ; return count ; aggregate: total / 3 |
| CS | triangle | 18 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1016 | - | 1.4757 | 0.0000 | sum_1 = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; sum_2 = sum_1 / 2 ; return sum_2 ; aggregate: total / 3 |
| CS | triangle | 19 | True | 1 | 1 | False | True | 0.4424 | True | True | 0.1016 | - | 0.8204 | -0.6553 | sum_over_pairs = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; edges_between_neighbors = sum_over_pairs / 2 ; return edges_between_neighbors ; aggregate: total / 3 |
| EE | degree | 0 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0094 | - | 0.0131 | 0.0074 | return size(project(P, D)) ; aggregate: total / n |
| EE | degree | 1 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 2 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 3 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 4 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0094 | - | 0.0131 | 0.0074 | return size(project(P, D)) ; aggregate: total / n |
| EE | degree | 5 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 6 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 7 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0094 | - | 0.0131 | 0.0074 | return size(project(P, D)) ; aggregate: total / n |
| EE | degree | 8 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | size_P = size(P) ; return size_P ; aggregate: total / n |
| EE | degree | 10 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 11 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 12 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0094 | - | 0.0131 | 0.0074 | return size(project(P, D)) ; aggregate: total / n |
| EE | degree | 13 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 14 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0094 | - | 0.0131 | 0.0074 | size_projected = size(project(P, D)) ; return size_projected ; aggregate: total / n |
| EE | degree | 15 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 16 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0094 | - | 0.0131 | 0.0074 | return size(project(P, D)) ; aggregate: total / n |
| EE | degree | 17 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0057 | 0.0000 | return size(P) ; aggregate: total / n |
| EE | degree | 18 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0094 | - | 0.0131 | 0.0074 | return size(project(P, D)) ; aggregate: total / n |
| EE | degree | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | 2-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| EE | 2-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | projected_P = project(P, D) ; size_projected_P = size(projected_P) ; return comb(size_projected_P, 2) ; aggregate: total |
| EE | 2-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | d = size(project(P, D)) ; return 0.5 * d * (d - 1) ; aggregate: total |
| EE | 2-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | contribution = comb(size(project(P, D)), 2) ; return contribution ; aggregate: total |
| EE | 2-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | result = comb(size(project(P, D)), 2) ; return result ; aggregate: total |
| EE | 2-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | projected = project(P, D) ; stars = comb(size(projected), 2) ; return stars ; aggregate: total |
| EE | 2-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 2) ; aggregate: total |
| EE | 2-star | 7 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| EE | 2-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 2) ; aggregate: total |
| EE | 2-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | s = size(project(P, D)) ; return (s * (s - 1)) / 2 ; aggregate: total |
| EE | 2-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | size_projected = size(project(P, D)) ; stars = comb(size_projected, 2) ; return stars ; aggregate: total |
| EE | 2-star | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | proj_P = project(P, D) ; size_proj = size(proj_P) ; return (size_proj * (size_proj - 1)) / 2 ; aggregate: total |
| EE | 2-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | projected_P = project(P, D) ; return comb(size(projected_P), 2) ; aggregate: total |
| EE | 2-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | projected = project(P, D) ; return (size(projected) * (size(projected) - 1)) / 2 ; aggregate: total |
| EE | 2-star | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 2) ; aggregate: total |
| EE | 2-star | 15 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| EE | 2-star | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | 2-star | 17 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | return comb(size(project(P, D)), 2) ; aggregate: total |
| EE | 2-star | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; count = comb(degree, 2) ; return count ; aggregate: total |
| EE | 2-star | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0137 | - | 0.0250 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 2) ; aggregate: total |
| EE | 3-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | degree = size(project(P, D)) ; return (degree * (degree - 1) * (degree - 2)) / 6 ; aggregate: total |
| EE | 3-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| EE | 3-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| EE | 3-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | degree = size(project(P, D)) ; return (degree * (degree - 1) * (degree - 2)) / 6 ; aggregate: total |
| EE | 3-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| EE | 3-star | 5 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | report = comb( size( project(P, D) ), 3 ) ; return report ; aggregate: total |
| EE | 3-star | 6 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total / 1 |
| EE | 3-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | projected_P = project(P, D) ; stars = comb(size(projected_P), 3) ; return stars ; aggregate: total |
| EE | 3-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | degree = size(project(P, D)) ; term1 = degree * (degree - 1) ; term2 = term1 * (degree - 2) ; return term2 / 6 ; aggregate: total |
| EE | 3-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | d = size(project(P, D)) ; term1 = d ; term2 = d - 1 ; term3 = d - 2 ; count = term1 * term2 * term3 / 6 ; return count ; aggregate: total |
| EE | 3-star | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| EE | 3-star | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| EE | 3-star | 12 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | return comb( size( project( P, D ) ), 3 ) ; aggregate: total |
| EE | 3-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | d = size(project(P, D)) ; return d * (d - 1) * (d - 2) / 6 ; aggregate: total |
| EE | 3-star | 14 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| EE | 3-star | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 3) ; aggregate: total |
| EE | 3-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | proj_p = project(P, D) ; d = size(proj_p) ; return d * (d - 1) * (d - 2) / 6 ; aggregate: total |
| EE | 3-star | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | degree = size(project(P, D)) ; return (degree * (degree - 1) * (degree - 2)) / 6 ; aggregate: total |
| EE | 3-star | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | k = size(project(P, D)) ; return (k * (k - 1) * (k - 2)) / 6 ; aggregate: total |
| EE | 3-star | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0126 | - | 0.0402 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| EE | triangle | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1358 | - | 0.2680 | 0.0000 | projected_P = project(P, D) ; sum_v = sum(sum(A(v, w) for w in projected_P) for v in projected_P) ; return 0.5 * sum_v ; aggregate: total / 3 |
| EE | triangle | 1 | True | 1 | 2 | False | False | 0.4487 | True | True | 0.6982 | - | 0.1265 | -0.1415 | result = 0.5 * sum( size( project(P, D) & N(v) ) for v in project(P, D) ) ; return result ; aggregate: total / 3 |
| EE | triangle | 2 | True | 1 | 2 | False | False | 0.4487 | True | True | 0.6982 | - | 0.1265 | -0.1415 | count = sum( size( project(P, D) & N(u) ) for u in project(P, D) ) ; return count ; aggregate: total / 6 |
| EE | triangle | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1358 | - | 0.2680 | 0.0000 | return 0.5 * sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; aggregate: total / 3 |
| EE | triangle | 4 | True | 1 | 1 | False | True | 0.9889 | True | True | 0.1358 | - | 0.2625 | -0.0055 | return (sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) )) / 2 ; aggregate: total / 3 |
| EE | triangle | 5 | True | 1 | 2 | False | True | 0.9889 | True | True | 0.1358 | - | 0.2625 | -0.0055 | Q = project(P, D) ; sum_edges = sum( sum( A(u, v) for v in Q ) for u in Q ) ; return sum_edges / 2 ; aggregate: total / 3 |
| EE | triangle | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1358 | - | 0.2680 | 0.0000 | projected_P = project(P, D) ; sum_over_v_w = sum(sum(A(v, w) for w in projected_P) for v in projected_P) ; triangle_count = 0.5 * sum_over_v_w ; return triangle_count ; aggregate: total / 3 |
| EE | triangle | 7 | True | 1 | 1 | False | True | 0.9889 | True | True | 0.1358 | - | 0.2625 | -0.0055 | projected_neighbors = project(P, D) ; S = projected_neighbors ; sum1 = sum( sum( A(v, w) for w in S ) for v in S ) ; count = sum1 / 2 ; return count ; aggregate: total / 3 |
| EE | triangle | 8 | True | 1 | 2 | False | False | 0.4487 | True | True | 0.6982 | - | 0.1265 | -0.1415 | s = project(P, D) ; sum_size = sum( size(N(v) & s) for v in s ) ; return sum_size / 2 ; aggregate: total / 3 |
| EE | triangle | 9 | True | 1 | 2 | False | True | 0.9889 | True | True | 0.1358 | - | 0.2625 | -0.0055 | sum_vw = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return 0.5 * sum_vw ; aggregate: total / 3 |
| EE | triangle | 10 | True | 1 | 3 | False | True | 0.9889 | True | True | 0.1358 | - | 0.2625 | -0.0055 | projected = project(P, D) ; sum_pairs = sum( sum( A(u, w) for w in projected ) for u in projected ) / 2 ; return sum_pairs ; aggregate: total / 3 |
| EE | triangle | 11 | True | 1 | 2 | False | True | 0.9889 | True | True | 0.1358 | - | 0.2625 | -0.0055 | return (sum(sum(A(v, w) for w in project(P, D)) for v in project(P, D)) / 2) ; aggregate: total / 3 |
| EE | triangle | 12 | True | 1 | 1 | False | True | 0.9889 | True | True | 0.1358 | - | 0.2625 | -0.0055 | return 0.5 * sum( sum( A(u, v) for v in project(P, D) ) for u in project(P, D) ) ; aggregate: total / 3 |
| EE | triangle | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1358 | - | 0.2680 | 0.0000 | sum_over_pairs = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return sum_over_pairs / 2 ; aggregate: total / 3 |
| EE | triangle | 14 | True | 1 | 2 | False | True | 0.9889 | True | True | 0.1358 | - | 0.2625 | -0.0055 | return sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) * 0.5 ; aggregate: total / 3 |
| EE | triangle | 15 | True | 1 | 2 | False | True | 0.9889 | True | True | 0.1358 | - | 0.2625 | -0.0055 | projected = project(P, D) ; sum_edges = sum( sum( A(u, w) for w in projected ) for u in projected ) ; return sum_edges / 2 ; aggregate: total / 3 |
| EE | triangle | 16 | True | 1 | 1 | False | True | 0.9889 | True | True | 0.1358 | - | 0.2625 | -0.0055 | S = project(P, D) ; sum_ordered = sum( sum( A(j, k) for k in S ) for j in S ) ; sum_pairs = 0.5 * sum_ordered ; return sum_pairs ; aggregate: total / 3 |
| EE | triangle | 17 | True | 1 | 1 | False | True | 0.9889 | True | True | 0.1358 | - | 0.2625 | -0.0055 | sum1 = sum( sum(A(u, v) for v in project(P, D)) for u in project(P, D) ) ; return 0.5 * sum1 ; aggregate: total / 3 |
| EE | triangle | 18 | True | 1 | 2 | False | True | 0.9889 | True | True | 0.1358 | - | 0.2625 | -0.0055 | return sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) / 2 ; aggregate: total / 3 |
| EE | triangle | 19 | True | 1 | 1 | False | True | 0.9889 | True | True | 0.1358 | - | 0.2625 | -0.0055 | S = project(P, D) ; inner_sum = sum(sum(A(v, w) for w in S) for v in S) ; term = 0.5 * inner_sum ; return term ; aggregate: total / 3 |
