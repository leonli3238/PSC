# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 20 independent design(s), 3 draft(s) x up to 1 restart(s), selection first, tighten 0, early stop off, normalisation on, prompt v1-repeat3 (core v1-repeat3, 59e2ef21182529df), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = PSC, noise-aware gate on (τ = 2, 8 releases per graph).

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: derived GS / reference GS at the design-time bound D = min(n−1, 10); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 20 | 0.8000 | [0.58, 0.92] | 0.8000 | 0.2000 | 1.8125 | 1.0000 | 2.0500 | 10 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| PM | 5-star | 20 | 0.9000 | [0.70, 0.97] | 0.9000 | 0.3000 | 1.7222 | 1.0000 | 1.8500 | 11 | 0.2222 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| PM | triangle | 20 | 0.0000 | [0.00, 0.16] | 0.0000 | 0.0000 | - | 1.0000 | 3.0000 | 0 | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 20 | 1.0000 | [0.84, 1.00] | 1.0000 | 0.4500 | 1.6000 | 1.0000 | 1.6000 | 11 | 0.1500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0.1227 | 0.1227 | 0.1227 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| PM | 5-star | 0.2874 | 0.2874 | 0.2874 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| PM | triangle | - | - | 1.0295 | - | - | - | - |
| PM | degree-moment2 | 0.0433 | 0.0433 | 0.0433 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | size_projected = size(project(P, D)) ; return comb(size_projected, 3) ; aggregate: total |
| PM | 3-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| PM | 3-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| PM | 3-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; return (degree * (degree - 1) * (degree - 2)) / 6 ; aggregate: total |
| PM | 3-star | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; count = (degree * (degree - 1) * (degree - 2)) / 6 ; return count ; aggregate: total |
| PM | 3-star | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; count = comb(d, 3) ; return count ; aggregate: total |
| PM | 3-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| PM | 3-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | bounded_degree = size(project(P, D)) ; stars = comb(bounded_degree, 3) ; return stars ; aggregate: total |
| PM | 3-star | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| PM | 3-star | 12 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 13 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; value = comb(d, 3) ; return value ; aggregate: total |
| PM | 3-star | 14 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| PM | 3-star | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; term1 = degree * (degree - 1) ; term2 = term1 * (degree - 2) ; result = term2 / 6 ; return result ; aggregate: total |
| PM | 3-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; count = (degree * (degree - 1) * (degree - 2)) / 6 ; return count ; aggregate: total |
| PM | 3-star | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| PM | 3-star | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; return degree * (degree - 1) * (degree - 2) / 6 ; aggregate: total |
| PM | 3-star | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| PM | 5-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | size_P = size(project(P, D)) ; return comb(size_P, 5) ; aggregate: total |
| PM | 5-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | size_P = size(P) ; projected_size = min(size_P, D) ; result = comb(projected_size, 5) ; return result ; aggregate: total |
| PM | 5-star | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 5-star | 3 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 5) ; aggregate: total |
| PM | 5-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | degree = size(project(P, D)) ; count = comb(degree, 5) ; return count ; aggregate: total |
| PM | 5-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | degree = size(project(P, D)) ; stars = comb(degree, 5) ; return stars ; aggregate: total |
| PM | 5-star | 6 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 5) ; aggregate: total |
| PM | 5-star | 8 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; count = comb(degree, 5) ; return count ; aggregate: total |
| PM | 5-star | 10 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 5) ; aggregate: total |
| PM | 5-star | 11 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 5) ; aggregate: total |
| PM | 5-star | 12 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 5) ; aggregate: total |
| PM | 5-star | 13 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected_degree = project(P, D) ; return comb(size(projected_degree), 5) ; aggregate: total |
| PM | 5-star | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 5) ; aggregate: total |
| PM | 5-star | 15 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 5) ; aggregate: total |
| PM | 5-star | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected_degree = project(P, D) ; count = comb(size(projected_degree), 5) ; return count ; aggregate: total |
| PM | 5-star | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 5-star | 19 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | triangle | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 12 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 13 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 17 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | d = size(project(P, D)) ; return d * d ; aggregate: total |
| PM | degree-moment2 | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | return size(project(P, D)) * size(project(P, D)) ; aggregate: total |
| PM | degree-moment2 | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | projected_P = project(P, D) ; size_projected = size(projected_P) ; return size_projected * size_projected ; aggregate: total |
| PM | degree-moment2 | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return pow(degree, 2) ; aggregate: total |
| PM | degree-moment2 | 4 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 5 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 6 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | return size(project(P, D)) * size(project(P, D)) ; aggregate: total |
| PM | degree-moment2 | 9 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | return size(project(P, D)) * size(project(P, D)) ; aggregate: total |
| PM | degree-moment2 | 10 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 11 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | s = size(project(P, D)) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 13 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | s = size(project(P, D)) ; report = pow(s, 2) ; return report ; aggregate: total |
| PM | degree-moment2 | 14 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 15 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | size_p = size(project(P, D)) ; return size_p * size_p ; aggregate: total |
| PM | degree-moment2 | 16 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | s = size(project(P, D)) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 17 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | return size(project(P, D)) * size(project(P, D)) ; aggregate: total |
| PM | degree-moment2 | 18 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree_projected = project(P, D) ; degree_squared = size(degree_projected) * size(degree_projected) ; return degree_squared ; aggregate: total |
| PM | degree-moment2 | 19 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | s = size(project(P, D)) ; return s * s ; aggregate: total |
