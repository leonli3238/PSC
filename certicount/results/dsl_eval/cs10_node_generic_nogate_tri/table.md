# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 20 independent design(s), 3 draft(s) x up to 1 restart(s), selection first, own-row check on, tighten 1, early stop off, normalisation on, feedback full, prompt generic (core generic, 62a207c03a9c4864), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate off.

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | triangle | 20 | 0.5000 | [0.30, 0.70] | 0.5000 | 0.2500 | 1.8000 | 1.0000 | 2.4000 | 10 | 0.0000 | 0.9000 | 1.0000 | 1.0000 | 1.0000 | 0.9462 | 1.0000 | 0.9461 |
| CU | triangle | 20 | 0.4500 | [0.26, 0.66] | 0.4500 | 0.2000 | 1.7778 | 1.0000 | 2.4500 | 9 | 0.0000 | 0.8889 | 1.0000 | 1.0000 | 1.0000 | 0.9402 | 1.0000 | 0.9417 |
| Do | triangle | 20 | 0.6500 | [0.43, 0.82] | 0.6500 | 0.3000 | 1.6923 | 1.0000 | 2.1500 | 13 | 0.0000 | 0.9231 | 1.0000 | 1.0000 | 1.0000 | 0.9586 | 1.0000 | 0.9567 |
| ML | triangle | 20 | 0.5000 | [0.30, 0.70] | 0.5000 | 0.1500 | 2.1000 | 1.0000 | 2.5500 | 10 | 0.0000 | 0.7000 | 1.0000 | 1.0000 | 1.0000 | 0.8386 | 1.0000 | 0.8366 |
| CS | triangle | 20 | 0.4500 | [0.26, 0.66] | 0.4500 | 0.3000 | 1.5556 | 1.0000 | 2.3500 | 9 | 0.0000 | 0.7778 | 1.0000 | 1.0000 | 1.0000 | 0.8805 | 1.0000 | 0.8772 |
| EE | triangle | 20 | 0.6500 | [0.43, 0.82] | 0.6500 | 0.3000 | 1.7692 | 1.0000 | 2.2500 | 13 | 0.0000 | 0.7692 | 1.0000 | 1.0000 | 0.9231 | 0.9274 | 1.6699 | 0.9188 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | triangle | 0.2670 | 0.1263 | 0.1263 | 0.1408 | 1.4077 | 0.9000 | 0.0000 |
| CU | triangle | 0.9909 | 1.0465 | 1.0465 | -0.0555 | 1.03e-16 | 0.8889 | 0.2867 |
| Do | triangle | 0.7079 | 0.7280 | 0.7280 | -0.0201 | 0.0000 | 0.9231 | 0.2492 |
| ML | triangle | 0.2353 | 0.2795 | 0.2795 | -0.0443 | 0.0000 | 0.7000 | 0.0000 |
| CS | triangle | 1.3517 | 1.4757 | 1.4757 | -0.1240 | 0.0000 | 0.7778 | 0.2133 |
| EE | triangle | 0.3796 | 0.2680 | 0.2680 | 0.1116 | 1.8752 | 0.6923 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | triangle | 0 | True | 1 | 1 | False | False | 0.4606 | True | True | 0.2248 | - | 1.5339 | 1.4077 | S = project(P, D) ; sum_edges = sum(size(S & N(v)) for v in S) ; edges_between_neighbors = sum_edges / 2 ; return edges_between_neighbors ; aggregate: total / 3 |
| PM | triangle | 1 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | total = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return total ; aggregate: total / 6 |
| PM | triangle | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_over_pairs = sum( sum( A(v, w) for w in S ) for v in S ) ; edges_between_neighbors = sum_over_pairs / 2 ; return edges_between_neighbors ; aggregate: total / 3 |
| PM | triangle | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | projected_P = project(P, D) ; total = sum( sum( A(u, v) for v in projected_P ) for u in projected_P ) / 2 ; return total ; aggregate: total / 3 |
| PM | triangle | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | projected = project(P, D) ; sum_ordered = sum( sum( A(a, b) for b in projected ) for a in projected ) ; sum_unordered = sum_ordered / 2 ; return sum_unordered ; aggregate: total / 3 |
| PM | triangle | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 12 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | return sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) / 2 ; aggregate: total / 3 |
| PM | triangle | 13 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 14 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | projected_P = project(P, D) ; total_edges_between_neighbors = sum( sum( A(v, w) for w in projected_P ) for v in projected_P ) ; return total_edges_between_neighbors ; aggregate: total / 6 |
| PM | triangle | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | return (sum(sum(A(v, w) for w in project(P, D)) for v in project(P, D))) / 2 ; aggregate: total / 3 |
| PM | triangle | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | p_proj = project(P, D) ; return sum( sum( A(v, w) for w in p_proj ) for v in p_proj ) ; aggregate: total / 6 |
| PM | triangle | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | projected = project(P, D) ; sum_sum = sum( sum( A(v, w) for w in projected ) for v in projected ) ; return sum_sum ; aggregate: total / 6 |
| PM | triangle | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2066 | - | 1.0465 | 0.0000 | P_proj = project(P, D) ; sum_jk = sum( sum( A(j, k) for k in P_proj ) for j in P_proj ) ; contribution = sum_jk / 2 ; return contribution ; aggregate: total / 3 |
| CU | triangle | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle | 4 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.2066 | - | 1.0465 | 0.0000 | P_proj = project(P, D) ; total_pairs = sum( sum( A(u, w) for w in P_proj ) for u in P_proj ) ; return total_pairs ; aggregate: total / 6 |
| CU | triangle | 5 | True | 1 | 1 | False | False | 0.4755 | True | True | 0.4865 | - | 0.5466 | -0.4999 | return sum( size( project(P, D) & N(u) ) for u in project(P, D) ) / 2 ; aggregate: total / 3 |
| CU | triangle | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2066 | - | 1.0465 | 1.03e-16 | count = sum( sum( A(u, v) for v in project(P, D) ) for u in project(P, D) ) ; return count / 6 ; aggregate: total |
| CU | triangle | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle | 12 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.2066 | - | 1.0465 | 0.0000 | S = project(P, D) ; ordered_sum = sum(sum(A(v, w) for w in S) for v in S) ; unordered_pairs = ordered_sum / 2 ; return unordered_pairs ; aggregate: total / 3 |
| CU | triangle | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2066 | - | 1.0465 | 1.03e-16 | S = project(P, D) ; sum_pairs = sum( sum( A(v, w) for w in S ) for v in S ) ; contribution = sum_pairs / 6 ; return contribution ; aggregate: total |
| CU | triangle | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2066 | - | 1.0465 | 0.0000 | P_proj = project(P, D) ; count = sum(sum(A(v, w) for w in P_proj) for v in P_proj) ; return count ; aggregate: total / 6 |
| CU | triangle | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2066 | - | 1.0465 | 0.0000 | S = project(P, D) ; total = sum( sum( A(j, k) for k in S ) for j in S ) / 2 ; return total ; aggregate: total / 3 |
| CU | triangle | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2066 | - | 1.0465 | 0.0000 | P_proj = project(P, D) ; sum1 = sum( sum( A(j, k) for k in P_proj ) for j in P_proj ) ; count = sum1 / 2 ; return count ; aggregate: total / 3 |
| Do | triangle | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7280 | 0.0000 | S = project(P, D) ; sum_A = sum( sum( A(v, w) for w in S ) for v in S ) ; count = sum_A / 2 ; return count ; aggregate: total / 3 |
| Do | triangle | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7280 | 0.0000 | P_proj = project(P, D) ; return sum( sum( A(u, v) for v in P_proj ) for u in P_proj ) / 2 ; aggregate: total / 3 |
| Do | triangle | 3 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7280 | 0.0000 | S = project(P, D) ; count = sum( sum( A(v, w) for w in S ) for v in S ) ; return count ; aggregate: total / 6 |
| Do | triangle | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7280 | 0.0000 | S = project(P, D) ; sum_A = sum( sum( A(u, v) for v in S ) for u in S ) ; edges_between_neighbors = sum_A / 2 ; return edges_between_neighbors ; aggregate: total / 3 |
| Do | triangle | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7280 | 0.0000 | projected = project(P, D) ; sum_ordered = sum(sum(A(u, v) for v in projected) for u in projected) ; sum_unordered = sum_ordered / 2 ; return sum_unordered ; aggregate: total / 3 |
| Do | triangle | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7280 | 0.0000 | S = project(P, D) ; sum_edges = sum( sum( A(v, w) for w in S ) for v in S ) ; return sum_edges / 2 ; aggregate: total / 3 |
| Do | triangle | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7280 | 0.0000 | S = project(P, D) ; sum_ordered = sum( sum( A(w, u) for u in S ) for w in S ) ; return sum_ordered / 2 ; aggregate: total / 3 |
| Do | triangle | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7280 | 0.0000 | S = project(P, D) ; sum_pairs = sum( sum( A(v, w) for w in S ) for v in S ) ; return sum_pairs ; aggregate: total / 6 |
| Do | triangle | 12 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7280 | 0.0000 | total = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return total ; aggregate: total / 6 |
| Do | triangle | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7280 | 0.0000 | s = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in s ) for u in s ) ; count = sum_uv / 2 ; return count ; aggregate: total / 3 |
| Do | triangle | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7280 | 0.0000 | S = project(P, D) ; sum_A = sum( sum( A(j, k) for k in S ) for j in S ) ; edges = sum_A / 2 ; return edges ; aggregate: total / 3 |
| Do | triangle | 15 | True | 1 | 1 | False | False | 0.4376 | True | True | 0.5704 | - | 0.4663 | -0.2617 | P_proj = project(P, D) ; sum_over_j = sum( size(P_proj & N(j)) for j in P_proj ) ; num_edges = sum_over_j / 2 ; return num_edges ; aggregate: total / 3 |
| Do | triangle | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1772 | - | 0.7280 | 0.0000 | Q = project(P, D) ; total_pairs = sum( sum( A(j, k) for k in Q ) for j in Q ) ; return total_pairs ; aggregate: total / 6 |
| Do | triangle | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle | 0 | True | 1 | 1 | False | False | 0.4553 | True | True | 0.7586 | - | 0.1320 | -0.1476 | return sum( size(N(u) & project(P, D)) for u in project(P, D) ) / 2 ; aggregate: total / 3 |
| ML | triangle | 1 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1836 | - | 0.2795 | 0.0000 | total = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return total ; aggregate: total / 6 |
| ML | triangle | 2 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1836 | - | 0.2795 | 0.0000 | neighbors = project(P, D) ; sum_edges = sum( sum( A(v, w) for w in neighbors ) for v in neighbors ) ; count = sum_edges / 2 ; return count ; aggregate: total / 3 |
| ML | triangle | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle | 6 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1836 | - | 0.2795 | 0.0000 | S = project(P, D) ; return sum( sum( A(z, w) for w in S ) for z in S ) ; aggregate: total / 6 |
| ML | triangle | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle | 10 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1836 | - | 0.2795 | 0.0000 | return sum( sum( A(j, k) for k in project(P, D) ) for j in project(P, D) ) ; aggregate: total / 6 |
| ML | triangle | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle | 12 | True | 1 | 2 | False | False | 0.4553 | True | True | 0.7586 | - | 0.1320 | -0.1476 | T = project(P, D) ; sum_over_v = sum( size(T & N(v)) for v in T ) ; count = sum_over_v / 2 ; return count ; aggregate: total / 3 |
| ML | triangle | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1836 | - | 0.2795 | 0.0000 | neighbors = project(P, D) ; sum_edges = sum( sum( A(j, k) for k in neighbors ) for j in neighbors ) ; number_of_pairs = sum_edges * 0.5 ; return number_of_pairs ; aggregate: total / 3 |
| ML | triangle | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle | 15 | True | 1 | 1 | False | False | 0.4553 | True | True | 0.7586 | - | 0.1320 | -0.1476 | S = project(P, D) ; total = sum( size(S & N(u)) for u in S ) ; return total ; aggregate: total / 6 |
| ML | triangle | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1836 | - | 0.2795 | 0.0000 | S = project(P, D) ; sum_pairs = sum( sum( A(v, w) for w in S ) for v in S ) ; return sum_pairs / 2 ; aggregate: total / 3 |
| ML | triangle | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1836 | - | 0.2795 | 0.0000 | P_projected = project(P, D) ; sum_u_w = sum( sum( A(u, w) for w in P_projected ) for u in P_projected ) ; return sum_u_w / 2 ; aggregate: total / 3 |
| ML | triangle | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.4757 | 0.0000 | S = project(P, D) ; sum_pairs = sum(sum(A(u, v) for v in S) for u in S) ; return sum_pairs / 2 ; aggregate: total / 3 |
| CS | triangle | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1016 | - | 1.4757 | 0.0000 | s = project(P, D) ; sum_A = sum( sum( A(u, v) for v in s ) for u in s ) ; count = sum_A / 2 ; return count ; aggregate: total / 3 |
| CS | triangle | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 6 | True | 1 | 1 | False | False | 0.4472 | True | True | 0.7722 | - | 0.9178 | -0.5579 | S = project(P, D) ; sum_size = sum( size(S & N(u)) for u in S ) ; return sum_size / 2 ; aggregate: total / 3 |
| CS | triangle | 7 | True | 1 | 1 | False | False | 0.4472 | True | True | 0.7722 | - | 0.9178 | -0.5579 | S = project(P, D) ; sum_edges = sum( size(S & N(j)) for j in S ) ; edges = sum_edges / 2 ; return edges ; aggregate: total / 3 |
| CS | triangle | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.4757 | 0.0000 | P_proj = project(P, D) ; sum_over_u = sum( sum( A(u, v) for v in P_proj ) for u in P_proj ) ; count = sum_over_u / 2 ; return count ; aggregate: total / 3 |
| CS | triangle | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 11 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1016 | - | 1.4757 | 0.0000 | projected_neighbors = project(P, D) ; count = sum( sum( A(v, w) for w in projected_neighbors ) for v in projected_neighbors ) ; return count ; aggregate: total / 6 |
| CS | triangle | 12 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1016 | - | 1.4757 | 0.0000 | Q = project(P, D) ; count = sum(sum(A(u, v) for v in Q) for u in Q) / 2 ; return count ; aggregate: total / 3 |
| CS | triangle | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.4757 | 0.0000 | return sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; aggregate: total / 6 |
| CS | triangle | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1016 | - | 1.4757 | 0.0000 | neighbors = project(P, D) ; sum_ordered = sum(sum(A(v, w) for w in neighbors) for v in neighbors) ; return sum_ordered / 2 ; aggregate: total / 3 |
| CS | triangle | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle | 0 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1358 | - | 0.2680 | 0.0000 | return sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) / 2 ; aggregate: total / 3 |
| EE | triangle | 1 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1358 | - | 0.2680 | 0.0000 | return sum( sum( A(u, v) for u in project(P, D) ) for v in project(P, D) ) / 2 ; aggregate: total / 3 |
| EE | triangle | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1358 | - | 0.2680 | 0.0000 | S = project(P, D) ; sum_over_pairs = sum( sum( A(j, k) for k in S ) for j in S ) ; edges_between_neighbors = sum_over_pairs / 2 ; return edges_between_neighbors ; aggregate: total / 3 |
| EE | triangle | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1358 | - | 0.2680 | 0.0000 | Q = project(P, D) ; sum_pairs = sum( sum( A(u, w) for w in Q ) for u in Q ) ; edges_between_neighbors = sum_pairs / 2 ; return edges_between_neighbors ; aggregate: total / 3 |
| EE | triangle | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1358 | - | 0.2680 | 0.0000 | S = project(P, D) ; sum_edges = sum(sum(A(u, v) for v in S) for u in S) ; edges = sum_edges / 2 ; return edges ; aggregate: total / 3 |
| EE | triangle | 7 | True | 1 | 1 | False | True | 1.5988 | True | True | 5.5402 | - | 2.1432 | 1.8752 | return sum( sum( A(v, w) * A(w, v) for w in project(P, D) ) for v in project(P, D) ) ; aggregate: total / 6 |
| EE | triangle | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1358 | - | 0.2680 | 0.0000 | neighbors = project(P, D) ; sum_ordered = sum( sum( A(u, v) for v in neighbors ) for u in neighbors ) ; edges_between_neighbors = sum_ordered / 2 ; return edges_between_neighbors ; aggregate: total / 3 |
| EE | triangle | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1358 | - | 0.2680 | 0.0000 | P_proj = project(P, D) ; sum_uv = sum( sum( A(u, v) for v in P_proj ) for u in P_proj ) ; num_pairs = sum_uv / 2 ; return num_pairs ; aggregate: total / 3 |
| EE | triangle | 11 | True | 1 | 1 | False | False | 0.4487 | True | True | 0.6982 | - | 0.1265 | -0.1415 | P_proj = project(P, D) ; sum_edges = sum( size( N(u) & P_proj ) for u in P_proj ) ; contribution = sum_edges / 2 ; return contribution ; aggregate: total / 3 |
| EE | triangle | 12 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle | 13 | True | 1 | 2 | False | False | 0.4487 | True | True | 0.6982 | - | 0.1265 | -0.1415 | S = project(P, D) ; sum_v = sum( size(S & N(v)) for v in S ) ; contribution = sum_v / 2 ; return contribution ; aggregate: total / 3 |
| EE | triangle | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1358 | - | 0.2680 | 0.0000 | return sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) / 2 ; aggregate: total / 3 |
| EE | triangle | 15 | True | 1 | 1 | False | False | 0.4487 | True | True | 0.6982 | - | 0.1265 | -0.1415 | p = project(P, D) ; s = sum( size( p & N(u) ) for u in p ) ; return s / 2 ; aggregate: total / 3 |
| EE | triangle | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle | 18 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1358 | - | 0.2680 | 0.0000 | total = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return total / 2 ; aggregate: total / 3 |
| EE | triangle | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
