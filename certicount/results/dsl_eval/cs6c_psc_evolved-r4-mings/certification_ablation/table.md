# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs6c_psc_evolved-r4-mings` (40 designs, 246 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 45 | 0 | 5 | 2 | 0 | 0 | 0 | 0 | 0 | 38 | 0.111 | 38 | 0 | 0 | 1 | 0 | 0 | 0 |
| 5-star | 45 | 0 | 3 | 4 | 0 | 1 | 0 | 1 | 0 | 36 | 0.111 | 38 | 1 | 0.0263 | inf | 0 | 0 | 0 |
| triangle | 107 | 0 | 43 | 3 | 0 | 13 | 32 | 8 | 0 | 8 | 0.897 | 61 | 25 | 0.41 | 10.1 | 0 | 0 | 32 |
| degree-moment2 | 49 | 0 | 5 | 3 | 0 | 4 | 0 | 0 | 0 | 37 | 0.184 | 41 | 4 | 0.0976 | 1.57 | 0 | 0 | 0 |
| all | 246 | 0 | 56 | 12 | 0 | 18 | 32 | 9 | 0 | 119 | 0.468 | 178 | 30 | 0.169 | inf | 0 | 0 | 32 |
