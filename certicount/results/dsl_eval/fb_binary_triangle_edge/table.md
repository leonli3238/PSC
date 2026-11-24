# DSL design evaluation (goal 2: error added by the LLM designer)

designer = vllm / Qwen3-8B, temperature = 0.6, 30 independent design(s), 3 draft(s) x up to 1 restart(s) per release (rows, matrix), selection simulated (public Holme-Kim graphs, average degrees 4,8,16, 8 releases each, never chosen at a score >= 1; run-time choice on Chung-Lu graphs of the published noisy degrees), own-row check on, tighten 0, early stop off, normalisation on, feedback binary, prompt generic (core generic, 62a207c03a9c4864), ε = 2.0, 20 runs per design (noise of run i: seed [0, i]), mechanism = floor_tight, architecture = per-node (edge clipping + unbiased matrix A, α = 5), noise-aware gate off.

`noise_free_pass` / `noise_free_bias`: the gate's statistic for every accepted design (median relative error of the estimate through the real release on public Holme-Kim graphs, final Laplace noise left out; certicount.dsl.noisy_gate), recorded with the gate off too.

## Design quality

`accept_rate`: designs that produced a program; `first_loop_rate`: accepted without a restart; `first_try_rate`: accepted at the first draft. `gs_ratio`: |c|·GS / the reference's at the design-time bound D = min(n−1, 10), c the aggregate's factor (a constant moved between program and aggregate does not count); `noise_ratio`: final noise |c|·GS/ε3 over the reference's, per run; `semantic_pass`: independent utility test; `sound`: no falsifier counterexample.

| dataset | task | designs | accept_rate | accept_ci95 | first_loop_rate | first_try_rate | mean_iterations | mean_restarts | mean_llm_calls | distinct_programs | same_as_reference | split_match | semantic_pass | sound | noise_free_pass | gs_ratio | gs_ratio_max | noise_ratio | mean_candidates | runs_matrix | runs_rows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | triangle-edge | 30 | 0.3000 | [0.17, 0.48] | 0.3000 | 0.1000 | 2.0000 | 1.0000 | 5.6333 | 9 | 0.0000 | 0.4444 | 1.0000 | 1.0000 | 1.0000 | 1.0444 | 1.2000 | 0.9794 | 0.3000 | 0.4444 | 0.5556 |
| ML | triangle-edge | 30 | 0.3000 | [0.17, 0.48] | 0.3000 | 0.2000 | 1.4444 | 1.0000 | 5.4667 | 9 | 0.0000 | 0.4444 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9960 | 0.3000 | 0.4444 | 0.5556 |
| EE | triangle-edge | 30 | 0.2667 | [0.14, 0.44] | 0.2667 | 0.0667 | 2.1250 | 1.0000 | 5.7667 | 8 | 0.0000 | 0.7500 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9983 | 0.2667 | 0.7500 | 0.2500 |

## Accuracy (accepted designs, paired with GT-DSL on the same noise)

`design_error` = RE(designed) − RE(GT-DSL), mean over designs and runs (negative: better than the library algorithm); `design_exact`: share of runs whose estimate equals GT-DSL, excluding `both_zero` runs.

| dataset | task | relative_error | median_relative_error | gt_dsl_relative_error | design_error | design_error_max | design_exact | both_zero |
|---|---|---|---|---|---|---|---|---|
| CU | triangle-edge | 0.5506 | 0.5573 | 0.5848 | -0.0343 | 0.0000 | 0.4444 | 0.0889 |
| ML | triangle-edge | 0.3219 | 0.2923 | 0.3589 | -0.0370 | 0.0000 | 0.4444 | 0.0222 |
| EE | triangle-edge | 0.2870 | 0.2859 | 0.2859 | 0.0011 | 0.0042 | 0.7500 | 0.0000 |

## Designs

