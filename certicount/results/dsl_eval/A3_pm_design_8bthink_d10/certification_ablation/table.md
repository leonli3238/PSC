# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/A3_pm_design_8bthink_d10` (40 designs, 68 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | parse | duplicate | gs_failed | gs_loose | semantic | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| degree | 12 | 0 | 0 | 0 | 0 | 3 | 0 | 9 | 0.25 | 12 | 0 | 0 | 1 | 0 | 0 | 3 |
| 2-star | 21 | 5 | 0 | 0 | 6 | 1 | 0 | 9 | 0.571 | 16 | 6 | 0.375 | 1.67 | 0 | 0 | 1 |
| 3-star | 15 | 5 | 0 | 0 | 1 | 0 | 0 | 9 | 0.4 | 10 | 1 | 0.1 | 3.33 | 0 | 2 | 0 |
| triangle | 20 | 10 | 0 | 0 | 0 | 4 | 0 | 6 | 0.7 | 10 | 2 | 0.2 | 2 | 0 | 1 | 4 |
| all | 68 | 20 | 0 | 0 | 7 | 8 | 0 | 33 | 0.515 | 48 | 9 | 0.188 | 3.33 | 0 | 3 | 8 |
