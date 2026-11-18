# Step 1a: replay of the recorded drafts (no model call)

Gate: τ = 2.0, 8 releases per public Holme-Kim graph; evaluation error: mean RE over 20 paired code runs on the run's graph; catastrophic = RE > 10 x the reference program's.

## Per task

| source | task | drafts | old_accepted | old_catastrophic | new_accepted | new_catastrophic | rejected_by_gate | gate_rejected_catastrophic | rescued_parse | truncated | old_median_re | new_median_re | old_mean_re | new_mean_re | reference_re |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A3_pm_design_8bthink_d10 | 2-star | 21 | 9 | 2 | 7 | 0 | 2 | 2 | 0 | 0 | 0.0350 | 0.0350 | 9.8666 | 0.0350 | 0.0350 |
| A3_pm_design_8bthink_d10 | 3-star | 15 | 9 | 1 | 8 | 0 | 1 | 1 | 0 | 0 | 0.0970 | 0.0970 | 4.9762 | 0.0972 | 0.0970 |
| A3_pm_design_8bthink_d10 | degree | 12 | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 0.0028 | 0.0028 | 0.0028 | 0.0028 | 0.0028 |
| A3_pm_design_8bthink_d10 | triangle | 20 | 6 | 5 | 0 | 0 | 5 | 5 | 0 | 0 | 100.9995 | - | 84.4144 | - | 0.9548 |
| cs2_pm_psc-arch_d10 | 2-star | 19 | 10 | 1 | 8 | 0 | 1 | 1 | 0 | 0 | 0.0350 | 0.0350 | 4.4621 | 0.0350 | 0.0350 |
| cs2_pm_psc-arch_d10 | 3-star | 13 | 9 | 3 | 5 | 0 | 3 | 3 | 0 | 0 | 0.0977 | 0.0970 | 14.7615 | 0.0971 | 0.0970 |
| cs2_pm_psc-arch_d10 | degree | 11 | 10 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0.0028 | 0.0028 | 0.0028 | 0.0028 | 0.0028 |
| cs2_pm_psc-arch_d10 | triangle | 20 | 8 | 5 | 3 | 0 | 5 | 5 | 3 | 0 | 100.9995 | 1.4846 | 63.6824 | 1.4872 | 0.9548 |
| cs3_pm_node-arch_d10_a5.0 | 2-star | 15 | 10 | 3 | 7 | 0 | 3 | 3 | 0 | 0 | 0.0342 | 0.0084 | 13.2993 | 0.0231 | 0.0084 |
| cs3_pm_node-arch_d10_a5.0 | 3-star | 11 | 10 | 3 | 7 | 0 | 2 | 2 | 0 | 0 | 0.0790 | 0.0103 | 8.8637 | 0.0397 | 0.0103 |
| cs3_pm_node-arch_d10_a5.0 | degree | 13 | 10 | 7 | 4 | 1 | 6 | 6 | 0 | 0 | 13.0620 | 0.0064 | 7.8428 | 0.0139 | 0.0028 |
| cs3_pm_node-arch_d10_a5.0 | triangle | 29 | 2 | 1 | 1 | 1 | 1 | 0 | 8 | 1 | 1.3218 | 1.5350 | 1.3218 | 1.5350 | 0.1456 |

## Stage transitions (old -> new)

| old_stage | new_stage | drafts |
|---|---|---|
| accepted | accepted | 69 |
| accepted | gs_loose | 5 |
| accepted | noisy | 28 |
| gs_failed | gs_failed | 1 |
| gs_loose | gs_loose | 13 |
| parse | duplicate | 2 |
| parse | gs_loose | 7 |
| parse | noisy | 1 |
| parse | parse | 57 |
| parse | semantic | 1 |
| parse | truncated | 1 |
| semantic | semantic | 14 |

## Reference programs (must be accepted: yes)

| source | task | new_stage | noise_free_bias | pm_relative_error | program |
|---|---|---|---|---|---|
| cs2_pm_psc-arch_d10 | 2-star | accepted | 0.0068 | 0.0350 | return comb(size(project(P, D)), 2) ; aggregate: total |
| cs2_pm_psc-arch_d10 | 3-star | accepted | 0.0199 | 0.0970 | return comb(size(project(P, D)), 3) ; aggregate: total |
| cs2_pm_psc-arch_d10 | degree | accepted | 0.0000 | 0.0028 | return size(P) ; aggregate: total / n |
| cs2_pm_psc-arch_d10 | triangle | accepted | 0.6605 | 0.9548 | S = P & N(self) ; return 0.5 * sum(size(P & N(j)) for j in S) ; aggregate: total / 3 |
| cs3_pm_node-arch_d10_a5.0 | 2-star | accepted | 0.0144 | 0.0084 | return comb(size(project(P, D)), 2) ; aggregate: total |
| cs3_pm_node-arch_d10_a5.0 | 3-star | accepted | 0.0146 | 0.0103 | return comb(size(project(P, D)), 3) ; aggregate: total |
| cs3_pm_node-arch_d10_a5.0 | degree | accepted | 0.0000 | 0.0028 | return size(P) ; aggregate: total / n |
| cs3_pm_node-arch_d10_a5.0 | triangle | accepted | 0.0933 | 0.1456 | Q = project(P, D) ; return sum(sum(A(j, k) for k in Q) for j in Q) ; aggregate: total / 6 |
| A3_pm_design_8bthink_d10 | 2-star | accepted | 0.0068 | 0.0350 | return comb(size(project(P, D)), 2) ; aggregate: total |
| A3_pm_design_8bthink_d10 | 3-star | accepted | 0.0199 | 0.0970 | return comb(size(project(P, D)), 3) ; aggregate: total |
| A3_pm_design_8bthink_d10 | degree | accepted | 0.0000 | 0.0028 | return size(P) ; aggregate: total / n |
| A3_pm_design_8bthink_d10 | triangle | accepted | 0.6605 | 0.9548 | S = P & N(self) ; return 0.5 * sum(size(P & N(j)) for j in S) ; aggregate: total / 3 |
