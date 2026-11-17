# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs3_pm_node-arch_d10_a5.0` (40 designs, 68 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | parse | duplicate | gs_failed | gs_loose | semantic | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| degree | 13 | 1 | 0 | 0 | 0 | 2 | 0 | 10 | 0.231 | 12 | 1 | 0.0833 | 2.16 | 0 | 1 | 2 |
| 2-star | 15 | 2 | 0 | 1 | 2 | 0 | 0 | 10 | 0.333 | 13 | 5 | 0.385 | 5 | 0 | 2 | 0 |
| 3-star | 11 | 1 | 0 | 0 | 0 | 0 | 0 | 10 | 0.0909 | 10 | 1 | 0.1 | 3.33 | 0 | 1 | 0 |
| triangle | 29 | 26 | 0 | 0 | 0 | 1 | 0 | 2 | 0.931 | 3 | 2 | 0.667 | 2 | 0 | 2 | 1 |
| all | 68 | 30 | 0 | 1 | 2 | 3 | 0 | 32 | 0.529 | 38 | 9 | 0.237 | 5 | 0 | 6 | 3 |
