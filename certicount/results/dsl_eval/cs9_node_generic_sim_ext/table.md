# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 20 independent design(s), 3 draft(s) x up to 1 restart(s) per release (rows, matrix), selection simulated (public Holme-Kim graphs, average degrees 4,8,16, 8 releases each, never chosen at a score >= 1; run-time choice on Chung-Lu graphs of the published noisy degrees), own-row check on, tighten 1, early stop off, normalisation on, prompt generic (core generic, 62a207c03a9c4864), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate off.

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio | mean_candidates | runs_matrix | runs_rows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree-ge3 | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.7000 | 1.4000 | 1.0000 | 3.3500 | 20 | 0.0000 | 0.7500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0625 | 1.0000 | 0.0000 | 0.0000 |
| PM | triangle-edge | 20 | 0.5000 | [0.30, 0.70] | 0.5000 | 0.1000 | 2.1000 | 1.0000 | 5.7500 | 9 | 0.0000 | 0.3000 | 1.0000 | 1.0000 | 1.0000 | 1.0200 | 1.2000 | 1.0013 | 0.5000 | 0.3000 | 0.7000 |
| PM | triangle-node | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.4500 | 1.7500 | 1.0000 | 3.9500 | 20 | 0.0000 | 0.4500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9800 | 1.0000 | 0.5500 | 0.4500 |
| CU | degree-ge3 | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.7500 | 1.3158 | 1.0000 | 3.3000 | 15 | 0.0526 | 0.8421 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0395 | 0.9500 | 0.0000 | 0.0000 |
| CU | triangle-edge | 20 | 0.4500 | [0.26, 0.66] | 0.4500 | 0.0500 | 2.1111 | 1.0000 | 5.7500 | 9 | 0.0000 | 0.3333 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0425 | 0.5500 | 0.1644 | 0.8356 |
| CU | triangle-node | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.3500 | 1.8500 | 1.0000 | 3.9000 | 20 | 0.0000 | 0.2500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9700 | 1.0000 | 0.4000 | 0.6000 |
| Do | degree-ge3 | 20 | 0.9000 | [0.70, 0.97] | 0.9000 | 0.7500 | 1.2778 | 1.0000 | 3.3500 | 17 | 0.0000 | 0.8889 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0278 | 0.9000 | 0.0000 | 0.0000 |
| Do | triangle-edge | 20 | 0.5500 | [0.34, 0.74] | 0.5500 | 0.1500 | 2.0909 | 1.0000 | 5.8500 | 11 | 0.0000 | 0.2727 | 1.0000 | 1.0000 | 1.0000 | 1.0545 | 1.2000 | 0.9770 | 0.6000 | 0.2209 | 0.7791 |
| Do | triangle-node | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.5500 | 1.6000 | 1.0000 | 3.8000 | 20 | 0.0000 | 0.3500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9600 | 1.0000 | 0.5500 | 0.4500 |
| ML | degree-ge3 | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.7500 | 1.4500 | 1.0000 | 3.2500 | 19 | 0.0500 | 0.9000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0250 | 1.0000 | 0.0000 | 0.0000 |
| ML | triangle-edge | 20 | 0.4000 | [0.22, 0.61] | 0.4000 | 0.1000 | 2.1250 | 1.0000 | 5.9000 | 8 | 0.0000 | 0.3750 | 1.0000 | 1.0000 | 1.0000 | 1.0250 | 1.2000 | 1.0072 | 0.4000 | 0.3750 | 0.6250 |
| ML | triangle-node | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.6000 | 1.5000 | 1.0000 | 3.6500 | 20 | 0.0000 | 0.3500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9600 | 1.0000 | 0.5500 | 0.4500 |
| CS | degree-ge3 | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.7500 | 1.3500 | 1.0000 | 3.2000 | 18 | 0.0500 | 0.8000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0500 | 1.0000 | 0.0000 | 0.0000 |
| CS | triangle-edge | 20 | 0.4000 | [0.22, 0.61] | 0.4000 | 0.1000 | 2.1250 | 1.0000 | 5.8500 | 8 | 0.0000 | 0.2500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0154 | 0.4500 | 0.2500 | 0.7500 |
| CS | triangle-node | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.7500 | 1.2500 | 1.0000 | 3.6500 | 20 | 0.0000 | 0.4000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9400 | 1.0000 | 0.7000 | 0.3000 |
| EE | degree-ge3 | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.8000 | 1.2500 | 1.0000 | 3.4000 | 18 | 0.1000 | 0.7500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0625 | 1.0000 | 0.0000 | 0.0000 |
| EE | triangle-edge | 20 | 0.3500 | [0.18, 0.57] | 0.3500 | 0.0500 | 2.4286 | 1.0000 | 6.0500 | 7 | 0.0000 | 0.2857 | 1.0000 | 1.0000 | 1.0000 | 1.0571 | 1.2000 | 0.9899 | 0.3500 | 0.2857 | 0.7143 |
| EE | triangle-node | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.5500 | 1.6000 | 1.0000 | 3.6000 | 20 | 0.0000 | 0.2500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9600 | 1.0000 | 0.4500 | 0.5500 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | degree-ge3 | 0.0292 | 0.0281 | 0.0281 | 0.0011 | 0.0044 | 0.7500 | 0.0000 |
| PM | triangle-edge | 0.1912 | 0.1822 | 0.2086 | -0.0174 | 0.0000 | 0.3000 | 0.0000 |
| PM | triangle-node | 0.0743 | 0.0689 | 0.0724 | 0.0019 | 0.0219 | 0.1000 | 0.0000 |
| CU | degree-ge3 | 0.1075 | 0.1077 | 0.1077 | -0.0001175 | 0.0000 | 0.8421 | 0.0000 |
| CU | triangle-edge | 0.4986 | 0.4720 | 0.5598 | -0.0612 | 0.0000 | 0.1602 | 0.0278 |
| CU | triangle-node | 0.2167 | 0.1989 | 0.2418 | -0.0250 | 0.0277 | 0.0500 | 0.0000 |
| Do | degree-ge3 | 0.1139 | 0.1143 | 0.1143 | -0.0004575 | 0.0000 | 0.8889 | 0.0000 |
| Do | triangle-edge | 0.5648 | 0.5576 | 0.5188 | 0.0460 | 0.1002 | 0.2182 | 0.0427 |
| Do | triangle-node | 0.2408 | 0.2443 | 0.2276 | 0.0132 | 0.0390 | 0.1000 | 0.0000 |
| ML | degree-ge3 | 0.1175 | 0.1179 | 0.1179 | -0.0004278 | 0.0000 | 0.9000 | 0.0000 |
| ML | triangle-edge | 0.3739 | 0.3727 | 0.3873 | -0.0134 | 0.0099 | 0.3750 | 0.0287 |
| ML | triangle-node | 0.2085 | 0.2213 | 0.2174 | -0.0089 | 0.0055 | 0.2210 | 0.0000 |
| CS | degree-ge3 | 0.1766 | 0.1763 | 0.1763 | 0.0003065 | 0.0015 | 0.8000 | 0.0000 |
| CS | triangle-edge | 0.7128 | 0.7411 | 0.6280 | 0.0848 | 0.1130 | 0.2500 | 0.0750 |
| CS | triangle-node | 0.2692 | 0.2658 | 0.2346 | 0.0345 | 0.0604 | 0.1000 | 0.0000 |
| EE | degree-ge3 | 0.0602 | 0.0585 | 0.0585 | 0.0017 | 0.0069 | 0.7500 | 0.0000 |
| EE | triangle-edge | 0.2739 | 0.2694 | 0.3197 | -0.0458 | 0.0000 | 0.2857 | 0.0000 |
| EE | triangle-node | 0.1336 | 0.1325 | 0.1447 | -0.0111 | 0.0115 | 0.0500 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree-ge3 | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | s = size(P) ; return max(0, min(1, s - 2)) ; aggregate: total |
| PM | degree-ge3 | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | size_P = size(P) ; report = min(1, max(0, size_P - 2)) ; return report ; aggregate: total |
| PM | degree-ge3 | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | value = clip(size(P) - 2, 0, 1) ; return value ; aggregate: total |
| PM | degree-ge3 | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | size_P = size(P) ; value = size_P - 2 ; return clip(value, 0, 1) ; aggregate: total |
| PM | degree-ge3 | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | d = size(P) ; report = 1 - clip(3 - d, 0, 1) ; return report ; aggregate: total |
| PM | degree-ge3 | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | value = max(0, size(P) - 2) ; return clip(value, 0, 1) ; aggregate: total |
| PM | degree-ge3 | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | size_p = size(P) ; report = clip(size_p - 2, 0, 1) ; return report ; aggregate: total |
| PM | degree-ge3 | 7 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0325 | 0.0044 | d = size(project(P, D)) ; return clip(d - 2, 0, 1) ; aggregate: total |
| PM | degree-ge3 | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | d = size(P) ; report = clip( max(0, d - 2 ), 0, 1 ) ; return report ; aggregate: total |
| PM | degree-ge3 | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | value = size(P) ; result = max(0, min(1, value - 2)) ; return result ; aggregate: total |
| PM | degree-ge3 | 10 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0325 | 0.0044 | projected_P = project(P, D) ; report = clip(size(projected_P) - 2, 0, 1) ; return report ; aggregate: total |
| PM | degree-ge3 | 11 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0325 | 0.0044 | s = size(project(P, D)) ; return clip(comb(s, 3), 0, 1) ; aggregate: total |
| PM | degree-ge3 | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | report = max(0, min(1, size(P) - 2)) ; return report ; aggregate: total |
| PM | degree-ge3 | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | size_P = size(P) ; return clip(size_P - 2, 0, 1) ; aggregate: total |
| PM | degree-ge3 | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | s = size(P) ; return clip(s - 2, 0, 1) ; aggregate: total |
| PM | degree-ge3 | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | size_P = size(P) ; value = clip(size_P - 2, 0, 1) ; return value ; aggregate: total |
| PM | degree-ge3 | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | indicator = clip(size(P) - 2, 0, 1) ; return indicator ; aggregate: total |
| PM | degree-ge3 | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | return clip(size(P) - 3 + 1, 0, 1) ; aggregate: total |
| PM | degree-ge3 | 18 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0325 | 0.0044 | s = size(project(P, D)) ; t = s - 2 ; u = clip(t, 0, 1) ; return u ; aggregate: total |
| PM | degree-ge3 | 19 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0325 | 0.0044 | s = size(project(P, D)) ; report = clip(s - 2, 0, 1) ; return report ; aggregate: total |
| PM | triangle-edge | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 1 | True | 1 | 3 | False | False | 0.9947 | True | True | 0.2953 | - | 0.1925 | -0.0161 | return sum(clip(size(P & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| PM | triangle-edge | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.3215 | - | 0.2086 | 0.0000 | return sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| PM | triangle-edge | 7 | True | 1 | 2 | False | False | 1.0030 | True | True | 0.3048 | - | 0.1822 | -0.0263 | res = sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; return res ; aggregate: total / 2 |
| PM | triangle-edge | 8 | True | 1 | 3 | False | False | 1.0030 | True | True | 0.3048 | - | 0.1822 | -0.0263 | return sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| PM | triangle-edge | 9 | True | 1 | 2 | False | False | 1.0030 | True | True | 0.3048 | - | 0.1822 | -0.0263 | projected = project(P, D) ; total = sum( clip( size( N(v) & projected ), 0, 1 ) for v in projected ) ; return total ; aggregate: total / 2 |
| PM | triangle-edge | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 11 | True | 1 | 2 | False | False | 1.0030 | True | True | 0.3048 | - | 0.1822 | -0.0263 | total = sum( clip( size( project(P, D) & N(v) ), 0, 1 ) for v in project(P, D) ) ; return total ; aggregate: total / 2 |
| PM | triangle-edge | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3215 | - | 0.2086 | 0.0000 | projected_P = project(P, D) ; return sum( clip( sum( A(j, k) for k in projected_P ), 0, 1 ) for j in projected_P ) ; aggregate: total / 2 |
| PM | triangle-edge | 13 | True | 1 | 2 | False | False | 1.0030 | True | True | 0.3048 | - | 0.1822 | -0.0263 | return sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| PM | triangle-edge | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 17 | True | 1 | 3 | False | False | 1.0030 | True | True | 0.3048 | - | 0.1822 | -0.0263 | S = project(P, D) ; return sum(clip(size(S & N(v)), 0, 1) for v in S) ; aggregate: total / 2 |
| PM | triangle-edge | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3215 | - | 0.2086 | 0.0000 | P_proj = project(P, D) ; count_u = sum( clip( sum( A(w, v) for w in P_proj ), 0, 1 ) for v in P_proj ) ; return count_u ; aggregate: total / 2 |
| PM | triangle-edge | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-node | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2309 | - | 0.0797 | 0.0073 | P_proj = project(P, D) ; sum_edges = sum( sum( A(u, v) for v in P_proj ) for u in P_proj ) ; indicator = clip( sum_edges / 2, 0, 1 ) ; return indicator ; aggregate: total |
| PM | triangle-node | 1 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.2117 | - | 0.0705 | -0.0019 | sum_pairs = sum( sum( A(u, v) for v in P ) for u in P ) ; E = sum_pairs / 2 ; return clip(E, 0, 1) ; aggregate: total |
| PM | triangle-node | 2 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1387 | - | 0.0630 | -0.0093 | sum_edges = sum( sum( A(u, v) for v in P ) for u in P ) ; return clip(sum_edges, 0, 1) ; aggregate: total |
| PM | triangle-node | 3 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.4257 | - | 0.0673 | -0.0050 | projected = project(P, D) ; count = sum( size(N(v) & P) for v in projected ) ; return clip(count, 0, 1) ; aggregate: total |
| PM | triangle-node | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2928 | - | 0.0943 | 0.0219 | P_proj = project(P, D) ; sum_pairs = sum(sum(A(v, w) for w in P_proj) for v in P_proj) ; return clip(sum_pairs - 1, 0, 1) ; aggregate: total |
| PM | triangle-node | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2309 | - | 0.0797 | 0.0073 | Q = project(P, D) ; sum_ordered = sum( sum( A(v, w) for w in Q ) for v in Q ) ; sum_unordered = sum_ordered / 2 ; contribution = clip(sum_unordered, 0, 1) ; return contribution ; aggregate: total |
| PM | triangle-node | 6 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.4286 | - | 0.0674 | -0.0050 | return clip( sum( size( project(P, D) & N(v) ) for v in project(P, D) ), 0, 1 ) ; aggregate: total |
| PM | triangle-node | 7 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.4257 | - | 0.0673 | -0.0050 | return clip( sum( size(P & N(v)) for v in P ), 0, 1 ) ; aggregate: total |
| PM | triangle-node | 8 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.2309 | - | 0.0797 | 0.0073 | S = project(P, D) ; sum_edges = sum(sum(A(v, w) for w in S) for v in S) ; sum_edges2 = sum_edges / 2 ; result = clip(sum_edges2, 0, 1) ; return result ; aggregate: total |
| PM | triangle-node | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1679 | - | 0.0724 | 0.0000 | S = project(P, D) ; sum_A = sum(sum(A(v, w) for w in S) for v in S) ; indicator = clip(sum_A, 0, 1) ; return indicator ; aggregate: total |
| PM | triangle-node | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1679 | - | 0.0724 | 0.0000 | S = project(P, D) ; sum_over_pairs = sum( sum( A(u, v) for v in S ) for u in S ) ; contribution = clip( sum_over_pairs, 0, 1 ) ; return contribution ; aggregate: total |
| PM | triangle-node | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2928 | - | 0.0943 | 0.0219 | S = project(P, D) ; total_sum = sum( sum( A(u, v) for v in S ) for u in S ) ; value = clip( (total_sum - 1), 0, 1 ) ; return value ; aggregate: total |
| PM | triangle-node | 12 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.4286 | - | 0.0674 | -0.0050 | S = project(P, D) ; ordered_pairs = sum(size(N(v) & S) for v in S) ; return clip(ordered_pairs, 0, 1) ; aggregate: total |
| PM | triangle-node | 13 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.4286 | - | 0.0674 | -0.0050 | size_Pu = size(project(P, D)) ; sum_pairs = sum( size(N(j) & project(P, D)) for j in project(P, D) ) ; return clip( sum_pairs, 0, 1 ) ; aggregate: total |
| PM | triangle-node | 14 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.4286 | - | 0.0674 | -0.0050 | neighbors = project(P, D) ; sum_pairs = sum(size(neighbors & N(u)) for u in neighbors) ; count_pairs = sum_pairs / 2 ; return clip(count_pairs, 0, 1) ; aggregate: total |
| PM | triangle-node | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2309 | - | 0.0797 | 0.0073 | S = project(P, D) ; sum_ordered = sum(sum(A(x, y) for y in S) for x in S) ; sum_unordered = sum_ordered / 2 ; return clip(sum_unordered, 0, 1) ; aggregate: total |
| PM | triangle-node | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2928 | - | 0.0943 | 0.0219 | S = project(P, D) ; total_edges = sum( sum( A(u, v) for v in S ) for u in S ) ; result = clip( (total_edges - 1), 0, 1 ) ; return result ; aggregate: total |
| PM | triangle-node | 17 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.4286 | - | 0.0674 | -0.0050 | S = project(P, D) ; sum_val = sum(size(S & N(u)) for u in S) ; count_pairs = sum_val / 2 ; result = clip(count_pairs, 0, 1) ; return result ; aggregate: total |
| PM | triangle-node | 18 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.4286 | - | 0.0674 | -0.0050 | S = project(P, D) ; s = sum( size(S & N(y)) for y in S ) ; return clip(s, 0, 1) ; aggregate: total |
| PM | triangle-node | 19 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.4257 | - | 0.0673 | -0.0050 | count = sum( size(N(v) & P) for v in P ) ; return clip( count / 2, 0, 1 ) ; aggregate: total |
| CU | degree-ge3 | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | x = size(P) ; return clip(x - 2, 0, 1) ; aggregate: total |
| CU | degree-ge3 | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | x = size(P) ; return clip(x - 2, 0, 1) ; aggregate: total |
| CU | degree-ge3 | 2 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | size_P = size(P) ; return clip(size_P - 2, 0, 1) ; aggregate: total |
| CU | degree-ge3 | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | count = clip(size(P) - 2, 0, 1) ; return count ; aggregate: total |
| CU | degree-ge3 | 4 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | return clip(size(P) - 2, 0, 1) ; aggregate: total |
| CU | degree-ge3 | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | binary_value = clip(size(P) - 2, 0, 1) ; return binary_value ; aggregate: total |
| CU | degree-ge3 | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | count = clip(size(P) - 2, 0, 1) ; return count ; aggregate: total |
| CU | degree-ge3 | 7 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1069 | -0.0007443 | projected_p = project(P, D) ; degree = size(projected_p) ; report = min(1, max(0, degree - 2)) ; return report ; aggregate: total |
| CU | degree-ge3 | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | indicator = clip(size(P) - 2, 0, 1) ; return indicator ; aggregate: total |
| CU | degree-ge3 | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | d = size(P) ; return clip(d - 2, 0, 1) ; aggregate: total |
| CU | degree-ge3 | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | return clip(max(0, size(P) - 2), 0, 1) ; aggregate: total |
| CU | degree-ge3 | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | size_P = size(P) ; indicator = clip(size_P - 2, 0, 1) ; return indicator ; aggregate: total |
| CU | degree-ge3 | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | d = size(P) ; value = clip(d - 2, 0, 1) ; return value ; aggregate: total |
| CU | degree-ge3 | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | size_P = size(P) ; indicator = clip(size_P - 2, 0, 1) ; return indicator ; aggregate: total |
| CU | degree-ge3 | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | s = size(P) ; report = clip(s - 2, 0, 1) ; return report ; aggregate: total |
| CU | degree-ge3 | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | s = size(P) ; v = s - 2 ; return clip(v, 0, 1) ; aggregate: total |
| CU | degree-ge3 | 16 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1069 | -0.0007443 | s = size(project(P, D)) ; value = clip(max(0, s - 3 + 1), 0, 1) ; return value ; aggregate: total |
| CU | degree-ge3 | 17 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1069 | -0.0007443 | a = size(project(P, D)) ; b = a - 2 ; c = clip(b, 0, 1) ; return c ; aggregate: total |
| CU | degree-ge3 | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | degree-ge3 | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | s = size(P) ; report = clip(s - 2, 0, 1) ; return report ; aggregate: total |
| CU | triangle-edge | 0 | True | 1 | 2 | False | False | 1.0830 | True | True | 0.0762 | - | 0.4720 | -0.0878 | P_proj = project(P, D) ; return sum(clip(size(P_proj & N(v)), 0, 1) for v in P_proj) ; aggregate: total / 2 |
| CU | triangle-edge | 1 | True | 1 | 2 | False | False | 1.0830 | True | True | 0.0762 | - | 0.4720 | -0.0878 | P_proj = project(P, D) ; return sum( clip( size( N(v) & P_proj ), 0, 1 ) for v in P_proj ) ; aggregate: total / 2 |
| CU | triangle-edge | 2 | True | 1 | 2 | False | False | 1.0830 | True | True | 0.0762 | - | 0.4720 | -0.0878 | projected_neighbors = project(P, D) ; total = sum( clip(size(N(j) & projected_neighbors), 0, 1) for j in projected_neighbors ) ; return total ; aggregate: total / 2 |
| CU | triangle-edge | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 7 | True | 1 | 2 | False | False | 1.0830 | True | True | 0.0762 | - | 0.4720 | -0.0878 | return sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| CU | triangle-edge | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 9 | True | 1 | 2 | False | False | 1.0830 | True | True | 0.0762 | - | 0.4720 | -0.0878 | projected_P = project(P, D) ; return sum(clip(size(projected_P & N(v)), 0, 1) for v in projected_P) ; aggregate: total / 2 |
| CU | triangle-edge | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 12 | True | 1 | 3 | False | True | 0.9423 | True | True | 0.2953 | - | 0.5477 | -0.0120 | projected = project(P, D) ; sum_v = sum( clip( sum( A(v, w) for w in projected ), 0, 1 ) for v in projected ) ; return sum_v ; aggregate: total / 2 |
| CU | triangle-edge | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2953 | - | 0.5598 | 0.0000 | total = sum( clip( sum( A(u, w) for w in project(P, D) ), 0, 1 ) for u in project(P, D) ) ; return total ; aggregate: total / 2 |
| CU | triangle-edge | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 17 | True | 1 | 3 | False | True | 0.9423 | True | True | 0.2953 | - | 0.5477 | -0.0120 | neighbors = project(P, D) ; count = sum(clip(sum(A(v, w) for w in neighbors), 0, 1) for v in neighbors) ; return count ; aggregate: total / 2 |
| CU | triangle-edge | 18 | True | 1 | 1 | False | False | 1.0830 | True | True | 0.0762 | - | 0.4720 | -0.0878 | contrib = sum( clip( size( N(v) & project(P, D) ), 0, 1 ) for v in project(P, D) ) ; return contrib ; aggregate: total / 2 |
| CU | triangle-edge | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-node | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2063 | - | 0.2418 | 0.0000 | S = project(P, D) ; sum_pairs = sum( sum( A(u, v) for v in S ) for u in S ) ; return clip(sum_pairs, 0, 1) ; aggregate: total |
| CU | triangle-node | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2372 | - | 0.2695 | 0.0277 | sum_ordered = sum(sum(A(k, l) for l in project(P, D)) for k in project(P, D)) ; sum_edges = sum_ordered / 2 ; indicator = clip(sum_edges, 0, 1) ; return indicator ; aggregate: total |
| CU | triangle-node | 2 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | S = project(P, D) ; sum_edges = sum( size(N(u) & S) for u in S ) ; return clip(sum_edges, 0, 1) ; aggregate: total |
| CU | triangle-node | 3 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | proj = project(P, D) ; sum_val = sum(clip(size(N(j) & proj), 0, 1) for j in proj) ; return clip(sum_val, 0, 1) ; aggregate: total |
| CU | triangle-node | 4 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.2633 | - | 0.2167 | -0.0250 | sum_S = sum( sum( A(u, v) for v in P ) for u in P ) ; indicator = clip( sum_S / 2, 0, 1 ) ; return indicator ; aggregate: total |
| CU | triangle-node | 5 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | s = project(P, D) ; sum_val = sum(size(s & N(u)) for u in s) ; return clip(sum_val, 0, 1) ; aggregate: total |
| CU | triangle-node | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2372 | - | 0.2695 | 0.0277 | S = project(P, D) ; sum_A = sum(sum(A(i, j) for j in S) for i in S) ; edge_count = sum_A / 2 ; result = clip(edge_count, 0, 1) ; return result ; aggregate: total |
| CU | triangle-node | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2372 | - | 0.2695 | 0.0277 | S = project(P, D) ; sum_A = sum( sum( A(u, v) for v in S ) for u in S ) ; num_pairs = sum_A / 2 ; return clip(num_pairs, 0, 1) ; aggregate: total |
| CU | triangle-node | 8 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | s = sum( clip( size(N(v) & project(P, D)), 0, 1 ) for v in project(P, D) ) ; return clip(s, 0, 1) ; aggregate: total |
| CU | triangle-node | 9 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | return clip( sum( size(N(v) & project(P, D)) for v in project(P, D) ), 0, 1 ) ; aggregate: total |
| CU | triangle-node | 10 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | s = size(project(P, D)) ; t = sum(size(N(v) & project(P, D)) for v in project(P, D)) ; u = t / 2 ; return clip(u, 0, 1) ; aggregate: total |
| CU | triangle-node | 11 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | S = project(P, D) ; sum_over_y = sum( size(S & N(y)) for y in S ) ; indicator = clip(sum_over_y, 0, 1) ; return indicator ; aggregate: total |
| CU | triangle-node | 12 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | S = project(P, D) ; count = sum( size(N(v) & S) for v in S ) ; return clip(count, 0, 1) ; aggregate: total |
| CU | triangle-node | 13 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | S = project(P, D) ; sum_edges = sum( size(N(y) & S) for y in S ) ; edges_between_neighbors = sum_edges / 2 ; return clip(edges_between_neighbors, 0, 1) ; aggregate: total |
| CU | triangle-node | 14 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.2633 | - | 0.2167 | -0.0250 | sum_edges = sum( sum( A(v, w) for w in P ) for v in P ) ; sum_edges_over_2 = sum_edges / 2 ; contrib = clip( sum_edges_over_2, 0, 1 ) ; return contrib ; aggregate: total |
| CU | triangle-node | 15 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | S = project(P, D) ; total_pairs = sum( size(S & N(u)) for u in S ) ; return clip(total_pairs, 0, 1) ; aggregate: total |
| CU | triangle-node | 16 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | S = project(P, D) ; sum_edges = sum(size(N(v) & S) for v in S) ; num_edges = sum_edges / 2 ; indicator = clip(num_edges, 0, 1) ; return indicator ; aggregate: total |
| CU | triangle-node | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2372 | - | 0.2695 | 0.0277 | projected = project(P, D) ; sum_ordered = sum( sum( A(u, v) for v in projected ) for u in projected ) ; number = sum_ordered / 2 ; return clip(number, 0, 1) ; aggregate: total |
| CU | triangle-node | 18 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.2117 | - | 0.1942 | -0.0476 | sum_A = sum(sum(A(u, v) for v in P) for u in P) ; return clip(sum_A, 0, 1) ; aggregate: total |
| CU | triangle-node | 19 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | sum_val = sum( size( project(P, D) & N(v) ) for v in project(P, D) ) ; return clip( sum_val, 0, 1 ) ; aggregate: total |
| Do | degree-ge3 | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | size_P = size(P) ; return min(1, max(0, size_P - 2)) ; aggregate: total |
| Do | degree-ge3 | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | size_P = size(P) ; report = clip(size_P - 2, 0, 1) ; return report ; aggregate: total |
| Do | degree-ge3 | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | size_p = size(P) ; report = max(0, min(1, size_p - 2)) ; return report ; aggregate: total |
| Do | degree-ge3 | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | return clip( max(0, size(P) - 2), 0, 1 ) ; aggregate: total |
| Do | degree-ge3 | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | degree-ge3 | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | size_P = size(P) ; report = clip(size_P - 2, 0, 1) ; return report ; aggregate: total |
| Do | degree-ge3 | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | size_P = size(P) ; indicator = clip(size_P - 2, 0, 1) ; return indicator ; aggregate: total |
| Do | degree-ge3 | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | indicator = clip(size(P) - 2, 0, 1) ; return indicator ; aggregate: total |
| Do | degree-ge3 | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | degree-ge3 | 9 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | d = size(P) ; return clip(d - 2, 0, 1) ; aggregate: total |
| Do | degree-ge3 | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | report = clip(size(P) - 2, 0, 1) ; return report ; aggregate: total |
| Do | degree-ge3 | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | x = size(P) ; report = clip(x - 2, 0, 1) ; return report ; aggregate: total |
| Do | degree-ge3 | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | size_p = size(P) ; return clip(size_p - 2, 0, 1) ; aggregate: total |
| Do | degree-ge3 | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | return min(1, max(0, size(P) - 2)) ; aggregate: total |
| Do | degree-ge3 | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | value = max(0, min(1, size(P) - 2)) ; return value ; aggregate: total |
| Do | degree-ge3 | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | size_P = size(P) ; report = 1 - clip(3 - size_P, 0, 1) ; return report ; aggregate: total |
| Do | degree-ge3 | 16 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1102 | -0.0041 | projected_P = project(P, D) ; size_P = size(projected_P) ; return clip(size_P - 2, 0, 1) ; aggregate: total |
| Do | degree-ge3 | 17 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1102 | -0.0041 | d = size(project(P, D)) ; report = clip(max(0, d - 2), 0, 1) ; return report ; aggregate: total |
| Do | degree-ge3 | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | x = size(P) ; y = x - 2 ; return clip(y, 0, 1) ; aggregate: total |
| Do | degree-ge3 | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | size_P = size(P) ; return max(0, min(1, size_P - 2)) ; aggregate: total |
| Do | triangle-edge | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 3 | True | 1 | 2 | False | False | 0.9303 | True | True | 0.0289 | - | 0.6189 | 0.1002 | return sum(clip(size(N(v) & P), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| Do | triangle-edge | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 6 | True | 1 | 3 | False | False | 0.9303 | True | True | 0.0289 | - | 0.6189 | 0.1002 | projected_neighbors = project(P, D) ; result = sum( clip( size(N(v) & P), 0, 1 ) for v in projected_neighbors ) ; return result ; aggregate: total / 2 |
| Do | triangle-edge | 7 | True | 1 | 2 | False | False | 0.9990 | True | True | 0.0289 | - | 0.5576 | 0.0388 | total = sum( clip(size(project(P, D) & N(k)), 0, 1) for k in project(P, D) ) ; return total ; aggregate: total / 2 |
| Do | triangle-edge | 8 | True | 1 | 2 | False | False | 0.9303 | True | True | 0.0289 | - | 0.6189 | 0.1002 | S = project(P, D) ; return sum( clip( size( P & N(v) ), 0, 1 ) for v in S ) ; aggregate: total / 2 |
| Do | triangle-edge | 9 | True | 1 | 1 | False | True | 0.9606 | True | True | 0.3064 | - | 0.5303 | 0.0115 | return sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| Do | triangle-edge | 10 | True | 1 | 3 | False | False | 0.9990 | True | True | 0.0289 | - | 0.5576 | 0.0388 | projected = project(P, D) ; total = sum(clip(size(projected & N(v)), 0, 1) for v in projected) ; return total ; aggregate: total / 2 |
| Do | triangle-edge | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3064 | - | 0.5188 | 0.0000 | proj = project(P, D) ; return sum( clip( sum( A(v, w) for w in proj ), 0, 1 ) for v in proj ) ; aggregate: total / 2 |
| Do | triangle-edge | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3064 | - | 0.5188 | 0.0000 | P_proj = project(P, D) ; total = sum( clip( sum( A(v, w) for w in P_proj ), 0, 1 ) for v in P_proj ) ; return total ; aggregate: total / 2 |
| Do | triangle-edge | 13 | True | 1 | 3 | False | False | 0.9990 | True | True | 0.0289 | - | 0.5576 | 0.0388 | projected_P = project(P, D) ; count = sum( clip( size( projected_P & N(v) ), 0, 1 ) for v in projected_P ) ; return count ; aggregate: total / 2 |
| Do | triangle-edge | 14 | True | 1 | 2 | False | False | 0.9990 | True | True | 0.0289 | - | 0.5576 | 0.0388 | total = sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; return total ; aggregate: total / 2 |
| Do | triangle-edge | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 18 | True | 1 | 3 | False | False | 0.9990 | True | True | 0.0289 | - | 0.5576 | 0.0388 | sum_clip = sum( clip( size( N(v) & project( P, D ) ), 0, 1 ) for v in project( P, D ) ) ; return sum_clip ; aggregate: total / 2 |
| Do | triangle-edge | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-node | 0 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | S = project(P, D) ; total_pairs = sum(size(N(y) & S) for y in S) ; indicator = clip(total_pairs, 0, 1) ; return indicator ; aggregate: total |
| Do | triangle-node | 1 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | sum_val = sum( size( project(P, D) & N(y) ) for y in project(P, D) ) ; return clip( sum_val - 1, 0, 1 ) ; aggregate: total |
| Do | triangle-node | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1792 | - | 0.2276 | 0.0000 | S = project(P, D) ; sum_ordered = sum(sum(A(j, k) for k in S) for j in S) ; return clip(sum_ordered, 0, 1) ; aggregate: total |
| Do | triangle-node | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2911 | - | 0.2666 | 0.0390 | projected_P = project(P, D) ; sum_A = sum(sum(A(j, k) for k in projected_P) for j in projected_P) ; result = clip(sum_A - 1, 0, 1) ; return result ; aggregate: total |
| Do | triangle-node | 4 | True | 1 | 2 | False | False | 0.8000 | True | True | 0.2167 | - | 0.2275 | -0.0001265 | sum_ordered = sum(sum(A(u, v) for v in P) for u in P) ; sum_unordered = sum_ordered / 2 ; report = clip(sum_unordered, 0, 1) ; return report ; aggregate: total |
| Do | triangle-node | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2352 | - | 0.2428 | 0.0152 | S = project(P, D) ; total_ordered = sum( sum( A(u, v) for v in S ) for u in S ) ; unordered_pairs = total_ordered / 2 ; indicator = clip( unordered_pairs, 0, 1 ) ; return indicator ; aggregate: total |
| Do | triangle-node | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2352 | - | 0.2428 | 0.0152 | S = project(P, D) ; sum_ordered = sum( sum( A(v, w) for w in S ) for v in S ) ; sum_unordered = sum_ordered / 2 ; result = clip(sum_unordered, 0, 1) ; return result ; aggregate: total |
| Do | triangle-node | 7 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | s = sum(size(N(v) & project(P, D)) for v in project(P, D)) ; return clip(s, 0, 1) ; aggregate: total |
| Do | triangle-node | 8 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.2167 | - | 0.2275 | -0.0001265 | sum_ordered = sum( sum( A(u, v) for v in P ) for u in P ) ; sum_unordered = sum_ordered / 2 ; return clip( sum_unordered, 0, 1 ) ; aggregate: total |
| Do | triangle-node | 9 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | projected = project(P, D) ; sum_pairs = sum(size(projected & N(u)) for u in projected) ; return clip(sum_pairs / 2, 0, 1) ; aggregate: total |
| Do | triangle-node | 10 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | S = project(P, D) ; sum_edges = sum( size(N(y) & S) for y in S ) ; indicator = clip( sum_edges, 0, 1 ) ; return indicator ; aggregate: total |
| Do | triangle-node | 11 | True | 1 | 2 | False | False | 0.8000 | True | True | 0.2167 | - | 0.2275 | -0.0001265 | sum_edges = sum( sum( A(v, w) for w in P ) for v in P ) ; count = sum_edges / 2 ; return clip(count, 0, 1) ; aggregate: total |
| Do | triangle-node | 12 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2463 | 0.0186 | sum_pairs = sum( size( P & N(j) ) for j in P ) ; return clip( sum_pairs, 0, 1 ) ; aggregate: total |
| Do | triangle-node | 13 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.2167 | - | 0.2275 | -0.0001265 | sum_pairs = sum(sum(A(v, w) for w in P) for v in P) ; indicator = clip(sum_pairs / 2, 0, 1) ; return indicator ; aggregate: total |
| Do | triangle-node | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1792 | - | 0.2276 | 0.0000 | S = project(P, D) ; total_edges = sum( sum( A(u, v) for v in S ) for u in S ) ; value = clip( total_edges, 0, 1 ) ; return value ; aggregate: total |
| Do | triangle-node | 15 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | S = project(P, D) ; T = sum( size(S & N(y)) for y in S ) ; return clip(T, 0, 1) ; aggregate: total |
| Do | triangle-node | 16 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | S = project(P, D) ; sum_ = sum( size(S & N(y)) for y in S ) ; return clip(sum_, 0, 1) ; aggregate: total |
| Do | triangle-node | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2352 | - | 0.2428 | 0.0152 | projected_P = project(P, D) ; sum_ordered = sum( sum( A(j, k) for k in projected_P ) for j in projected_P ) ; sum_unordered = sum_ordered / 2 ; return clip( sum_unordered, 0, 1 ) ; aggregate: total |
| Do | triangle-node | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2352 | - | 0.2428 | 0.0152 | P_proj = project(P, D) ; sum_ordered = sum(sum(A(v, w) for w in P_proj) for v in P_proj) ; sum_edges = sum_ordered / 2 ; clip_sum = clip(sum_edges, 0, 1) ; return clip_sum ; aggregate: total |
| Do | triangle-node | 19 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | S = project(P, D) ; sum_pairs = sum(size(S & N(v)) for v in S) ; return clip(sum_pairs / 2, 0, 1) ; aggregate: total |
| ML | degree-ge3 | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | size_P = size(P) ; indicator = clip(size_P - 2, 0, 1) ; return indicator ; aggregate: total |
| ML | degree-ge3 | 1 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | s = size(P) ; return clip(s - 2, 0, 1) ; aggregate: total |
| ML | degree-ge3 | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | return clip(size(P) - 3 + 1, 0, 1) ; aggregate: total |
| ML | degree-ge3 | 3 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | size_P = size(P) ; report = min(max(size_P - 2, 0), 1) ; return report ; aggregate: total |
| ML | degree-ge3 | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | s = size(P) ; val = max(0, s - 2) ; report = clip(val, 0, 1) ; return report ; aggregate: total |
| ML | degree-ge3 | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | d = size(P) ; return clip(d - 2, 0, 1) ; aggregate: total |
| ML | degree-ge3 | 6 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | indicator = clip(size(P) - 3 + 1, 0, 1) ; return indicator ; aggregate: total |
| ML | degree-ge3 | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | size_P = size(P) ; value = clip(size_P - 2, 0, 1) ; return value ; aggregate: total |
| ML | degree-ge3 | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | contrib = clip(size(P) - 2, 0, 1) ; return contrib ; aggregate: total |
| ML | degree-ge3 | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | result = clip(size(P) - 2, 0, 1) ; return result ; aggregate: total |
| ML | degree-ge3 | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | x = size(P) ; report = clip(x - 2, 0, 1) ; return report ; aggregate: total |
| ML | degree-ge3 | 11 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1137 | -0.0043 | size_P = size(project(P, D)) ; return clip(size_P - 2, 0, 1) ; aggregate: total |
| ML | degree-ge3 | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | size_P = size(P) ; indicator = max(0, min(1, size_P - 2)) ; return indicator ; aggregate: total |
| ML | degree-ge3 | 13 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1137 | -0.0043 | projected_P = project(P, D) ; report = clip(size(projected_P) - 2, 0, 1) ; return report ; aggregate: total |
| ML | degree-ge3 | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | return max(0, min(1, size(P) - 2)) ; aggregate: total |
| ML | degree-ge3 | 15 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | report = clip(size(P) - 2, 0, 1) ; return report ; aggregate: total |
| ML | degree-ge3 | 16 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | return clip(size(P) - 2, 0, 1) ; aggregate: total |
| ML | degree-ge3 | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | size_P = size(P) ; contribution = clip(size_P - 2, 0, 1) ; return contribution ; aggregate: total |
| ML | degree-ge3 | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | size_P = size(P) ; indicator = max(0, min(1, size_P - 2)) ; return indicator ; aggregate: total |
| ML | degree-ge3 | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | return min(1, max(0, size(P) - 2)) ; aggregate: total |
| ML | triangle-edge | 0 | True | 1 | 2 | False | False | 1.0211 | True | True | 0.0380 | - | 0.3581 | -0.0292 | projected_neighbors = project(P, D) ; count = sum(clip(size(projected_neighbors & N(v)), 0, 1) for v in projected_neighbors) ; return count ; aggregate: total / 2 |
| ML | triangle-edge | 1 | True | 1 | 2 | False | False | 1.0211 | True | True | 0.0380 | - | 0.3581 | -0.0292 | projected = project(P, D) ; return sum(clip(size(projected & N(v)), 0, 1) for v in projected) ; aggregate: total / 2 |
| ML | triangle-edge | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3268 | - | 0.3873 | 0.0000 | s = sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; return s ; aggregate: total / 2 |
| ML | triangle-edge | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 7 | True | 1 | 3 | False | False | 1.0211 | True | True | 0.0380 | - | 0.3581 | -0.0292 | neighbors = project(P, D) ; count = sum(clip(size(neighbors & N(v)), 0, 1) for v in neighbors) ; return count ; aggregate: total / 2 |
| ML | triangle-edge | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 12 | True | 1 | 2 | False | False | 0.9731 | True | True | 0.0360 | - | 0.3971 | 0.0099 | return sum(clip(size(P & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| ML | triangle-edge | 13 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 14 | True | 1 | 3 | False | False | 1.0211 | True | True | 0.0380 | - | 0.3581 | -0.0292 | total = sum( clip( size( N(v) & project(P, D) ), 0, 1 ) for v in project(P, D) ) ; return total ; aggregate: total / 2 |
| ML | triangle-edge | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 16 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.3268 | - | 0.3873 | 0.0000 | projected = project(P, D) ; total = sum(clip(sum(A(v, w) for w in projected), 0, 1) for v in projected) ; return total ; aggregate: total / 2 |
| ML | triangle-edge | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3268 | - | 0.3873 | 0.0000 | S = project(P, D) ; sum_over_v = sum( clip( sum( A(v, w) for w in S ), 0, 1 ) for v in S ) ; return sum_over_v ; aggregate: total / 2 |
| ML | triangle-node | 0 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | S = project(P, D) ; total_pairs = sum( size(N(u) & S) for u in S ) ; return clip( total_pairs - 1, 0, 1 ) ; aggregate: total |
| ML | triangle-node | 1 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1738 | - | 0.1560 | -0.0614 | sum_pairs = sum( sum( A(u, v) for v in P ) for u in P ) ; result = clip( sum_pairs, 0, 1 ) ; return result ; aggregate: total |
| ML | triangle-node | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2008 | - | 0.2174 | 0.0000 | S = project(P, D) ; sum_over = sum( sum( A(u, v) for v in S ) for u in S ) ; value = clip(sum_over, 0, 1) ; return value ; aggregate: total |
| ML | triangle-node | 3 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.2158 | - | 0.1581 | -0.0593 | sum_pairs = sum(sum(A(u, v) for v in P) for u in P) ; value = sum_pairs / 2 ; return clip(value, 0, 1) ; aggregate: total |
| ML | triangle-node | 4 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | S = project(P, D) ; number_of_pairs = sum(size(S & N(k)) for k in S) ; count_j = clip(number_of_pairs, 0, 1) ; return count_j ; aggregate: total |
| ML | triangle-node | 5 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | S = project(P, D) ; total_pairs = sum( size(S & N(u)) for u in S ) ; result = clip(total_pairs - 1, 0, 1) ; return result ; aggregate: total |
| ML | triangle-node | 6 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | S = P ; count_edges = sum(size(N(v) & S) for v in S) ; return clip(count_edges / 2, 0, 1) ; aggregate: total |
| ML | triangle-node | 7 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | neighbors = project(P, D) ; sum_over_y = sum(size(N(y) & neighbors) for y in neighbors) ; count = sum_over_y / 2 ; result = clip(count, 0, 1) ; return result ; aggregate: total |
| ML | triangle-node | 8 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | P_proj = project(P, D) ; S = sum(size(N(v) & P_proj) for v in P_proj) ; result = clip(S, 0, 1) ; return result ; aggregate: total |
| ML | triangle-node | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2008 | - | 0.2174 | 0.0000 | S = project(P, D) ; sum_all_pairs = sum( sum( A(u, w) for w in S ) for u in S ) ; result = clip(sum_all_pairs, 0, 1) ; return result ; aggregate: total |
| ML | triangle-node | 10 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | S = project(P, D) ; sum_clip = sum(clip(size(N(u) & P), 0, 1) for u in S) ; return clip(sum_clip, 0, 1) ; aggregate: total |
| ML | triangle-node | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2320 | - | 0.2213 | 0.0039 | S = project(P, D) ; sum_ordered = sum( sum( A(u, v) for v in S ) for u in S ) ; sum_unordered = sum_ordered / 2 ; indicator = clip(sum_unordered, 0, 1) ; return indicator ; aggregate: total |
| ML | triangle-node | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2320 | - | 0.2213 | 0.0039 | sum_total = sum( sum( A(u, v) for v in project(P, D) ) for u in project(P, D) ) ; count = sum_total / 2 ; return clip(count, 0, 1) ; aggregate: total |
| ML | triangle-node | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2008 | - | 0.2174 | 0.0000 | P_projected = project(P, D) ; sum_A = sum( sum( A(u, v) for v in P_projected ) for u in P_projected ) ; return clip(sum_A, 0, 1) ; aggregate: total |
| ML | triangle-node | 14 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | S = project(P, D) ; sum_over_u = sum( size(N(u) & S) for u in S ) ; count = clip(sum_over_u, 0, 1) ; return count ; aggregate: total |
| ML | triangle-node | 15 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.2008 | - | 0.2174 | 0.0000 | return clip(sum(A(v, w) for v in project(P, D) for w in project(P, D)), 0, 1) ; aggregate: total |
| ML | triangle-node | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2320 | - | 0.2213 | 0.0039 | P_proj = project(P, D) ; sum_ordered = sum( sum(A(u, v) for v in P_proj) for u in P_proj ) ; sum_unordered = sum_ordered / 2 ; result = clip(sum_unordered, 0, 1) ; return result ; aggregate: total |
| ML | triangle-node | 17 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.2158 | - | 0.1581 | -0.0593 | sum_ordered = sum( sum( A(u, v) for v in P ) for u in P ) ; sum_unordered = sum_ordered / 2 ; return clip( sum_unordered, 0, 1 ) ; aggregate: total |
| ML | triangle-node | 18 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | sum_edges = sum(size(N(u) & project(P, D)) for u in project(P, D)) ; count = sum_edges / 2 ; return clip(count, 0, 1) ; aggregate: total |
| ML | triangle-node | 19 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.2158 | - | 0.1581 | -0.0593 | return clip( (sum( sum( A(u, v) for v in P ) for u in P )) / 2, 0, 1 ) ; aggregate: total |
| CS | degree-ge3 | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | d = size(P) ; indicator = clip(d - 2, 0, 1) ; return indicator ; aggregate: total |
| CS | degree-ge3 | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | x = size(P) ; return clip(x - 2, 0, 1) ; aggregate: total |
| CS | degree-ge3 | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | report = clip(size(P) - 2, 0, 1) ; return report ; aggregate: total |
| CS | degree-ge3 | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | return clip(max(0, size(P) - 2), 0, 1) ; aggregate: total |
| CS | degree-ge3 | 4 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | return clip(size(P) - 2, 0, 1) ; aggregate: total |
| CS | degree-ge3 | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | size_P = size(P) ; indicator = clip(size_P - 2, 0, 1) ; return indicator ; aggregate: total |
| CS | degree-ge3 | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | d = size(P) ; report = max(0, min(1, d - 2)) ; return report ; aggregate: total |
| CS | degree-ge3 | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | report = min(1, max(0, size(P) - 2)) ; return report ; aggregate: total |
| CS | degree-ge3 | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | s = size(P) ; s_minus_2 = s - 2 ; max_0 = max(0, s_minus_2) ; clipped = clip(max_0, 0, 1) ; return clipped ; aggregate: total |
| CS | degree-ge3 | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | d = size(P) ; indicator = clip(d - 2, 0, 1) ; return indicator ; aggregate: total |
| CS | degree-ge3 | 10 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1778 | 0.0015 | return clip(size(project(P, D)) - 2, 0, 1) ; aggregate: total |
| CS | degree-ge3 | 11 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1778 | 0.0015 | d = size(project(P, D)) ; return clip(d - 2, 0, 1) ; aggregate: total |
| CS | degree-ge3 | 12 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1778 | 0.0015 | projected_P = project(P, D) ; degree = size(projected_P) ; indicator = clip(degree - 2, 0, 1) ; return indicator ; aggregate: total |
| CS | degree-ge3 | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | size_P = size(P) ; return clip(size_P - 2, 0, 1) ; aggregate: total |
| CS | degree-ge3 | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | value = max(0, size(P) - 2) ; indicator = clip(value, 0, 1) ; return indicator ; aggregate: total |
| CS | degree-ge3 | 15 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1778 | 0.0015 | s = size(project(P, D)) ; indicator = max(0, min(1, s - 2)) ; return indicator ; aggregate: total |
| CS | degree-ge3 | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | d = size(P) ; return max(clip(d - 3, 0, 1), clip(d - 2, 0, 1)) ; aggregate: total |
| CS | degree-ge3 | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | size_P = size(P) ; report = clip(size_P - 2, 0, 1) ; return report ; aggregate: total |
| CS | degree-ge3 | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | size_P = size(P) ; return clip(size_P - 2, 0, 1) ; aggregate: total |
| CS | degree-ge3 | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | report = clip(max(size(P) - 2, 0), 0, 1) ; return report ; aggregate: total |
| CS | triangle-edge | 0 | True | 1 | 2 | False | False | 1.0205 | True | True | 0.0293 | - | 0.7411 | 0.1130 | return sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| CS | triangle-edge | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 9 | True | 1 | 3 | False | False | 1.0205 | True | True | 0.0293 | - | 0.7411 | 0.1130 | S = project(P, D) ; total_edges = sum(clip(size(N(v) & S), 0, 1) for v in S) ; return total_edges ; aggregate: total / 2 |
| CS | triangle-edge | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 11 | True | 1 | 2 | False | False | 1.0205 | True | True | 0.0293 | - | 0.7411 | 0.1130 | return sum(clip(size(N(v) & project(P, D)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| CS | triangle-edge | 12 | True | 1 | 1 | False | False | 1.0205 | True | True | 0.0293 | - | 0.7411 | 0.1130 | neighbors = project(P, D) ; return sum( clip( size( neighbors & N(v) ), 0, 1 ) for v in neighbors ) ; aggregate: total / 2 |
| CS | triangle-edge | 13 | True | 1 | 3 | False | False | 1.0205 | True | True | 0.0293 | - | 0.7411 | 0.1130 | projected_P = project(P, D) ; total = sum(clip(size(N(v) & projected_P), 0, 1) for v in projected_P) ; return total ; aggregate: total / 2 |
| CS | triangle-edge | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 15 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.2972 | - | 0.6280 | 0.0000 | return sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| CS | triangle-edge | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 17 | True | 1 | 2 | False | False | 1.0205 | True | True | 0.0293 | - | 0.7411 | 0.1130 | projected_P = project(P, D) ; return sum( clip( size( N(v) & projected_P ), 0, 1 ) for v in projected_P ) ; aggregate: total / 2 |
| CS | triangle-edge | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2972 | - | 0.6280 | 0.0000 | P_proj = project(P, D) ; sum_clip = sum(clip(sum(A(v, w) for w in P_proj), 0, 1) for v in P_proj) ; return sum_clip ; aggregate: total / 2 |
| CS | triangle-edge | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-node | 0 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1262 | - | 0.2658 | 0.0312 | s = sum( sum( A(u, v) for v in P ) for u in P ) ; return clip(s, 0, 1) ; aggregate: total |
| CS | triangle-node | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1712 | - | 0.2583 | 0.0237 | P_proj = project(P, D) ; sum_ordered = sum(sum(A(u, v) for v in P_proj) for u in P_proj) ; contribution = clip(sum_ordered / 2, 0, 1) ; return contribution ; aggregate: total |
| CS | triangle-node | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1712 | - | 0.2583 | 0.0237 | neighbors = project(P, D) ; sum_all_pairs = sum( sum( A(u, v) for v in neighbors ) for u in neighbors ) ; count_pairs = sum_all_pairs / 2 ; return clip(count_pairs, 0, 1) ; aggregate: total |
| CS | triangle-node | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1712 | - | 0.2583 | 0.0237 | projected_P = project(P, D) ; sum_ow = sum(sum(A(v, w) for w in projected_P) for v in projected_P) ; clipped_sum_ow = clip(sum_ow, 0, 2) ; edges_between_neighbors = clipped_sum_ow / 2 ; indicator = clip(edges_between_neighbors, 0, 1) ; return indicator ; aggregate: total |
| CS | triangle-node | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1302 | - | 0.2346 | 0.0000 | projected_P = project(P, D) ; sum_edges = sum( sum( A(b, c) for c in projected_P ) for b in projected_P ) ; node_count = clip(sum_edges, 0, 1) ; return node_count ; aggregate: total |
| CS | triangle-node | 5 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1673 | - | 0.2950 | 0.0604 | sum_edges = sum( sum( A(v, w) for w in P ) for v in P ) ; report = clip( sum_edges / 2, 0, 1 ) ; return report ; aggregate: total |
| CS | triangle-node | 6 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1014 | - | 0.2803 | 0.0456 | s = project(P, D) ; sum_val = sum( size(N(u) & s) for u in s ) ; return clip( sum_val, 0, 1 ) ; aggregate: total |
| CS | triangle-node | 7 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1673 | - | 0.2950 | 0.0604 | sum_A = sum( sum( A(j, k) for k in P ) for j in P ) ; count = clip( sum_A / 2, 0, 1 ) ; return count ; aggregate: total |
| CS | triangle-node | 8 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1262 | - | 0.2658 | 0.0312 | sum_A = sum( sum( A(u, v) for v in P ) for u in P ) ; indicator = clip( max(0, sum_A), 0, 1 ) ; return indicator ; aggregate: total |
| CS | triangle-node | 9 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1014 | - | 0.2806 | 0.0460 | s = sum(size(P & N(u)) for u in P) ; return clip(s - 1, 0, 1) ; aggregate: total |
| CS | triangle-node | 10 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1014 | - | 0.2803 | 0.0456 | projected_P = project(P, D) ; sum_over_u = sum(size(N(u) & projected_P) for u in projected_P) ; edges = sum_over_u / 2 ; return clip(edges, 0, 1) ; aggregate: total |
| CS | triangle-node | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1302 | - | 0.2346 | 0.0000 | s = project(P, D) ; sum_ordered = sum(sum(A(u, v) for v in s) for u in s) ; report = clip(sum_ordered, 0, 1) ; return report ; aggregate: total |
| CS | triangle-node | 12 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1014 | - | 0.2803 | 0.0456 | S = project(P, D) ; C = sum(size(S & N(u)) for u in S) ; return clip(C, 0, 1) ; aggregate: total |
| CS | triangle-node | 13 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1262 | - | 0.2658 | 0.0312 | sum_ = sum( sum( A(u, v) for v in P ) for u in P ) ; return clip( sum_, 0, 1 ) ; aggregate: total |
| CS | triangle-node | 14 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1673 | - | 0.2950 | 0.0604 | sum_uv = sum( sum( A(u, v) for v in P ) for u in P ) ; value = sum_uv / 2 ; return clip(value, 0, 1) ; aggregate: total |
| CS | triangle-node | 15 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1014 | - | 0.2803 | 0.0456 | S = project(P, D) ; count = sum( clip( size(N(u) & S), 0, 1 ) for u in S ) ; return clip(count, 0, 1) ; aggregate: total |
| CS | triangle-node | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1712 | - | 0.2583 | 0.0237 | P_projected = project(P, D) ; sum_all_pairs = sum(sum(A(u, v) for v in P_projected) for u in P_projected) ; sum_pairs = sum_all_pairs / 2 ; indicator = clip(sum_pairs, 0, 1) ; return indicator ; aggregate: total |
| CS | triangle-node | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1712 | - | 0.2583 | 0.0237 | S = project(P, D) ; sum_a = sum( sum( A(a, b) for b in S ) for a in S ) ; E = sum_a / 2 ; return clip(E, 0, 1) ; aggregate: total |
| CS | triangle-node | 18 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1014 | - | 0.2803 | 0.0456 | S = project(P, D) ; sum_ = sum( size(N(a) & S) for a in S ) ; edges = sum_ / 2 ; indicator = clip(edges, 0, 1) ; return indicator ; aggregate: total |
| CS | triangle-node | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1712 | - | 0.2583 | 0.0237 | P_projected = project(P, D) ; sum_A = sum( sum( A(u, v) for v in P_projected ) for u in P_projected ) ; sum_A_div_2 = sum_A / 2 ; return clip(sum_A_div_2, 0, 1) ; aggregate: total |
| EE | degree-ge3 | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | d = size(P) ; return max(0, min(1, d - 2)) ; aggregate: total |
| EE | degree-ge3 | 1 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0654 | 0.0069 | s = size(project(P, D)) ; return clip(s - 2, 0, 1) ; aggregate: total |
| EE | degree-ge3 | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | size_P = size(P) ; return clip(size_P - 2, 0, 1) ; aggregate: total |
| EE | degree-ge3 | 3 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | size_P = size(P) ; value = clip(size_P - 2, 0, 1) ; return value ; aggregate: total |
| EE | degree-ge3 | 4 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | return clip(size(P) - 2, 0, 1) ; aggregate: total |
| EE | degree-ge3 | 5 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | return clip(size(P) - 2, 0, 1) ; aggregate: total |
| EE | degree-ge3 | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | report = clip(size(P) - 2, 0, 1) ; return report ; aggregate: total |
| EE | degree-ge3 | 7 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0654 | 0.0069 | size_P = size(project(P, D)) ; report = clip(size_P - 2, 0, 1) ; return report ; aggregate: total |
| EE | degree-ge3 | 8 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0654 | 0.0069 | d = size(project(P, D)) ; report = clip(d - 2, 0, 1) ; return report ; aggregate: total |
| EE | degree-ge3 | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | size_p = size(P) ; indicator = clip(size_p - 2, 0, 1) ; return indicator ; aggregate: total |
| EE | degree-ge3 | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | indicator = max(0, size(P) - 2) ; return clip(indicator, 0, 1) ; aggregate: total |
| EE | degree-ge3 | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | size_P = size(P) ; indicator = clip(size_P - 2, 0, 1) ; return indicator ; aggregate: total |
| EE | degree-ge3 | 12 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0654 | 0.0069 | projected_P = project(P, D) ; size_P = size(projected_P) ; value = clip(size_P - 2, 0, 1) ; return value ; aggregate: total |
| EE | degree-ge3 | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | value = clip(size(P) - 2, 0, 1) ; return value ; aggregate: total |
| EE | degree-ge3 | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | x = size(P) ; value = max(0, min(1, x - 2)) ; return value ; aggregate: total |
| EE | degree-ge3 | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | indicator = clip(size(P) - 2, 0, 1) ; return indicator ; aggregate: total |
| EE | degree-ge3 | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | report = clip(size(P) - 2, 0, 1) ; return report ; aggregate: total |
| EE | degree-ge3 | 17 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0654 | 0.0069 | value = clip(size(project(P, D)) - 2, 0, 1) ; return value ; aggregate: total |
| EE | degree-ge3 | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | size_P = size(P) ; report = clip(size_P - 2, 0, 1) ; return report ; aggregate: total |
| EE | degree-ge3 | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | x = size(P) ; value = clip(max(0, x - 2), 0, 1) ; return value ; aggregate: total |
| EE | triangle-edge | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 6 | True | 1 | 2 | False | False | 0.9608 | True | True | 0.1634 | - | 0.2694 | -0.0503 | total = sum( clip( size( N(v) & P ), 0, 1 ) for v in project(P, D) ) ; return total ; aggregate: total / 2 |
| EE | triangle-edge | 7 | True | 1 | 2 | False | False | 1.0025 | True | True | 0.1782 | - | 0.2464 | -0.0733 | S = project(P, D) ; count = sum(clip(size(S & N(v)), 0, 1) for v in S) ; return count ; aggregate: total / 2 |
| EE | triangle-edge | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 10 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.3153 | - | 0.3197 | 0.0000 | total = sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; return total ; aggregate: total / 2 |
| EE | triangle-edge | 11 | True | 1 | 3 | False | False | 1.0025 | True | True | 0.1782 | - | 0.2464 | -0.0733 | s = sum(clip(size(N(v) & project(P, D)), 0, 1) for v in project(P, D)) ; return s ; aggregate: total / 2 |
| EE | triangle-edge | 12 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 13 | True | 1 | 3 | False | False | 0.9608 | True | True | 0.1634 | - | 0.2694 | -0.0503 | projected = project(P, D) ; count = sum(clip(size(P & N(v)), 0, 1) for v in projected) ; return count ; aggregate: total / 2 |
| EE | triangle-edge | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 15 | True | 1 | 3 | False | False | 1.0025 | True | True | 0.1782 | - | 0.2464 | -0.0733 | proj_p = project(P, D) ; total = sum(clip(size(proj_p & N(v)), 0, 1) for v in proj_p) ; return total ; aggregate: total / 2 |
| EE | triangle-edge | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3153 | - | 0.3197 | 0.0000 | P_proj = project(P, D) ; sum_val = sum(clip(sum(A(v, w) for w in P_proj), 0, 1) for v in P_proj) ; return sum_val ; aggregate: total / 2 |
| EE | triangle-edge | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-node | 0 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1776 | - | 0.1144 | -0.0303 | s = size(P) ; t = sum(sum(A(a, b) for b in P) for a in P) ; u = t / 2 ; v = clip(u, 0, 1) ; return v ; aggregate: total / 1 |
| EE | triangle-node | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2081 | - | 0.1562 | 0.0115 | projected_P = project(P, D) ; sum_all = sum(sum(A(u, v) for v in projected_P) for u in projected_P) ; sum_edges = sum_all / 2 ; result = clip(sum_edges, 0, 1) ; return result ; aggregate: total |
| EE | triangle-node | 2 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.2682 | - | 0.1322 | -0.0125 | S = project(P, D) ; total = sum(size(N(u) & P) for u in S) ; return clip(total, 0, 1) ; aggregate: total |
| EE | triangle-node | 3 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.2727 | - | 0.1325 | -0.0123 | neighbors = project(P, D) ; sum_edges = sum( size(N(j) & neighbors) for j in neighbors ) ; result = clip(sum_edges - 1, 0, 1) ; return result ; aggregate: total |
| EE | triangle-node | 4 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1232 | - | 0.1088 | -0.0360 | sum_A = sum(sum(A(u, v) for v in P) for u in P) ; indicator = clip(sum_A, 0, 1) ; return indicator ; aggregate: total |
| EE | triangle-node | 5 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.2727 | - | 0.1325 | -0.0123 | S = project(P, D) ; sum_intersections = sum( size(S & N(u)) for u in S ) ; return clip(sum_intersections, 0, 1) ; aggregate: total |
| EE | triangle-node | 6 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.2682 | - | 0.1322 | -0.0125 | S = P ; count = sum( size(N(w) & P) for w in S ) ; return clip(count, 0, 1) ; aggregate: total |
| EE | triangle-node | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2081 | - | 0.1562 | 0.0115 | projected = project(P, D) ; sum_all = sum( sum( A(u, v) for v in projected ) for u in projected ) ; sum_unordered = sum_all / 2 ; return clip(sum_unordered, 0, 1) ; aggregate: total |
| EE | triangle-node | 8 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.2727 | - | 0.1325 | -0.0123 | neighbors = project(P, D) ; count_pairs = sum( sum( size(N(y) & neighbors) for z in neighbors ) for y in neighbors ) / 2 ; return clip(count_pairs, 0, 1) ; aggregate: total |
| EE | triangle-node | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1510 | - | 0.1447 | 0.0000 | projected_P = project(P, D) ; s = sum( sum( A(v, w) for w in projected_P ) for v in projected_P ) ; return clip(s, 0, 1) ; aggregate: total |
| EE | triangle-node | 10 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.2682 | - | 0.1322 | -0.0125 | return clip( (sum( size(P & N(v)) for v in P ) / 2 ), 0, 1 ) ; aggregate: total |
| EE | triangle-node | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2081 | - | 0.1562 | 0.0115 | projected_P = project(P, D) ; sum_ordered = sum(sum(A(v, w) for w in projected_P) for v in projected_P) ; edges = sum_ordered / 2 ; indicator = clip(edges, 0, 1) ; return indicator ; aggregate: total |
| EE | triangle-node | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2081 | - | 0.1562 | 0.0115 | S = project(P, D) ; sum_A = sum( sum( A(u, v) for v in S ) for u in S ) ; sum_A_unordered = sum_A / 2 ; indicator = clip(sum_A_unordered, 0, 1) ; return indicator ; aggregate: total |
| EE | triangle-node | 13 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1232 | - | 0.1088 | -0.0360 | return clip(sum(sum(A(u, v) for v in P) for u in P), 0, 1) ; aggregate: total |
| EE | triangle-node | 14 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.2727 | - | 0.1325 | -0.0123 | S = project(P, D) ; T = sum(size(N(v) & S) for v in S) ; return clip(T, 0, 1) ; aggregate: total |
| EE | triangle-node | 15 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.2727 | - | 0.1325 | -0.0123 | sum_over_w = sum( size(N(w) & project(P, D)) for w in project(P, D) ) ; return clip(sum_over_w, 0, 1) ; aggregate: total |
| EE | triangle-node | 16 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.2727 | - | 0.1325 | -0.0123 | S = project(P, D) ; sum_over_u = sum(size(N(u) & S) for u in S) ; edges = sum_over_u / 2 ; return clip(edges, 0, 1) ; aggregate: total |
| EE | triangle-node | 17 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.2682 | - | 0.1322 | -0.0125 | sum_pairs = sum( size(P & N(u)) for u in P ) ; num_pairs = sum_pairs / 2 ; return clip(num_pairs, 0, 1) ; aggregate: total |
| EE | triangle-node | 18 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.2727 | - | 0.1325 | -0.0123 | s = project(P, D) ; total_edges = sum( size(N(k) & s) for k in s ) ; number_of_edges = total_edges / 2 ; return clip(number_of_edges, 0, 1) ; aggregate: total |
| EE | triangle-node | 19 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1776 | - | 0.1144 | -0.0303 | sum_ordered = sum( sum( A(u, v) for v in P ) for u in P ) ; sum_unordered = sum_ordered / 2 ; return clip( sum_unordered, 0, 1 ) ; aggregate: total |
