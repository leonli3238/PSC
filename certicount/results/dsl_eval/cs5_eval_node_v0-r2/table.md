# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 10 independent design(s), 3 draft(s) x up to 2 restart(s), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate on (τ = 2, 8 releases per graph).

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: derived GS / reference GS at the design-time bound D = min(n−1, 10); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 10 | 1.0000 | 0.9000 | 0.3000 | 2.0000 | 1.1000 | 2.3000 | 10 | 0.0000 | 0.4000 | 1.0000 | 1.0000 | 1.0000 | 1.1852 | 7.6016 | 1.4962 |
| PM | 5-star | 10 | 1.0000 | 0.8000 | 0.2000 | 1.8000 | 1.2000 | 2.4000 | 8 | 0.2000 | 0.7000 | 1.0000 | 1.0000 | 1.0000 | 0.7000 | 1.0000 | 0.7000 |
| PM | triangle | 10 | 1.0000 | 0.7000 | 0.4000 | 1.6000 | 1.3000 | 2.5000 | 10 | 0.0000 | 0.8000 | 1.0000 | 1.0000 | 1.0000 | 0.5719 | 1.0000 | 0.9385 |
| PM | degree-moment2 | 10 | 0.9000 | 0.4000 | 0.3000 | 1.3333 | 1.6000 | 3.3000 | 8 | 0.0000 | 0.2222 | 1.0000 | 1.0000 | 1.0000 | 3.2400 | 3.8500 | 5.5693 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0.0524 | 0.0737 | 0.0087 | 0.0436 | 0.1115 | 0.3000 | 0.0000 |
| PM | 5-star | 0.0523 | 0.0176 | 0.0176 | 0.0348 | 0.1159 | 0.7000 | 0.0000 |
| PM | triangle | 0.4069 | 0.1263 | 0.1263 | 0.2807 | 1.4033 | 0.8000 | 0.0000 |
| PM | degree-moment2 | 0.0420 | 0.0519 | 0.0074 | 0.0346 | 0.0445 | 0.0000 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | deg = size(project(P, D)) ; return comb(deg, 3) ; aggregate: total |
| PM | 3-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| PM | 3-star | 2 | True | 1 | 3 | False | False | 0.0000 | True | True | 1.4169 | - | 0.0737 | 0.0650 | report = comb(size(project(N(self), D)), 3) ; return report ; aggregate: total |
| PM | 3-star | 3 | True | 1 | 2 | False | True | 1.0084 | True | True | 0.0146 | - | 0.0088 | 5.879e-05 | degree = size(project(P, D)) ; return degree * (degree - 1) * (degree - 2) / 6 ; aggregate: total |
| PM | 3-star | 4 | True | 1 | 1 | False | False | 0.0000 | True | True | 1.4169 | - | 0.0737 | 0.0650 | projected = project(N(self), D) ; d = size(projected) ; count = comb(d, 3) ; return count ; aggregate: total |
| PM | 3-star | 5 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_P = project(P, D) ; return comb(size(projected_P), 3) ; aggregate: total |
| PM | 3-star | 6 | True | 2 | 2 | False | False | 0.0000 | True | True | 1.4169 | - | 0.0737 | 0.0650 | name = clip(size(N(self)), 0, D) ; return comb(name, 3) ; aggregate: total |
| PM | 3-star | 7 | True | 1 | 3 | False | False | 10.9534 | True | True | 0.1845 | - | 0.1202 | 0.1115 | projected_neighbors = project(P, D) ; degree_estimate = sum(A(self, v) for v in projected_neighbors) ; count = degree_estimate * (degree_estimate - 1) * (degree_estimate - 2) / 6 ; return count ; aggregate: total |
| PM | 3-star | 8 | True | 1 | 1 | False | False | 0.0000 | True | True | 1.4169 | - | 0.0737 | 0.0650 | count = comb(size(project(N(self), D)), 3) ; return count ; aggregate: total |
| PM | 3-star | 9 | True | 1 | 3 | False | False | 0.0000 | True | True | 1.4169 | - | 0.0737 | 0.0650 | name = comb(size(project(N(self), D)), 3) ; return name ; aggregate: total |
| PM | 5-star | 0 | True | 2 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected_P = project(P, D) ; count = comb(size(projected_P), 5) ; return count ; aggregate: total |
| PM | 5-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | name = comb(size(project(P, D)), 5) ; return name ; aggregate: total |
| PM | 5-star | 2 | True | 1 | 3 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 3 | True | 2 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | degree = size(project(P, D)) ; count = comb(degree, 5) ; return count ; aggregate: total |
| PM | 5-star | 4 | True | 1 | 2 | False | False | 0.0000 | True | True | 0.4055 | - | 0.1335 | 0.1159 | size_n = size(N(self)) ; projected_size = min(size_n, D) ; count = comb(projected_size, 5) ; return count ; aggregate: total |
| PM | 5-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | size_proj = size(project(P, D)) ; return comb(size_proj, 5) ; aggregate: total |
| PM | 5-star | 6 | True | 1 | 3 | True | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | return comb(size(project(P, D)), 5) ; aggregate: total |
| PM | 5-star | 7 | True | 1 | 2 | False | False | 0.0000 | True | True | 0.4055 | - | 0.1335 | 0.1159 | name = comb(size(project(N(self), D)), 5) ; return name ; aggregate: total |
| PM | 5-star | 8 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | name = comb(size(project(P, D)), 5) ; return name ; aggregate: total |
| PM | 5-star | 9 | True | 1 | 2 | False | False | 0.0000 | True | True | 0.4055 | - | 0.1335 | 0.1159 | name = project(N(self), D) ; result = comb(size(name), 5) ; return result ; aggregate: total |
| PM | triangle | 0 | True | 2 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | projected = project(P, D) ; sum_A = sum( A(v, w) for v in projected for w in projected ) ; edges = sum_A / 2 ; return edges ; aggregate: total / 3 |
| PM | triangle | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | name = project(P, D) ; sum_A = sum( A(v, w) for v in name for w in name ) ; return sum_A / 2 ; aggregate: total / 3 |
| PM | triangle | 2 | True | 2 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | P_proj = project(P, D) ; return sum( A(v, w) for v in P_proj for w in P_proj ) ; aggregate: total / 6 |
| PM | triangle | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_A = sum( A(v, w) for v in S for w in S ) ; return sum_A / 2 ; aggregate: total / 3 |
| PM | triangle | 4 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | projected = project(P, D) ; sum_edges = sum( sum( A(i, k) for k in projected ) for i in projected ) / 2 ; return sum_edges ; aggregate: total / 3 |
| PM | triangle | 5 | True | 1 | 1 | False | False | 0.6924 | True | True | 0.2248 | - | 1.5296 | 1.4033 | name = project(P, D) ; count = sum( size(N(v) & name) for v in name ) ; return count / 2 ; aggregate: total / 3 |
| PM | triangle | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | name = sum( A(v, w) for v in project(P, D) for w in project(P, D) ) ; return name / 2 ; aggregate: total / 3 |
| PM | triangle | 7 | True | 1 | 1 | False | False | 0.6924 | True | True | 0.2248 | - | 1.5296 | 1.4033 | S = project(P, D) ; sum_size = sum( size(N(v) & S) for v in S ) ; return sum_size / 2 ; aggregate: total / 3 |
| PM | triangle | 8 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | name = sum( A(v, w) for v in project(P, D) for w in project(P, D) ) ; return name ; aggregate: total / 6 |
| PM | triangle | 9 | True | 2 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; return sum(A(v, w) for v in S for w in S) / 2 ; aggregate: total / 3 |
| PM | degree-moment2 | 0 | True | 1 | 1 | False | False | 6.8736 | True | True | 0.0514 | - | 0.0519 | 0.0445 | projected_neighbors = project(P, D) ; degree_estimate = sum( A(self, y) for y in projected_neighbors ) ; squared_degree = degree_estimate * degree_estimate ; return squared_degree ; aggregate: total |
| PM | degree-moment2 | 1 | True | 2 | 3 | False | False | 6.8736 | True | True | 0.0514 | - | 0.0519 | 0.0445 | name = sum(A(self, j) for j in project(P, D)) ; return name * name ; aggregate: total |
| PM | degree-moment2 | 2 | True | 2 | 1 | False | True | 1.0042 | True | True | 0.0140 | - | 0.0075 | 8.795e-05 | name = size(project(P, D)) ; return name * name ; aggregate: total |
| PM | degree-moment2 | 3 | True | 2 | 1 | False | False | 6.8736 | True | True | 0.0514 | - | 0.0519 | 0.0445 | s = sum(A(self, j) for j in project(P, D)) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 4 | True | 1 | 2 | False | False | 6.8736 | True | True | 0.0514 | - | 0.0519 | 0.0445 | name = sum(A(self, y) for y in project(P, D)) ; return name * name ; aggregate: total |
| PM | degree-moment2 | 5 | True | 2 | 1 | False | True | 1.0042 | True | True | 0.0140 | - | 0.0075 | 8.795e-05 | projected = project(P, D) ; degree = size(projected) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 6 | False | 2 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 7 | True | 2 | 1 | False | False | 6.8736 | True | True | 0.0514 | - | 0.0519 | 0.0445 | s = sum(A(self, y) for y in project(P, D)) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 8 | True | 1 | 1 | False | False | 6.8736 | True | True | 0.0514 | - | 0.0519 | 0.0445 | sum_A = sum(A(self, y) for y in project(P, D)) ; return sum_A * sum_A ; aggregate: total |
| PM | degree-moment2 | 9 | True | 1 | 1 | False | False | 6.8736 | True | True | 0.0514 | - | 0.0519 | 0.0445 | sum_A = sum(A(self, y) for y in project(P, D)) ; return sum_A * sum_A ; aggregate: total |
