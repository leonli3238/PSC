# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 10 independent design(s), 3 draft(s) x up to 2 restart(s), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = PSC, noise-aware gate on (τ = 2, 8 releases per graph).

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: derived GS / reference GS at the design-time bound D = min(n−1, 10); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 10 | 1.0000 | 0.9000 | 0.4000 | 1.9000 | 1.1000 | 2.2000 | 10 | 0.1000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.1500 | 1.2500 | 1.0051 |
| PM | 5-star | 10 | 1.0000 | 0.9000 | 0.4000 | 1.5000 | 1.1000 | 1.8000 | 7 | 0.1000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| PM | triangle | 10 | 0.6000 | 0.5000 | 0.1000 | 1.8333 | 1.5000 | 3.8000 | 6 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.6605 | 3.1111 | 1.5028 |
| PM | degree-moment2 | 10 | 1.0000 | 1.0000 | 0.6000 | 1.5000 | 1.0000 | 1.5000 | 7 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.1053 | 1.1053 | 1.0042 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0.1233 | 0.1237 | 0.1227 | 0.000596 | 0.0009933 | 0.4000 | 0.0000 |
| PM | 5-star | 0.2874 | 0.2874 | 0.2874 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| PM | triangle | 1.6939 | 1.6929 | 1.0295 | 0.6645 | 0.6696 | 0.0000 | 0.0500 |
| PM | degree-moment2 | 0.0435 | 0.0435 | 0.0433 | 0.0001752 | 0.0001752 | 0.0000 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0 | True | 1 | 3 | False | True | 1.0085 | True | True | 0.0199 | - | 0.1237 | 0.0009933 | name = size(project(P, D)) ; return name * (name - 1) * (name - 2) / 6 ; aggregate: total |
| PM | 3-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; count = comb(degree, 3) ; return count ; aggregate: total |
| PM | 3-star | 2 | True | 1 | 3 | False | True | 1.0085 | True | True | 0.0199 | - | 0.1237 | 0.0009933 | degree = size(project(P, D)) ; count = degree * (degree - 1) * (degree - 2) / 6 ; return count ; aggregate: total |
| PM | 3-star | 3 | True | 1 | 1 | False | True | 1.0085 | True | True | 0.0199 | - | 0.1237 | 0.0009933 | projected_P = project(P, D) ; degree = size(projected_P) ; num_3stars = degree * (degree - 1) * (degree - 2) / 6 ; return num_3stars ; aggregate: total |
| PM | 3-star | 4 | True | 1 | 3 | False | True | 1.0085 | True | True | 0.0199 | - | 0.1237 | 0.0009933 | projected_set = project(P, D) ; projected_degree = size(projected_set) ; term = projected_degree * (projected_degree - 1) * (projected_degree - 2) / 6 ; return term ; aggregate: total |
| PM | 3-star | 5 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | return comb( size(project(P, D)), 3 ) ; aggregate: total |
| PM | 3-star | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 7 | True | 2 | 2 | False | True | 1.0085 | True | True | 0.0199 | - | 0.1237 | 0.0009933 | d = size(project(P, D)) ; return d * (d - 1) * (d - 2) / 6 ; aggregate: total |
| PM | 3-star | 8 | True | 1 | 2 | False | True | 1.0085 | True | True | 0.0199 | - | 0.1237 | 0.0009933 | P_bounded = project(P, D) ; degree = size(P_bounded) ; count = (degree * (degree - 1) * (degree - 2)) / 6 ; return count ; aggregate: total |
| PM | 3-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | name = comb(size(project(P, D)), 3) ; return name ; aggregate: total |
| PM | 5-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | name = comb(size(project(P, D)), 5) ; return name ; aggregate: total |
| PM | 5-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | name = project(P, D) ; return comb(size(name), 5) ; aggregate: total |
| PM | 5-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | name = comb(size(project(P, D)), 5) ; return name ; aggregate: total |
| PM | 5-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | name = comb(size(project(P, D)), 5) ; return name ; aggregate: total |
| PM | 5-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; count = comb(degree, 5) ; return count ; aggregate: total |
| PM | 5-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | name = comb(size(project(P, D)), 5) ; return name ; aggregate: total |
| PM | 5-star | 6 | True | 2 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 5) ; aggregate: total |
| PM | 5-star | 7 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected = project(P, D) ; count = comb(size(projected), 5) ; return count ; aggregate: total |
| PM | 5-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | clipped_degree = project(P, D) ; count = comb(size(clipped_degree), 5) ; return count ; aggregate: total |
| PM | triangle | 0 | True | 1 | 1 | False | True | 1.5021 | True | True | 0.2506 | - | 1.6929 | 0.6635 | count = sum( size( project(P, D) & N(v) ) for v in project(P, D) ) ; return count / 2 ; aggregate: total / 3 |
| PM | triangle | 1 | False | 2 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 2 | True | 1 | 2 | False | True | 1.5021 | True | True | 0.2506 | - | 1.6929 | 0.6635 | neighbors = project(P, D) ; return sum( size(neighbors & N(v)) for v in neighbors ) ; aggregate: total / 6 |
| PM | triangle | 3 | False | 2 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 4 | True | 1 | 3 | False | True | 1.5063 | True | True | 0.2523 | - | 1.6991 | 0.6696 | projected_set = project(P, D) ; sum_neighbors = sum( size(P & N(u)) for u in projected_set ) ; count = sum_neighbors / 2 ; return count ; aggregate: total / 3 |
| PM | triangle | 5 | True | 1 | 2 | False | True | 1.5021 | True | True | 0.2506 | - | 1.6929 | 0.6635 | count = sum( size(N(u) & project(P, D)) for u in project(P, D) ) / 2 ; return count / 3 ; aggregate: total |
| PM | triangle | 6 | True | 2 | 1 | False | True | 1.5021 | True | True | 0.2506 | - | 1.6929 | 0.6635 | P_proj = project(P, D) ; count = sum(size(P_proj & N(j)) for j in P_proj) / 2 ; return count ; aggregate: total / 3 |
| PM | triangle | 7 | False | 2 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 8 | False | 2 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 9 | True | 1 | 2 | False | True | 1.5021 | True | True | 0.2506 | - | 1.6929 | 0.6635 | projected_P = project(P, D) ; sum_u = sum( size(N(u) & projected_P) for u in projected_P ) ; return sum_u / 2 ; aggregate: total / 3 |
| PM | degree-moment2 | 0 | True | 1 | 2 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | name = size(project(P, D)) ; return name * name ; aggregate: total |
| PM | degree-moment2 | 1 | True | 1 | 1 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | name = size(project(P, D)) ; return name * name ; aggregate: total |
| PM | degree-moment2 | 2 | True | 1 | 1 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 3 | True | 1 | 3 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | return size(project(P, D)) * size(project(P, D)) ; aggregate: total |
| PM | degree-moment2 | 4 | True | 1 | 1 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | s = size(project(P, D)) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 5 | True | 1 | 2 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 6 | True | 1 | 1 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | projected_P = project(P, D) ; degree = size(projected_P) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 7 | True | 1 | 1 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | name = size(project(P, D)) * size(project(P, D)) ; return name ; aggregate: total |
| PM | degree-moment2 | 8 | True | 1 | 1 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 9 | True | 1 | 2 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | bounded_degree = size(project(P, D)) ; report = bounded_degree * bounded_degree ; return report ; aggregate: total |
