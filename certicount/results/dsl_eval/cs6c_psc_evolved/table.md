# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 10 independent design(s), 3 draft(s) x up to 1 restart(s), selection first, tighten 0, early stop off, normalisation on, prompt g1c3 (core v1, f4723269c9dad172), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = PSC, noise-aware gate on (τ = 2, 8 releases per graph).

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: derived GS / reference GS at the design-time bound D = min(n−1, 10); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 10 | 1.0000 | [0.72, 1.00] | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 9 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| PM | 5-star | 10 | 1.0000 | [0.72, 1.00] | 1.0000 | 0.9000 | 1.1000 | 1.0000 | 1.1000 | 9 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| PM | triangle | 10 | 0.3000 | [0.11, 0.60] | 0.3000 | 0.1000 | 1.6667 | 1.0000 | 2.6000 | 3 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.3333 | 2.0000 | 1.0000 |
| PM | degree-moment2 | 10 | 1.0000 | [0.72, 1.00] | 1.0000 | 0.9000 | 1.1000 | 1.0000 | 1.1000 | 8 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

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
| PM | 3-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | neighbors = project(P, D) ; k = size(neighbors) ; result = comb(k, 3) ; return result ; aggregate: total |
| PM | 3-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; result = comb(degree, 3) ; return result ; aggregate: total |
| PM | 3-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | s = size(project(P, D)) ; return comb(s, 3) ; aggregate: total |
| PM | 3-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | k = size(project(P, D)) ; return comb(k, 3) ; aggregate: total |
| PM | 3-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | projected_P = project(P, D) ; k = size(projected_P) ; return comb(k, 3) ; aggregate: total |
| PM | 3-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | projected = project(P, D) ; d = size(projected) ; return (d * (d - 1) * (d - 2)) / 6 ; aggregate: total |
| PM | 3-star | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | projected = project(P, D) ; d = size(projected) ; return comb(d, 3) ; aggregate: total |
| PM | 3-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | projected_P = project(P, D) ; projected_size = size(projected_P) ; return comb(projected_size, 3) ; aggregate: total |
| PM | 3-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; count = comb(degree, 3) ; return count ; aggregate: total |
| PM | 3-star | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; count = comb(degree, 3) ; return count ; aggregate: total |
| PM | 5-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected_P = project(P, D) ; return comb(size(projected_P), 5) ; aggregate: total |
| PM | 5-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | size_proj = size(project(P, D)) ; return comb(size_proj, 5) ; aggregate: total |
| PM | 5-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | s = size(P) ; projected = project(P, D) ; projected_size = size(projected) ; result = comb(projected_size, 5) ; return result ; aggregate: total |
| PM | 5-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | size_p = size(project(P, D)) ; c = comb(size_p, 5) ; return c ; aggregate: total |
| PM | 5-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | s = project(P, D) ; c = comb(size(s), 5) ; return c ; aggregate: total |
| PM | 5-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | s = size(project(P, D)) ; return comb(s, 5) ; aggregate: total |
| PM | 5-star | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | s = size(project(P, D)) ; c = comb(s, 5) ; return c ; aggregate: total |
| PM | 5-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected = project(P, D) ; k = size(projected) ; return comb(k, 5) ; aggregate: total |
| PM | 5-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected_P = project(P, D) ; count = comb(size(projected_P), 5) ; return count ; aggregate: total |
| PM | 5-star | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | s = size(project(P, D)) ; return comb(s, 5) ; aggregate: total |
| PM | triangle | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | P_projected = project(P, D) ; count = sum( size(N(v) & P_projected) for v in P_projected ) ; return count / 2 ; aggregate: total / 3 |
| PM | triangle | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | common = project(P, D) ; count = sum( size( common & N(j) ) for j in common ) ; return count ; aggregate: total / 6 |
| PM | triangle | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2506 | - | 1.5868 | 0.5573 | projected_P = project(P, D) ; sum_over_u = sum(size(N(u) & projected_P) for u in projected_P) ; return sum_over_u / 2 ; aggregate: total / 3 |
| PM | triangle | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; squared_degree = degree * degree ; return squared_degree ; aggregate: total |
| PM | degree-moment2 | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | size_projected = size(project(P, D)) ; return pow(size_projected, 2) ; aggregate: total |
| PM | degree-moment2 | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | projected_p = project(P, D) ; size_p = size(projected_p) ; return size_p * size_p ; aggregate: total |
| PM | degree-moment2 | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | s = size(project(P, D)) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | projected_P = project(P, D) ; degree_squared = size(projected_P) * size(projected_P) ; return degree_squared ; aggregate: total |
| PM | degree-moment2 | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | projected_p = project(P, D) ; size_p = size(projected_p) ; return size_p * size_p ; aggregate: total |
| PM | degree-moment2 | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | s_proj = project(P, D) ; s = size(s_proj) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0062 | - | 0.0433 | 0.0000 | size_P = size(project(P, D)) ; return size_P * size_P ; aggregate: total |
