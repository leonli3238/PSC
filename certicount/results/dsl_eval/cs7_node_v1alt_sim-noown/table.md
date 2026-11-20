# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 20 independent design(s), 3 draft(s) x up to 1 restart(s) per release (rows, matrix), selection simulated (public Holme-Kim graphs, average degrees 4,8,16, 8 releases each, never chosen at a score >= 1; run-time choice on Chung-Lu graphs of the published noisy degrees), own-row check off, tighten 1, early stop off, normalisation on, prompt v1-alt (core v1-alt, b3ea0cb2b6add266), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate off.

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio | mean_candidates | runs_matrix | runs_rows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 20 | 0.8500 | [0.64, 0.95] | 0.8500 | 0.6000 | 1.2941 | 1.0000 | 2.9000 | 13 | 0.1765 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.5500 | 0.0000 | 0.0000 |
| PM | 5-star | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.5500 | 1.4211 | 1.0000 | 2.7500 | 15 | 0.1579 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.4000 | 0.0000 | 0.0000 |
| PM | triangle | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.6000 | 1.5500 | 1.0000 | 3.1000 | 20 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.8000 | 1.0000 | 0.0000 |
| PM | degree-moment2 | 20 | 0.9000 | [0.70, 0.97] | 0.9000 | 0.6000 | 1.3333 | 1.0000 | 3.9000 | 10 | 0.3333 | 0.9444 | 1.0000 | 1.0000 | 1.0000 | 1.1583 | 3.8500 | 1.3263 | 1.1500 | 0.0556 | 0.0000 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0.0087 | 0.0087 | 0.0087 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| PM | 5-star | 0.0176 | 0.0176 | 0.0176 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| PM | triangle | 0.1263 | 0.1263 | 0.1263 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| PM | degree-moment2 | 0.0099 | 0.0074 | 0.0074 | 0.0025 | 0.0445 | 0.9444 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | proj = project(P, D) ; degree = size(proj) ; stars = (degree * (degree - 1) * (degree - 2)) / 6 ; return stars ; aggregate: total |
| PM | 3-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_P = project(P, D) ; size_P = size(projected_P) ; term1 = size_P * (size_P - 1) ; term2 = term1 * (size_P - 2) ; return term2 / 6 ; aggregate: total |
| PM | 3-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_neighbors = project(P, D) ; k = size(projected_neighbors) ; return k * (k - 1) * (k - 2) / 6 ; aggregate: total |
| PM | 3-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | proj_P = project(P, D) ; degree = size(proj_P) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_P = project(P, D) ; size_projected_P = size(projected_P) ; return comb(size_projected_P, 3) ; aggregate: total |
| PM | 3-star | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_neighbors = project(P, D) ; degree = size(projected_neighbors) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| PM | 3-star | 9 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| PM | 3-star | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | d = size(project(P, D)) ; stars = comb(d, 3) ; return stars ; aggregate: total |
| PM | 3-star | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| PM | 3-star | 12 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| PM | 3-star | 13 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| PM | 3-star | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | neighbors = size(project(P, D)) ; return comb(neighbors, 3) ; aggregate: total |
| PM | 3-star | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | degree = size(project(P, D)) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| PM | 3-star | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_neighbors = project(P, D) ; degree = size(projected_neighbors) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| PM | 3-star | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 5-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; report = comb(degree, 5) ; return report ; aggregate: total |
| PM | 5-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 5) ; aggregate: total |
| PM | 5-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected_p = project(P, D) ; size_p = size(projected_p) ; return comb(size_p, 5) ; aggregate: total |
| PM | 5-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 5) ; aggregate: total |
| PM | 5-star | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 5-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected_P = project(P, D) ; return comb(size(projected_P), 5) ; aggregate: total |
| PM | 5-star | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected = project(P, D) ; size_projected = size(projected) ; result = comb(size_projected, 5) ; return result ; aggregate: total |
| PM | 5-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected_p = project(P, D) ; c = comb(size(projected_p), 5) ; return c ; aggregate: total |
| PM | 5-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 5) ; aggregate: total |
| PM | 5-star | 9 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected = project(P, D) ; size_proj = size(projected) ; return comb(size_proj, 5) ; aggregate: total |
| PM | 5-star | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | s = size(project(P, D)) ; return comb(s, 5) ; aggregate: total |
| PM | 5-star | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | degree = size(project(P, D)) ; count = comb(degree, 5) ; return count ; aggregate: total |
| PM | 5-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | k = size(project(P, D)) ; return comb(k, 5) ; aggregate: total |
| PM | 5-star | 14 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected_P = project(P, D) ; size_projected = size(projected_P) ; return comb(size_projected, 5) ; aggregate: total |
| PM | 5-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 5) ; aggregate: total |
| PM | 5-star | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 5) ; aggregate: total |
| PM | 5-star | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 5) ; aggregate: total |
| PM | 5-star | 19 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | triangle | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | return 0.5 * sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; aggregate: total / 3 |
| PM | triangle | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_v = sum( sum( A(v, w) for w in S ) for v in S ) ; return sum_v / 2 ; aggregate: total / 3 |
| PM | triangle | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; total_edges = sum( sum( A(v, w) for w in S ) for v in S ) ; contribution = total_edges / 2 ; return contribution ; aggregate: total / 3 |
| PM | triangle | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | return sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) / 2 ; aggregate: total / 3 |
| PM | triangle | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | sum_u_w_A = sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) ; return sum_u_w_A / 2 ; aggregate: total / 3 |
| PM | triangle | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | s = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return s / 2 ; aggregate: total / 3 |
| PM | triangle | 6 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | return sum(sum(A(v, w) for w in project(P, D)) for v in project(P, D)) ; aggregate: total / 6 |
| PM | triangle | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | sum_edges = sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) ; return sum_edges / 2 ; aggregate: total / 3 |
| PM | triangle | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | P_projected = project(P, D) ; contribution = 0.5 * sum( sum( A(u, v) for v in P_projected ) for u in P_projected ) ; return contribution ; aggregate: total / 3 |
| PM | triangle | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_edges = sum( sum( A(u, v) for v in S ) for u in S ) ; return sum_edges / 2 ; aggregate: total / 3 |
| PM | triangle | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_j_k = sum( sum( A(j, k) for k in S ) for j in S ) ; edges_between_neighbors = sum_j_k / 2 ; return edges_between_neighbors ; aggregate: total / 3 |
| PM | triangle | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | return (sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) )) / 2 ; aggregate: total / 3 |
| PM | triangle | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | Q = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in Q ) for u in Q ) ; return sum_uv / 2 ; aggregate: total / 3 |
| PM | triangle | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_uv = sum(sum(A(u, v) for v in S) for u in S) ; return 0.5 * sum_uv ; aggregate: total / 3 |
| PM | triangle | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | s_neighbors = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in s_neighbors ) for u in s_neighbors ) ; return 0.5 * sum_uv ; aggregate: total / 3 |
| PM | triangle | 15 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | Q = project(P, D) ; sum_uv = sum( sum( A(v, w) for w in Q ) for v in Q ) ; return sum_uv ; aggregate: total / 6 |
| PM | triangle | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_A = sum( sum( A(u, v) for v in S ) for u in S ) ; return 0.5 * sum_A ; aggregate: total / 3 |
| PM | triangle | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | total = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) * 0.5 ; return total ; aggregate: total / 3 |
| PM | triangle | 18 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | projected_P = project(P, D) ; contribution = 0.5 * sum( sum( A(v, w) for w in projected_P ) for v in projected_P ) ; return contribution ; aggregate: total / 3 |
| PM | triangle | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in S ) for u in S ) ; return sum_uv / 2 ; aggregate: total / 3 |
| PM | degree-moment2 | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return pow(degree, 2) ; aggregate: total |
| PM | degree-moment2 | 2 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | s = size(project(P, D)) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 4 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | s = size(project(P, D)) ; return pow(s, 2) ; aggregate: total |
| PM | degree-moment2 | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | s = size(project(P, D)) ; return pow(s, 2) ; aggregate: total |
| PM | degree-moment2 | 7 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | s = size(project(P, D)) ; return pow(s, 2) ; aggregate: total |
| PM | degree-moment2 | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | size_projected = size(project(P, D)) ; return size_projected * size_projected ; aggregate: total |
| PM | degree-moment2 | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | projected_P = project(P, D) ; size_projected = size(projected_P) ; return pow(size_projected, 2) ; aggregate: total |
| PM | degree-moment2 | 11 | True | 1 | 1 | False | False | 6.8736 | True | True | 0.0514 | - | 0.0519 | 0.0445 | degree = sum(A(self, j) for j in project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | size_p = size(project(P, D)) ; return pow(size_p, 2) ; aggregate: total |
| PM | degree-moment2 | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | size_projected = size(project(P, D)) ; return pow(size_projected, 2) ; aggregate: total |
| PM | degree-moment2 | 14 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | degree = size(project(P, D)) ; return pow(degree, 2) ; aggregate: total |
| PM | degree-moment2 | 16 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | size_p = size(project(P, D)) ; return pow(size_p, 2) ; aggregate: total |
| PM | degree-moment2 | 19 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
