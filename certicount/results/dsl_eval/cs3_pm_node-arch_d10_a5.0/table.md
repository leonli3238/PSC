# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 10 independent design(s), 3 draft(s) x up to 1 restart(s), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5).

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: derived GS / reference GS at the design-time bound D = min(n−1, 10); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | gs_ratio | gs_ratio_max | noise_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 10 | 1.0000 | 1.0000 | 0.8000 | 1.3000 | 1.0000 | 1.3000 | 6 | 0.2000 | 0.2000 | 1.0000 | 1.0000 | 0.5164 | 2.1640 | 0.8660 |
| PM | 2-star | 10 | 1.0000 | 1.0000 | 0.5000 | 1.5000 | 1.0000 | 1.5000 | 5 | 0.0000 | 0.5000 | 1.0000 | 1.0000 | 1.2887 | 3.9436 | 1.8758 |
| PM | 3-star | 10 | 1.0000 | 1.0000 | 0.9000 | 1.1000 | 1.0000 | 1.1000 | 8 | 0.0000 | 0.4000 | 1.0000 | 1.0000 | 283.5278 | 2831.2778 | 0.6838 |
| PM | triangle | 10 | 0.2000 | 0.2000 | 0.0000 | 2.5000 | 1.0000 | 2.9000 | 2 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 9.5180 | 18.3171 | 0.8960 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|
| PM | degree | 7.8372 | 0.0030 | 7.8342 | 13.0502 | 0.2000 | 0.0000 |
| PM | 2-star | 13.2802 | 0.0074 | 13.2728 | 44.2124 | 0.5000 | 0.0000 |
| PM | 3-star | 8.8471 | 0.0087 | 8.8384 | 43.9153 | 0.4000 | 0.0000 |
| PM | triangle | 1.4497 | 0.1263 | 1.3235 | 1.4033 | 0.0000 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 1 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 13.0532 | 13.0502 | size_N = size(N(self)) ; return size_N ; aggregate: total / n |
| PM | degree | 2 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 13.0532 | 13.0502 | size_N_self = size(N(self)) ; return size_N_self ; aggregate: total / n |
| PM | degree | 3 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 13.0532 | 13.0502 | return size(N(self)) ; aggregate: total / n |
| PM | degree | 4 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 13.0532 | 13.0502 | return size(N(self)) ; aggregate: total / n |
| PM | degree | 5 | True | 1 | 2 | False | False | 0.0000 | True | True | - | 13.0532 | 13.0502 | return size(N(self)) ; aggregate: total / n |
| PM | degree | 6 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 13.0532 | 13.0502 | return size(N(self)) ; aggregate: total / n |
| PM | degree | 7 | True | 1 | 3 | False | False | 5.4099 | True | True | - | 0.0384 | 0.0354 | return sum(A(self, y) for y in project(P, D)) ; aggregate: total / n |
| PM | degree | 8 | True | 1 | 1 | False | False | 1.2500 | True | True | - | 0.0080 | 0.0050 | return size(project(P, D)) ; aggregate: total / n |
| PM | degree | 9 | True | 1 | 1 | True | True | 1.0000 | True | True | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | 2-star | 0 | True | 1 | 1 | False | False | 6.8789 | True | True | - | 0.0528 | 0.0454 | projected = project(P, D) ; sum_A = sum(A(self, y) for y in projected) ; two_stars = sum_A * (sum_A - 1) / 2 ; return two_stars ; aggregate: total |
| PM | 2-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.0074 | 0.0000 | name = comb(size(project(P, D)), 2) ; return name ; aggregate: total |
| PM | 2-star | 2 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 44.2198 | 44.2124 | name = size(N(self)) ; return comb(name, 2) ; aggregate: total |
| PM | 2-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.0074 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; count = comb(degree, 2) ; return count ; aggregate: total |
| PM | 2-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.0074 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; count = comb(degree, 2) ; return count ; aggregate: total |
| PM | 2-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.0074 | 0.0000 | name = comb(size(project(P, D)), 2) ; return name ; aggregate: total |
| PM | 2-star | 6 | True | 1 | 2 | False | False | 0.0000 | True | True | - | 44.2198 | 44.2124 | name = size(N(self)) ; return comb(name, 2) ; aggregate: total |
| PM | 2-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.0074 | 0.0000 | name = comb(size(project(P, D)), 2) ; return name ; aggregate: total |
| PM | 2-star | 8 | True | 1 | 2 | False | False | 0.0000 | True | True | - | 44.2198 | 44.2124 | name = size(N(self)) ; return comb(name, 2) ; aggregate: total |
| PM | 2-star | 9 | True | 1 | 2 | False | False | 6.8789 | True | True | - | 0.0528 | 0.0454 | sum_A = sum(A(self, j) for j in project(P, D)) ; report = sum_A * (sum_A - 1) / 2 ; return report ; aggregate: total |
| PM | 3-star | 0 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 0.0737 | 0.0650 | projected_neighbors = project(N(self), D) ; degree = size(projected_neighbors) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| PM | 3-star | 1 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 0.0737 | 0.0650 | projected = project(N(self), D) ; report = comb(size(projected), 3) ; return report ; aggregate: total |
| PM | 3-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.0087 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| PM | 3-star | 3 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 0.0737 | 0.0650 | projected_neighbors = project(N(self), D) ; degree = size(projected_neighbors) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| PM | 3-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.0087 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.0087 | 0.0000 | name = comb(size(project(P, D)), 3) ; return name ; aggregate: total |
| PM | 3-star | 6 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 43.9240 | 43.9153 | name = size(N(self)) ; return name * (name - 1) * (name - 2) / 6 ; aggregate: total |
| PM | 3-star | 7 | True | 1 | 1 | False | False | 2.8377 | True | True | - | 0.3669 | 0.3582 | stars = size(P) * (size(P) - 1) * (size(P) - 2) / 6 ; return stars ; aggregate: total |
| PM | 3-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.0087 | 0.0000 | name = comb(size(project(P, D)), 3) ; return name ; aggregate: total |
| PM | 3-star | 9 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 43.9240 | 43.9153 | name = size(N(self)) ; return comb(name, 3) ; aggregate: total |
| PM | triangle | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - |
| PM | triangle | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - |
| PM | triangle | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - |
| PM | triangle | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - |
| PM | triangle | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - |
| PM | triangle | 5 | True | 1 | 2 | False | False | 1.0995 | True | True | - | 1.3699 | 1.2436 | sum_pairs = sum( sum( A(v, w) for w in P ) for v in P ) ; return sum_pairs / 2 ; aggregate: total / 3 |
| PM | triangle | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - |
| PM | triangle | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - |
| PM | triangle | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - |
| PM | triangle | 9 | True | 1 | 3 | False | False | 0.6924 | True | True | - | 1.5296 | 1.4033 | S = project(P, D) ; sum_edges = sum(size(N(v) & S) for v in S) ; return sum_edges ; aggregate: total / 6 |
