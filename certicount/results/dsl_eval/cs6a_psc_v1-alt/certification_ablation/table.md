# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs6a_psc_v1-alt` (80 designs, 159 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 44 | 0 | 4 | 1 | 0 | 17 | 0 | 4 | 0 | 18 | 0.568 | 39 | 17 | 0.436 | 3.33 | 0 | 0 | 0 |
| 5-star | 33 | 0 | 0 | 0 | 0 | 11 | 0 | 3 | 0 | 19 | 0.424 | 33 | 11 | 0.333 | inf | 0 | 0 | 0 |
| triangle | 46 | 0 | 5 | 4 | 0 | 11 | 5 | 10 | 0 | 11 | 0.674 | 37 | 11 | 0.297 | 1.5 | 0 | 0 | 5 |
| degree-moment2 | 36 | 0 | 4 | 0 | 0 | 11 | 0 | 2 | 0 | 19 | 0.472 | 32 | 11 | 0.344 | 1.57 | 0 | 0 | 0 |
| all | 159 | 0 | 13 | 5 | 0 | 50 | 5 | 19 | 0 | 67 | 0.547 | 141 | 50 | 0.355 | inf | 0 | 0 | 5 |
