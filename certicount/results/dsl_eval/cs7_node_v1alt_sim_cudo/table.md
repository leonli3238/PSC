# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 20 independent design(s), 3 draft(s) x up to 1 restart(s) per release (rows, matrix), selection simulated (public Holme-Kim graphs, average degrees 4,8,16, 8 releases each, never chosen at a score >= 1; run-time choice on Chung-Lu graphs of the published noisy degrees), own-row check on, tighten 1, early stop off, normalisation on, prompt v1-alt (core v1-alt, b3ea0cb2b6add266), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate off.

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio | mean_candidates | runs_matrix | runs_rows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | triangle | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.1500 | 2.1000 | 1.0000 | 3.9000 | 19 | 0.0000 | 0.0500 | 1.0000 | 1.0000 | 1.0000 | 0.4890 | 1.0000 | 0.4689 | 1.8000 | 0.0500 | 0.9500 |
| Do | triangle | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.4000 | 1.7500 | 1.0000 | 4.1000 | 19 | 0.0000 | 0.8500 | 1.0000 | 1.0000 | 1.0000 | 0.9193 | 1.0000 | 0.5218 | 1.7000 | 0.1500 | 0.8500 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| CU | triangle | 0.5530 | 0.5233 | 1.0465 | -0.4935 | 0.0000 | 0.0500 | 0.0430 |
| Do | triangle | 0.4721 | 0.4185 | 0.7280 | -0.2559 | 0.0000 | 0.1500 | 0.0405 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | triangle | 0 | True | 1 | 1 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | S = project(P, D) ; sum_v = sum( size(S & N(v)) for v in S ) ; contribution = 0.5 * sum_v ; return contribution ; aggregate: total / 3 |
| CU | triangle | 1 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.2066 | - | 1.0465 | 0.0000 | s = project(P, D) ; sum_edges = 0.5 * sum( sum( A(u, w) for w in s ) for u in s ) ; return sum_edges ; aggregate: total / 3 |
| CU | triangle | 2 | True | 1 | 2 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | s = sum( size( project(P, D) & N(u) ) for u in project(P, D) ) ; return s / 2 ; aggregate: total / 3 |
| CU | triangle | 3 | True | 1 | 2 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | val = 0.5 * sum( size(N(j) & project(P, D)) for j in project(P, D) ) ; return val ; aggregate: total / 3 |
| CU | triangle | 4 | True | 1 | 3 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | return sum( size( project(P, D) & N(u) ) for u in project(P, D) ) / 2 ; aggregate: total / 3 |
| CU | triangle | 5 | True | 1 | 2 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | S = project(P, D) ; edges_in_S = 0.5 * sum(size(S & N(v)) for v in S) ; return edges_in_S ; aggregate: total / 3 |
| CU | triangle | 6 | True | 1 | 2 | False | False | 0.4755 | True | True | 0.4865 | - | 0.5466 | -0.4999 | projected_neighbors = project(P, D) ; total_pairs = sum( size(projected_neighbors & N(u)) for u in projected_neighbors ) ; return 0.5 * total_pairs ; aggregate: total / 3 |
| CU | triangle | 7 | True | 1 | 2 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | return 0.5 * sum( size( project(P, D) & N(v) ) for v in project(P, D) ) ; aggregate: total / 3 |
| CU | triangle | 8 | True | 1 | 2 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | s = sum( size(N(u) & project(P, D)) for u in project(P, D) ) ; return 0.5 * s ; aggregate: total / 3 |
| CU | triangle | 9 | True | 1 | 2 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | s = sum( size( N(v) & project(P, D) ) for v in project(P, D) ) ; return 0.5 * s ; aggregate: total / 3 |
| CU | triangle | 10 | True | 1 | 1 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | sum_v = sum( size( project(P, D) & N(v) ) for v in project(P, D) ) ; count = 0.5 * sum_v ; return count ; aggregate: total / 3 |
| CU | triangle | 11 | True | 1 | 2 | False | False | 0.4755 | True | True | 0.4865 | - | 0.5466 | -0.4999 | return 0.5 * sum(size(project(P, D) & N(v)) for v in project(P, D)) ; aggregate: total / 3 |
| CU | triangle | 12 | True | 1 | 3 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | S = project(P, D) ; contrib = sum( size(S & N(v)) for v in S ) / 2 ; return contrib ; aggregate: total / 3 |
| CU | triangle | 13 | True | 1 | 2 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | contrib = 0.5 * sum(size(N(v) & project(P, D)) for v in project(P, D)) ; return contrib ; aggregate: total / 3 |
| CU | triangle | 14 | True | 1 | 2 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | S = project(P, D) ; edges_in_S = 0.5 * sum(size(S & N(j)) for j in S) ; return edges_in_S ; aggregate: total / 3 |
| CU | triangle | 15 | True | 1 | 3 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | projected_neighbors = project(P, D) ; sum_edges = sum( size(N(u) & projected_neighbors) for u in projected_neighbors ) ; return 0.5 * sum_edges ; aggregate: total / 3 |
| CU | triangle | 16 | True | 1 | 3 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | return 0.5 * sum( size( project(P, D) & N(v) ) for v in project(P, D) ) ; aggregate: total / 3 |
| CU | triangle | 17 | True | 1 | 2 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | S = project(P, D) ; contribution = sum( size(S & N(u)) for u in S ) ; return contribution ; aggregate: total / 6 |
| CU | triangle | 18 | True | 1 | 2 | False | False | 0.4755 | True | True | 0.4865 | - | 0.5466 | -0.4999 | s = project(P, D) ; sum_edges = sum( size(s & N(u)) for u in s ) ; count = 0.5 * sum_edges ; return count ; aggregate: total / 3 |
| CU | triangle | 19 | True | 1 | 1 | False | False | 0.4344 | True | True | 0.4865 | - | 0.5233 | -0.5232 | s = project(P, D) ; sum_edges = sum(size(s & N(v)) for v in s) ; return 0.5 * sum_edges ; aggregate: total / 3 |
| Do | triangle | 0 | True | 1 | 3 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4185 | -0.3095 | sum_edges = sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) ; return sum_edges ; aggregate: total / 6 |
| Do | triangle | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7280 | 0.0000 | S = project(P, D) ; total_pairs = sum( sum( A(u, v) for v in S ) for u in S ) ; connected_pairs = 0.5 * total_pairs ; return connected_pairs ; aggregate: total / 3 |
| Do | triangle | 2 | True | 1 | 2 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4185 | -0.3095 | return 0.5 * sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) ; aggregate: total / 3 |
| Do | triangle | 3 | True | 1 | 1 | False | False | 0.4376 | True | True | 0.5704 | - | 0.4663 | -0.2617 | S = project(P, D) ; sum_edges = sum(size(S & N(u)) for u in S) ; edges_count = sum_edges / 2 ; return edges_count ; aggregate: total / 3 |
| Do | triangle | 4 | True | 1 | 2 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4185 | -0.3095 | Q = project(P, D) ; sum_edges = sum( sum( A(u, w) for w in Q ) for u in Q ) ; triangle_count = sum_edges / 2 ; return triangle_count ; aggregate: total / 3 |
| Do | triangle | 5 | True | 1 | 3 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4185 | -0.3095 | sum_val = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return sum_val / 2 ; aggregate: total / 3 |
| Do | triangle | 6 | True | 1 | 3 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4185 | -0.3095 | projected_neighbors = project(P, D) ; sum_vw = sum( sum( A(v, w) for w in projected_neighbors ) for v in projected_neighbors ) ; return sum_vw / 2 ; aggregate: total / 3 |
| Do | triangle | 7 | True | 1 | 2 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4185 | -0.3095 | S = project(P, D) ; sum_u_w = sum( sum( A(u, w) for w in S ) for u in S ) ; contribution = 0.5 * sum_u_w ; return contribution ; aggregate: total / 3 |
| Do | triangle | 8 | True | 1 | 2 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4185 | -0.3095 | sum_uv = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; edges_between_neighbors = 0.5 * sum_uv ; return edges_between_neighbors ; aggregate: total / 3 |
| Do | triangle | 9 | True | 1 | 1 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4185 | -0.3095 | S = project(P, D) ; sum_edges = sum( sum( A(u, v) for v in S ) for u in S ) ; return sum_edges / 2 ; aggregate: total / 3 |
| Do | triangle | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7280 | 0.0000 | projected = project(P, D) ; total = sum( sum( A(v, w) for w in projected ) for v in projected ) / 2 ; return total ; aggregate: total / 3 |
| Do | triangle | 11 | True | 1 | 1 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4185 | -0.3095 | S = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in S ) for u in S ) ; return 0.5 * sum_uv ; aggregate: total / 3 |
| Do | triangle | 12 | True | 1 | 1 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4185 | -0.3095 | total_pairs = sum( sum( A(u, v) for v in project(P, D) ) for u in project(P, D) ) / 2 ; return total_pairs ; aggregate: total / 3 |
| Do | triangle | 13 | True | 1 | 2 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4185 | -0.3095 | projected_P = project(P, D) ; sum_v_w = sum( sum( A(v, w) for w in projected_P ) for v in projected_P ) ; edges = 0.5 * sum_v_w ; return edges ; aggregate: total / 3 |
| Do | triangle | 14 | True | 1 | 2 | False | False | 0.4376 | True | True | 0.5704 | - | 0.4663 | -0.2617 | return 0.5 * sum(size(project(P, D) & N(v)) for v in project(P, D)) ; aggregate: total / 3 |
| Do | triangle | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7280 | 0.0000 | return 0.5 * sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) ; aggregate: total / 3 |
| Do | triangle | 16 | True | 1 | 1 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4185 | -0.3095 | projected = project(P, D) ; sum_ordered = sum(sum(A(v, w) for w in projected) for v in projected) ; count = sum_ordered / 2 ; return count ; aggregate: total / 3 |
| Do | triangle | 17 | True | 1 | 1 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4185 | -0.3095 | S = project(P, D) ; sum_ordered = sum( sum( A(v, w) for w in S ) for v in S ) ; return 0.5 * sum_ordered ; aggregate: total / 3 |
| Do | triangle | 18 | True | 1 | 2 | False | False | 0.4376 | True | True | 0.5704 | - | 0.4663 | -0.2617 | S = project(P, D) ; sum_edges = sum( size(N(v) & S) for v in S ) ; return sum_edges / 2 ; aggregate: total / 3 |
| Do | triangle | 19 | True | 1 | 1 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4185 | -0.3095 | projected_P = project(P, D) ; contrib = 0.5 * sum( sum( A(u, v) for v in projected_P ) for u in projected_P ) ; return contrib ; aggregate: total / 3 |
