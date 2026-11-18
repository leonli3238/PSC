# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 10 independent design(s), 3 draft(s) x up to 1 restart(s), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate on (τ = 2, 8 releases per graph).

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: derived GS / reference GS at the design-time bound D = min(n−1, 10); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 10 | 0.6000 | 0.6000 | 0.5000 | 1.1667 | 1.0000 | 1.9000 | 6 | 0.0000 | 0.5000 | 1.0000 | 1.0000 | 1.0000 | 0.5000 | 1.0000 | 0.5000 |
| PM | 5-star | 10 | 0.8000 | 0.8000 | 0.7000 | 1.2500 | 1.0000 | 1.6000 | 6 | 0.0000 | 0.8750 | 1.0000 | 1.0000 | 1.0000 | 0.8750 | 1.0000 | 0.8750 |
| PM | triangle | 10 | 0.6000 | 0.6000 | 0.5000 | 1.3333 | 1.0000 | 2.0000 | 6 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.5880 | 1.0000 | 1.0003 |
| PM | degree-moment2 | 10 | 0.8000 | 0.8000 | 0.4000 | 1.6250 | 1.0000 | 1.9000 | 7 | 0.1250 | 0.3750 | 1.0000 | 1.0000 | 1.0000 | 2.8075 | 3.8500 | 4.6720 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0.0412 | 0.0412 | 0.0087 | 0.0325 | 0.0650 | 0.5000 | 0.0000 |
| PM | 5-star | 0.0321 | 0.0176 | 0.0176 | 0.0145 | 0.1159 | 0.8750 | 0.0000 |
| PM | triangle | 0.1267 | 0.1263 | 0.1263 | 0.0003872 | 0.0023 | 0.8333 | 0.0000 |
| PM | degree-moment2 | 0.0353 | 0.0519 | 0.0074 | 0.0278 | 0.0445 | 0.1250 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | 3-star | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; count = comb(degree, 3) ; return count ; aggregate: total |
| PM | 3-star | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| PM | 3-star | 5 | True | 1 | 1 | False | False | 0.0000 | True | True | 1.4169 | - | 0.0737 | 0.0650 | name = size(project(N(self), D)) * (size(project(N(self), D)) - 1) * (size(project(N(self), D)) - 2) / 6 ; return name ; aggregate: total |
| PM | 3-star | 6 | True | 1 | 2 | False | False | 0.0000 | True | True | 1.4169 | - | 0.0737 | 0.0650 | name = project(N(self), D) ; return comb(size(name), 3) ; aggregate: total |
| PM | 3-star | 7 | True | 1 | 1 | False | False | 0.0000 | True | True | 1.4169 | - | 0.0737 | 0.0650 | projected = project(N(self), D) ; d = size(projected) ; return d * (d - 1) * (d - 2) / 6 ; aggregate: total |
| PM | 3-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| PM | 3-star | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 5-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | name = size(project(P, D)) ; return comb(name, 5) ; aggregate: total |
| PM | 5-star | 1 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | name = size(project(P, D)) ; return comb(name, 5) ; aggregate: total |
| PM | 5-star | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected_P = project(P, D) ; degree = size(projected_P) ; return comb(degree, 5) ; aggregate: total |
| PM | 5-star | 3 | True | 1 | 1 | False | False | 0.0000 | True | True | 0.4055 | - | 0.1335 | 0.1159 | name = size(project(N(self), D)) ; return comb(name, 5) ; aggregate: total |
| PM | 5-star | 4 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected_P = project(P, D) ; count = comb(size(projected_P), 5) ; return count ; aggregate: total |
| PM | 5-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected_P = project(P, D) ; count = comb(size(projected_P), 5) ; return count ; aggregate: total |
| PM | 5-star | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 5-star | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | name = comb(size(project(P, D)), 5) ; return name ; aggregate: total |
| PM | 5-star | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 5-star | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0139 | - | 0.0176 | 0.0000 | projected = project(P, D) ; size_projected = size(projected) ; return comb(size_projected, 5) ; aggregate: total |
| PM | triangle | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | return sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) / 2 ; aggregate: total / 3 |
| PM | triangle | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_pairs = sum( A(v, w) for v in S for w in S ) ; count = sum_pairs / 2 ; return count ; aggregate: total / 3 |
| PM | triangle | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 4 | True | 1 | 1 | False | True | 1.0021 | True | True | 0.0933 | - | 0.1286 | 0.0023 | S = project(P, D) ; sum_A = sum(A(v, w) for v in S for w in S) ; sum_diag = sum(A(v, v) for v in S) ; return (sum_A - sum_diag) / 2 ; aggregate: total / 3 |
| PM | triangle | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | proj = project(P, D) ; sum_A = sum(A(j, k) for j in proj for k in proj) ; edges = sum_A / 2 ; return edges ; aggregate: total / 3 |
| PM | triangle | 8 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | name = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) / 2 ; return name ; aggregate: total / 3 |
| PM | triangle | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | name = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return name ; aggregate: total / 6 |
| PM | degree-moment2 | 0 | True | 1 | 2 | False | False | 6.8736 | True | True | 0.0514 | - | 0.0519 | 0.0445 | degree = sum(A(self, y) for y in project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 1 | True | 1 | 1 | False | True | 1.0042 | True | True | 0.0140 | - | 0.0075 | 8.795e-05 | s = size(project(P, D)) ; return s * s ; aggregate: total |
| PM | degree-moment2 | 2 | True | 1 | 1 | False | False | 6.8736 | True | True | 0.0514 | - | 0.0519 | 0.0445 | degree = sum(A(self, j) for j in project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 3 | True | 1 | 1 | False | False | 6.8736 | True | True | 0.0514 | - | 0.0519 | 0.0445 | sum_A = sum(A(self, y) for y in project(P, D)) ; return sum_A * sum_A ; aggregate: total |
| PM | degree-moment2 | 4 | True | 1 | 3 | False | False | 6.8736 | True | True | 0.0514 | - | 0.0519 | 0.0445 | degree = sum(A(self, y) for y in project(P, D)) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree-moment2 | 6 | True | 1 | 2 | True | True | 1.0000 | True | True | 0.0140 | - | 0.0074 | 0.0000 | return pow(size(project(P, D)), 2) ; aggregate: total |
| PM | degree-moment2 | 7 | True | 1 | 1 | False | True | 1.0042 | True | True | 0.0140 | - | 0.0075 | 8.795e-05 | projected = project(P, D) ; degree = size(projected) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 8 | True | 1 | 2 | False | False | 6.8736 | True | True | 0.0514 | - | 0.0519 | 0.0445 | projected = project(P, D) ; degree = sum(A(self, j) for j in projected) ; return degree * degree ; aggregate: total |
| PM | degree-moment2 | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
