# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 10 independent design(s), 3 draft(s) x up to 1 restart(s), ε = 2.0, 100 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate on (τ = 2, 8 releases per graph).

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: derived GS / reference GS at the design-time bound D = min(n−1, 10); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 10 | 0.7000 | 0.7000 | 0.4000 | 1.5714 | 1.0000 | 2.0000 | 6 | 0.2857 | 0.4286 | 1.0000 | 1.0000 | 1.0000 | 1.4988 | 2.1640 | 2.9257 |
| PM | 2-star | 10 | 0.6000 | 0.6000 | 0.2000 | 2.0000 | 1.0000 | 2.4000 | 6 | 0.0000 | 0.8333 | 1.0000 | 1.0000 | 1.0000 | 1.5276 | 3.9436 | 1.9812 |
| PM | 3-star | 10 | 0.9000 | 0.9000 | 0.6000 | 1.5556 | 1.0000 | 1.7000 | 8 | 0.0000 | 0.8889 | 1.0000 | 1.0000 | 1.0000 | 1.7613 | 7.6016 | 2.1069 |
| PM | triangle | 10 | 0.8000 | 0.8000 | 0.4000 | 1.8750 | 1.0000 | 2.1000 | 8 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.6875 | 1.0000 | 1.0000 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| PM | degree | 0.0189 | 0.0080 | 0.0030 | 0.0159 | 0.0354 | 0.4286 | 0.0000 |
| PM | 2-star | 0.0150 | 0.0075 | 0.0074 | 0.0076 | 0.0454 | 0.5000 | 0.0000 |
| PM | 3-star | 0.0211 | 0.0087 | 0.0087 | 0.0124 | 0.1115 | 0.7778 | 0.0000 |
| PM | triangle | 0.1263 | 0.1263 | 0.1263 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PM | degree | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | name = size(P) ; return name ; aggregate: total / n |
| PM | degree | 1 | True | 1 | 1 | False | False | 1.2500 | True | True | 0.0079 | - | 0.0080 | 0.0050 | return size(project(P, D)) ; aggregate: total / n |
| PM | degree | 2 | True | 1 | 2 | False | False | 5.4099 | True | True | 0.0586 | - | 0.0384 | 0.0354 | return sum(A(self, y) for y in project(P, D)) ; aggregate: total / n |
| PM | degree | 3 | True | 1 | 2 | False | False | 5.4099 | True | True | 0.0586 | - | 0.0384 | 0.0354 | name = sum(A(self, j) for j in project(P, D)) ; return name ; aggregate: total / n |
| PM | degree | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | degree | 7 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | degree | 8 | True | 1 | 3 | False | False | 5.4099 | True | True | 0.0586 | - | 0.0384 | 0.0354 | name = sum(A(self, y) for y in project(P, D)) ; return name ; aggregate: total / n |
| PM | degree | 9 | True | 1 | 1 | True | True | 1.0000 | True | True | 0.0000 | - | 0.0030 | 0.0000 | return size(P) ; aggregate: total / n |
| PM | 2-star | 0 | True | 1 | 1 | False | True | 1.0042 | True | True | 0.0144 | - | 0.0075 | 9.104e-05 | projected_neighbors = project(P, D) ; degree = size(projected_neighbors) ; stars = (degree * (degree - 1)) / 2 ; return stars ; aggregate: total |
| PM | 2-star | 1 | True | 1 | 3 | False | False | 6.8789 | True | True | 0.0563 | - | 0.0528 | 0.0454 | name = sum(A(self, y) for y in project(P, D)) ; report = name * (name - 1) / 2 ; return report ; aggregate: total |
| PM | 2-star | 2 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | degree = size(project(P, D)) ; count = comb(degree, 2) ; return count ; aggregate: total |
| PM | 2-star | 3 | True | 1 | 2 | False | True | 1.0042 | True | True | 0.0144 | - | 0.0075 | 9.104e-05 | degree = size(project(P, D)) ; count = degree * (degree - 1) / 2 ; return count ; aggregate: total |
| PM | 2-star | 4 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | projected_P = project(P, D) ; return comb(size(projected_P), 2) ; aggregate: total |
| PM | 2-star | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0144 | - | 0.0074 | 0.0000 | d = size(project(P, D)) ; return comb(d, 2) ; aggregate: total |
| PM | 2-star | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 2-star | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 2-star | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 2-star | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; count = comb(degree, 3) ; return count ; aggregate: total |
| PM | 3-star | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | 3-star | 2 | True | 1 | 1 | False | True | 1.0084 | True | True | 0.0146 | - | 0.0088 | 5.879e-05 | projected_P = project(P, D) ; degree = size(projected_P) ; return degree * (degree - 1) * (degree - 2) / 6 ; aggregate: total |
| PM | 3-star | 3 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected = project(P, D) ; degree = size(projected) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| PM | 3-star | 4 | True | 1 | 3 | False | False | 10.9534 | True | True | 0.1845 | - | 0.1202 | 0.1115 | return (sum(A(self, j) for j in project(P, D)) * (sum(A(self, j) for j in project(P, D)) - 1) * (sum(A(self, j) for j in project(P, D)) - 2)) / 6 ; aggregate: total |
| PM | 3-star | 5 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | k = size(project(P, D)) ; return comb(k, 3) ; aggregate: total |
| PM | 3-star | 6 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_neighbors = project(P, D) ; degree = size(projected_neighbors) ; report = comb(degree, 3) ; return report ; aggregate: total |
| PM | 3-star | 7 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected = project(P, D) ; return comb(size(projected), 3) ; aggregate: total |
| PM | 3-star | 8 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | projected_neighbors = project(P, D) ; degree = size(projected_neighbors) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| PM | 3-star | 9 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0146 | - | 0.0087 | 0.0000 | k = size(project(P, D)) ; return comb(k, 3) ; aggregate: total |
| PM | triangle | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_ordered = sum( sum( A(v, w) for w in S ) for v in S ) ; sum_unordered = sum_ordered / 2 ; return sum_unordered ; aggregate: total / 3 |
| PM | triangle | 1 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | projected_neighbors = project(P, D) ; sum_pairs = sum(A(v, w) for v in projected_neighbors for w in projected_neighbors) ; return sum_pairs / 2 ; aggregate: total / 3 |
| PM | triangle | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_A = sum( A(y, z) for y in S for z in S ) ; return sum_A ; aggregate: total / 6 |
| PM | triangle | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | neighbors = project(P, D) ; sum_pairs = sum( A(v, w) for v in neighbors for w in neighbors ) ; return sum_pairs ; aggregate: total / 6 |
| PM | triangle | 4 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | name = sum(A(v, w) for v in project(P, D) for w in project(P, D)) / 2 ; return name ; aggregate: total / 3 |
| PM | triangle | 5 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | S = project(P, D) ; sum_pairs = sum(A(v, w) for v in S for w in S) ; return sum_pairs ; aggregate: total / 6 |
| PM | triangle | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| PM | triangle | 7 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | sum_pairs = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return sum_pairs / 2 ; aggregate: total / 3 |
| PM | triangle | 8 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.0933 | - | 0.1263 | 0.0000 | return sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) / 2 ; aggregate: total / 3 |
| PM | triangle | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
