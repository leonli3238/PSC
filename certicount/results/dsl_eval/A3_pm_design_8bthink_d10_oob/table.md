# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 10 independent design(s), 3 draft(s) x up to 1 restart(s), ε = 2.0, 10 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: derived GS / reference GS at the design-time bound D = min(n−1, 10); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | gs_ratio | gs_ratio_max | noise_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 4-star | 10 | 0.9000 | 0.9000 | 0.2000 | 1.7778 | 1.0000 | 1.9000 | 7 | 0.1111 | 0.8889 | 1.0000 | 1.0000 | 0.8889 | 1.0000 | 0.8889 |
| PM | 5-star | 10 | 0.9000 | 0.9000 | 0.4000 | 1.5556 | 1.0000 | 1.7000 | 8 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| PM | degree-moment2 | 10 | 1.0000 | 1.0000 | 0.6000 | 1.5000 | 1.0000 | 1.5000 | 9 | 0.0000 | 0.7000 | 1.0000 | 1.0000 | 15.0632 | 47.6316 | 1.1586 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|
| PM | 4-star | 3.4785 | 0.1531 | 3.3254 | 29.9282 | 0.8889 | 0.0000 |
| PM | 5-star | 0.2142 | 0.2142 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| PM | degree-moment2 | 0.0445 | 0.0312 | 0.0134 | 0.0442 | 0.0000 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 4-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.1531 | 0.0000 | name = comb(size(project(P, D)), 4) ; return name ; aggregate: total |
| PM | 4-star | 1 | True | 1 | 1 | False | False | 0.0000 | True | True | - | 30.0813 | 29.9282 | name = comb(size(N(self)), 4) ; return name ; aggregate: total |
| PM | 4-star | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - |
| PM | 4-star | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.1531 | 0.0000 | projected_degree = project(P, D) ; size_projected = size(projected_degree) ; count = comb(size_projected, 4) ; return count ; aggregate: total |
| PM | 4-star | 4 | True | 1 | 2 | True | True | 1.0000 | True | True | - | 0.1531 | 0.0000 | return comb(size(project(P, D)), 4) ; aggregate: total |
| PM | 4-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.1531 | 0.0000 | name = size(project(P, D)) ; count = comb(name, 4) ; return count ; aggregate: total |
| PM | 4-star | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.1531 | 0.0000 | count = comb(size(project(P, D)), 4) ; return count ; aggregate: total |
| PM | 4-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.1531 | 0.0000 | name = comb(size(project(P, D)), 4) ; return name ; aggregate: total |
| PM | 4-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.1531 | 0.0000 | name = comb(size(project(P, D)), 4) ; return name ; aggregate: total |
| PM | 4-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.1531 | 0.0000 | projected_degree = size(project(P, D)) ; count = comb(projected_degree, 4) ; return count ; aggregate: total |
| PM | 5-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.2142 | 0.0000 | count = comb(size(project(P, D)), 5) ; return count ; aggregate: total |
| PM | 5-star | 1 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.2142 | 0.0000 | name = comb( size( project(P, D) ), 5 ) ; return name ; aggregate: total |
| PM | 5-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.2142 | 0.0000 | name = comb(size(project(P, D)), 5) ; return name ; aggregate: total |
| PM | 5-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.2142 | 0.0000 | projected_P = project(P, D) ; name = comb(size(projected_P), 5) ; return name ; aggregate: total |
| PM | 5-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.2142 | 0.0000 | projected_neighbors = project(P, D) ; projected_size = size(projected_neighbors) ; return comb(projected_size, 5) ; aggregate: total |
| PM | 5-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.2142 | 0.0000 | name = project(P, D) ; count = comb(size(name), 5) ; return count ; aggregate: total |
| PM | 5-star | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - |
| PM | 5-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | - | 0.2142 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; return comb(degree, 5) ; aggregate: total |
| PM | 5-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.2142 | 0.0000 | name = comb(size(project(P, D)), 5) ; return name ; aggregate: total |
| PM | 5-star | 9 | True | 1 | 2 | False | True | 1.0000 | True | True | - | 0.2142 | 0.0000 | name = project(P, D) ; return comb(size(name), 5) ; aggregate: total |
| PM | degree-moment2 | 0 | True | 1 | 1 | False | False | 1.5190 | True | True | - | 0.0754 | 0.0442 | name = size(P) ; return name * name ; aggregate: total |
| PM | degree-moment2 | 1 | True | 1 | 1 | False | True | 1.0042 | True | True | - | 0.0313 | 0.0001207 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 2 | True | 1 | 1 | False | True | 1.0042 | True | True | - | 0.0313 | 0.0001207 | projected_P = project(P, D) ; s = size(projected_P) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 3 | True | 1 | 1 | False | False | 1.5190 | True | True | - | 0.0754 | 0.0442 | s = size(P) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 4 | True | 1 | 1 | False | True | 1.0042 | True | True | - | 0.0313 | 0.0001207 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 5 | True | 1 | 2 | False | True | 1.0042 | True | True | - | 0.0313 | 0.0001207 | clipped_size = size(project(P, D)) ; return clipped_size * clipped_size ; aggregate: total |
| PM | degree-moment2 | 6 | True | 1 | 1 | False | False | 1.5190 | True | True | - | 0.0754 | 0.0442 | degree = size(P) ; report = degree * degree ; return report ; aggregate: total |
| PM | degree-moment2 | 7 | True | 1 | 2 | False | True | 1.0042 | True | True | - | 0.0313 | 0.0001207 | projected_P = project(P, D) ; return size(projected_P) * size(projected_P) ; aggregate: total |
| PM | degree-moment2 | 8 | True | 1 | 3 | False | True | 1.0042 | True | True | - | 0.0313 | 0.0001207 | d_proj = project(P, D) ; d_proj_size = size(d_proj) ; return d_proj_size * d_proj_size ; aggregate: total |
| PM | degree-moment2 | 9 | True | 1 | 2 | False | True | 1.0042 | True | True | - | 0.0313 | 0.0001207 | s = size(project(P, D)) ; s_squared = s * s ; return s_squared ; aggregate: total |
