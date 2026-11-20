# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 20 independent design(s), 3 draft(s) x up to 1 restart(s), selection first, own-row check off, tighten 0, early stop off, normalisation on, prompt v1-alt (core v1-alt, b3ea0cb2b6add266), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate on (τ = 2, 8 releases per graph).

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.3500 | 1.7895 | 1.0000 | 1.8500 | 18 | 0.0526 | 0.8421 | 1.0000 | 1.0000 | 1.0000 | 0.8421 | 1.0000 | 0.8421 |
| PM | 5-star | 20 | 0.9000 | [0.70, 0.97] | 0.9000 | 0.1500 | 2.0556 | 1.0000 | 2.1500 | 10 | 0.3333 | 0.5556 | 1.0000 | 1.0000 | 1.0000 | 0.5556 | 1.0000 | 0.5556 |
| PM | triangle | 20 | 0.6000 | [0.39, 0.78] | 0.6000 | 0.3000 | 1.5833 | 1.0000 | 2.1500 | 12 | 0.0000 | 0.2500 | 1.0000 | 1.0000 | 1.0000 | 0.5966 | 1.0000 | 0.5955 |
| PM | degree-moment2 | 20 | 0.6500 | [0.43, 0.82] | 0.6500 | 0.3000 | 1.7692 | 1.0000 | 2.2000 | 7 | 0.2308 | 0.9231 | 1.0000 | 1.0000 | 1.0000 | 1.2192 | 3.8500 | 1.4518 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0.0190 | 0.0087 | 0.0087 | 0.0103 | 0.0650 | 0.8421 | 0.0000 |
| PM | 5-star | 0.0691 | 0.0176 | 0.0176 | 0.0515 | 0.1159 | 0.5556 | 0.0000 |
| PM | triangle | 1.1820 | 1.5339 | 0.1263 | 1.0557 | 1.4077 | 0.2500 | 0.0000 |
| PM | degree-moment2 | 0.0109 | 0.0074 | 0.0074 | 0.0034 | 0.0445 | 0.9231 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return (degree * (degree - 1) * (degree - 2)) / 6 ; aggregate: total |
| PM | 3-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | size_S = size(project(P, D)) ; return comb(size_S, 3) ; aggregate: total |
| PM | 3-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| PM | 3-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| PM | 3-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | neighbors = project(P, D) ; degree = size(neighbors) ; term1 = degree * (degree - 1) ; term2 = term1 * (degree - 2) ; return term2 / 6 ; aggregate: total |
| PM | 3-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected = project(P, D) ; d = size(projected) ; return comb(d, 3) ; aggregate: total |
| PM | 3-star | 6 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| PM | 3-star | 7 | True | 1 | 3 | False | False | 0.0000 | True | True | 1.4169 | - | 0.0737 | 0.0650 | d = size(project(N(self), D)) ; return comb(d, 3) ; aggregate: total |
| PM | 3-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| PM | 3-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_neighbors = project(P, D) ; degree = size(projected_neighbors) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 10 | True | 1 | 2 | False | False | 0.0000 | True | True | 1.4169 | - | 0.0737 | 0.0650 | projected = project(N(self), D) ; return (size(projected) * (size(projected) - 1) * (size(projected) - 2)) / 6 ; aggregate: total |
| PM | 3-star | 11 | True | 1 | 2 | False | False | 0.0000 | True | True | 1.4169 | - | 0.0737 | 0.0650 | degree = size(project(N(self), D)) ; return (degree * (degree - 1) * (degree - 2)) / 6 ; aggregate: total |
| PM | 3-star | 12 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| PM | 3-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | proj_P = project(P, D) ; degree = size(proj_P) ; term1 = degree * (degree - 1) ; term2 = term1 * (degree - 2) ; count = term2 / 6 ; return count ; aggregate: total |
| PM | 3-star | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_P = project(P, D) ; size_projected_P = size(projected_P) ; return comb(size_projected_P, 3) ; aggregate: total |
| PM | 3-star | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | degree = size(project(P, D)) ; count = (degree * (degree - 1) * (degree - 2)) / 6 ; return count ; aggregate: total |
| PM | 3-star | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | size_projected = size(project(P, D)) ; count = size_projected * (size_projected - 1) * (size_projected - 2) / 6 ; return count ; aggregate: total |
| PM | 3-star | 19 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| PM | 5-star | 0 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 1 | True | 1 | 2 | False | False | 0.0000 | True | True | 0.4055 | - | 0.1335 | 0.1159 | return comb(size(project(N(self), D)), 5) ; aggregate: total |
| PM | 5-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected = project(P, D) ; size_projected = size(projected) ; return comb(size_projected, 5) ; aggregate: total |
| PM | 5-star | 3 | True | 1 | 2 | False | False | 0.0000 | True | True | 0.4055 | - | 0.1335 | 0.1159 | projected_N_self = project(N(self), D) ; size_projected_N_self = size(projected_N_self) ; return comb(size_projected_N_self, 5) ; aggregate: total |
| PM | 5-star | 4 | True | 1 | 3 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected = project(P, D) ; s = size(projected) ; return comb(s, 5) ; aggregate: total |
| PM | 5-star | 6 | True | 1 | 3 | False | False | 0.0000 | True | True | 0.4055 | - | 0.1335 | 0.1159 | size_N_self = size(project(N(self), D)) ; return comb(size_N_self, 5) ; aggregate: total |
| PM | 5-star | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 5-star | 8 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 9 | True | 1 | 1 | False | False | 0.0000 | True | True | 0.4055 | - | 0.1335 | 0.1159 | size_N_self = size(project(N(self), D)) ; return comb(size_N_self, 5) ; aggregate: total |
| PM | 5-star | 10 | True | 1 | 2 | False | False | 0.0000 | True | True | 0.4055 | - | 0.1335 | 0.1159 | return comb(size(project(N(self), D)), 5) ; aggregate: total |
| PM | 5-star | 11 | True | 1 | 2 | False | False | 0.0000 | True | True | 0.4055 | - | 0.1335 | 0.1159 | return comb(size(project(N(self), D)), 5) ; aggregate: total |
| PM | 5-star | 12 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 5-star | 13 | True | 1 | 3 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | size_P_projected = size(project(P, D)) ; return comb(size_P_projected, 5) ; aggregate: total |
| PM | 5-star | 15 | True | 1 | 3 | False | False | 0.0000 | True | True | 0.4055 | - | 0.1335 | 0.1159 | size_projected = size(project(N(self), D)) ; return comb(size_projected, 5) ; aggregate: total |
| PM | 5-star | 16 | True | 1 | 2 | False | False | 0.0000 | True | True | 0.4055 | - | 0.1335 | 0.1159 | projected = project(N(self), D) ; size_projected = size(projected) ; count = comb(size_projected, 5) ; return count ; aggregate: total |
| PM | 5-star | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 5) ; aggregate: total |
| PM | 5-star | 18 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 19 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | triangle | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; report = sum( sum( A(u, w) for w in S ) for u in S ) / 2 ; return report ; aggregate: total / 3 |
| PM | triangle | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 3 | True | 1 | 1 | False | False | 0.4606 | True | True | 0.2248 | - | 1.5339 | 1.4077 | S = project(P, D) ; sum_over_v = sum(size(S & N(v)) for v in S) ; contribution = 0.5 * sum_over_v ; return contribution ; aggregate: total / 3 |
| PM | triangle | 4 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | return 0.5 * sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; aggregate: total / 3 |
| PM | triangle | 5 | True | 1 | 2 | False | False | 0.4606 | True | True | 0.2248 | - | 1.5339 | 1.4077 | return 0.5 * sum( size( project(P, D) & N(u) ) for u in project(P, D) ) ; aggregate: total / 3 |
| PM | triangle | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 7 | True | 1 | 1 | False | False | 0.4606 | True | True | 0.2248 | - | 1.5339 | 1.4077 | neighbors = project(P, D) ; sum_u = sum(size(N(u) & neighbors) for u in neighbors) ; contribution = sum_u / 2 ; return contribution ; aggregate: total / 3 |
| PM | triangle | 8 | True | 1 | 2 | False | False | 0.4606 | True | True | 0.2248 | - | 1.5339 | 1.4077 | proj = project(P, D) ; sum_edges = sum(size(N(v) & proj) for v in proj) ; return sum_edges / 2 ; aggregate: total / 3 |
| PM | triangle | 9 | True | 1 | 2 | False | False | 0.4606 | True | True | 0.2248 | - | 1.5339 | 1.4077 | count = 0.5 * sum( size( N(u) & project(P, D) ) for u in project(P, D) ) ; return count ; aggregate: total / 3 |
| PM | triangle | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | P_proj = project(P, D) ; sum_pairs = 0.5 * sum( sum( A(u, v) for v in P_proj ) for u in P_proj ) ; return sum_pairs ; aggregate: total / 3 |
| PM | triangle | 11 | True | 1 | 2 | False | False | 0.4606 | True | True | 0.2248 | - | 1.5339 | 1.4077 | return 0.5 * sum(size(project(P, D) & N(v)) for v in project(P, D)) ; aggregate: total / 3 |
| PM | triangle | 12 | True | 1 | 1 | False | False | 0.4606 | True | True | 0.2248 | - | 1.5339 | 1.4077 | term = sum( size( N(u) & project(P, D) ) for u in project(P, D) ) ; result = 0.5 * term ; return result ; aggregate: total / 3 |
| PM | triangle | 13 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 14 | True | 1 | 1 | False | False | 0.4606 | True | True | 0.2248 | - | 1.5339 | 1.4077 | projected_neighbors = project(P, D) ; sum_size = sum(size(projected_neighbors & N(v)) for v in projected_neighbors) ; count = 0.5 * sum_size ; return count ; aggregate: total / 3 |
| PM | triangle | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 17 | True | 1 | 1 | False | False | 0.4606 | True | True | 0.2248 | - | 1.5339 | 1.4077 | S = project(P, D) ; sum_edges = sum(size(N(v) & S) for v in S) ; return sum_edges / 2 ; aggregate: total / 3 |
| PM | triangle | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 1 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 2 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | size_projected = size(project(P, D)) ; return pow(size_projected, 2) ; aggregate: total |
| PM | degree-moment2 | 3 | True | 1 | 3 | False | False | 6.8736 | True | True | 0.0514 | - | 0.0519 | 0.0445 | s = sum(A(self, y) for y in project(P, D)) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | size_p = size(project(P, D)) ; return pow(size_p, 2) ; aggregate: total |
| PM | degree-moment2 | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return pow(degree, 2) ; aggregate: total |
| PM | degree-moment2 | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | size_p = size(project(P, D)) ; return pow(size_p, 2) ; aggregate: total |
| PM | degree-moment2 | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | s = size(project(P, D)) ; return pow(s, 2) ; aggregate: total |
| PM | degree-moment2 | 9 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 10 | True | 1 | 3 | True | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return pow(degree, 2) ; aggregate: total |
| PM | degree-moment2 | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | projected_P = project(P, D) ; size_projected = size(projected_P) ; return pow(size_projected, 2) ; aggregate: total |
| PM | degree-moment2 | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | s = size(project(P, D)) ; return pow(s, 2) ; aggregate: total |
| PM | degree-moment2 | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | size_projected = size(project(P, D)) ; return pow(size_projected, 2) ; aggregate: total |
| PM | degree-moment2 | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
