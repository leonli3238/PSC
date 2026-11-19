# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 20 independent design(s), 3 draft(s) x up to 1 restart(s), selection first, tighten 0, early stop off, normalisation on, prompt v0 (core v1, 898628ff51a8d8c9), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = PSC, noise-aware gate on (τ = 2, 8 releases per graph).

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: derived GS / reference GS at the design-time bound D = min(n−1, 10); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 20 | 0.8000 | [0.58, 0.92] | 0.8000 | 0.1000 | 2.2500 | 1.0000 | 2.4000 | 16 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| PM | 5-star | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.5500 | 1.4211 | 1.0000 | 1.5000 | 16 | 0.0526 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| PM | triangle | 20 | 0.3000 | [0.15, 0.52] | 0.3000 | 0.1000 | 2.1667 | 1.0000 | 2.7500 | 6 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.1667 | 2.0000 | 1.0000 |
| PM | degree-moment2 | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.2000 | 1.9000 | 1.0000 | 1.9000 | 15 | 0.1000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0.1227 | 0.1227 | 0.1227 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| PM | 5-star | 0.2874 | 0.2874 | 0.2874 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| PM | triangle | 1.5868 | 1.5868 | 1.0295 | 0.5573 | 0.5573 | 0.0000 | 0.0000 |
| PM | degree-moment2 | 0.0433 | 0.0433 | 0.0433 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 3) ; aggregate: total |
| PM | 3-star | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; return (degree * (degree - 1) * (degree - 2)) / 6 ; aggregate: total |
| PM | 3-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | size_P = size(project(P, D)) ; stars = size_P * (size_P - 1) * (size_P - 2) / 6 ; return stars ; aggregate: total |
| PM | 3-star | 4 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | size_proj = size(project(P, D)) ; count = size_proj * (size_proj - 1) * (size_proj - 2) / 6 ; return count ; aggregate: total |
| PM | 3-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; contribution = degree * (degree - 1) * (degree - 2) / 6 ; return contribution ; aggregate: total |
| PM | 3-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | k = size(project(P, D)) ; report = k * (k - 1) * (k - 2) / 6 ; return report ; aggregate: total |
| PM | 3-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| PM | 3-star | 8 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | size_proj = size(project(P, D)) ; return (size_proj * (size_proj - 1) * (size_proj - 2)) / 6 ; aggregate: total |
| PM | 3-star | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 10 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | size_proj = size(project(P, D)) ; return size_proj * (size_proj - 1) * (size_proj - 2) / 6 ; aggregate: total |
| PM | 3-star | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| PM | 3-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 3) ; aggregate: total |
| PM | 3-star | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 15 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | size_P = size(project(P, D)) ; term = size_P * (size_P - 1) * (size_P - 2) / 6 ; return term ; aggregate: total |
| PM | 3-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; count = comb(degree, 3) ; return count ; aggregate: total |
| PM | 3-star | 17 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; return degree * (degree - 1) * (degree - 2) / 6 ; aggregate: total |
| PM | 3-star | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; return d * (d - 1) * (d - 2) / 6 ; aggregate: total |
| PM | 3-star | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | size_P = size(project(P, D)) ; count = size_P * (size_P - 1) * (size_P - 2) / 6 ; return count ; aggregate: total |
| PM | 5-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | k = size(project(P, D)) ; return comb(k,5) ; aggregate: total |
| PM | 5-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected_p = project(P, D) ; combo = comb(size(projected_p), 5) ; return combo ; aggregate: total |
| PM | 5-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | s = size(project(P, D)) ; return comb(s, 5) ; aggregate: total |
| PM | 5-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 5) ; aggregate: total |
| PM | 5-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | s = project(P, D) ; return comb(size(s), 5) ; aggregate: total |
| PM | 5-star | 5 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 5) ; aggregate: total |
| PM | 5-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | neighbors = project(P, D) ; count = comb(size(neighbors), 5) ; return count ; aggregate: total |
| PM | 5-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | s = size(project(P, D)) ; return comb(s, 5) ; aggregate: total |
| PM | 5-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 5) ; aggregate: total |
| PM | 5-star | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected = project(P, D) ; count = comb(size(projected), 5) ; return count ; aggregate: total |
| PM | 5-star | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | size_P = size(P) ; bounded_size = min(size_P, D) ; count = comb(bounded_size, 5) ; return count ; aggregate: total |
| PM | 5-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected = project(P, D) ; count = comb(size(projected), 5) ; return count ; aggregate: total |
| PM | 5-star | 13 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 5-star | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected_p = project(P, D) ; size_p = size(projected_p) ; return comb(size_p, 5) ; aggregate: total |
| PM | 5-star | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | k_proj = size(project(P, D)) ; value = comb(k_proj, 5) ; return value ; aggregate: total |
| PM | 5-star | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected_p = project(P, D) ; projected_size = size(projected_p) ; count = comb(projected_size, 5) ; return count ; aggregate: total |
| PM | 5-star | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected_degree = min(size(P), D) ; value = comb(projected_degree, 5) ; return value ; aggregate: total |
| PM | 5-star | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | size_p = size(project(P, D)) ; count = comb(size_p, 5) ; return count ; aggregate: total |
| PM | 5-star | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 5) ; aggregate: total |
| PM | triangle | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 1 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | count = sum( size(N(v) & project(P, D)) for v in project(P, D) ) ; return count / 2 ; aggregate: total / 3 |
| PM | triangle | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | projected_P = project(P, D) ; edges = sum( size( projected_P & N(v) ) for v in projected_P ) ; return edges / 2 ; aggregate: total / 3 |
| PM | triangle | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 12 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 13 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 14 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | sum_u_in_P = sum( size(N(u) & project(P, D)) for u in project(P, D) ) ; count_v = sum_u_in_P / 2 ; return count_v ; aggregate: total / 3 |
| PM | triangle | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | count = sum( size( project(P, D) & N(w) ) for w in project(P, D) ) ; return count ; aggregate: total / 6 |
| PM | triangle | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | projected_P = project(P, D) ; sum_edges = sum( size(N(v) & projected_P) for v in projected_P ) ; count = sum_edges / 2 ; return count ; aggregate: total / 3 |
| PM | triangle | 19 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | neighbors = project(P, D) ; count = sum(size(neighbors & N(u)) for u in neighbors) / 2 ; return count ; aggregate: total / 3 |
| PM | degree-moment2 | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | size_p = size(project(P, D)) ; return pow(size_p, 2) ; aggregate: total |
| PM | degree-moment2 | 1 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | return size(project(P, D)) * size(project(P, D)) ; aggregate: total |
| PM | degree-moment2 | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | projected_degree = project(P, D) ; projected_degree_count = size(projected_degree) ; report = projected_degree_count * projected_degree_count ; return report ; aggregate: total |
| PM | degree-moment2 | 3 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | size_projected = size(project(P, D)) ; return size_projected * size_projected ; aggregate: total |
| PM | degree-moment2 | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; report = degree * degree ; return report ; aggregate: total |
| PM | degree-moment2 | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | projected_P = project(P, D) ; size_projected = size(projected_P) ; return size_projected * size_projected ; aggregate: total |
| PM | degree-moment2 | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | s_proj = project(P, D) ; s = size(s_proj) ; report = s * s ; return report ; aggregate: total |
| PM | degree-moment2 | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return pow(degree, 2) ; aggregate: total |
| PM | degree-moment2 | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | d = size(project(P, D)) ; return d * d ; aggregate: total |
| PM | degree-moment2 | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | s = size(project(P, D)) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | size_p = size(project(P, D)) ; squared = pow(size_p, 2) ; return squared ; aggregate: total |
| PM | degree-moment2 | 13 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 15 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return pow(degree, 2) ; aggregate: total |
| PM | degree-moment2 | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | s = size(project(P, D)) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | projected = project(P, D) ; s = size(projected) ; squared = pow(s, 2) ; return squared ; aggregate: total |
| PM | degree-moment2 | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | d = size(project(P, D)) ; return d * d ; aggregate: total |
