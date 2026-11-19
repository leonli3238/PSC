# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs6a_psc_v1-repeat3` (80 designs, 170 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 41 | 0 | 6 | 3 | 0 | 11 | 1 | 4 | 0 | 16 | 0.537 | 32 | 11 | 0.344 | 3.33 | 0 | 0 | 1 |
| 5-star | 37 | 0 | 2 | 2 | 0 | 12 | 0 | 3 | 0 | 18 | 0.46 | 33 | 12 | 0.364 | inf | 0 | 0 | 0 |
| triangle | 60 | 0 | 24 | 2 | 0 | 4 | 14 | 16 | 0 | 0 | 0.967 | 34 | 5 | 0.147 | 7.33 | 0 | 0 | 14 |
| degree-moment2 | 32 | 0 | 1 | 0 | 0 | 10 | 1 | 0 | 0 | 20 | 0.375 | 31 | 11 | 0.355 | 4 | 0 | 0 | 1 |
| all | 170 | 0 | 33 | 7 | 0 | 37 | 16 | 23 | 0 | 54 | 0.641 | 130 | 39 | 0.3 | inf | 0 | 0 | 16 |
