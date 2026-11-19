# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 20 independent design(s), 3 draft(s) x up to 1 restart(s), selection first, tighten 0, early stop off, normalisation on, prompt v1-alt (core v1-alt, b3ea0cb2b6add266), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = PSC, noise-aware gate on (τ = 2, 8 releases per graph).

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: derived GS / reference GS at the design-time bound D = min(n−1, 10); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 20 | 0.9000 | [0.70, 0.97] | 0.9000 | 0.0500 | 2.1111 | 1.0000 | 2.2000 | 16 | 0.0556 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| PM | 5-star | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.4500 | 1.5789 | 1.0000 | 1.6500 | 13 | 0.3158 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| PM | triangle | 20 | 0.5500 | [0.34, 0.74] | 0.5500 | 0.1500 | 1.7273 | 1.0000 | 2.3000 | 11 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.8788 | 1.0000 | 1.0000 |
| PM | degree-moment2 | 20 | 0.9500 | [0.76, 0.99] | 0.9500 | 0.3500 | 1.7368 | 1.0000 | 1.8000 | 9 | 0.2105 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

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
| PM | 3-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| PM | 3-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | size_p = size(project(P, D)) ; return (size_p * (size_p - 1) * (size_p - 2)) / 6 ; aggregate: total |
| PM | 3-star | 4 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; count = comb(degree, 3) ; return count ; aggregate: total |
| PM | 3-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; t1 = d * (d - 1) ; t2 = t1 * (d - 2) ; res = t2 / 6 ; return res ; aggregate: total |
| PM | 3-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 3) ; aggregate: total |
| PM | 3-star | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| PM | 3-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; return (pow(d, 3) - 3 * pow(d, 2) + 2 * d) / 6 ; aggregate: total |
| PM | 3-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | projected_degree = project(P, D) ; degree = size(projected_degree) ; result = comb(degree, 3) ; return result ; aggregate: total |
| PM | 3-star | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 3) ; aggregate: total |
| PM | 3-star | 12 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; return (degree * (degree - 1) * (degree - 2)) / 6 ; aggregate: total |
| PM | 3-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | bounded_P = project(P, D) ; degree = size(bounded_P) ; term1 = degree ; term2 = degree - 1 ; term3 = degree - 2 ; result = term1 * term2 * term3 / 6 ; return result ; aggregate: total |
| PM | 3-star | 14 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | projected_P = project(P, D) ; clip_size = size(projected_P) ; return comb(clip_size, 3) ; aggregate: total |
| PM | 3-star | 15 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | return comb(size(project(P, D)), 3) ; aggregate: total |
| PM | 3-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| PM | 3-star | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| PM | 3-star | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | s = size(project(P, D)) ; d = s ; c = d * (d - 1) * (d - 2) / 6 ; return c ; aggregate: total |
| PM | 3-star | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 5-star | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | size_proj = size(project(P, D)) ; return comb(size_proj, 5) ; aggregate: total |
| PM | 5-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected = project(P, D) ; size_projected = size(projected) ; return comb(size_projected, 5) ; aggregate: total |
| PM | 5-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | size_P = size(project(P, D)) ; report = comb(size_P, 5) ; return report ; aggregate: total |
| PM | 5-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 5) ; aggregate: total |
| PM | 5-star | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 5-star | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | s = size(project(P, D)) ; c = comb(s, 5) ; return c ; aggregate: total |
| PM | 5-star | 7 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 5) ; aggregate: total |
| PM | 5-star | 9 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 10 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 11 | True | 1 | 3 | True | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected_P = project(P, D) ; return comb(size(projected_P), 5) ; aggregate: total |
| PM | 5-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected_neighbors = project(P, D) ; degree = size(projected_neighbors) ; return comb(degree, 5) ; aggregate: total |
| PM | 5-star | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 5) ; aggregate: total |
| PM | 5-star | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | size_P = size(P) ; projected_size = min(size_P, D) ; result = comb(projected_size, 5) ; return result ; aggregate: total |
| PM | 5-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected_P = project(P, D) ; size_projected_P = size(projected_P) ; return comb(size_projected_P, 5) ; aggregate: total |
| PM | 5-star | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected_degree = size(project(P, D)) ; return comb(projected_degree, 5) ; aggregate: total |
| PM | 5-star | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected_P = project(P, D) ; return comb(size(projected_P), 5) ; aggregate: total |
| PM | 5-star | 19 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | triangle | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | return 0.5 * sum( size( N(v) & project(P, D) ) for v in project(P, D) ) ; aggregate: total / 3 |
| PM | triangle | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | return 0.5 * sum( size( project(P, D) & N(v) ) for v in project(P, D) ) ; aggregate: total / 3 |
| PM | triangle | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | count = 0.5 * sum(size(N(u) & project(P, D)) for u in project(P, D)) ; return count ; aggregate: total / 3 |
| PM | triangle | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | projected_P = project(P, D) ; total_pairs = sum( size(projected_P & N(u)) for u in projected_P ) ; count = 0.5 * total_pairs ; return count ; aggregate: total / 3 |
| PM | triangle | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | contrib = 0.5 * sum( size( N(u) & project(P, D) ) for u in project(P, D) ) ; return contrib ; aggregate: total / 3 |
| PM | triangle | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | sum_size = sum( size( project(P, D) & N(j) ) for j in project(P, D) ) ; return 0.5 * sum_size ; aggregate: total / 3 |
| PM | triangle | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | sum_1 = sum( size( project(P, D) & N(v) ) for v in project(P, D) ) ; return 0.5 * sum_1 / 3 ; aggregate: total |
| PM | triangle | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | sum_ = sum( size( project(P, D) & N(v) ) for v in project(P, D) ) ; return 0.5 * sum_ / 3 ; aggregate: total |
| PM | triangle | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | sum1 = sum( size( project(P, D) & N(j) ) for j in project(P, D) ) ; return 0.5 * sum1 ; aggregate: total / 3 |
| PM | triangle | 13 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 16 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | return 0.5 * sum( size( project(P, D) & N(u) ) for u in project(P, D) ) ; aggregate: total / 3 |
| PM | triangle | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | return 0.5 * sum(size(project(P, D) & N(u)) for u in project(P, D)) ; aggregate: total / 3 |
| PM | triangle | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 0 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | size_projected = size(project(P, D)) ; return pow(size_projected, 2) ; aggregate: total |
| PM | degree-moment2 | 1 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 2 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | clipped_degree = size(project(P, D)) ; report = pow(clipped_degree, 2) ; return report ; aggregate: total |
| PM | degree-moment2 | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 5 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | s = size(project(P, D)) ; return pow(s, 2) ; aggregate: total |
| PM | degree-moment2 | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | size_P = size(project(P, D)) ; return pow(size_P, 2) ; aggregate: total |
| PM | degree-moment2 | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return pow(degree, 2) ; aggregate: total |
| PM | degree-moment2 | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 10 | True | 1 | 3 | True | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | clamped = size(project(P, D)) ; return clamped * clamped ; aggregate: total |
| PM | degree-moment2 | 12 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | size_p = size(project(P, D)) ; return pow(size_p, 2) ; aggregate: total |
| PM | degree-moment2 | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return pow(degree, 2) ; aggregate: total |
| PM | degree-moment2 | 15 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | s = size(project(P, D)) ; return pow(s, 2) ; aggregate: total |
| PM | degree-moment2 | 18 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
