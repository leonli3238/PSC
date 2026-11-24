# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 20 independent design(s), 3 draft(s) x up to 1 restart(s) per release (rows, matrix), selection simulated (public Holme-Kim graphs, average degrees 4,8,16, 8 releases each, never chosen at a score >= 1; run-time choice on Chung-Lu graphs of the published noisy degrees), own-row check on, tighten 1, early stop off, normalisation on, prompt generic (core generic, 62a207c03a9c4864), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate off.

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio | mean_candidates | runs_matrix | runs_rows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree-ge3 | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.7000 | 1.3500 | 1.0000 | 2.9500 | 18 | 0.0000 | 0.7000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0750 | 1.0000 | 0.0000 | 0.0000 |
| PM | triangle-edge | 20 | 0.5500 | [0.34, 0.74] | 0.5500 | 0.0500 | 2.1818 | 1.0000 | 5.9000 | 10 | 0.0000 | 0.2727 | 1.0000 | 1.0000 | 1.0000 | 1.0727 | 1.2000 | 0.9990 | 0.6000 | 0.2909 | 0.7091 |
| PM | triangle-node | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.5000 | 1.6000 | 1.0000 | 3.5500 | 20 | 0.0000 | 0.3500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9800 | 1.0000 | 0.4500 | 0.5500 |
| CU | degree-ge3 | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.7500 | 1.3000 | 1.0000 | 3.2000 | 18 | 0.1000 | 0.8000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0500 | 1.0000 | 0.0000 | 0.0000 |
| CU | triangle-edge | 20 | 0.4000 | [0.22, 0.61] | 0.4000 | 0.1000 | 2.0000 | 1.0000 | 5.8000 | 7 | 0.0000 | 0.5000 | 1.0000 | 1.0000 | 1.0000 | 1.0250 | 1.2000 | 1.0319 | 0.4000 | 0.5000 | 0.5000 |
| CU | triangle-node | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.3000 | 1.9000 | 1.0000 | 3.8000 | 20 | 0.0000 | 0.2000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9800 | 1.0500 | 0.3000 | 0.7000 |
| Do | degree-ge3 | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.5500 | 1.5000 | 1.0000 | 3.0000 | 17 | 0.0000 | 0.8500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0375 | 1.0000 | 0.0000 | 0.0000 |
| Do | triangle-edge | 20 | 0.4000 | [0.22, 0.61] | 0.4000 | 0.0500 | 2.2500 | 1.0000 | 5.9500 | 7 | 0.0000 | 0.3750 | 1.0000 | 1.0000 | 1.0000 | 1.0250 | 1.2000 | 0.9859 | 0.4500 | 0.3038 | 0.6963 |
| Do | triangle-node | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.4500 | 1.7500 | 1.0000 | 3.5000 | 20 | 0.0000 | 0.2000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9700 | 1.0500 | 0.3500 | 0.6500 |
| ML | degree-ge3 | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.5000 | 1.6500 | 1.0000 | 3.1500 | 17 | 0.0500 | 0.7000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0750 | 1.0000 | 0.0000 | 0.0000 |
| ML | triangle-edge | 20 | 0.4500 | [0.26, 0.66] | 0.4500 | 0.0500 | 2.0000 | 1.0000 | 5.8000 | 8 | 0.0000 | 0.2222 | 1.0000 | 1.0000 | 1.0000 | 1.0444 | 1.2000 | 1.0058 | 0.4500 | 0.2222 | 0.7778 |
| ML | triangle-node | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.3000 | 1.8421 | 1.0000 | 3.7000 | 19 | 0.0000 | 0.2632 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9895 | 0.9500 | 0.3158 | 0.6842 |
| CS | degree-ge3 | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.8000 | 1.2500 | 1.0000 | 3.0000 | 18 | 0.1000 | 0.6500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0875 | 1.0000 | 0.0000 | 0.0000 |
| CS | triangle-edge | 20 | 0.5000 | [0.30, 0.70] | 0.5000 | 0.1000 | 2.0000 | 1.0000 | 5.7000 | 10 | 0.0000 | 0.1000 | 1.0000 | 1.0000 | 1.0000 | 1.0600 | 1.2000 | 0.9973 | 0.5000 | 0.1000 | 0.9000 |
| CS | triangle-node | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.6000 | 1.4211 | 1.0000 | 3.5500 | 19 | 0.0000 | 0.2105 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9368 | 1.0000 | 0.5263 | 0.4737 |
| EE | degree-ge3 | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.8500 | 1.2000 | 1.0000 | 3.0500 | 18 | 0.0500 | 0.9500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0125 | 1.0000 | 0.0000 | 0.0000 |
| EE | triangle-edge | 20 | 0.5000 | [0.30, 0.70] | 0.5000 | 0.0500 | 2.6000 | 1.0000 | 5.9500 | 10 | 0.0000 | 0.2000 | 1.0000 | 1.0000 | 1.0000 | 1.0200 | 1.2000 | 0.9978 | 0.5000 | 0.2000 | 0.8000 |
| EE | triangle-node | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.5000 | 1.5500 | 1.0000 | 3.8500 | 20 | 0.0000 | 0.5000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9800 | 1.0000 | 0.6000 | 0.4000 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | degree-ge3 | 0.0294 | 0.0281 | 0.0281 | 0.0013 | 0.0044 | 0.7000 | 0.0000 |
| PM | triangle-edge | 0.1923 | 0.1925 | 0.2086 | -0.0163 | 0.0000 | 0.2909 | 0.0000 |
| PM | triangle-node | 0.0705 | 0.0674 | 0.0724 | -0.0018 | 0.0073 | 0.1500 | 0.0000 |
| CU | degree-ge3 | 0.1075 | 0.1077 | 0.1077 | -0.0001489 | 0.0000 | 0.8000 | 0.0000 |
| CU | triangle-edge | 0.5220 | 0.5402 | 0.5598 | -0.0378 | 0.0000 | 0.5000 | 0.0750 |
| CU | triangle-node | 0.2138 | 0.1989 | 0.2418 | -0.0280 | 0.0628 | 0.0500 | 0.0000 |
| Do | degree-ge3 | 0.1137 | 0.1143 | 0.1143 | -0.0006176 | 0.0000 | 0.8500 | 0.0000 |
| Do | triangle-edge | 0.5521 | 0.5576 | 0.5188 | 0.0334 | 0.1002 | 0.3000 | 0.0513 |
| Do | triangle-node | 0.2411 | 0.2458 | 0.2276 | 0.0135 | 0.0186 | 0.1500 | 0.0000 |
| ML | degree-ge3 | 0.1167 | 0.1179 | 0.1179 | -0.0013 | 0.0000 | 0.7000 | 0.0000 |
| ML | triangle-edge | 0.3733 | 0.3581 | 0.3873 | -0.0140 | 0.0099 | 0.2222 | 0.0211 |
| ML | triangle-node | 0.2188 | 0.2230 | 0.2174 | 0.0014 | 0.0082 | 0.1274 | 0.0000 |
| CS | degree-ge3 | 0.1768 | 0.1763 | 0.1763 | 0.0005363 | 0.0015 | 0.6500 | 0.0000 |
| CS | triangle-edge | 0.7523 | 0.7411 | 0.6280 | 0.1243 | 0.1881 | 0.1000 | 0.0540 |
| CS | triangle-node | 0.2783 | 0.2803 | 0.2346 | 0.0436 | 0.0933 | 0.1053 | 0.0000 |
| EE | degree-ge3 | 0.0588 | 0.0585 | 0.0585 | 0.0003458 | 0.0069 | 0.9500 | 0.0000 |
| EE | triangle-edge | 0.2634 | 0.2464 | 0.3197 | -0.0563 | 0.0000 | 0.2000 | 0.0000 |
| EE | triangle-node | 0.1386 | 0.1386 | 0.1447 | -0.0062 | 0.0243 | 0.3500 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree-ge3 | 0 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0325 | 0.0044 | projected_P = project(P, D) ; size_P = size(projected_P) ; y = size_P - 2 ; return clip(y, 0, 1) ; aggregate: total |
| PM | degree-ge3 | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | d = size(P) ; report = clip(d - 2, 0, 1) ; return report ; aggregate: total |
| PM | degree-ge3 | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | s = size(P) ; value = clip(s - 2, 0, 1) ; return value ; aggregate: total |
| PM | degree-ge3 | 3 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0325 | 0.0044 | projected = project(P, D) ; degree = size(projected) ; return max(0, min(1, degree - 2)) ; aggregate: total |
| PM | degree-ge3 | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | size_P = size(P) ; indicator = clip(size_P - 2, 0, 1) ; return indicator ; aggregate: total |
| PM | degree-ge3 | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | size_p = size(P) ; value = clip(size_p - 2, 0, 1) ; return value ; aggregate: total |
| PM | degree-ge3 | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | size_P = size(P) ; value = clip(size_P - 2, 0, 1) ; return value ; aggregate: total |
| PM | degree-ge3 | 7 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0325 | 0.0044 | return clip(size(project(P, D)) - 2, 0, 1) ; aggregate: total |
| PM | degree-ge3 | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | value = size(P) ; result = clip(value - 2, 0, 1) ; return result ; aggregate: total |
| PM | degree-ge3 | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | size_p = size(P) ; return clip(size_p - 2, 0, 1) ; aggregate: total |
| PM | degree-ge3 | 10 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0325 | 0.0044 | d = size(project(P, D)) ; return max(0, min(1, d - 2)) ; aggregate: total |
| PM | degree-ge3 | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | indicator = clip(size(P) - 2, 0, 1) ; return indicator ; aggregate: total |
| PM | degree-ge3 | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | indicator = clip(size(P), 0, 3) - clip(size(P), 0, 2) ; return indicator ; aggregate: total |
| PM | degree-ge3 | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | s = size(P) ; report = clip(s - 2, 0, 1) ; return report ; aggregate: total |
| PM | degree-ge3 | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | d = size(P) ; report = clip(d - 2, 0, 1) ; return report ; aggregate: total |
| PM | degree-ge3 | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | degree = size(P) ; return clip(degree - 2, 0, 1) ; aggregate: total |
| PM | degree-ge3 | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | report = clip(size(P) - 2, 0, 1) ; return report ; aggregate: total |
| PM | degree-ge3 | 17 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0325 | 0.0044 | indicator = clip(size(project(P, D)) - 2, 0, 1) ; return indicator ; aggregate: total |
| PM | degree-ge3 | 18 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0325 | 0.0044 | projected_P = project(P, D) ; size_P = size(projected_P) ; return clip(size_P - 3 + 1, 0, 1) ; aggregate: total |
| PM | degree-ge3 | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0281 | 0.0000 | s = size(P) ; value = clip(s - 2, 0, 1) ; return value ; aggregate: total |
| PM | triangle-edge | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 1 | True | 1 | 2 | False | False | 0.9934 | True | True | 0.2953 | - | 0.1832 | -0.0253 | projected = project(P, D) ; return sum( clip( size( P & N(v) ), 0, 1 ) for v in projected ) ; aggregate: total / 2 |
| PM | triangle-edge | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.3215 | - | 0.2086 | 0.0000 | return sum(clip(sum(A(v, w) for w in project(P, D)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| PM | triangle-edge | 3 | True | 1 | 2 | False | False | 0.9947 | True | True | 0.2953 | - | 0.1925 | -0.0161 | return sum(clip(size(P & N(j)), 0, 1) for j in project(P, D)) ; aggregate: total / 2 |
| PM | triangle-edge | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 7 | True | 1 | 2 | False | False | 1.0030 | True | True | 0.3048 | - | 0.1822 | -0.0263 | return sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| PM | triangle-edge | 8 | True | 1 | 3 | False | False | 1.0030 | True | True | 0.3048 | - | 0.1822 | -0.0263 | return sum( clip( size( project(P, D) & N(v) ), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| PM | triangle-edge | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.3215 | - | 0.2086 | 0.0000 | s = sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; return s ; aggregate: total / 2 |
| PM | triangle-edge | 13 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle-edge | 15 | True | 1 | 2 | False | False | 1.0030 | True | True | 0.3048 | - | 0.1822 | -0.0263 | return sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| PM | triangle-edge | 16 | True | 1 | 2 | False | False | 0.9947 | True | True | 0.2953 | - | 0.1925 | -0.0161 | total = sum( clip( size( P & N(v) ), 0, 1 ) for v in project(P, D) ) ; return total ; aggregate: total / 2 |
| PM | triangle-edge | 17 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.3215 | - | 0.2086 | 0.0000 | total = sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; return total ; aggregate: total / 2 |
| PM | triangle-edge | 18 | True | 1 | 1 | False | False | 1.0030 | True | True | 0.3048 | - | 0.1822 | -0.0263 | count = sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; return count ; aggregate: total / 2 |
| PM | triangle-edge | 19 | True | 1 | 3 | False | False | 0.9947 | True | True | 0.2953 | - | 0.1925 | -0.0161 | return sum(clip(size(P & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| PM | triangle-node | 0 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1387 | - | 0.0630 | -0.0093 | s = sum( sum( A(u, v) for v in P ) for u in P ) ; return clip( max(0, s), 0, 1 ) ; aggregate: total |
| PM | triangle-node | 1 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.4286 | - | 0.0674 | -0.0050 | projected = project(P, D) ; sum_pairs = sum(size(projected & N(u)) for u in projected) ; clipped_sum = clip(sum_pairs, 0, 2) ; pairs = clipped_sum / 2 ; count = clip(pairs, 0, 1) ; return count ; aggregate: total |
| PM | triangle-node | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1679 | - | 0.0724 | 0.0000 | S = project(P, D) ; sum_T = sum(sum(A(u, v) for v in S) for u in S) ; return clip(sum_T, 0, 1) ; aggregate: total |
| PM | triangle-node | 3 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.4257 | - | 0.0673 | -0.0050 | sum_pairs = sum( size(P & N(v)) for v in P ) ; report = clip( sum_pairs - 1, 0, 1 ) ; return report ; aggregate: total |
| PM | triangle-node | 4 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.4286 | - | 0.0674 | -0.0050 | return clip(sum(size(N(u) & project(P, D)) for u in project(P, D)), 0, 1) ; aggregate: total |
| PM | triangle-node | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2309 | - | 0.0797 | 0.0073 | S = project(P, D) ; sum_all_ordered = sum( sum( A(u, v) for v in S ) for u in S ) ; sum_edges = sum_all_ordered / 2 ; indicator = clip(sum_edges, 0, 1) ; return indicator ; aggregate: total |
| PM | triangle-node | 6 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.4257 | - | 0.0673 | -0.0050 | S = P ; sum_pairs = sum(size(S & N(v)) for v in S) ; contribution = clip(sum_pairs, 0, 1) ; return contribution ; aggregate: total |
| PM | triangle-node | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2309 | - | 0.0797 | 0.0073 | S = project(P, D) ; total_pairs = sum( sum( A(j, k) for k in S ) for j in S ) ; sum_pairs = total_pairs / 2 ; result = clip(sum_pairs, 0, 1) ; return result ; aggregate: total |
| PM | triangle-node | 8 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.4286 | - | 0.0674 | -0.0050 | projected_neighbors = project(P, D) ; sum_pairs = sum(sum(size(N(v) & projected_neighbors) for v in projected_neighbors) for u in projected_neighbors) ; return clip(sum_pairs, 0, 1) ; aggregate: total |
| PM | triangle-node | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2309 | - | 0.0797 | 0.0073 | S = project(P, D) ; sum_over_pairs = sum( sum( A(v, w) for w in S ) for v in S ) ; value = sum_over_pairs / 2 ; count_u = clip(value, 0, 1) ; return count_u ; aggregate: total |
| PM | triangle-node | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1679 | - | 0.0724 | 0.0000 | projected_P = project(P, D) ; sum_pairs = sum( sum( A(j, k) for k in projected_P ) for j in projected_P ) ; contribution = clip(sum_pairs, 0, 1) ; return contribution ; aggregate: total |
| PM | triangle-node | 11 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.4257 | - | 0.0673 | -0.0050 | return clip( (sum( size(N(v) & P) for v in P )) / 2, 0, 1 ) ; aggregate: total |
| PM | triangle-node | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1679 | - | 0.0724 | 0.0000 | S = project(P, D) ; sum_pairs = sum(sum(A(u, v) for v in S) for u in S) ; return clip(sum_pairs, 0, 1) ; aggregate: total |
| PM | triangle-node | 13 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.4286 | - | 0.0674 | -0.0050 | return clip( sum( size( project(P, D) & N(j) ) for j in project(P, D) ), 0, 1 ) ; aggregate: total |
| PM | triangle-node | 14 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.4286 | - | 0.0674 | -0.0050 | P_bounded = project(P, D) ; sum_val = sum( size(N(j) & P_bounded) for j in P_bounded ) ; return clip( sum_val - 1, 0, 1 ) ; aggregate: total |
| PM | triangle-node | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2309 | - | 0.0797 | 0.0073 | S = project(P, D) ; sum_over_pairs = sum( sum( A(u, v) for v in S ) for u in S ) ; sum_over_pairs_div_2 = sum_over_pairs / 2 ; indicator = clip(sum_over_pairs_div_2, 0, 1) ; return indicator ; aggregate: total |
| PM | triangle-node | 16 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.4286 | - | 0.0674 | -0.0050 | S = project(P, D) ; sum_edges = sum( size(N(v) & S) for v in S ) ; total_edges = sum_edges / 2 ; return clip(total_edges, 0, 1) ; aggregate: total |
| PM | triangle-node | 17 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.4286 | - | 0.0674 | -0.0050 | proj_p = project(P, D) ; total_pairs = sum( size(proj_p & N(j)) for j in proj_p ) ; return clip(total_pairs, 0, 1) ; aggregate: total |
| PM | triangle-node | 18 | True | 1 | 2 | False | False | 0.8000 | True | True | 0.2117 | - | 0.0705 | -0.0019 | sum_over_ordered_pairs = sum( sum( A(v, w) for w in P ) for v in P ) ; sum_over_unordered_pairs = sum_over_ordered_pairs / 2 ; report = clip( sum_over_unordered_pairs, 0, 1 ) ; return report ; aggregate: total |
| PM | triangle-node | 19 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.4286 | - | 0.0674 | -0.0050 | proj = project(P, D) ; sum_total = sum( size(N(u) & proj) for u in proj ) ; return clip( sum_total, 0, 1 ) ; aggregate: total |
| CU | degree-ge3 | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | size_P = size(P) ; difference = size_P - 2 ; clipped = clip(max(difference, 0), 0, 1) ; return clipped ; aggregate: total |
| CU | degree-ge3 | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | return clip(max(0, size(P) - 2), 0, 1) ; aggregate: total |
| CU | degree-ge3 | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | size_P = size(P) ; return clip(max(0, size_P - 2), 0, 1) ; aggregate: total |
| CU | degree-ge3 | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | size_P = size(P) ; value = clip(max(size_P - 2, 0), 0, 1) ; return value ; aggregate: total |
| CU | degree-ge3 | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | size_P = size(P) ; return clip(size_P - 2, 0, 1) ; aggregate: total |
| CU | degree-ge3 | 5 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | return clip(size(P) - 2, 0, 1) ; aggregate: total |
| CU | degree-ge3 | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | count = min(1, max(0, size(P) - 2)) ; return count ; aggregate: total |
| CU | degree-ge3 | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | binary = clip(size(P) - 2, 0, 1) ; return binary ; aggregate: total |
| CU | degree-ge3 | 8 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | return clip(size(P) - 2, 0, 1) ; aggregate: total |
| CU | degree-ge3 | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | s = size(P) ; indicator = clip(s - 2, 0, 1) ; return indicator ; aggregate: total |
| CU | degree-ge3 | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | return clip(max(0, size(P) - 2), 0, 1) ; aggregate: total |
| CU | degree-ge3 | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | result = clip(size(P) - 2, 0, 1) ; return result ; aggregate: total |
| CU | degree-ge3 | 12 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1069 | -0.0007443 | s = size(project(P, D)) ; return clip(s - 2, 0, 1) ; aggregate: total |
| CU | degree-ge3 | 13 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1069 | -0.0007443 | d = size(project(P, D)) ; indicator = clip(d - 2, 0, 1) ; return indicator ; aggregate: total |
| CU | degree-ge3 | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | report = clip(size(P) - 2, 0, 1) ; return report ; aggregate: total |
| CU | degree-ge3 | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | size_P = size(P) ; val = min(1, size_P - 2) ; return max(0, val) ; aggregate: total |
| CU | degree-ge3 | 16 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1069 | -0.0007443 | size_P_proj = size(project(P, D)) ; count = clip(size_P_proj - 2, 0, 1) ; return count ; aggregate: total |
| CU | degree-ge3 | 17 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1069 | -0.0007443 | s = size(project(P, D)) ; return clip(comb(s, 3), 0, 1) ; aggregate: total |
| CU | degree-ge3 | 18 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | d = size(P) ; report = clip(max(0, d - 2), 0, 1) ; return report ; aggregate: total |
| CU | degree-ge3 | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1077 | 0.0000 | s = size(P) ; val = clip(max(s - 2, 0), 0, 1) ; return val ; aggregate: total |
| CU | triangle-edge | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 2 | True | 1 | 3 | False | False | 1.0060 | True | True | 0.0762 | - | 0.5207 | -0.0391 | projected = project(P, D) ; count = sum( clip(size(N(v) & P), 0, 1) for v in projected ) ; return count ; aggregate: total / 2 |
| CU | triangle-edge | 3 | True | 1 | 2 | False | False | 1.0830 | True | True | 0.0762 | - | 0.4720 | -0.0878 | total = sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; return total ; aggregate: total / 2 |
| CU | triangle-edge | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2953 | - | 0.5598 | 0.0000 | S = project(P, D) ; count = sum( clip( sum( A(v, w) for w in S ), 0, 1 ) for v in S ) ; return count ; aggregate: total / 2 |
| CU | triangle-edge | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2953 | - | 0.5598 | 0.0000 | projected = project(P, D) ; sum_over_v = sum(clip(sum(A(v, w) for w in projected), 0, 1) for v in projected) ; return sum_over_v ; aggregate: total / 2 |
| CU | triangle-edge | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2953 | - | 0.5598 | 0.0000 | P_proj = project(P, D) ; sum_total = sum( clip( sum( A(v, w) for w in P_proj ), 0, 1 ) for v in P_proj ) ; return sum_total ; aggregate: total / 2 |
| CU | triangle-edge | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2953 | - | 0.5598 | 0.0000 | P_d = project(P, D) ; total = sum(clip(sum(A(v, w) for w in P_d), 0, 1) for v in P_d) ; return total ; aggregate: total / 2 |
| CU | triangle-edge | 9 | True | 1 | 2 | False | False | 1.0830 | True | True | 0.0762 | - | 0.4720 | -0.0878 | return sum( clip( size( project(P, D) & N(v) ), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| CU | triangle-edge | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 12 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 13 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 17 | True | 1 | 3 | False | False | 1.0830 | True | True | 0.0762 | - | 0.4720 | -0.0878 | total = sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; return total ; aggregate: total / 2 |
| CU | triangle-edge | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-node | 0 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | P_projected = project(P, D) ; sum_edges = sum(size(N(u) & P_projected) for u in P_projected) ; num_edges = sum_edges / 2 ; return clip(num_edges, 0, 1) ; aggregate: total |
| CU | triangle-node | 1 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | S = project(P, D) ; sum_w = sum( size(N(w) & S) for w in S ) ; edges = sum_w / 2 ; return clip(edges, 0, 1) ; aggregate: total |
| CU | triangle-node | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2372 | - | 0.2695 | 0.0277 | S = project(P, D) ; sum_ordered = sum( sum(A(j, k) for k in S) for j in S ) ; sum_unordered = sum_ordered / 2 ; indicator = clip(sum_unordered, 0, 1) ; return indicator ; aggregate: total |
| CU | triangle-node | 3 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | projected_P = project(P, D) ; sum_size = sum( size(N(j) & projected_P) for j in projected_P ) ; count_u = sum_size / 2 ; return clip(count_u, 0, 1) ; aggregate: total |
| CU | triangle-node | 4 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | S = project(P, D) ; sum_pairs = sum( size(S & N(j)) for j in S ) ; return clip( sum_pairs / 2, 0, 1 ) ; aggregate: total |
| CU | triangle-node | 5 | True | 1 | 2 | False | False | 0.8000 | True | True | 0.2117 | - | 0.1942 | -0.0476 | sum_pairs = sum( sum( A(v, w) for w in P ) for v in P ) ; positive_sum = max(0, sum_pairs) ; indicator = clip(positive_sum, 0, 1) ; return indicator ; aggregate: total |
| CU | triangle-node | 6 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | projected_P = project(P, D) ; count = sum(size(projected_P & N(u)) for u in projected_P) ; report = clip(count, 0, 1) ; return report ; aggregate: total |
| CU | triangle-node | 7 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | s = sum( size( project(P, D) & N(v) ) for v in project(P, D) ) ; return clip( s / 2, 0, 1 ) ; aggregate: total |
| CU | triangle-node | 8 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.2633 | - | 0.2167 | -0.0250 | sum_uv = sum( sum( A(u, v) for u in P ) for v in P ) ; sum_A = sum_uv / 2 ; return clip( sum_A, 0, 1 ) ; aggregate: total |
| CU | triangle-node | 9 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | S = project(P, D) ; sum_over_u = sum( size(S & N(u)) for u in S ) ; is_triangle = clip(sum_over_u, 0, 1) ; return is_triangle ; aggregate: total |
| CU | triangle-node | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2680 | - | 0.3046 | 0.0628 | P_projected = project(P, D) ; s = sum( sum( A(u, v) for v in P_projected ) for u in P_projected ) ; return clip(s - 1, 0, 1) ; aggregate: total |
| CU | triangle-node | 11 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | projected_neighbors = project(P, D) ; count = sum(size(projected_neighbors & N(j)) for j in projected_neighbors) / 2 ; return clip(count, 0, 1) ; aggregate: total |
| CU | triangle-node | 12 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | neighbors = project(P, D) ; count = sum(size(N(u) & neighbors) for u in neighbors) ; return clip(count, 0, 1) ; aggregate: total |
| CU | triangle-node | 13 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | P_projected = project(P, D) ; count_pairs = sum( sum( size(N(u) & P_projected) for u in P_projected ) for v in P_projected ) ; return clip(count_pairs, 0, 1) ; aggregate: total / 1 |
| CU | triangle-node | 14 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | P_self = project(P, D) ; count = sum( clip( size(N(y) & P_self), 0, 1 ) for y in P_self ) ; return clip(count, 0, 1) ; aggregate: total |
| CU | triangle-node | 15 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1938 | -0.0480 | return clip( sum( size( project(P, D) & N(j) ) for j in project(P, D) ), 0, 1 ) ; aggregate: total |
| CU | triangle-node | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2372 | - | 0.2695 | 0.0277 | S = project(P, D) ; sum_pairs = sum( sum( A(v, w) for v in S ) for w in S ) ; edges_between_neighbors = sum_pairs / 2 ; indicator = clip(edges_between_neighbors, 0, 1) ; return indicator ; aggregate: total |
| CU | triangle-node | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2063 | - | 0.2418 | 0.0000 | projected = project(P, D) ; sum_pairs = sum( sum( A(u, v) for v in projected ) for u in projected ) ; result = clip( sum_pairs, 0, 1 ) ; return result ; aggregate: total |
| CU | triangle-node | 18 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1987 | -0.0430 | sum_pairs = sum(size(N(v) & P) for v in P) ; count = clip(sum_pairs / 2, 0, 1) ; return count ; aggregate: total |
| CU | triangle-node | 19 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1522 | - | 0.1989 | -0.0428 | S = project(P, D) ; sum_pairs = sum( size(S & N(u)) for u in S ) ; return clip(sum_pairs, 0, 1) ; aggregate: total |
| Do | degree-ge3 | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | s = size(P) ; report = clip(s - 2, 0, 1) ; return report ; aggregate: total |
| Do | degree-ge3 | 1 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1102 | -0.0041 | projected_P = project(P, D) ; report = clip(size(projected_P) - 2, 0, 1) ; return report ; aggregate: total |
| Do | degree-ge3 | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | size_P = size(P) ; indicator = clip(size_P - 2, 0, 1) ; return indicator ; aggregate: total |
| Do | degree-ge3 | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | return clip( (size(P) - 3) + 1, 0, 1 ) ; aggregate: total |
| Do | degree-ge3 | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | report = clip(size(P) - 2, 0, 1) ; return report ; aggregate: total |
| Do | degree-ge3 | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | d = size(P) ; report = min(1, max(0, d - 2)) ; return report ; aggregate: total |
| Do | degree-ge3 | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | report = clip(size(P) - 2, 0, 1) ; return report ; aggregate: total |
| Do | degree-ge3 | 7 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | s = size(P) ; return clip(s - 2, 0, 1) ; aggregate: total |
| Do | degree-ge3 | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | d = size(P) ; return 1 - clip(3 - d, 0, 1) ; aggregate: total |
| Do | degree-ge3 | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | report = max(0, min(1, size(P) - 2)) ; return report ; aggregate: total |
| Do | degree-ge3 | 10 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1102 | -0.0041 | projected_P = project(P, D) ; degree = size(projected_P) ; value = degree - 2 ; report = clip(value, 0, 1) ; return report ; aggregate: total |
| Do | degree-ge3 | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | size_P = size(P) ; value = clip(size_P - 2, 0, 1) ; return value ; aggregate: total |
| Do | degree-ge3 | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | size_P = size(P) ; return clip(size_P - 2, 0, 1) ; aggregate: total |
| Do | degree-ge3 | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | value = clip(size(P) - 2, 0, 1) ; return value ; aggregate: total |
| Do | degree-ge3 | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | report = max(0, min(1, size(P) - 2)) ; return report ; aggregate: total |
| Do | degree-ge3 | 15 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1102 | -0.0041 | return min(1, max(0, size(project(P, D)) - 2)) ; aggregate: total |
| Do | degree-ge3 | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | size_P = size(P) ; return clip(size_P - 2, 0, 1) ; aggregate: total |
| Do | degree-ge3 | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | s = size(P) ; indicator = clip(s - 2, 0, 1) ; return indicator ; aggregate: total |
| Do | degree-ge3 | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | s = size(P) ; t = clip(s - 2, 0, 1) ; return t ; aggregate: total |
| Do | degree-ge3 | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1143 | 0.0000 | degree = size(P) ; report = clip(degree - 2, 0, 1) ; return report ; aggregate: total |
| Do | triangle-edge | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.3064 | - | 0.5188 | 0.0000 | S = project(P, D) ; count = sum( clip( sum( A(v, w) for w in S ), 0, 1 ) for v in S ) ; return count ; aggregate: total / 2 |
| Do | triangle-edge | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 4 | True | 1 | 2 | False | False | 0.9303 | True | True | 0.0289 | - | 0.6189 | 0.1002 | projected = project(P, D) ; sum_clip = sum(clip(size(P & N(v)), 0, 1) for v in projected) ; return sum_clip ; aggregate: total / 2 |
| Do | triangle-edge | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3064 | - | 0.5188 | 0.0000 | S = project(P, D) ; sum_total = sum(clip(sum(A(v, w) for w in S), 0, 1) for v in S) ; return sum_total ; aggregate: total / 2 |
| Do | triangle-edge | 7 | True | 1 | 3 | False | True | 0.9606 | True | True | 0.3064 | - | 0.5303 | 0.0115 | total = sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; return total ; aggregate: total / 2 |
| Do | triangle-edge | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 12 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 13 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 14 | True | 1 | 2 | False | False | 0.9990 | True | True | 0.0289 | - | 0.5576 | 0.0388 | total = sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; return total ; aggregate: total / 2 |
| Do | triangle-edge | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-edge | 16 | True | 1 | 3 | False | False | 0.9990 | True | True | 0.0289 | - | 0.5576 | 0.0388 | total = sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; return total ; aggregate: total / 2 |
| Do | triangle-edge | 17 | True | 1 | 3 | False | False | 0.9990 | True | True | 0.0289 | - | 0.5576 | 0.0388 | return sum( clip(size( project(P, D) & N(v) ), 0, 1) for v in project(P, D) ) ; aggregate: total / 2 |
| Do | triangle-edge | 18 | True | 1 | 2 | False | False | 0.9990 | True | True | 0.0289 | - | 0.5576 | 0.0388 | neighbors = project(P, D) ; return sum( clip(size(N(v) & neighbors), 0, 1) for v in neighbors ) ; aggregate: total / 2 |
| Do | triangle-edge | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| Do | triangle-node | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1792 | - | 0.2276 | 0.0000 | P_proj = project(P, D) ; sum_pairs = sum( sum(A(v, w) for w in P_proj) for v in P_proj ) ; max_sum = max(0, sum_pairs) ; result_u = clip(max_sum, 0, 1) ; return result_u ; aggregate: total |
| Do | triangle-node | 1 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | return clip( sum( size( N(j) & project(P, D) ) for j in project(P, D) ), 0, 1 ) ; aggregate: total |
| Do | triangle-node | 2 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | S = project(P, D) ; sum_edges = sum(size(N(u) & S) for u in S) ; edges_between_neighbors = sum_edges / 2 ; indicator = clip(edges_between_neighbors, 0, 1) ; return indicator ; aggregate: total |
| Do | triangle-node | 3 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | P_prime = project(P, D) ; total_pairs = sum( size(P_prime & N(z)) for z in P_prime ) ; return clip(total_pairs, 0, 1) ; aggregate: total |
| Do | triangle-node | 4 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | return clip( sum( clip( size( N(u) & project(P, D) ), 0, 1 ) for u in project(P, D) ), 0, 1 ) ; aggregate: total |
| Do | triangle-node | 5 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.2927 | - | 0.2454 | 0.0178 | s = sum( sum( A(u, v) for v in P ) for u in P ) ; return clip( (s - 1) / 1, 0, 1 ) ; aggregate: total |
| Do | triangle-node | 6 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | sum_ = sum( size( project(P, D) & N(j) ) for j in project(P, D) ) ; x = sum_ / 2 ; return clip(x, 0, 1) ; aggregate: total |
| Do | triangle-node | 7 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2463 | 0.0186 | count = sum( size(N(j) & P) for j in P ) / 2 ; return clip(count, 0, 1) ; aggregate: total |
| Do | triangle-node | 8 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | P_proj = project(P, D) ; count = sum( size( N(u) & P_proj ) for u in P_proj ) ; result = clip( count, 0, 1 ) ; return result ; aggregate: total |
| Do | triangle-node | 9 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | total_pairs = sum( size( project(P, D) & N(u) ) for u in project(P, D) ) ; return clip(total_pairs, 0, 1) ; aggregate: total |
| Do | triangle-node | 10 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | sum_val = sum( size(N(u) & project(P, D)) for u in project(P, D) ) ; indicator = clip( sum_val, 0, 1 ) ; return indicator ; aggregate: total |
| Do | triangle-node | 11 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.2167 | - | 0.2275 | -0.0001265 | return clip( (sum( sum( A(u, v) for v in P ) for u in P )) / 2, 0, 1 ) ; aggregate: total |
| Do | triangle-node | 12 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.2167 | - | 0.2275 | -0.0001265 | sum_ordered = sum( sum( A(u, v) for v in P ) for u in P ) ; sum_unordered = sum_ordered * 0.5 ; return clip(sum_unordered, 0, 1) ; aggregate: total |
| Do | triangle-node | 13 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | s = sum(size(project(P, D) & N(j)) for j in project(P, D)) ; return clip(s / 2, 0, 1) ; aggregate: total |
| Do | triangle-node | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2352 | - | 0.2428 | 0.0152 | P_proj = project(P, D) ; sum_A = sum(sum(A(j, k) for k in P_proj) for j in P_proj) ; S = sum_A / 2 ; return clip(S, 0, 1) ; aggregate: total |
| Do | triangle-node | 15 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2463 | 0.0186 | total = sum( clip( size( N(y) & P ), 0, 1 ) for y in project(P, D) ) ; return clip( total, 0, 1 ) ; aggregate: total |
| Do | triangle-node | 16 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | return clip( sum( size( N(v) & project(P, D) ) for v in project(P, D) ), 0, 1 ) ; aggregate: total |
| Do | triangle-node | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1792 | - | 0.2276 | 0.0000 | sum_pairs = sum( sum( A(u, w) for w in project(P, D) ) for u in project(P, D) ) ; return clip(sum_pairs, 0, 1) ; aggregate: total |
| Do | triangle-node | 18 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.0962 | - | 0.2458 | 0.0182 | S = project(P, D) ; common = sum(size(N(v) & S) for v in S) ; count = clip(common / 2, 0, 1) ; return count ; aggregate: total |
| Do | triangle-node | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1792 | - | 0.2276 | 0.0000 | sum_pairs = sum( sum( A(u, v) for v in project(P, D) ) for u in project(P, D) ) ; report = clip( sum_pairs, 0, 1 ) ; return report ; aggregate: total |
| ML | degree-ge3 | 0 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1137 | -0.0043 | degree = size(project(P, D)) ; clip_val = clip(degree - 2, 0, 1) ; return clip_val ; aggregate: total |
| ML | degree-ge3 | 1 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1137 | -0.0043 | s = size(project(P, D)) ; report = min(1, comb(s, 3)) ; return report ; aggregate: total |
| ML | degree-ge3 | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | indicator = clip(size(P) - 2, 0, 1) ; return indicator ; aggregate: total |
| ML | degree-ge3 | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | value = clip(size(P) - 2, 0, 1) ; return value ; aggregate: total |
| ML | degree-ge3 | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | size_P = size(P) ; report = max(0, min(1, size_P - 2)) ; return report ; aggregate: total |
| ML | degree-ge3 | 5 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | size_P = size(P) ; return clip(size_P - 2, 0, 1) ; aggregate: total |
| ML | degree-ge3 | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | indicator = clip( size(P) - 2, 0, 1 ) ; return indicator ; aggregate: total |
| ML | degree-ge3 | 7 | True | 1 | 3 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1137 | -0.0043 | s = size(project(P, D)) ; return clip(s - 2, 0, 1) ; aggregate: total |
| ML | degree-ge3 | 8 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1137 | -0.0043 | size_projected = size(project(P, D)) ; contribution = min(1, max(0, size_projected - 2)) ; return contribution ; aggregate: total |
| ML | degree-ge3 | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | indicator = max(0, min(1, size(P) - 2)) ; return indicator ; aggregate: total |
| ML | degree-ge3 | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | indicator = 1 - clip(3 - size(P), 0, 1) ; return indicator ; aggregate: total |
| ML | degree-ge3 | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | indicator = clip(size(P) - 2, 0, 1) ; return indicator ; aggregate: total |
| ML | degree-ge3 | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | report = clip(size(P) - 2, 0, 1) ; return report ; aggregate: total |
| ML | degree-ge3 | 13 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | return clip(size(P) - 2, 0, 1) ; aggregate: total |
| ML | degree-ge3 | 14 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1137 | -0.0043 | projected_p = project(P, D) ; size_p = size(projected_p) ; value = clip(size_p - 2, 0, 1) ; return value ; aggregate: total |
| ML | degree-ge3 | 15 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | x = size(P) ; return clip(x - 2, 0, 1) ; aggregate: total |
| ML | degree-ge3 | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | report = clip(size(P) - 2, 0, 1) ; return report ; aggregate: total |
| ML | degree-ge3 | 17 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1137 | -0.0043 | size_p = size(project(P, D)) ; return min(1, comb(size_p, 3)) ; aggregate: total |
| ML | degree-ge3 | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | s = size(P) ; return clip(s - 2, 0, 1) ; aggregate: total |
| ML | degree-ge3 | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1179 | 0.0000 | size_P = size(P) ; return clip(size_P - 2, 0, 1) ; aggregate: total |
| ML | triangle-edge | 0 | True | 1 | 2 | False | False | 1.0211 | True | True | 0.0380 | - | 0.3581 | -0.0292 | total = sum( clip( size( project(P, D) & N(v) ), 0, 1 ) for v in project(P, D) ) ; return total ; aggregate: total / 2 |
| ML | triangle-edge | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 5 | True | 1 | 2 | False | False | 1.0211 | True | True | 0.0380 | - | 0.3581 | -0.0292 | neighbors = project(P, D) ; count = sum(clip(size(N(v) & neighbors), 0, 1) for v in neighbors) ; return count ; aggregate: total / 2 |
| ML | triangle-edge | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 10 | True | 1 | 3 | False | False | 1.0211 | True | True | 0.0380 | - | 0.3581 | -0.0292 | return sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| ML | triangle-edge | 11 | True | 1 | 2 | False | False | 0.9731 | True | True | 0.0360 | - | 0.3971 | 0.0099 | sum_clip = sum(clip(size(P & N(v)), 0, 1) for v in project(P, D)) ; return sum_clip ; aggregate: total / 2 |
| ML | triangle-edge | 12 | True | 1 | 2 | False | False | 1.0211 | True | True | 0.0380 | - | 0.3581 | -0.0292 | return sum( clip( size( N(v) & project(P, D) ), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| ML | triangle-edge | 13 | True | 1 | 2 | False | False | 1.0211 | True | True | 0.0380 | - | 0.3581 | -0.0292 | return sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| ML | triangle-edge | 14 | True | 1 | 2 | False | False | 0.9731 | True | True | 0.0360 | - | 0.3971 | 0.0099 | projected_neighbors = project(P, D) ; count = sum(clip(size(N(v) & P), 0, 1) for v in projected_neighbors) ; return count / 2 ; aggregate: total |
| ML | triangle-edge | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3268 | - | 0.3873 | 0.0000 | P_proj = project(P, D) ; return sum( clip( sum( A(v, w) for w in P_proj ), 0, 1 ) for v in P_proj ) ; aggregate: total / 2 |
| ML | triangle-edge | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.3268 | - | 0.3873 | 0.0000 | total = sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; return total ; aggregate: total / 2 |
| ML | triangle-node | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2008 | - | 0.2174 | 0.0000 | S = project(P, D) ; sum_A = sum(sum(A(u, v) for v in S) for u in S) ; return clip(max(0, sum_A), 0, 1) ; aggregate: total |
| ML | triangle-node | 1 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | P_proj = project(P, D) ; sum_over_v = sum(size(N(v) & P_proj) for v in P_proj) ; return clip(sum_over_v, 0, 1) ; aggregate: total |
| ML | triangle-node | 2 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1738 | - | 0.1560 | -0.0614 | s = sum( sum( A(j, k) for k in P ) for j in P ) ; return clip(s, 0, 1) ; aggregate: total |
| ML | triangle-node | 3 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | projected = project(P, D) ; count = sum(size(projected & N(y)) for y in projected) ; result = clip(count, 0, 1) ; return result ; aggregate: total |
| ML | triangle-node | 4 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | total_pairs = sum( size(N(v) & P) for v in P ) ; number_of_pairs = total_pairs / 2 ; return clip(number_of_pairs, 0, 1) ; aggregate: total |
| ML | triangle-node | 5 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | sum_size = sum(size(N(j) & P) for j in P) ; return clip(sum_size, 0, 1) ; aggregate: total |
| ML | triangle-node | 6 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | sum_pairs = sum( size(N(u) & P) for u in P ) ; value = clip( sum_pairs - 1, 0, 1 ) ; return value ; aggregate: total |
| ML | triangle-node | 7 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | projected_P = project(P, D) ; sum_pairs = sum( size(projected_P & N(v)) for v in projected_P ) ; indicator = clip(sum_pairs, 0, 1) ; return indicator ; aggregate: total |
| ML | triangle-node | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2320 | - | 0.2213 | 0.0039 | S = project(P, D) ; sum_edges_all = sum(A(j, k) for j in S for k in S) ; sum_edges = sum_edges_all / 2 ; count = clip(sum_edges, 0, 1) ; return count ; aggregate: total |
| ML | triangle-node | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2008 | - | 0.2174 | 0.0000 | P_proj = project(P, D) ; sum_pairs = sum( sum( A(u, v) for v in P_proj ) for u in P_proj ) ; return clip(sum_pairs, 0, 1) ; aggregate: total |
| ML | triangle-node | 10 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | projected = project(P, D) ; sum_edges = sum( size(N(u) & projected) for u in projected ) ; count = clip( sum_edges / 2, 0, 1 ) ; return count ; aggregate: total |
| ML | triangle-node | 11 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | S = project(P, D) ; sum_val = sum( size(N(v) & S) for v in S ) ; return clip( sum_val, 0, 1 ) ; aggregate: total |
| ML | triangle-node | 12 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | proj_neighbors = project(P, D) ; sum_pairs = sum(size(N(u) & proj_neighbors) for u in proj_neighbors) ; count = clip(sum_pairs, 0, 1) ; return count ; aggregate: total |
| ML | triangle-node | 13 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | proj_p = project(P, D) ; sum_edges = sum( size(N(v) & proj_p) for v in proj_p ) ; edges_between_neighbors = sum_edges / 2 ; result = clip(edges_between_neighbors, 0, 1) ; return result ; aggregate: total |
| ML | triangle-node | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2320 | - | 0.2213 | 0.0039 | Pu = project(P, D) ; sum_ordered = sum( sum( A(v, w) for w in Pu ) for v in Pu ) ; sum_unordered = sum_ordered / 2 ; clip_unordered = clip( sum_unordered, 0, 1 ) ; return clip_unordered ; aggregate: total |
| ML | triangle-node | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-node | 16 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | P_proj = project(P, D) ; sum_pairs = sum(size(N(v) & P_proj) for v in P_proj) ; contribution = clip(sum_pairs, 0, 1) ; return contribution ; aggregate: total |
| ML | triangle-node | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2631 | - | 0.2257 | 0.0082 | projected_P = project(P, D) ; sum_sum = sum(sum(A(v, w) for w in projected_P) for v in projected_P) ; return clip(sum_sum - 1, 0, 1) ; aggregate: total |
| ML | triangle-node | 18 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | S = project(P, D) ; total = sum( size(N(j) & S) for j in S ) ; return clip(total, 0, 1) ; aggregate: total |
| ML | triangle-node | 19 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.1471 | - | 0.2230 | 0.0055 | sum_pairs = sum( size( project(P, D) & N(v) ) for v in project(P, D) ) ; return clip( sum_pairs, 0, 1 ) ; aggregate: total |
| CS | degree-ge3 | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | return clip(size(P) - 2, 0, 1) ; aggregate: total |
| CS | degree-ge3 | 1 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1778 | 0.0015 | d = size(project(P, D)) ; return clip(d - 2, 0, 1) ; aggregate: total |
| CS | degree-ge3 | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | size_P = size(P) ; value = max(0, size_P - 2) ; report = clip(value, 0, 1) ; return report ; aggregate: total |
| CS | degree-ge3 | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | size_p = size(P) ; report = clip(size_p - 2, 0, 1) ; return report ; aggregate: total |
| CS | degree-ge3 | 4 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | return clip(size(P) - 2, 0, 1) ; aggregate: total |
| CS | degree-ge3 | 5 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1778 | 0.0015 | return clip(comb(size(project(P, D)), 3), 0, 1) ; aggregate: total |
| CS | degree-ge3 | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | value = clip(size(P) - 2, 0, 1) ; return value ; aggregate: total |
| CS | degree-ge3 | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | d = size(P) ; value = max(d - 2, 0) ; return clip(value, 0, 1) ; aggregate: total |
| CS | degree-ge3 | 8 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | report = clip(size(P) - 2, 0, 1) ; return report ; aggregate: total |
| CS | degree-ge3 | 9 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1778 | 0.0015 | s = size(project(P, D)) ; return clip(s - 2, 0, 1) ; aggregate: total |
| CS | degree-ge3 | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | size_P = size(P) ; return clip(size_P - 2, 0, 1) ; aggregate: total |
| CS | degree-ge3 | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | size_P = size(P) ; value = clip(size_P - 2, 0, 1) ; return value ; aggregate: total |
| CS | degree-ge3 | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | value = clip(size(P) - 2, 0, 1) ; return value ; aggregate: total |
| CS | degree-ge3 | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | x = size(P) ; return clip(x - 2, 0, 1) ; aggregate: total |
| CS | degree-ge3 | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | s = size(P) ; value = clip(max(0, s - 2), 0, 1) ; return value ; aggregate: total |
| CS | degree-ge3 | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.1763 | 0.0000 | degree = size(P) ; report = 1 - clip(3 - degree, 0, 1) ; return report ; aggregate: total |
| CS | degree-ge3 | 16 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1778 | 0.0015 | s = size(project(P, D)) ; return clip(comb(s, 3), 0, 1) ; aggregate: total |
| CS | degree-ge3 | 17 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1778 | 0.0015 | s = size(project(P, D)) ; x = s - 2 ; return clip(x, 0, 1) ; aggregate: total |
| CS | degree-ge3 | 18 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1778 | 0.0015 | return clip(size(project(P, D)) - 2, 0, 1) ; aggregate: total |
| CS | degree-ge3 | 19 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.1778 | 0.0015 | projected = project(P, D) ; d = size(projected) ; return clip(d - 2, 0, 1) ; aggregate: total |
| CS | triangle-edge | 0 | True | 1 | 1 | False | False | 1.0205 | True | True | 0.0293 | - | 0.7411 | 0.1130 | return sum( clip( size(project(P, D) & N(v)), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| CS | triangle-edge | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 2 | True | 1 | 2 | False | False | 0.9499 | True | True | 0.0273 | - | 0.8161 | 0.1881 | neighbors = project(P, D) ; sum_ = sum( clip( size( P & N(v) ), 0, 1 ) for v in neighbors ) ; return sum_ ; aggregate: total / 2 |
| CS | triangle-edge | 3 | True | 1 | 2 | False | False | 1.0205 | True | True | 0.0293 | - | 0.7411 | 0.1130 | result = sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; return result ; aggregate: total / 2 |
| CS | triangle-edge | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 5 | True | 1 | 3 | False | False | 1.0205 | True | True | 0.0293 | - | 0.7411 | 0.1130 | return sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| CS | triangle-edge | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2972 | - | 0.6280 | 0.0000 | S = project(P, D) ; return sum( clip( sum( A(v, w) for w in S ), 0, 1 ) for v in S ) ; aggregate: total / 2 |
| CS | triangle-edge | 10 | True | 1 | 3 | False | False | 0.9499 | True | True | 0.0273 | - | 0.8161 | 0.1881 | proj_P = project(P, D) ; sum_expr = sum(clip(size(N(v) & P), 0, 1) for v in proj_P) ; return sum_expr ; aggregate: total / 2 |
| CS | triangle-edge | 11 | True | 1 | 2 | False | False | 1.0205 | True | True | 0.0293 | - | 0.7411 | 0.1130 | projected_P = project(P, D) ; return sum(clip(size(projected_P & N(v)), 0, 1) for v in projected_P) ; aggregate: total / 2 |
| CS | triangle-edge | 12 | True | 1 | 2 | False | False | 1.0205 | True | True | 0.0293 | - | 0.7411 | 0.1130 | return sum( clip( size( project(P, D) & N(y) ), 0, 1 ) for y in project(P, D) ) ; aggregate: total / 2 |
| CS | triangle-edge | 13 | True | 1 | 2 | False | False | 0.9499 | True | True | 0.0273 | - | 0.8161 | 0.1881 | projected = project(P, D) ; total = sum( clip( size( P & N(v) ), 0, 1 ) for v in projected ) ; return total ; aggregate: total / 2 |
| CS | triangle-edge | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 17 | True | 1 | 2 | False | False | 1.0205 | True | True | 0.0293 | - | 0.7411 | 0.1130 | projected_P = project(P, D) ; return sum(clip(size(N(v) & projected_P), 0, 1) for v in projected_P) ; aggregate: total / 2 |
| CS | triangle-edge | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-edge | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-node | 0 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1014 | - | 0.2803 | 0.0456 | S = project(P, D) ; sum_edges = sum( size(N(u) & S) for u in S ) ; E = sum_edges / 2 ; return clip(E, 0, 1) ; aggregate: total |
| CS | triangle-node | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1302 | - | 0.2346 | 0.0000 | neighbors = project(P, D) ; sum_ordered_pairs = sum( sum( A(v, w) for w in neighbors ) for v in neighbors ) ; result = clip(sum_ordered_pairs, 0, 1) ; return result ; aggregate: total |
| CS | triangle-node | 2 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1014 | - | 0.2806 | 0.0460 | a = sum( size( P & N(v) ) for v in P ) ; return clip(a, 0, 1) ; aggregate: total |
| CS | triangle-node | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1302 | - | 0.2346 | 0.0000 | proj = project(P, D) ; sum_pairs = sum(sum(A(u, v) for v in proj) for u in proj) ; indicator = clip(sum_pairs, 0, 1) ; return indicator ; aggregate: total |
| CS | triangle-node | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1712 | - | 0.2583 | 0.0237 | S = project(P, D) ; ordered_sum = sum( sum( A(j, k) for k in S ) for j in S ) ; unordered_sum = ordered_sum / 2 ; result = clip( unordered_sum, 0, 1 ) ; return result ; aggregate: total |
| CS | triangle-node | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CS | triangle-node | 6 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1262 | - | 0.2658 | 0.0312 | sum_ordered = sum( sum( A(v, w) for w in P ) for v in P ) ; clipped = clip(sum_ordered, 0, 1) ; return clipped ; aggregate: total |
| CS | triangle-node | 7 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1014 | - | 0.2806 | 0.0460 | sum_ = sum( size(P & N(j)) for j in P ) ; return clip(sum_, 0, 1) ; aggregate: total |
| CS | triangle-node | 8 | True | 1 | 3 | False | False | 1.0000 | True | True | 0.1014 | - | 0.2803 | 0.0456 | S = project(P, D) ; return clip( (sum( size( N(u) & S ) for u in S )) / 2, 0, 1 ) ; aggregate: total |
| CS | triangle-node | 9 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.2211 | - | 0.3280 | 0.0933 | sum_pairs = sum( sum( A(j, k) for k in P ) for j in P ) ; contribution = clip( sum_pairs - 1, 0, 1 ) ; return contribution ; aggregate: total |
| CS | triangle-node | 10 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1014 | - | 0.2803 | 0.0456 | S = project(P, D) ; sum_over_v = sum( size(S & N(v)) for v in S ) ; return clip( sum_over_v - 1, 0, 1 ) ; aggregate: total |
| CS | triangle-node | 11 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1673 | - | 0.2950 | 0.0604 | sum_ordered = sum(sum(A(u, v) for v in P) for u in P) ; sum_unordered = sum_ordered / 2 ; return clip(sum_unordered, 0, 1) ; aggregate: total |
| CS | triangle-node | 12 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.2211 | - | 0.3280 | 0.0933 | S = sum( sum( A(u, v) for v in P ) for u in P ) ; contribution = clip(S - 1, 0, 1) ; return contribution ; aggregate: total |
| CS | triangle-node | 13 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.1014 | - | 0.2806 | 0.0460 | sum_val = sum( size(N(v) & P) for v in P ) ; return clip(sum_val, 0, 1) ; aggregate: total |
| CS | triangle-node | 14 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1673 | - | 0.2950 | 0.0604 | sum_ordered = sum( sum( A(u, v) for v in P ) for u in P ) ; sum_unordered = sum_ordered / 2 ; max_sum = max(0, sum_unordered) ; clipped = clip(max_sum, 0, 1) ; return clipped ; aggregate: total |
| CS | triangle-node | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1712 | - | 0.2583 | 0.0237 | S = project(P, D) ; sum_ordered = sum( sum( A(u, v) for v in S ) for u in S ) ; sum_edges = sum_ordered / 2 ; return clip(sum_edges, 0, 1) ; aggregate: total |
| CS | triangle-node | 16 | True | 1 | 2 | False | False | 0.8000 | True | True | 0.1262 | - | 0.2658 | 0.0312 | s = sum( sum( A(u, v) for v in P ) for u in P ) ; return clip( s, 0, 1 ) ; aggregate: total |
| CS | triangle-node | 17 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1014 | - | 0.2803 | 0.0456 | neighbors = project(P, D) ; count = sum( size(N(v) & neighbors) for v in neighbors ) ; return clip(count, 0, 1) ; aggregate: total |
| CS | triangle-node | 18 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1014 | - | 0.2803 | 0.0456 | projected_P = project(P, D) ; sum_size = sum(size(projected_P & N(u)) for u in projected_P) ; return clip(sum_size - 1, 0, 1) ; aggregate: total |
| CS | triangle-node | 19 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.1014 | - | 0.2806 | 0.0460 | S = project(P, D) ; count = sum( size(N(v) & P) for v in S ) ; return clip(count, 0, 1) ; aggregate: total |
| EE | degree-ge3 | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | s = size(P) ; return clip(max(0, s - 2), 0, 1) ; aggregate: total |
| EE | degree-ge3 | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | s = size(P) ; report = clip(s - 2, 0, 1) ; return report ; aggregate: total |
| EE | degree-ge3 | 2 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | size_P = size(P) ; report = clip(size_P - 2, 0, 1) ; return report ; aggregate: total |
| EE | degree-ge3 | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | d = size(P) ; value = max(0, d - 2) ; return clip(value, 0, 1) ; aggregate: total |
| EE | degree-ge3 | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | indicator = clip(size(P) - 2, 0, 1) ; return indicator ; aggregate: total |
| EE | degree-ge3 | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | s = size(P) ; return max(0, min(1, s - 2)) ; aggregate: total |
| EE | degree-ge3 | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | value = max(0, size(P) - 2) ; indicator = clip(value, 0, 1) ; return indicator ; aggregate: total |
| EE | degree-ge3 | 7 | True | 1 | 2 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0654 | 0.0069 | return clip(size(project(P, D)) - 2, 0, 1) ; aggregate: total |
| EE | degree-ge3 | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | d = size(P) ; return clip(d - 2, 0, 1) ; aggregate: total |
| EE | degree-ge3 | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | indicator = clip(size(P) - 2, 0, 1) ; return indicator ; aggregate: total |
| EE | degree-ge3 | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | return min(1, max(0, size(P) - 2)) ; aggregate: total |
| EE | degree-ge3 | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | degree = size(P) ; indicator = clip(degree - 2, 0, 1) ; return indicator ; aggregate: total |
| EE | degree-ge3 | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | result = clip(size(P) - 2, 0, 1) ; return result ; aggregate: total |
| EE | degree-ge3 | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | degree = size(P) ; indicator = max(0, min(1, degree - 2)) ; return indicator ; aggregate: total |
| EE | degree-ge3 | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | size_P = size(P) ; indicator = clip(size_P - 2, 0, 1) ; return indicator ; aggregate: total |
| EE | degree-ge3 | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | report = clip(size(P) - 2, 0, 1) ; return report ; aggregate: total |
| EE | degree-ge3 | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | d = size(P) ; x = max(0, d - 2) ; return clip(x, 0, 1) ; aggregate: total |
| EE | degree-ge3 | 17 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | return clip(size(P) - 2, 0, 1) ; aggregate: total |
| EE | degree-ge3 | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | s = size(P) ; return clip(s - 2, 0, 1) ; aggregate: total |
| EE | degree-ge3 | 19 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0585 | 0.0000 | size_P = size(P) ; indicator = clip(size_P - 2, 0, 1) ; return indicator ; aggregate: total |
| EE | triangle-edge | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 1 | True | 1 | 2 | False | False | 1.0025 | True | True | 0.1782 | - | 0.2464 | -0.0733 | S = project(P, D) ; return sum( clip( size(S & N(v)), 0, 1 ) for v in S ) ; aggregate: total / 2 |
| EE | triangle-edge | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 3 | True | 1 | 3 | False | False | 1.0025 | True | True | 0.1782 | - | 0.2464 | -0.0733 | projected = project(P, D) ; sum = sum( clip( size( N(v) & projected ), 0, 1 ) for v in projected ) ; return sum ; aggregate: total / 2 |
| EE | triangle-edge | 4 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.3153 | - | 0.3197 | 0.0000 | P_proj = project(P, D) ; sum_v = sum(clip(sum(A(v, w) for w in P_proj), 0, 1) for v in P_proj) ; return sum_v ; aggregate: total / 2 |
| EE | triangle-edge | 5 | True | 1 | 3 | False | False | 1.0025 | True | True | 0.1782 | - | 0.2464 | -0.0733 | S = project(P, D) ; count = sum(clip(size(S & N(v)), 0, 1) for v in S) ; return count ; aggregate: total / 2 |
| EE | triangle-edge | 6 | True | 1 | 2 | False | False | 1.0025 | True | True | 0.1782 | - | 0.2464 | -0.0733 | neighbors = project(P, D) ; count = sum( clip( size( neighbors & N(v) ), 0, 1 ) for v in neighbors ) ; return count ; aggregate: total / 2 |
| EE | triangle-edge | 7 | True | 1 | 3 | False | False | 1.0025 | True | True | 0.1782 | - | 0.2464 | -0.0733 | return sum( clip( size( project(P, D) & N(v) ), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| EE | triangle-edge | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 9 | True | 1 | 1 | False | False | 1.0025 | True | True | 0.1782 | - | 0.2464 | -0.0733 | P_proj = project(P, D) ; return sum(clip(size(P_proj & N(v)), 0, 1) for v in P_proj) ; aggregate: total / 2 |
| EE | triangle-edge | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 12 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 13 | True | 1 | 3 | False | False | 1.0025 | True | True | 0.1782 | - | 0.2464 | -0.0733 | return sum( clip( size( project(P, D) & N(v) ), 0, 1 ) for v in project(P, D) ) / 2 ; aggregate: total |
| EE | triangle-edge | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 15 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.3153 | - | 0.3197 | 0.0000 | return sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| EE | triangle-edge | 16 | True | 1 | 3 | False | False | 0.9608 | True | True | 0.1634 | - | 0.2694 | -0.0503 | total = sum( clip( size( N(v) & P ), 0, 1 ) for v in project(P, D) ) ; return total ; aggregate: total / 2 |
| EE | triangle-edge | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-node | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2081 | - | 0.1562 | 0.0115 | P_projected = project(P, D) ; sum_all_pairs = sum(sum(A(u, v) for v in P_projected) for u in P_projected) ; sum_pairs_u_less_v = sum_all_pairs / 2 ; contribution = clip(max(0, sum_pairs_u_less_v), 0, 1) ; return contribution ; aggregate: total |
| EE | triangle-node | 1 | True | 1 | 1 | False | False | 0.8000 | True | True | 0.1232 | - | 0.1088 | -0.0360 | sum_ordered = sum(sum(A(u, v) for v in P) for u in P) ; return clip(sum_ordered, 0, 1) ; aggregate: total |
| EE | triangle-node | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1510 | - | 0.1447 | 0.0000 | S = project(P, D) ; sum_pairs = sum( sum( A(v, w) for w in S ) for v in S ) ; indicator = clip( sum_pairs, 0, 1 ) ; return indicator ; aggregate: total |
| EE | triangle-node | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1510 | - | 0.1447 | 0.0000 | S = project(P, D) ; sum_pairs = sum( sum( A(v, w) for w in S ) for v in S ) ; result = clip(sum_pairs, 0, 1) ; return result ; aggregate: total |
| EE | triangle-node | 4 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.1510 | - | 0.1447 | 0.0000 | S = project(P, D) ; sum_edges = sum( sum( A(v, w) for w in S ) for v in S ) ; result = clip( sum_edges, 0, 1 ) ; return result ; aggregate: total |
| EE | triangle-node | 5 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.2727 | - | 0.1325 | -0.0123 | S = project(P, D) ; sum_over_u = sum(size(S & N(u)) for u in S) ; return clip(sum_over_u, 0, 1) ; aggregate: total |
| EE | triangle-node | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2652 | - | 0.1690 | 0.0243 | S = project(P, D) ; sum_A = sum(sum(A(v, w) for w in S) for v in S) ; indicator = clip(sum_A - 1, 0, 1) ; return indicator ; aggregate: total |
| EE | triangle-node | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1510 | - | 0.1447 | 0.0000 | neighbors = project(P, D) ; sum_A = sum(sum(A(j, k) for k in neighbors) for j in neighbors) ; clipped_sum = clip(sum_A, 0, 1) ; return clipped_sum ; aggregate: total |
| EE | triangle-node | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1510 | - | 0.1447 | 0.0000 | P_projected = project(P, D) ; sum_over_pairs = sum( sum( A(j, k) for k in P_projected ) for j in P_projected ) ; max_sum = max( sum_over_pairs, 0 ) ; result = clip( max_sum, 0, 1 ) ; return result ; aggregate: total |
| EE | triangle-node | 9 | True | 1 | 2 | False | False | 0.8000 | True | True | 0.1232 | - | 0.1088 | -0.0360 | sum_jk = sum( sum( A(j, k) for k in P ) for j in P ) ; return clip( sum_jk, 0, 1 ) ; aggregate: total |
| EE | triangle-node | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2081 | - | 0.1562 | 0.0115 | S = project(P, D) ; sum_ordered = sum(sum(A(u, v) for v in S) for u in S) ; sum_unordered = sum_ordered / 2 ; count = clip(sum_unordered, 0, 1) ; return count ; aggregate: total |
| EE | triangle-node | 11 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.2727 | - | 0.1325 | -0.0123 | return clip( sum( size(N(v) & project(P, D)) for v in project(P, D) ), 0, 1 ) ; aggregate: total |
| EE | triangle-node | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.1510 | - | 0.1447 | 0.0000 | S = project(P, D) ; sum_over_u_v = sum(sum(A(u, v) for v in S) for u in S) ; indicator = clip(sum_over_u_v, 0, 1) ; return indicator ; aggregate: total |
| EE | triangle-node | 13 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.2727 | - | 0.1325 | -0.0123 | S = project(P, D) ; sum_size = sum( size(S & N(u)) for u in S ) ; return clip( max(0, sum_size - 1), 0, 1 ) ; aggregate: total |
| EE | triangle-node | 14 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.2682 | - | 0.1322 | -0.0125 | count = sum(size(P & N(u)) for u in P) / 2 ; return clip(count, 0, 1) ; aggregate: total |
| EE | triangle-node | 15 | True | 1 | 1 | False | False | 1.0000 | True | True | 0.2682 | - | 0.1322 | -0.0125 | sum_v_in_P = sum(size(N(v) & P) for v in P) ; return clip(sum_v_in_P, 0, 1) ; aggregate: total |
| EE | triangle-node | 16 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.2727 | - | 0.1325 | -0.0123 | sum_S = sum( size(N(v) & project(P, D)) for v in project(P, D) ) ; return clip(sum_S, 0, 1) ; aggregate: total |
| EE | triangle-node | 17 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.2727 | - | 0.1325 | -0.0123 | S = project(P, D) ; edges = sum( size(N(v) & S) for v in S ) / 2 ; count = clip(edges, 0, 1) ; return count ; aggregate: total |
| EE | triangle-node | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.1510 | - | 0.1447 | 0.0000 | P_proj = project(P, D) ; sum_pairs = sum(sum(A(v, w) for w in P_proj) for v in P_proj) ; indicator = clip(sum_pairs, 0, 1) ; return indicator ; aggregate: total |
| EE | triangle-node | 19 | True | 1 | 2 | False | False | 1.0000 | True | True | 0.2727 | - | 0.1325 | -0.0123 | projected = project(P, D) ; total_pairs = sum( size(projected & N(v)) for v in projected ) ; indicator = clip(total_pairs, 0, 1) ; return indicator ; aggregate: total |
