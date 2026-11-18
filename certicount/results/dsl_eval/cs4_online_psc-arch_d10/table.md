# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 10 independent design(s), 3 draft(s) x up to 1 restart(s), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = PSC, noise-aware gate on (τ = 2, 8 releases per graph).

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: derived GS / reference GS at the design-time bound D = min(n−1, 10); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 10 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 5 | 0.6000 | 0.9000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0250 |
| PM | 2-star | 10 | 0.9000 | 0.9000 | 0.6000 | 1.3333 | 1.0000 | 1.5000 | 7 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0123 | 1.1111 | 1.0005 |
| PM | 3-star | 10 | 1.0000 | 1.0000 | 0.2000 | 2.1000 | 1.0000 | 2.1000 | 9 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.1000 | 1.2500 | 1.0034 |
| PM | triangle | 10 | 0.2000 | 0.2000 | 0.0000 | 2.0000 | 1.0000 | 2.8000 | 2 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.5556 | 1.5556 | 1.5021 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | degree | 0.0030 | 0.0030 | 0.0030 | 4.896e-05 | 0.0004896 | 0.9000 | 0.0000 |
| PM | 2-star | 0.0443 | 0.0443 | 0.0443 | 1.997e-05 | 0.0001797 | 0.8889 | 0.0000 |
| PM | 3-star | 0.1231 | 0.1227 | 0.1227 | 0.0003973 | 0.0009933 | 0.6000 | 0.0000 |
| PM | triangle | 1.6929 | 1.6929 | 1.0295 | 0.6635 | 0.6635 | 0.0000 | 0.0500 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 0 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | degree = size(P) ; return degree ; aggregate: total / n |
| PM | degree | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | size_P = size(P) ; return size_P ; aggregate: total / n |
| PM | degree | 3 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 4 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 5 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0000 | - | 0.0035 | 0.0004896 | size_p = size(project(P, D)) ; return size_p ; aggregate: total / n |
| PM | degree | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | name = size(P) ; return name ; aggregate: total / n |
| PM | degree | 7 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 8 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 9 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | 2-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0068 | - | 0.0443 | 0.0000 | name = comb(size(project(P, D)), 2) ; return name ; aggregate: total |
| PM | 2-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0068 | - | 0.0443 | 0.0000 | size_p = size(project(P, D)) ; return comb(size_p, 2) ; aggregate: total |
| PM | 2-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0068 | - | 0.0443 | 0.0000 | projected = project(P, D) ; count = comb(size(projected), 2) ; return count ; aggregate: total |
| PM | 2-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0068 | - | 0.0443 | 0.0000 | name = comb(size(project(P, D)), 2) ; return name ; aggregate: total |
| PM | 2-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0068 | - | 0.0443 | 0.0000 | projected_p = project(P, D) ; value = comb(size(projected_p), 2) ; return value ; aggregate: total |
| PM | 2-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0068 | - | 0.0443 | 0.0000 | name = size(project(P, D)) ; return comb(name, 2) ; aggregate: total |
| PM | 2-star | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0068 | - | 0.0443 | 0.0000 | name = comb(size(project(P, D)), 2) ; return name ; aggregate: total |
| PM | 2-star | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 2-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0068 | - | 0.0443 | 0.0000 | name = project(P, D) ; return comb(size(name), 2) ; aggregate: total |
| PM | 2-star | 9 | True | 1 | 2 | False | True | 1.0043 | True | True | 0.0068 | - | 0.0445 | 0.0001797 | name = (size(project(P, D)) * (size(project(P, D)) - 1)) / 2 ; return name ; aggregate: total |
| PM | 3-star | 0 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | bounded_P = project(P, D) ; name = comb(size(bounded_P), 3) ; return name ; aggregate: total |
| PM | 3-star | 1 | True | 1 | 2 | False | True | 1.0085 | True | True | 0.0199 | - | 0.1237 | 0.0009933 | projected_P = project(P, D) ; d = size(projected_P) ; return d * (d - 1) * (d - 2) / 6 ; aggregate: total |
| PM | 3-star | 2 | True | 1 | 2 | False | True | 1.0085 | True | True | 0.0199 | - | 0.1237 | 0.0009933 | projected_degree = project(P, D) ; degree = size(projected_degree) ; return degree * (degree - 1) * (degree - 2) / 6 ; aggregate: total |
| PM | 3-star | 3 | True | 1 | 2 | False | True | 1.0085 | True | True | 0.0199 | - | 0.1237 | 0.0009933 | degree = size(project(P, D)) ; return degree * (degree - 1) * (degree - 2) / 6 ; aggregate: total |
| PM | 3-star | 4 | True | 1 | 1 | False | True | 1.0085 | True | True | 0.0199 | - | 0.1237 | 0.0009933 | projected_P = project(P, D) ; degree = size(projected_P) ; count = degree * (degree - 1) * (degree - 2) / 6 ; return count ; aggregate: total |
| PM | 3-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | projected_P = project(P, D) ; count = comb(size(projected_P), 3) ; return count ; aggregate: total |
| PM | 3-star | 6 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | name = project(P, D) ; return comb(size(name), 3) ; aggregate: total |
| PM | 3-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | name = size(project(P, D)) ; count = comb(name, 3) ; return count ; aggregate: total |
| PM | 3-star | 8 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | name = size(project(P, D)) ; count = comb(name, 3) ; return count ; aggregate: total |
| PM | 3-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0199 | - | 0.1227 | 0.0000 | name = size(project(P, D)) ; return comb(name, 3) ; aggregate: total |
| PM | triangle | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 2 | True | 1 | 2 | False | True | 1.5021 | True | True | 0.2506 | - | 1.6929 | 0.6635 | P_projected = project(P, D) ; sum_edges = sum(size(N(v) & P_projected) for v in P_projected) ; edges_between_neighbors = sum_edges / 2 ; return edges_between_neighbors ; aggregate: total / 3 |
| PM | triangle | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 5 | True | 1 | 2 | False | True | 1.5021 | True | True | 0.2506 | - | 1.6929 | 0.6635 | S = project(P, D) ; sum_edges = sum( size(N(v) & S) for v in S ) ; return sum_edges / 2 ; aggregate: total / 3 |
| PM | triangle | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
