# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs5_eval_psc_v0-r2` (40 designs, 93 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 22 | 0 | 5 | 0 | 0 | 5 | 0 | 2 | 0 | 10 | 0.545 | 17 | 5 | 0.294 | 3.33 | 0 | 6 | 0 |
| 5-star | 18 | 0 | 1 | 0 | 0 | 4 | 1 | 2 | 0 | 10 | 0.444 | 17 | 4 | 0.235 | inf | 0 | 0 | 1 |
| triangle | 38 | 0 | 13 | 1 | 0 | 0 | 10 | 8 | 0 | 6 | 0.816 | 24 | 6 | 0.25 | 2 | 0 | 5 | 10 |
| degree-moment2 | 15 | 0 | 2 | 0 | 0 | 3 | 0 | 0 | 0 | 10 | 0.333 | 13 | 3 | 0.231 | 1.57 | 0 | 10 | 0 |
| all | 93 | 0 | 21 | 1 | 0 | 12 | 11 | 12 | 0 | 36 | 0.602 | 71 | 18 | 0.254 | inf | 0 | 21 | 11 |
