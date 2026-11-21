# Degree probe report

## Confirmation sets (each at its own family α)

| model | set | source | pairs | tested | violations | violations_real_count | violation_share_upper95 | eps_lb_max | eps_lb_median | max_delta_llm |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-1.7B | main | screen_top | 40 | 40 | 38 | 33 | 0.991 | 4.2 | 4.11 | 449 |
| Qwen3-1.7B | main_div | screen_top | 40 | 40 | 38 | 27 | 0.991 | 4.21 | 3.63 | 449 |
| Qwen3-1.7B | nodes | nodes | 36 | 36 | 31 | 29 | 0.944 | 4.01 | 3.51 | 437 |
| Qwen3-1.7B | random | random_ref | 60 | 60 | 7 | 7 | 0.208 | 3.64 | 0.918 | 395 |
| Qwen3-8B | main_div | screen_top | 40 | 40 | 24 | 20 | 0.731 | 4.19 | 3.25 | 406 |
| Qwen3-8B | nodes | nodes | 20 | 20 | 15 | 15 | 0.896 | 4.3 | 2.94 | 332 |
| Qwen3-8B | random | random_ref | 60 | 60 | 4 | 4 | 0.146 | 3.51 | 1.09 | 41 |
| Qwen3-8B | transfer | confirmed | 38 | 38 | 8 | 8 | 0.348 | 2.42 | 0 | 352 |

## Joint Bonferroni over the sets (family α = 0.05, scope = all)

Every tested pair of the scope is re-bounded at α/M from its stored evaluation counts (the test was chosen on selection trials only); these are the numbers for a single joint claim.

| scope | M | alpha_pair | violations_family | violations_family_real_count |
|---|---|---|---|---|
| all | 334 | 0.00015 | 163 | 141 |

| scope | set | tested | violations_design | violations_family | violations_family_real_count | eps_lb_family_max |
|---|---|---|---|---|---|---|
| all | Qwen3-1.7B/main | 40 | 38 | 38 | 33 | 3.94 |
| all | Qwen3-1.7B/main_div | 40 | 38 | 38 | 27 | 3.95 |
| all | Qwen3-1.7B/nodes | 36 | 31 | 31 | 29 | 3.74 |
| all | Qwen3-1.7B/random | 60 | 7 | 7 | 7 | 3.44 |
| all | Qwen3-8B/main_div | 40 | 24 | 24 | 20 | 3.93 |
| all | Qwen3-8B/nodes | 20 | 15 | 14 | 14 | 3.95 |
| all | Qwen3-8B/random | 60 | 4 | 4 | 4 | 3.3 |
| all | Qwen3-8B/transfer | 38 | 8 | 7 | 7 | 2.29 |

## Node level

| model | set | bin | nodes | with_candidate | tested | confirmed | confirmed_share |
|---|---|---|---|---|---|---|---|
| Qwen3-1.7B | nodes | 1-10 | 12 | 0 | 0 | 0 | 0 |
| Qwen3-1.7B | nodes | 11-30 | 30 | 19 | 19 | 14 | 0.467 |
| Qwen3-1.7B | nodes | 31-60 | 8 | 8 | 8 | 8 | 1 |
| Qwen3-1.7B | nodes | 61-120 | 8 | 7 | 7 | 7 | 0.875 |
| Qwen3-1.7B | nodes | >120 | 2 | 2 | 2 | 2 | 1 |
| Qwen3-1.7B | nodes | all | 60 | 36 | 36 | 31 | 0.517 |
| Qwen3-8B | nodes | 1-10 | 12 | 0 | 0 | 0 | 0 |
| Qwen3-8B | nodes | 11-30 | 30 | 2 | 2 | 2 | 0.0667 |
| Qwen3-8B | nodes | 31-60 | 8 | 8 | 8 | 6 | 0.75 |
| Qwen3-8B | nodes | 61-120 | 8 | 8 | 8 | 6 | 0.75 |
| Qwen3-8B | nodes | >120 | 2 | 2 | 2 | 1 | 0.5 |
| Qwen3-8B | nodes | all | 60 | 20 | 20 | 15 | 0.25 |

## Transfer of confirmed violations

| model | set | from | source_violations | retained | retention |
|---|---|---|---|---|---|
| Qwen3-8B | transfer | probe_pm_degree_qwen3-1.7b | 38 | 8 | 0.211 |

## Screen: execution by model × degree bin

| model | bin | trials | exec_error | abs_err_mean | json | number | failed | length_cut | tok_mean | jitter_inputs |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-1.7B | 1-10 | 1112 | 0.0018 | 0.0018 | 1 | 0 | 0 | 0 | 87 | 0 |
| Qwen3-1.7B | 11-30 | 2430 | 0.323 | 0.515 | 1 | 0 | 0 | 0 | 154 | 0.00918 |
| Qwen3-1.7B | 31-60 | 7462 | 0.883 | 6.1 | 1 | 0.000134 | 0 | 0.000134 | 381 | 0.0478 |
| Qwen3-1.7B | 61-120 | 7154 | 0.998 | 55.1 | 0.997 | 0.00335 | 0 | 0.00182 | 488 | 0.0204 |
| Qwen3-1.7B | >120 | 1954 | 1 | 94.7 | 1 | 0 | 0 | 0 | 320 | 0.00206 |
| Qwen3-8B | 1-10 | 1112 | 0 | 0 | 1 | 0 | 0 | 0 | 97.2 | 0 |
| Qwen3-8B | 11-30 | 2430 | 0.0317 | 0.0317 | 1 | 0 | 0 | 0 | 150 | 0.00334 |
| Qwen3-8B | 31-60 | 7462 | 0.749 | 2.35 | 1 | 0 | 0 | 0 | 289 | 0.188 |
| Qwen3-8B | 61-120 | 7154 | 0.999 | 13.4 | 1 | 0 | 0 | 0 | 450 | 0.265 |
| Qwen3-8B | >120 | 1954 | 0.999 | 56.1 | 1 | 0 | 0 | 0 | 582 | 0.497 |
