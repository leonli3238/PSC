# Degree probe report

## Confirmation sets (each at its own family α)

| model | set | source | pairs | tested | violations | violations_real_count | violation_share_upper95 | eps_lb_max | eps_lb_median | max_delta_llm |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-8B | main_div | screen_top | 40 | 40 | 24 | 20 | 0.731 | 4.19 | 3.25 | 406 |
| Qwen3-8B | nodes | nodes | 20 | 20 | 15 | 15 | 0.896 | 4.3 | 2.94 | 332 |
| certicount-program | main_div | file | 40 | 40 | 0 | 0 | 0.0722 | 1.47 | 0.956 | 1 |
| certicount-program | nodes | file | 20 | 20 | 0 | 0 | 0.139 | 1.32 | 0.988 | 1 |

## Joint Bonferroni over the sets (family α = 0.05, scope = all)

Every tested pair of the scope is re-bounded at α/M from its stored evaluation counts (the test was chosen on selection trials only); these are the numbers for a single joint claim.

| scope | M | alpha_pair | violations_family | violations_family_real_count |
|---|---|---|---|---|
| all | 120 | 0.000417 | 38 | 34 |

| scope | set | tested | violations_design | violations_family | violations_family_real_count | eps_lb_family_max |
|---|---|---|---|---|---|---|
| all | Qwen3-8B/main_div | 40 | 24 | 24 | 20 | 4.05 |
| all | Qwen3-8B/nodes | 20 | 15 | 14 | 14 | 4.06 |
| all | certicount-program/main_div | 40 | 0 | 0 | 0 | 1.4 |
| all | certicount-program/nodes | 20 | 0 | 0 | 0 | 1.23 |

## Node level

| model | set | bin | nodes | with_candidate | tested | confirmed | confirmed_share |
|---|---|---|---|---|---|---|---|
| Qwen3-8B | nodes | 1-10 | 12 | 0 | 0 | 0 | 0 |
| Qwen3-8B | nodes | 11-30 | 30 | 2 | 2 | 2 | 0.0667 |
| Qwen3-8B | nodes | 31-60 | 8 | 8 | 8 | 6 | 0.75 |
| Qwen3-8B | nodes | 61-120 | 8 | 8 | 8 | 6 | 0.75 |
| Qwen3-8B | nodes | >120 | 2 | 2 | 2 | 1 | 0.5 |
| Qwen3-8B | nodes | all | 60 | 20 | 20 | 15 | 0.25 |

## Transfer of confirmed violations

(none)

## Screen: execution by model × degree bin

| model | bin | trials | exec_error | abs_err_mean | json | number | failed | length_cut | tok_mean | jitter_inputs |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-8B | 1-10 | 1112 | 0 | 0 | 1 | 0 | 0 | 0 | 97.2 | 0 |
| Qwen3-8B | 11-30 | 2430 | 0.0317 | 0.0317 | 1 | 0 | 0 | 0 | 150 | 0.00334 |
| Qwen3-8B | 31-60 | 7462 | 0.749 | 2.35 | 1 | 0 | 0 | 0 | 289 | 0.188 |
| Qwen3-8B | 61-120 | 7154 | 0.999 | 13.4 | 1 | 0 | 0 | 0 | 450 | 0.265 |
| Qwen3-8B | >120 | 1954 | 0.999 | 56.1 | 1 | 0 | 0 | 0 | 582 | 0.497 |
