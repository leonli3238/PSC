# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs2_pm_psc-arch_d10` (40 designs, 63 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | parse | duplicate | gs_failed | gs_loose | semantic | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| degree | 11 | 0 | 0 | 0 | 0 | 1 | 0 | 10 | 0.0909 | 11 | 0 | 0 | 1 | 0 | 0 | 1 |
| 2-star | 19 | 6 | 0 | 0 | 3 | 0 | 0 | 10 | 0.474 | 13 | 4 | 0.308 | 1.67 | 0 | 1 | 0 |
| 3-star | 13 | 3 | 0 | 0 | 1 | 0 | 0 | 9 | 0.308 | 10 | 2 | 0.2 | 3.33 | 0 | 2 | 0 |
| triangle | 20 | 10 | 0 | 0 | 0 | 2 | 0 | 8 | 0.6 | 10 | 1 | 0.1 | 2.5 | 0 | 3 | 2 |
| all | 63 | 19 | 0 | 0 | 4 | 3 | 0 | 37 | 0.413 | 44 | 7 | 0.159 | 3.33 | 0 | 6 | 3 |
