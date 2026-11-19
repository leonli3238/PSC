# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs6c_psc_v1-r4-mings` (40 designs, 321 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 74 | 0 | 1 | 3 | 0 | 20 | 0 | 17 | 0 | 33 | 0.513 | 70 | 20 | 0.286 | 3.33 | 0 | 0 | 0 |
| 5-star | 66 | 0 | 8 | 2 | 0 | 14 | 0 | 4 | 0 | 38 | 0.394 | 56 | 14 | 0.25 | inf | 0 | 0 | 0 |
| triangle | 107 | 0 | 44 | 1 | 0 | 19 | 19 | 19 | 0 | 5 | 0.944 | 62 | 19 | 0.306 | 10 | 0 | 0 | 19 |
| degree-moment2 | 74 | 0 | 13 | 1 | 0 | 23 | 0 | 0 | 0 | 37 | 0.486 | 60 | 23 | 0.383 | 1.57 | 0 | 0 | 0 |
| all | 321 | 0 | 66 | 7 | 0 | 76 | 19 | 40 | 0 | 113 | 0.626 | 248 | 76 | 0.306 | inf | 0 | 0 | 19 |
