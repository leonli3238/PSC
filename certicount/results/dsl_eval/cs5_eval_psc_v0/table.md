# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 10 independent design(s), 3 draft(s) x up to 1 restart(s), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = PSC, noise-aware gate on (τ = 2, 8 releases per graph).

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: derived GS / reference GS at the design-time bound D = min(n−1, 10); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 10 | 0.9000 | 0.9000 | 0.4000 | 1.5556 | 1.0000 | 1.7000 | 9 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.1389 | 1.2500 | 1.0047 |
| PM | 5-star | 10 | 0.9000 | 0.9000 | 0.4000 | 1.6667 | 1.0000 | 1.8000 | 7 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| PM | triangle | 10 | 0.4000 | 0.4000 | 0.2000 | 1.7500 | 1.0000 | 2.5000 | 4 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.9444 | 3.1111 | 1.5021 |
| PM | degree-moment2 | 10 | 1.0000 | 1.0000 | 0.6000 | 1.4000 | 1.0000 | 1.4000 | 8 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.1053 | 1.1053 | 1.0042 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0.1232 | 0.1237 | 0.1227 | 0.0005518 | 0.0009933 | 0.4444 | 0.0000 |
| PM | 5-star | 0.2874 | 0.2874 | 0.2874 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| PM | triangle | 1.6929 | 1.6929 | 1.0295 | 0.6635 | 0.6635 | 0.0000 | 0.0500 |
| PM | degree-moment2 | 0.0435 | 0.0435 | 0.0433 | 0.0001752 | 0.0001752 | 0.0000 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; count = comb(degree, 3) ; return count ; aggregate: total |
| PM | 3-star | 1 | True | 1 | 2 | False | True | 1.0085 | True | True | 0.0199 | - | 0.1237 | 0.0009933 | name = size(project(P, D)) ; count = name * (name - 1) * (name - 2) / 6 ; return count ; aggregate: total |
| PM | 3-star | 2 | True | 1 | 2 | False | True | 1.0085 | True | True | 0.0199 | - | 0.1237 | 0.0009933 | degree = size(project(P, D)) ; contribution = degree * (degree - 1) * (degree - 2) / 6 ; return contribution ; aggregate: total |
| PM | 3-star | 3 | True | 1 | 1 | False | True | 1.0085 | True | True | 0.0199 | - | 0.1237 | 0.0009933 | projected_P = project(P, D) ; d = size(projected_P) ; count = d * (d - 1) * (d - 2) / 6 ; return count ; aggregate: total |
| PM | 3-star | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 5 | True | 1 | 2 | False | True | 1.0085 | True | True | 0.0199 | - | 0.1237 | 0.0009933 | projected = project(P, D) ; degree = size(projected) ; value = (degree * (degree - 1) * (degree - 2)) / 6 ; return value ; aggregate: total |
| PM | 3-star | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| PM | 3-star | 8 | True | 1 | 2 | False | True | 1.0085 | True | True | 0.0199 | - | 0.1237 | 0.0009933 | projected_neighbors = project(P, D) ; projected_size = size(projected_neighbors) ; value = projected_size * (projected_size - 1) * (projected_size - 2) / 6 ; return value ; aggregate: total |
| PM | 3-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | name = size(project(P, D)) ; report = comb(name, 3) ; return report ; aggregate: total |
| PM | 5-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | capped_degree = project(P, D) ; count = comb(size(capped_degree), 5) ; return count ; aggregate: total |
| PM | 5-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected_P = project(P, D) ; return comb(size(projected_P), 5) ; aggregate: total |
| PM | 5-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | name = comb(size(project(P, D)), 5) ; return name ; aggregate: total |
| PM | 5-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | name = comb( size(project(P, D)), 5 ) ; return name ; aggregate: total |
| PM | 5-star | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | name = size(project(P, D)) ; report = comb(name, 5) ; return report ; aggregate: total |
| PM | 5-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | name = comb(size(project(P, D)), 5) ; return name ; aggregate: total |
| PM | 5-star | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | projected = project(P, D) ; size_proj = size(projected) ; count = comb(size_proj, 5) ; return count ; aggregate: total |
| PM | 5-star | 7 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | name = comb(size(project(P, D)), 5) ; return name ; aggregate: total |
| PM | 5-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0527 | - | 0.2874 | 0.0000 | clipped_degree = project(P, D) ; return comb(size(clipped_degree), 5) ; aggregate: total |
| PM | 5-star | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 0 | True | 1 | 2 | False | True | 1.5021 | True | True | 0.2506 | - | 1.6929 | 0.6635 | report = sum( size(N(v) & project(P, D)) for v in project(P, D) ) / 2 ; return report ; aggregate: total / 3 |
| PM | triangle | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 4 | True | 1 | 1 | False | True | 1.5021 | True | True | 0.2506 | - | 1.6929 | 0.6635 | P_proj = project(P, D) ; total_ordered = sum( size(P_proj & N(v)) for v in P_proj ) ; count = total_ordered / 2 ; return count ; aggregate: total / 3 |
| PM | triangle | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 6 | True | 1 | 3 | False | True | 1.5021 | True | True | 0.2506 | - | 1.6929 | 0.6635 | projected_P = project(P, D) ; sum_edges = sum( size(N(u) & projected_P) for u in projected_P ) ; count = sum_edges / 2 ; return count ; aggregate: total / 3 |
| PM | triangle | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 8 | True | 1 | 1 | False | True | 1.5021 | True | True | 0.2506 | - | 1.6929 | 0.6635 | P_proj = project(P, D) ; return sum( size(P_proj & N(v)) for v in P_proj ) ; aggregate: total / 6 |
| PM | triangle | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 0 | True | 1 | 2 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | s = size(project(P, D)) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 1 | True | 1 | 1 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | name = size(project(P, D)) ; return name * name ; aggregate: total |
| PM | degree-moment2 | 2 | True | 1 | 1 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | size_p = size(project(P, D)) ; return size_p * size_p ; aggregate: total |
| PM | degree-moment2 | 3 | True | 1 | 1 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | name = project(P, D) ; return size(name) * size(name) ; aggregate: total |
| PM | degree-moment2 | 4 | True | 1 | 1 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | s = size(project(P, D)) ; report = s * s ; return report ; aggregate: total |
| PM | degree-moment2 | 5 | True | 1 | 2 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | s = project(P, D) ; return size(s) * size(s) ; aggregate: total |
| PM | degree-moment2 | 6 | True | 1 | 2 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | projected = project(P, D) ; degree = size(projected) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 7 | True | 1 | 1 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 8 | True | 1 | 2 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | s = size(project(P, D)) ; report = s * s ; return report ; aggregate: total |
| PM | degree-moment2 | 9 | True | 1 | 1 | False | True | 1.0042 | True | True | 0.0062 | - | 0.0435 | 0.0001752 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
