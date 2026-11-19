# CS6b: offline replay of the recorded runs (no model call)

## Problem 2: format-only repairs (28 of 102 parse failures rescued)

| source | parse_failures | rescued | left |
|---|---|---|---|
| cs2_pm_psc-arch_d10 | 16 | 5 | 11 |
| cs4_online_psc-arch_d10 | 21 | 2 | 19 |
| cs5_eval_psc_v0 | 18 | 3 | 15 |
| cs5_eval_psc_v0-r2 | 21 | 6 | 15 |
| cs5_eval_psc_evolved | 26 | 12 | 14 |

Parse failures left, by category (example: the first draft of the category):

| category | drafts | example |
|---|---|---|
| set_as_number | 16 | degree = project(P, D) ; return comb(degree, 2) |
| condition_in_sum | 14 | name = sum(1 for a in N(self) for b in N(self) if a < b) ; return name |
| unknown_node_name | 13 | sum_val = sum( size(N(v) & N(u)) for v in N(u) ) ; return sum_val / 2 |
| floor_div_in_aggregate | 7 | name = comb(size(N(self)), 2) ; return name |
| name_reassigned | 5 | name = size(project(P, D)) ; name = comb(name, 2) ; return name |
| project_args | 3 | k = size(P) ; k_proj = project(k, D) ; return comb(k_proj, 2) |
| procedural_loop | 3 | count = 0 ; for v in P: ;     for w in P - {v}: ;         count += size(N(v) & N(w)) ; return count |
| literal_or_index | 3 | name = sum( size(N(y) & {z}) * size(N(z) & {y}) for y in project(P, D) for z in project(P, D) ) ; return name |
| comb_nonconstant_k | 3 | s = project(P, D) ; k = 5 ; name = comb(size(s), k) ; return name |
| power_operator | 3 | s = project(P, D) ; return size(s) ** 2 |
| missing_return | 3 | name = sum( sum( (size(P & N(v)) - size(P & N(v) - {v})) * (size(N(v) & P) - size(N(v) & P - {v})) for v in P ) ) |
| unknown_function | 1 | degree = size(P) ; count = degree * (degree - 1) * (degree - 2) / 6 ; return count + LaplaceNoise((D - 1) * (D - 2) / 2) |

## Problem 1: GS of the accepted programs, recorded (old deriver) vs current deriver

`loose`: GS > 1.05 x reference GS at the design-time bound. `re_*`: mean relative error over the run's seeds (paired); `re_reference`: the reference program (GT-DSL) of the run.

| source | task | accepted | gs_ratio_old | gs_ratio_new | loose_old | loose_new | re_old | re_new | re_reference |
|---|---|---|---|---|---|---|---|---|---|
| cs2_pm_psc-arch_d10 | degree | 10 | 1.0000 | 1.0000 | 0 | 0 | 0.0030 | 0.0030 | 0.0030 |
| cs2_pm_psc-arch_d10 | 2-star | 10 | 5.8222 | 5.8111 | 1 | 1 | 4.4644 | 4.4644 | 0.0443 |
| cs2_pm_psc-arch_d10 | 3-star | 9 | 315.1698 | 313.7500 | 2 | 1 | 14.7504 | 14.7501 | 0.1227 |
| cs2_pm_psc-arch_d10 | triangle | 8 | 0.8056 | 0.6667 | 3 | 1 | 63.6189 | 63.5924 | 1.0295 |
| cs4_online_psc-arch_d10 | degree | 10 | 1.0000 | 1.0000 | 0 | 0 | 0.0030 | 0.0030 | 0.0030 |
| cs4_online_psc-arch_d10 | 2-star | 9 | 1.0123 | 1.0000 | 1 | 0 | 0.0443 | 0.0443 | 0.0443 |
| cs4_online_psc-arch_d10 | 3-star | 10 | 1.1000 | 1.0000 | 4 | 0 | 0.1231 | 0.1227 | 0.1227 |
| cs4_online_psc-arch_d10 | triangle | 2 | 1.5556 | 1.0000 | 2 | 0 | 1.6929 | 1.5868 | 1.0295 |
| cs5_eval_psc_v0 | 3-star | 9 | 1.1389 | 1.0000 | 5 | 0 | 0.1232 | 0.1227 | 0.1227 |
| cs5_eval_psc_v0 | 5-star | 9 | 1.0000 | 1.0000 | 0 | 0 | 0.2874 | 0.2874 | 0.2874 |
| cs5_eval_psc_v0 | triangle | 4 | 1.9444 | 1.2500 | 4 | 1 | 1.6929 | 1.5868 | 1.0295 |
| cs5_eval_psc_v0 | degree-moment2 | 10 | 1.1053 | 1.0000 | 10 | 0 | 0.0435 | 0.0433 | 0.0433 |
| cs5_eval_psc_v0-r2 | 3-star | 10 | 1.1500 | 1.0000 | 6 | 0 | 0.1233 | 0.1227 | 0.1227 |
| cs5_eval_psc_v0-r2 | 5-star | 10 | 1.0000 | 1.0000 | 0 | 0 | 0.2874 | 0.2874 | 0.2874 |
| cs5_eval_psc_v0-r2 | triangle | 6 | 1.6605 | 1.1667 | 5 | 2 | 1.6939 | 1.6055 | 1.0295 |
| cs5_eval_psc_v0-r2 | degree-moment2 | 10 | 1.1053 | 1.0000 | 10 | 0 | 0.0435 | 0.0433 | 0.0433 |
| cs5_eval_psc_evolved | 3-star | 8 | 1.0000 | 1.0000 | 0 | 0 | 0.1227 | 0.1227 | 0.1227 |
| cs5_eval_psc_evolved | 5-star | 10 | 1.0000 | 1.0000 | 0 | 0 | 0.2874 | 0.2874 | 0.2874 |
| cs5_eval_psc_evolved | triangle | 3 | 2.0741 | 1.3333 | 3 | 1 | 1.6929 | 1.5868 | 1.0295 |
| cs5_eval_psc_evolved | degree-moment2 | 8 | 1.0789 | 1.0000 | 6 | 0 | 0.0434 | 0.0433 | 0.0433 |
