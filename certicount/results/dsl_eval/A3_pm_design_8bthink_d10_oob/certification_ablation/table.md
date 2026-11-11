# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/A3_pm_design_8bthink_d10_oob` (30 designs, 51 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | parse | duplicate | gs_failed | gs_loose | semantic | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4-star | 19 | 5 | 0 | 0 | 5 | 0 | 0 | 9 | 0.526 | 14 | 5 | 0.357 | inf | 0 | 0 | 0 |
| 5-star | 17 | 4 | 0 | 0 | 4 | 0 | 0 | 9 | 0.471 | 13 | 4 | 0.308 | inf | 0 | 0 | 0 |
| degree-moment2 | 15 | 5 | 0 | 0 | 0 | 0 | 0 | 10 | 0.333 | 10 | 3 | 0.3 | 1.57 | 0 | 10 | 0 |
| all | 51 | 14 | 0 | 0 | 9 | 0 | 0 | 28 | 0.451 | 37 | 12 | 0.324 | inf | 0 | 10 | 0 |
