# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 30 independent design(s), 3 draft(s) x up to 1 restart(s) per release (rows, matrix), selection simulated (public Holme-Kim graphs, average degrees 4,8,16, 8 releases each, never chosen at a score >= 1; run-time choice on Chung-Lu graphs of the published noisy degrees), own-row check on, tighten 0, early stop off, normalisation on, feedback none, prompt generic (core generic, 62a207c03a9c4864), ε = 2.0, 20 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate off.

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio | mean_candidates | runs_matrix | runs_rows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | triangle-edge | 30 | 0.4000 | [0.25, 0.58] | 0.4000 | 0.1333 | 1.9167 | 1.0000 | 5.5667 | 11 | 0.0000 | 0.7500 | 1.0000 | 1.0000 | 1.0000 | 1.0167 | 1.2000 | 1.0007 | 0.4000 | 0.7500 | 0.2500 |
| Do | triangle-edge | 30 | 0.3667 | [0.22, 0.54] | 0.3667 | 0.1000 | 2.1818 | 1.0000 | 5.7000 | 9 | 0.0000 | 0.4545 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9759 | 0.3667 | 0.4545 | 0.5455 |
| CS | triangle-edge | 30 | 0.2333 | [0.12, 0.41] | 0.2333 | 0.0000 | 2.4286 | 1.0000 | 5.8667 | 7 | 0.0000 | 0.5714 | 1.0000 | 1.0000 | 1.0000 | 1.0286 | 1.2000 | 0.9700 | 0.2333 | 0.5714 | 0.4286 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | triangle-edge | 0.2241 | 0.2208 | 0.2208 | 0.0032 | 0.0193 | 0.7500 | 0.0000 |
| Do | triangle-edge | 0.5072 | 0.4952 | 0.5216 | -0.0144 | 0.0000 | 0.4545 | 0.0227 |
| CS | triangle-edge | 0.8544 | 0.7749 | 0.7749 | 0.0795 | 0.2865 | 0.5714 | 0.1714 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | triangle-edge | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.3215 | - | 0.2208 | 0.0000 | s = sum(clip(sum(A(v, w) for w in project(P, D)), 0, 1) for v in project(P, D)) ; return s ; aggregate: total / 2 |
| PM | triangle-edge | 1 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.3215 | - | 0.2208 | 0.0000 | return sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| PM | triangle-edge | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.3215 | - | 0.2208 | 0.0000 | P_proj = project(P, D) ; sum_over_v = sum( clip( sum( A(v, w) for w in P_proj ), 0, 1 ) for v in P_proj ) ; return sum_over_v ; aggregate: total / 2 |
| PM | triangle-edge | 7 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.3215 | - | 0.2208 | 0.0000 | contrib = sum(clip(sum(A(v, w) for w in project(P, D)), 0, 1) for v in project(P, D)) ; return contrib ; aggregate: total / 2 |
| PM | triangle-edge | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 9 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.3215 | - | 0.2208 | 0.0000 | P_proj = project(P, D) ; sum_v = sum(clip(sum(A(v, w) for w in P_proj), 0, 1) for v in P_proj) ; return sum_v ; aggregate: total / 2 |
| PM | triangle-edge | 10 | True | 1 | 1 | False | False | 1.0056 | True | True | 0.3048 | - | 0.2305 | 0.0097 | S = project(P, D) ; sum_clip = sum(clip(size(S & N(v)), 0, 1) for v in S) ; return sum_clip ; aggregate: total / 2 |
| PM | triangle-edge | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.3215 | - | 0.2208 | 0.0000 | return sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| PM | triangle-edge | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3215 | - | 0.2208 | 0.0000 | project_p = project(P, D) ; total_u = sum( clip( sum( A(v, w) for w in project_p ), 0, 1 ) for v in project_p ) ; return total_u ; aggregate: total / 2 |
| PM | triangle-edge | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3215 | - | 0.2208 | 0.0000 | projected_P = project(P, D) ; sum_v = sum( clip( sum( A(v, w) for w in projected_P ), 0, 1 ) for v in projected_P ) ; return sum_v ; aggregate: total / 2 |
| PM | triangle-edge | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3215 | - | 0.2208 | 0.0000 | neighbors_u = project(P, D) ; sum_over_v = sum( clip( sum( A(v, w) for w in neighbors_u ), 0, 1 ) for v in neighbors_u ) ; return sum_over_v ; aggregate: total / 2 |
| PM | triangle-edge | 20 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 21 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 22 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 23 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 24 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 25 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 26 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 27 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 28 | True | 1 | 2 | False | False | 0.9973 | True | True | 0.2953 | - | 0.2401 | 0.0193 | neighbors = project(P, D) ; contribution = sum(clip(size(P & N(v)), 0, 1) for v in neighbors) ; return contribution ; aggregate: total / 2 |
| PM | triangle-edge | 29 | True | 1 | 2 | False | False | 1.0056 | True | True | 0.3048 | - | 0.2305 | 0.0097 | projected = project(P, D) ; count = sum( clip( size( projected & N(v) ), 0, 1 ) for v in projected ) ; return count ; aggregate: total / 2 |
| Do | triangle-edge | 0 | True | 1 | 3 | False | False | 0.9559 | True | True | 0.0289 | - | 0.4952 | -0.0264 | P_proj = project(P, D) ; count = sum( clip( size( P_proj & N(v) ), 0, 1 ) for v in P_proj ) ; return count ; aggregate: total / 2 |
| Do | triangle-edge | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 3 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.3064 | - | 0.5216 | 0.0000 | return sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| Do | triangle-edge | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 8 | True | 1 | 1 | False | False | 0.9559 | True | True | 0.0289 | - | 0.4952 | -0.0264 | P_proj = project(P, D) ; contrib = sum(clip(size(P_proj & N(v)), 0, 1) for v in P_proj) ; return contrib ; aggregate: total / 2 |
| Do | triangle-edge | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3064 | - | 0.5216 | 0.0000 | projected_neighbors = project(P, D) ; sum_over_v = sum( clip( sum( A(v, w) for w in projected_neighbors ), 0, 1 ) for v in projected_neighbors ) ; return sum_over_v ; aggregate: total / 2 |
| Do | triangle-edge | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.3064 | - | 0.5216 | 0.0000 | P_proj = project(P, D) ; total = sum(clip(sum(A(v, w) for w in P_proj), 0, 1) for v in P_proj) ; return total ; aggregate: total / 2 |
| Do | triangle-edge | 13 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 19 | True | 1 | 1 | False | False | 0.9559 | True | True | 0.0289 | - | 0.4952 | -0.0264 | P_proj = project(P, D) ; count = sum(clip(size(P_proj & N(v)), 0, 1) for v in P_proj) ; return count ; aggregate: total / 2 |
| Do | triangle-edge | 20 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 21 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 22 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 23 | True | 1 | 2 | False | False | 0.9559 | True | True | 0.0289 | - | 0.4952 | -0.0264 | return sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| Do | triangle-edge | 24 | True | 1 | 3 | False | False | 0.9559 | True | True | 0.0289 | - | 0.4952 | -0.0264 | return sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| Do | triangle-edge | 25 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.3064 | - | 0.5216 | 0.0000 | return sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| Do | triangle-edge | 26 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.3064 | - | 0.5216 | 0.0000 | neighbors_u = project(P, D) ; sum_over_v = sum( clip( sum( A(v, w) for w in neighbors_u ), 0, 1 ) for v in neighbors_u ) ; return sum_over_v ; aggregate: total / 2 |
| Do | triangle-edge | 27 | True | 1 | 2 | False | False | 0.9559 | True | True | 0.0289 | - | 0.4952 | -0.0264 | S = project(P, D) ; count = sum( clip( size( N(v) & S ), 0, 1 ) for v in S ) ; return count ; aggregate: total / 2 |
| Do | triangle-edge | 28 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 29 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 3 | True | 1 | 2 | False | False | 0.9529 | True | True | 0.0293 | - | 0.9099 | 0.1351 | projected_P = project(P, D) ; return sum(clip(size(projected_P & N(v)), 0, 1) for v in projected_P) ; aggregate: total / 2 |
| CS | triangle-edge | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 8 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.2972 | - | 0.7749 | 0.0000 | sum_clip = sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; return sum_clip ; aggregate: total / 2 |
| CS | triangle-edge | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2972 | - | 0.7749 | 0.0000 | S = project(P, D) ; sum_over_v = sum( clip( sum( A(v, w) for w in S ), 0, 1 ) for v in S ) ; return sum_over_v ; aggregate: total / 2 |
| CS | triangle-edge | 13 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.2972 | - | 0.7749 | 0.0000 | P_proj = project(P, D) ; sum_contribution = sum( clip( sum( A(v, w) for w in P_proj ), 0, 1 ) for v in P_proj ) ; return sum_contribution ; aggregate: total / 2 |
| CS | triangle-edge | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 18 | True | 1 | 3 | False | False | 0.8843 | True | True | 0.0273 | - | 1.0614 | 0.2865 | projected_neighbors = project(P, D) ; sum_val = sum(clip(size(P & N(v)), 0, 1) for v in projected_neighbors) ; return sum_val ; aggregate: total / 2 |
| CS | triangle-edge | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 20 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 21 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 22 | True | 1 | 2 | False | False | 0.9529 | True | True | 0.0293 | - | 0.9099 | 0.1351 | neighbors = project(P, D) ; return sum( clip(size(N(v) & neighbors), 0, 1) for v in neighbors ) ; aggregate: total / 2 |
| CS | triangle-edge | 23 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 24 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 25 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 26 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 27 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2972 | - | 0.7749 | 0.0000 | sum_v_clip = sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; return sum_v_clip ; aggregate: total / 2 |
| CS | triangle-edge | 28 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 29 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