| dataset | task | design | accepted | restarts | iterations | same_as_reference | split_match | noise_ratio | semantic_pass | sound | noise_free_bias | search_score | relative_error | design_error | program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | triangle-edge | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 2 | True | 1 | 2 | False | False | 0.9921 | True | True | 0.0762 | - | 0.5004 | -0.0844 | projected_neighbors = project(P, D) ; total = sum(clip(size(projected_neighbors & N(v)), 0, 1) for v in projected_neighbors) ; return total ; aggregate: total / 2 |
| CU | triangle-edge | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 12 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2953 | - | 0.5848 | 0.0000 | total = sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; return total ; aggregate: total / 2 |
| CU | triangle-edge | 13 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 15 | True | 1 | 1 | False | False | 0.9190 | True | True | 0.0762 | - | 0.5573 | -0.0275 | return sum( clip( size( P & N(v) ), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| CU | triangle-edge | 16 | True | 1 | 3 | False | False | 0.9921 | True | True | 0.0762 | - | 0.5004 | -0.0844 | return sum(clip(size(project(P, D) & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| CU | triangle-edge | 17 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.2953 | - | 0.5848 | 0.0000 | projected_P = project(P, D) ; return sum( clip( sum( A(v, w) for w in projected_P ), 0, 1 ) for v in projected_P ) ; aggregate: total / 2 |
| CU | triangle-edge | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 20 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.2953 | - | 0.5848 | 0.0000 | projected_neighbors = project(P, D) ; sum_over_v = sum( clip( sum( A(v, w) for w in projected_neighbors ), 0, 1 ) for v in projected_neighbors ) ; return sum_over_v ; aggregate: total / 2 |
| CU | triangle-edge | 21 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.2953 | - | 0.5848 | 0.0000 | projected = project(P, D) ; count = sum( clip( sum( A(v, w) for w in projected ), 0, 1 ) for v in projected ) ; return count ; aggregate: total / 2 |
| CU | triangle-edge | 22 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 23 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 24 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 25 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 26 | True | 1 | 2 | False | False | 0.9190 | True | True | 0.0762 | - | 0.5573 | -0.0275 | return sum(clip(size(P & N(v)), 0, 1) for v in project(P, D)) ; aggregate: total / 2 |
| CU | triangle-edge | 27 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| CU | triangle-edge | 28 | True | 1 | 3 | False | False | 0.9921 | True | True | 0.0762 | - | 0.5004 | -0.0844 | neighbors = project(P, D) ; count = sum(clip(size(neighbors & N(v)), 0, 1) for v in neighbors) ; return count ; aggregate: total / 2 |
| CU | triangle-edge | 29 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 0 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3268 | - | 0.3589 | 0.0000 | projected_neighbors = project(P, D) ; sum_v = sum( clip( sum( A(v, w) for w in projected_neighbors ), 0, 1 ) for v in projected_neighbors ) ; return sum_v ; aggregate: total / 2 |
| ML | triangle-edge | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 2 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3268 | - | 0.3589 | 0.0000 | S = project(P, D) ; sum_v = sum( clip( sum( A(v, w) for w in S ), 0, 1 ) for v in S ) ; return sum_v ; aggregate: total / 2 |
| ML | triangle-edge | 3 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 5 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3268 | - | 0.3589 | 0.0000 | return sum( clip( sum( A(v, w) for w in project(P, D) ), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| ML | triangle-edge | 6 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.3268 | - | 0.3589 | 0.0000 | projected = project(P, D) ; sum_v = sum( clip( sum( A(v, w) for w in projected ), 0, 1 ) for v in projected ) ; return sum_v ; aggregate: total / 2 |
| ML | triangle-edge | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 8 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 9 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 12 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 13 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 14 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 16 | True | 1 | 1 | False | False | 0.9928 | True | True | 0.0380 | - | 0.2923 | -0.0666 | projected = project(P, D) ; return sum(clip(size(projected & N(v)), 0, 1) for v in projected) ; aggregate: total / 2 |
| ML | triangle-edge | 17 | True | 1 | 3 | False | False | 0.9928 | True | True | 0.0380 | - | 0.2923 | -0.0666 | return sum( clip( size( project(P, D) & N(v) ), 0, 1 ) for v in project(P, D) ) ; aggregate: total / 2 |
| ML | triangle-edge | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 19 | True | 1 | 1 | False | False | 0.9928 | True | True | 0.0380 | - | 0.2923 | -0.0666 | S = project(P, D) ; return sum( clip( size( S & N(v) ), 0, 1 ) for v in S ) ; aggregate: total / 2 |
| ML | triangle-edge | 20 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 21 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 22 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 23 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 24 | True | 1 | 1 | False | False | 0.9928 | True | True | 0.0380 | - | 0.2923 | -0.0666 | projected_P = project(P, D) ; sum_val = sum(clip(size(projected_P & N(v)), 0, 1) for v in projected_P) ; return sum_val ; aggregate: total / 2 |
| ML | triangle-edge | 25 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 26 | True | 1 | 2 | False | False | 0.9928 | True | True | 0.0380 | - | 0.2923 | -0.0666 | projected_P = project(P, D) ; return sum(clip(size(projected_P & N(v)), 0, 1) for v in projected_P) ; aggregate: total / 2 |
| ML | triangle-edge | 27 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 28 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| ML | triangle-edge | 29 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 0 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 1 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 2 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 3 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.3153 | - | 0.2859 | 0.0000 | projected_neighbors = project(P, D) ; sum_over_v = sum( clip( sum( A(v, w) for w in projected_neighbors ), 0, 1 ) for v in projected_neighbors ) ; return sum_over_v ; aggregate: total / 2 |
| EE | triangle-edge | 4 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 5 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 6 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 7 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 8 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.3153 | - | 0.2859 | 0.0000 | total = sum(clip(sum(A(v, w) for w in project(P, D)), 0, 1) for v in project(P, D)) ; return total ; aggregate: total / 2 |
| EE | triangle-edge | 9 | True | 1 | 3 | False | False | 0.9933 | True | True | 0.1782 | - | 0.2901 | 0.0042 | projected = project(P, D) ; count = sum(clip(size(N(v) & projected), 0, 1) for v in projected) ; return count ; aggregate: total / 2 |
| EE | triangle-edge | 10 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 11 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 12 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 13 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 14 | True | 1 | 1 | False | False | 0.9933 | True | True | 0.1782 | - | 0.2901 | 0.0042 | P_proj = project(P, D) ; return sum(clip(size(P_proj & N(v)), 0, 1) for v in P_proj) ; aggregate: total / 2 |
| EE | triangle-edge | 15 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 16 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 17 | True | 1 | 3 | False | True | 1.0000 | True | True | 0.3153 | - | 0.2859 | 0.0000 | P_proj = project(P, D) ; count = sum(clip(sum(A(v, w) for w in P_proj), 0, 1) for v in P_proj) ; return count ; aggregate: total / 2 |
| EE | triangle-edge | 18 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 19 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 20 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 21 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 22 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 23 | True | 1 | 1 | False | True | 1.0000 | True | True | 0.3153 | - | 0.2859 | 0.0000 | P_proj = project(P, D) ; sum_over_v = sum( clip( sum( A(v, w) for w in P_proj ), 0, 1 ) for v in P_proj ) ; return sum_over_v ; aggregate: total / 2 |
| EE | triangle-edge | 24 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 25 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 26 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.3153 | - | 0.2859 | 0.0000 | proj = project(P, D) ; sum_clip = sum( clip( sum( A(v, w) for w in proj ), 0, 1 ) for v in proj ) ; return sum_clip ; aggregate: total / 2 |
| EE | triangle-edge | 27 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 28 | False | 1 | 3 | - | - | - | - | - | - | - | - | - | - |
| EE | triangle-edge | 29 | True | 1 | 2 | False | True | 1.0000 | True | True | 0.3153 | - | 0.2859 | 0.0000 | projected_neighbors = project(P, D) ; count = sum( clip( sum( A(v, w) for w in projected_neighbors ), 0, 1 ) for v in projected_neighbors ) ; return count ; aggregate: total / 2 |
