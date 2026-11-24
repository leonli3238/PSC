# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 30 independent design(s), 3 draft(s) x up to 1 restart(s) per release (rows, matrix), selection simulated (public Holme-Kim graphs, average degrees 4,8,16, 8 releases each, never chosen at a score >= 1; run-time choice on Chung-Lu graphs of the published noisy degrees), own-row check on, tighten 0, early stop off, normalisation on, feedback full, prompt generic (core generic, 62a207c03a9c4864), ε = 2.0, 20 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate off.

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio | mean_candidates | runs_matrix | runs_rows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | triangle | 30 | 0.9667 | [0.83, 0.99] | 0.9667 | 0.5000 | 1.5517 | 1.0000 | 4.2667 | 28 | 0.0000 | 0.9655 | 1.0000 | 1.0000 | 1.0000 | 0.9815 | 1.0000 | 0.9814 | 1.2667 | 0.9655 | 0.0345 |
| Do | triangle | 30 | 0.7667 | [0.59, 0.88] | 0.7667 | 0.5667 | 1.3478 | 1.0000 | 4.6000 | 23 | 0.0000 | 0.9565 | 1.0000 | 1.0000 | 1.0000 | 0.9766 | 1.0000 | 0.8768 | 0.9000 | 0.7826 | 0.2174 |
| CS | triangle | 30 | 0.8000 | [0.63, 0.90] | 0.8000 | 0.4667 | 1.5833 | 1.0000 | 4.7667 | 24 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.8828 | 0.9667 | 0.7917 | 0.2083 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | triangle | 0.1935 | 0.1456 | 0.1456 | 0.0480 | 1.3910 | 0.9655 | 0.0000 |
| Do | triangle | 0.6828 | 0.7512 | 0.7512 | -0.0685 | 1.735e-19 | 0.7826 | 0.2348 |
| CS | triangle | 1.4776 | 1.6339 | 1.6339 | -0.1563 | 0.0000 | 0.7917 | 0.2979 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | triangle | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | neighbors = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in neighbors ) for u in neighbors ) ; contribution = sum_uv / 2 ; return contribution ; aggregate: total / 3 |
| PM | triangle | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | total = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) / 2 ; return total ; aggregate: total / 3 |
| PM | triangle | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | s = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return s ; aggregate: total / 6 |
| PM | triangle | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | S = project(P, D) ; sum_over_pairs = sum( sum( A(v, w) for w in S ) for v in S ) ; return sum_over_pairs ; aggregate: total / 6 |
| PM | triangle | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | S = project(P, D) ; sum_vw = sum( sum( A(v, w) for w in S ) for v in S ) ; edges_between_neighbors = sum_vw / 2 ; return edges_between_neighbors ; aggregate: total / 3 |
| PM | triangle | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | proj = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in proj ) for u in proj ) ; return sum_uv / 2 ; aggregate: total / 3 |
| PM | triangle | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | P_proj = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in P_proj ) for u in P_proj ) ; return sum_uv ; aggregate: total / 6 |
| PM | triangle | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | s = project(P, D) ; return sum( sum( A(u, v) for v in s ) for u in s ) ; aggregate: total / 6 |
| PM | triangle | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | S = project(P, D) ; sum_total = sum( sum( A(u, v) for v in S ) for u in S ) ; contribution = sum_total / 2 ; return contribution ; aggregate: total / 3 |
| PM | triangle | 10 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | projected_P = project(P, D) ; sum_uv = sum(sum(A(u, v) for v in projected_P) for u in projected_P) ; return sum_uv ; aggregate: total / 6 |
| PM | triangle | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | s = project(P, D) ; sum_edges = sum( sum( A(j, k) for k in s ) for j in s ) ; return sum_edges / 2 ; aggregate: total / 3 |
| PM | triangle | 12 | True | 1 | 3 | False | False | 0.4618 | True | True | 0.2248 | - | 1.5366 | 1.3910 | neighbors = project(P, D) ; sum_v = sum(size(neighbors & N(v)) for v in neighbors) ; return sum_v / 2 ; aggregate: total / 3 |
| PM | triangle | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | P_proj = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in P_proj ) for u in P_proj ) ; return sum_uv / 2 ; aggregate: total / 3 |
| PM | triangle | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | S = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in S ) for u in S ) ; contribution = sum_uv / 2 ; return contribution ; aggregate: total / 3 |
| PM | triangle | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | s = sum( sum( A(u, v) for v in project(P, D) ) for u in project(P, D) ) ; return s / 2 ; aggregate: total / 3 |
| PM | triangle | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | projected = project(P, D) ; sum_ordered = sum( sum( A(v, w) for w in projected ) for v in projected ) ; contribution = sum_ordered / 2 ; return contribution ; aggregate: total / 3 |
| PM | triangle | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | s = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return s ; aggregate: total / 6 |
| PM | triangle | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | return (sum( sum( A(k, l) for l in project(P, D) ) for k in project(P, D) )) / 2 ; aggregate: total / 3 |
| PM | triangle | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | S = project(P, D) ; sum_A = sum( sum( A(v, w) for w in S ) for v in S ) ; return sum_A ; aggregate: total / 6 |
| PM | triangle | 20 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | S = project(P, D) ; sum_uv = sum(sum(A(u, v) for v in S) for u in S) ; return sum_uv / 2 ; aggregate: total / 3 |
| PM | triangle | 21 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | return sum( sum( A(j, k) for k in project(P, D) ) for j in project(P, D) ) / 2 ; aggregate: total / 3 |
| PM | triangle | 22 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | return sum(sum(A(u, v) for v in project(P, D)) for u in project(P, D)) / 2 ; aggregate: total / 3 |
| PM | triangle | 23 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | return (sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) )) / 2 ; aggregate: total / 3 |
| PM | triangle | 24 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | projected_P = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in projected_P ) for u in projected_P ) ; sum_uv_over_2 = sum_uv / 2 ; return sum_uv_over_2 ; aggregate: total / 3 |
| PM | triangle | 25 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | S = project(P, D) ; sum_pairs = sum( sum( A(v, w) for w in S ) for v in S ) ; contribution = sum_pairs / 2 ; return contribution ; aggregate: total / 3 |
| PM | triangle | 26 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | S = project(P, D) ; return sum( sum( A(v, w) for w in S ) for v in S ) ; aggregate: total / 6 |
| PM | triangle | 27 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | S = project(P, D) ; return sum(sum(A(u, v) for v in S) for u in S) / 2 ; aggregate: total / 3 |
| PM | triangle | 28 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | projected_P = project(P, D) ; sum_ordered = sum( sum( A(u, v) for v in projected_P ) for u in projected_P ) ; sum_unordered = sum_ordered / 2 ; return sum_unordered ; aggregate: total / 3 |
| PM | triangle | 29 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1456 | 0.0000 | projected = project(P, D) ; sum_pairs = sum( sum( A(k, l) for l in projected ) for k in projected ) ; return sum_pairs / 2 ; aggregate: total / 3 |
| Do | triangle | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | s = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in s ) for u in s ) ; return sum_uv ; aggregate: total / 6 |
| Do | triangle | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | S = project(P, D) ; sum_pairs = sum( sum( A(u, v) for v in S ) for u in S ) ; contribution = sum_pairs / 2 ; return contribution ; aggregate: total / 3 |
| Do | triangle | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | projected_P = project(P, D) ; sum_uv_A = sum( sum( A(u, v) for v in projected_P ) for u in projected_P ) ; contribution = sum_uv_A / 2 ; return contribution ; aggregate: total / 3 |
| Do | triangle | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | projected_p = project(P, D) ; sum_vw = sum( sum( A(v, w) for w in projected_p ) for v in projected_p ) ; return sum_vw ; aggregate: total / 6 |
| Do | triangle | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | sum_uv = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return sum_uv / 2 ; aggregate: total / 3 |
| Do | triangle | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | projected_P = project(P, D) ; sum_pairs = sum( sum( A(v, w) for w in projected_P ) for v in projected_P ) ; return sum_pairs / 2 ; aggregate: total / 3 |
| Do | triangle | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | return sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) / 2 ; aggregate: total / 3 |
| Do | triangle | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | total = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return total ; aggregate: total / 6 |
| Do | triangle | 11 | True | 1 | 1 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4451 | -0.3061 | S = project(P, D) ; sum_A = sum( sum( A(u, v) for v in S ) for u in S ) ; edges = sum_A / 2 ; return edges ; aggregate: total / 3 |
| Do | triangle | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | S = project(P, D) ; sum_A = sum(sum(A(i, j) for j in S) for i in S) ; edges = sum_A / 2 ; return edges ; aggregate: total / 3 |
| Do | triangle | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | S = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in S ) for u in S ) ; return sum_uv * 0.5 ; aggregate: total / 3 |
| Do | triangle | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | S = project(P, D) ; sum_A = sum( sum( A(u, v) for v in S ) for u in S ) ; return sum_A ; aggregate: total / 6 |
| Do | triangle | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle | 18 | True | 1 | 1 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4451 | -0.3061 | S = project(P, D) ; sum_ordered = sum( sum( A(v, w) for w in S ) for v in S ) ; contribution = sum_ordered / 2 ; return contribution ; aggregate: total / 3 |
| Do | triangle | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | S = project(P, D) ; sum_over_u_v = sum( sum( A(u, v) for v in S ) for u in S ) ; return sum_over_u_v ; aggregate: total / 6 |
| Do | triangle | 20 | True | 1 | 1 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4451 | -0.3061 | S = project(P, D) ; sum_ordered = sum( sum( A(u, v) for u in S ) for v in S ) ; sum_unordered = sum_ordered / 2 ; return sum_unordered ; aggregate: total / 3 |
| Do | triangle | 21 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | return sum( sum( A(u, v) for v in project(P, D) ) for u in project(P, D) ) ; aggregate: total / 6 |
| Do | triangle | 22 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 1.735e-19 | return (sum( sum( A(u, v) for v in project(P, D) ) for u in project(P, D) )) / 2 / 3 ; aggregate: total |
| Do | triangle | 23 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | projected = project(P, D) ; sum_edges = sum( sum( A(j, k) for k in projected ) for j in projected ) ; return sum_edges ; aggregate: total / 6 |
| Do | triangle | 24 | True | 1 | 1 | False | False | 0.4172 | True | True | 0.5704 | - | 0.4008 | -0.3504 | S = project(P, D) ; sum_over_y = sum(size(S & N(y)) for y in S) ; count_pairs = sum_over_y / 2 ; return count_pairs ; aggregate: total / 3 |
| Do | triangle | 25 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | projected_P = project(P, D) ; sum_uv = sum(sum(A(u, v) for v in projected_P) for u in projected_P) ; return sum_uv / 2 ; aggregate: total / 3 |
| Do | triangle | 26 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle | 27 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 1.735e-19 | total = sum( sum( A(j, k) for k in project(P, D) ) for j in project(P, D) ) ; return total / 6 ; aggregate: total |
| Do | triangle | 28 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7512 | 0.0000 | S = project(P, D) ; return sum( sum( A(u, v) for v in S ) for u in S ) / 2 ; aggregate: total / 3 |
| Do | triangle | 29 | True | 1 | 1 | False | True | 0.4374 | True | True | 0.1772 | - | 0.4451 | -0.3061 | S = project(P, D) ; sum_ordered = sum( sum( A(u, v) for v in S ) for u in S ) ; sum_unordered = sum_ordered / 2 ; return sum_unordered ; aggregate: total / 3 |
| CS | triangle | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | s = sum( sum( A(u, v) for v in project(P, D) ) for u in project(P, D) ) ; return s / 2 ; aggregate: total / 3 |
| CS | triangle | 2 | True | 1 | 2 | False | True | 0.4374 | True | True | 0.1016 | - | 0.8837 | -0.7502 | total = sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) ; return total ; aggregate: total / 6 |
| CS | triangle | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | S = project(P, D) ; sum_edges = sum( sum( A(u, v) for v in S ) for u in S ) ; contribution = sum_edges / 2 ; return contribution ; aggregate: total / 3 |
| CS | triangle | 4 | True | 1 | 2 | False | True | 0.4374 | True | True | 0.1016 | - | 0.8837 | -0.7502 | s = project(P, D) ; sum_ajk = sum( sum( A(j, k) for k in s ) for j in s ) ; return sum_ajk / 2 ; aggregate: total / 3 |
| CS | triangle | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | S = project(P, D) ; sum_ordered = sum( sum( A(u, v) for v in S ) for u in S ) ; sum_unordered = sum_ordered / 2 ; return sum_unordered ; aggregate: total / 3 |
| CS | triangle | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 7 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | sum_pairs = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return sum_pairs ; aggregate: total / 6 |
| CS | triangle | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | sum_ = sum( A(j, k) for j in project(P, D) for k in project(P, D) ) ; return sum_ ; aggregate: total / 6 |
| CS | triangle | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | S = project(P, D) ; return sum( sum( A(u, v) for v in S ) for u in S ) ; aggregate: total / 6 |
| CS | triangle | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | S = project(P, D) ; sum_uv = sum(sum(A(u, v) for v in S) for u in S) ; contribution = sum_uv / 2 ; return contribution ; aggregate: total / 3 |
| CS | triangle | 11 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | S = project(P, D) ; sum_vw = sum(sum(A(v, w) for w in S) for v in S) ; return sum_vw ; aggregate: total / 6 |
| CS | triangle | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | s = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in s ) for u in s ) ; return sum_uv / 2 ; aggregate: total / 3 |
| CS | triangle | 13 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | return sum( sum( A(k, l) for l in project(P, D) ) for k in project(P, D) ) / 2 ; aggregate: total / 3 |
| CS | triangle | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 15 | True | 1 | 2 | False | True | 0.4374 | True | True | 0.1016 | - | 0.8837 | -0.7502 | total = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return total ; aggregate: total / 6 |
| CS | triangle | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | s = project(P, D) ; sum_a = sum( sum( A(u, v) for v in s ) for u in s ) ; edges = sum_a / 2 ; return edges ; aggregate: total / 3 |
| CS | triangle | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 18 | True | 1 | 1 | False | True | 0.4374 | True | True | 0.1016 | - | 0.8837 | -0.7502 | S = project(P, D) ; sum_A = sum( sum( A(y, z) for z in S ) for y in S ) ; count = sum_A / 2 ; return count ; aggregate: total / 3 |
| CS | triangle | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | return sum( sum( A(j, k) for k in project(P, D) ) for j in project(P, D) ) / 2 ; aggregate: total / 3 |
| CS | triangle | 20 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | Q = project(P, D) ; sum_uv_A = sum(sum(A(u, v) for v in Q) for u in Q) ; edges_between_neighbors = sum_uv_A / 2 ; return edges_between_neighbors ; aggregate: total / 3 |
| CS | triangle | 21 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | S = project(P, D) ; T = sum( sum( A(u, v) for v in S ) for u in S ) ; return T / 2 ; aggregate: total / 3 |
| CS | triangle | 22 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | projected = project(P, D) ; sum_edges = sum( sum( A(v, w) for w in projected ) for v in projected ) ; return sum_edges / 2 ; aggregate: total / 3 |
| CS | triangle | 23 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | s = project(P, D) ; sum_over_u_v = sum( sum( A(u, v) for v in s ) for u in s ) ; return sum_over_u_v / 2 ; aggregate: total / 3 |
| CS | triangle | 24 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | S = project(P, D) ; sum_ordered = sum(sum(A(u, v) for v in S) for u in S) ; return sum_ordered / 2 ; aggregate: total / 3 |
| CS | triangle | 25 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 26 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | proj = project(P, D) ; sum_uv = sum( sum( A(v, w) for w in proj ) for v in proj ) ; return sum_uv / 2 ; aggregate: total / 3 |
| CS | triangle | 27 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 28 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.6339 | 0.0000 | return sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; aggregate: total / 6 |
| CS | triangle | 29 | True | 1 | 1 | False | True | 0.4374 | True | True | 0.1016 | - | 0.8837 | -0.7502 | total = sum( sum( A(j, k) for k in project(P, D) ) for j in project(P, D) ) / 2 ; return total ; aggregate: total / 3 |
