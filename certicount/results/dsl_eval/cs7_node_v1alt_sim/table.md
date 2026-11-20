# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 20 independent design(s), 3 draft(s) x up to 1 restart(s) per release (rows, matrix), selection simulated (public Holme-Kim graphs, average degrees 4,8,16, 8 releases each, never chosen at a score >= 1; run-time choice on Chung-Lu graphs of the published noisy degrees), own-row check on, tighten 1, early stop off, normalisation on, prompt v1-alt (core v1-alt, b3ea0cb2b6add266), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate off.

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio | mean_candidates | runs_matrix | runs_rows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.1500 | 1.9000 | 1.0000 | 3.6000 | 16 | 0.2000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| PM | 5-star | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.5000 | 1.5000 | 1.0000 | 3.2000 | 7 | 0.5000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| PM | triangle | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.3000 | 1.9000 | 1.0000 | 3.9000 | 19 | 0.0000 | 0.9500 | 1.0000 | 1.0000 | 1.0000 | 0.9731 | 1.0000 | 0.9730 | 1.9000 | 0.9500 | 0.0500 |
| PM | degree-moment2 | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.5000 | 1.4737 | 1.0000 | 4.2500 | 12 | 0.2105 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9500 | 0.0000 | 0.0000 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0.0087 | 0.0087 | 0.0087 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| PM | 5-star | 0.0176 | 0.0176 | 0.0176 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| PM | triangle | 0.1967 | 0.1263 | 0.1263 | 0.0704 | 1.4077 | 0.9500 | 0.0000 |
| PM | degree-moment2 | 0.0074 | 0.0074 | 0.0074 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | degree = size(project(P, D)) ; return (degree * (degree - 1) * (degree - 2)) / 6 ; aggregate: total |
| PM | 3-star | 1 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| PM | 3-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 3) ; aggregate: total |
| PM | 3-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | size_projected = size(project(P, D)) ; return (size_projected * (size_projected - 1) * (size_projected - 2)) / 6 ; aggregate: total |
| PM | 3-star | 4 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected = project(P, D) ; size_deg = size(projected) ; term1 = size_deg * (size_deg - 1) ; term2 = term1 * (size_deg - 2) ; result = term2 / 6 ; return result ; aggregate: total |
| PM | 3-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | proj = project(P, D) ; degree = size(proj) ; term = degree * (degree - 1) * (degree - 2) / 6 ; return term ; aggregate: total |
| PM | 3-star | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| PM | 3-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_neighbors = project(P, D) ; size_proj = size(projected_neighbors) ; return comb(size_proj, 3) ; aggregate: total |
| PM | 3-star | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_neighbors = project(P, D) ; degree = size(projected_neighbors) ; term1 = degree * (degree - 1) ; term2 = term1 * (degree - 2) ; return term2 / 6 ; aggregate: total |
| PM | 3-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| PM | 3-star | 11 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| PM | 3-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | size_P = size(project(P, D)) ; term1 = size_P * (size_P - 1) ; term2 = term1 * (size_P - 2) ; count = term2 / 6 ; return count ; aggregate: total |
| PM | 3-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_p = project(P, D) ; size_projected_p = size(projected_p) ; return comb(size_projected_p, 3) ; aggregate: total |
| PM | 3-star | 14 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| PM | 3-star | 15 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| PM | 3-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | size_S = size(project(P, D)) ; return (size_S * (size_S - 1) * (size_S - 2)) / 6 ; aggregate: total |
| PM | 3-star | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | degree = size(project(P, D)) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| PM | 3-star | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 3) ; aggregate: total |
| PM | 5-star | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 5) ; aggregate: total |
| PM | 5-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | count = comb(size(project(P, D)), 5) ; return count ; aggregate: total |
| PM | 5-star | 3 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 5) ; aggregate: total |
| PM | 5-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 5) ; aggregate: total |
| PM | 5-star | 6 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | name = size(project(P, D)) ; return comb(name, 5) ; aggregate: total |
| PM | 5-star | 8 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 5) ; aggregate: total |
| PM | 5-star | 10 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 11 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 5) ; aggregate: total |
| PM | 5-star | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 5) ; aggregate: total |
| PM | 5-star | 14 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 15 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected = project(P, D) ; size_proj = size(projected) ; return comb(size_proj, 5) ; aggregate: total |
| PM | 5-star | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 5) ; aggregate: total |
| PM | 5-star | 18 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 19 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | triangle | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | P_proj = project(P, D) ; sum_edges = sum( sum( A(u, w) for w in P_proj ) for u in P_proj ) ; contribution = sum_edges / 2 ; return contribution ; aggregate: total / 3 |
| PM | triangle | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; total_pairs = sum( sum( A(u, v) for v in S ) for u in S ) ; return total_pairs / 2 ; aggregate: total / 3 |
| PM | triangle | 2 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_pairs = sum( sum( A(v, w) for w in S ) for v in S ) ; term = sum_pairs / 2 ; return term ; aggregate: total / 3 |
| PM | triangle | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; return sum(sum(A(v, w) for w in S) for v in S) / 2 ; aggregate: total / 3 |
| PM | triangle | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_uv = sum( sum( A(v, w) for w in S ) for v in S ) ; return sum_uv / 2 ; aggregate: total / 3 |
| PM | triangle | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | projected_neighbors = project(P, D) ; sum_vw = sum( sum( A(v, w) for w in projected_neighbors ) for v in projected_neighbors ) ; return sum_vw / 2 ; aggregate: total / 3 |
| PM | triangle | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_uv = sum(sum(A(u, v) for v in S) for u in S) ; return sum_uv / 2 ; aggregate: total / 3 |
| PM | triangle | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_over_pairs = sum( sum( A(v, w) for w in S ) for v in S ) ; contribution = 0.5 * sum_over_pairs ; return contribution ; aggregate: total / 3 |
| PM | triangle | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | P_projected = project(P, D) ; sum_edges = sum( sum( A(u, v) for v in P_projected ) for u in P_projected ) ; contribution = sum_edges / 2 ; return contribution ; aggregate: total / 3 |
| PM | triangle | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | projected_neighbors = project(P, D) ; sum_A = sum(sum(A(v, w) for w in projected_neighbors) for v in projected_neighbors) ; edges = sum_A / 2 ; return edges ; aggregate: total / 3 |
| PM | triangle | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; edges_between_neighbors = sum( sum( A(u, w) for w in S ) for u in S ) / 2 ; return edges_between_neighbors ; aggregate: total / 3 |
| PM | triangle | 11 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | return sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) / 2 ; aggregate: total / 3 |
| PM | triangle | 12 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | sum_vw = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; sum_edges = sum_vw / 2 ; return sum_edges ; aggregate: total / 3 |
| PM | triangle | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | total = sum( 0.5 * sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return total ; aggregate: total / 3 |
| PM | triangle | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | return 0.5 * sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) ; aggregate: total / 3 |
| PM | triangle | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | projected_P = project(P, D) ; s = sum(sum(A(v, w) for w in projected_P) for v in projected_P) ; return s / 2 ; aggregate: total / 3 |
| PM | triangle | 16 | True | 1 | 2 | False | False | 0.4606 | True | True | 0.2248 | - | 1.5339 | 1.4077 | return 0.5 * sum(size(N(v) & project(P, D)) for v in project(P, D)) ; aggregate: total / 3 |
| PM | triangle | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | return (sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) )) / 2 ; aggregate: total / 3 |
| PM | triangle | 18 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | total = sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) ; return total * 0.5 ; aggregate: total / 3 |
| PM | triangle | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | return 0.5 * sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) ; aggregate: total / 3 |
| PM | degree-moment2 | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | s = size(project(P, D)) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | size_projected = size(project(P, D)) ; return pow(size_projected, 2) ; aggregate: total |
| PM | degree-moment2 | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | degree = size(project(P, D)) ; return pow(degree, 2) ; aggregate: total |
| PM | degree-moment2 | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | s = size(project(P, D)) ; return pow(s, 2) ; aggregate: total |
| PM | degree-moment2 | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return pow(degree, 2) ; aggregate: total |
| PM | degree-moment2 | 5 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | projected_P = project(P, D) ; size_projected_P = size(projected_P) ; return pow(size_projected_P, 2) ; aggregate: total |
| PM | degree-moment2 | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | s = size(project(P, D)) ; return pow(s, 2) ; aggregate: total |
| PM | degree-moment2 | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | size_projected = size(project(P, D)) ; contribution = pow(size_projected, 2) ; return contribution ; aggregate: total |
| PM | degree-moment2 | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | projected_P = project(P, D) ; size_p = size(projected_P) ; return pow(size_p, 2) ; aggregate: total |
| PM | degree-moment2 | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | size_projected = size(project(P, D)) ; return pow(size_projected, 2) ; aggregate: total |
| PM | degree-moment2 | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | degree = size(project(P, D)) ; return pow(degree, 2) ; aggregate: total |
| PM | degree-moment2 | 13 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 14 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | s = size(project(P, D)) ; return pow(s, 2) ; aggregate: total |
| PM | degree-moment2 | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 17 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | size_P = size(project(P, D)) ; return pow(size_P, 2) ; aggregate: total |
| PM | degree-moment2 | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; squared_degree = pow(degree, 2) ; return squared_degree ; aggregate: total |
