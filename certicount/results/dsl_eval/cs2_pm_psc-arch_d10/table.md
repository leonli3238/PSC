# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 10 independent design(s), 3 draft(s) x up to 1 restart(s), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = PSC.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: derived GS / reference GS at the design-time bound D = min(n−1, 10); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | gs_ratio | gs_ratio_max | noise_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 10 | 1.0000 | 1.0000 | 0.9000 | 1.1000 | 1.0000 | 1.1000 | 6 | 0.5000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| PM | 2-star | 10 | 1.0000 | 1.0000 | 0.4000 | 1.9000 | 1.0000 | 1.9000 | 8 | 0.0000 | 0.8000 | 1.0000 | 1.0000 | 5.8222 | 50.2222 | 0.9537 |
| PM | 3-star | 10 | 0.9000 | 0.9000 | 0.8000 | 1.1111 | 1.0000 | 1.3000 | 9 | 0.0000 | 0.5556 | 1.0000 | 1.0000 | 315.1698 | 2831.2778 | 0.8854 |
| PM | triangle | 10 | 0.8000 | 0.8000 | 0.4000 | 1.7500 | 1.0000 | 2.0000 | 8 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 0.8056 | 3.3333 | 0.5638 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|
| PM | degree | 0.0030 | 0.0030 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| PM | 2-star | 4.4644 | 0.0443 | 4.4201 | 44.1755 | 0.8000 | 0.0000 |
| PM | 3-star | 14.7504 | 0.1227 | 14.6277 | 43.8013 | 0.4444 | 0.0000 |
| PM | triangle | 63.6189 | 1.0295 | 62.5894 | 99.7438 | 0.0000 | 0.0188 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.0030 | 0.0000 | s = size(P) ; return s ; aggregate: total / n |
| PM | degree | 1 | True | 1 | 1 | True | True | 1.0000 | True | True | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 2 | True | 1 | 1 | True | True | 1.0000 | True | True | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.0030 | 0.0000 | size_P = size(P) ; return size_P ; aggregate: total / n |
| PM | degree | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.0030 | 0.0000 | report = size(P) ; return report ; aggregate: total / n |
| PM | degree | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.0030 | 0.0000 | name = size(P) ; return name ; aggregate: total / n |
| PM | degree | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.0030 | 0.0000 | size_p = size(P) ; return size_p ; aggregate: total / n |
| PM | degree | 7 | True | 1 | 1 | True | True | 1.0000 | True | True | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 8 | True | 1 | 1 | True | True | 1.0000 | True | True | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 9 | True | 1 | 1 | True | True | 1.0000 | True | True | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | 2-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.0443 | 0.0000 | name = comb(size(project(P, D)), 2) ; return name ; aggregate: total |
| PM | 2-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.0443 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 2) ; aggregate: total |
| PM | 2-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.0443 | 0.0000 | name = comb(size(project(P, D)), 2) ; return name ; aggregate: total |
| PM | 2-star | 3 | True | 1 | 1 | False | False | 1.5370 | True | True | - | 0.0693 | 0.0250 | name = size(P) ; return name * (name - 1) / 2 ; aggregate: total |
| PM | 2-star | 4 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 44.2198 | 44.1755 | name = comb(size(N(self)), 2) ; return name ; aggregate: total |
| PM | 2-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.0443 | 0.0000 | projected = project(P, D) ; count = comb(size(projected), 2) ; return count ; aggregate: total |
| PM | 2-star | 6 | True | 1 | 3 | False | True | 1.0000 | True | True | - | 0.0443 | 0.0000 | k = size(project(P, D)) ; result = comb(k, 2) ; return result ; aggregate: total |
| PM | 2-star | 7 | True | 1 | 3 | False | True | 1.0000 | True | True | - | 0.0443 | 0.0000 | k_proj = project(P, D) ; k = size(k_proj) ; return comb(k, 2) ; aggregate: total |
| PM | 2-star | 8 | True | 1 | 3 | False | True | 1.0000 | True | True | - | 0.0443 | 0.0000 | name = comb(size(project(P, D)), 2) ; return name ; aggregate: total |
| PM | 2-star | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.0443 | 0.0000 | degree_capped = project(P, D) ; count = comb(size(degree_capped), 2) ; return count ; aggregate: total |
| PM | 3-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.1227 | 0.0000 | s = size(project(P, D)) ; name = comb(s, 3) ; return name ; aggregate: total |
| PM | 3-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.1227 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.1227 | 0.0000 | d_proj = size(project(P, D)) ; three_stars = comb(d_proj, 3) ; return three_stars ; aggregate: total |
| PM | 3-star | 3 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 43.9240 | 43.8013 | name = comb(size(N(self)), 3) ; return name ; aggregate: total |
| PM | 3-star | 4 | True | 1 | 1 | False | True | 1.0085 | True | True | - | 0.1237 | 0.0009933 | d = size(project(P, D)) ; return d * (d - 1) * (d - 2) / 6 ; aggregate: total |
| PM | 3-star | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 6 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 43.9240 | 43.8013 | name = size(project(N(self), D)) ; return name * (name - 1) * (name - 2) / 6 ; aggregate: total |
| PM | 3-star | 7 | True | 1 | 1 | False | False | 2.9599 | True | True | - | 0.3669 | 0.2442 | degree = size(P) ; stars = degree * (degree - 1) * (degree - 2) / 6 ; return stars ; aggregate: total |
| PM | 3-star | 8 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 43.9240 | 43.8013 | name = size(N(self)) ; return comb(name, 3) ; aggregate: total |
| PM | 3-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.1227 | 0.0000 | name = comb(size(project(P, D)), 3) ; return name ; aggregate: total |
| PM | triangle | 0 | True | 1 | 1 | False | True | 0.0000 | True | True | - | 100.7733 | 99.7438 | projected_neighbors = project(N(self), D) ; sum_v = sum( size(projected_neighbors & N(v)) for v in projected_neighbors ) ; edges_between_neighbors = sum_v / 2 ; return edges_between_neighbors ; aggregate: total / 3 |
| PM | triangle | 1 | True | 1 | 1 | False | True | 1.5021 | True | True | - | 1.6929 | 0.6635 | projected_P = project(P, D) ; edges = sum( size( N(v) & projected_P ) for v in projected_P ) ; return edges / 2 ; aggregate: total / 3 |
| PM | triangle | 2 | True | 1 | 3 | False | True | 0.0000 | True | True | - | 100.7733 | 99.7438 | name = sum(size(N(a) & N(self)) for a in N(self)) ; return name / 2 ; aggregate: total / 3 |
| PM | triangle | 3 | True | 1 | 2 | False | True | 0.0000 | True | True | - | 100.7733 | 99.7438 | sum_edges = sum( size(N(u) & N(self)) for u in N(self) ) ; count = sum_edges / 2 ; return count ; aggregate: total / 3 |
| PM | triangle | 4 | True | 1 | 1 | False | True | 1.5063 | True | True | - | 1.6991 | 0.6696 | neighbors = project(P, D) ; sum_val = sum( size(N(v) & P) for v in neighbors ) ; return sum_val ; aggregate: total / 6 |
| PM | triangle | 5 | True | 1 | 3 | False | True | 1.5021 | True | True | - | 1.6929 | 0.6635 | projected_P = project(P, D) ; inner_sum = sum( size(projected_P & N(v)) for v in projected_P ) ; return inner_sum / 2 ; aggregate: total / 3 |
| PM | triangle | 6 | True | 1 | 1 | False | True | 0.0000 | True | True | - | 100.7733 | 99.7438 | s = project(N(self), D) ; sum_val = sum( size(N(v) & s) for v in s ) ; return sum_val / 2 ; aggregate: total / 3 |
| PM | triangle | 7 | True | 1 | 2 | False | True | 0.0000 | True | True | - | 100.7733 | 99.7438 | neighbors = project(N(self), D) ; count = sum( size(N(self) & N(u)) for u in neighbors ) ; return count ; aggregate: total / 6 |
| PM | triangle | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - |
| PM | triangle | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - |
