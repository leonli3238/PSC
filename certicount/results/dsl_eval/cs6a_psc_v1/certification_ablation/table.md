# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs6a_psc_v1` (80 designs, 171 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 48 | 0 | 5 | 2 | 0 | 12 | 0 | 13 | 0 | 16 | 0.625 | 41 | 12 | 0.293 | 3.33 | 0 | 0 | 0 |
| 5-star | 30 | 0 | 0 | 0 | 0 | 8 | 0 | 3 | 0 | 19 | 0.367 | 30 | 8 | 0.267 | inf | 0 | 0 | 0 |
| triangle | 55 | 0 | 14 | 1 | 0 | 9 | 15 | 10 | 0 | 6 | 0.873 | 40 | 16 | 0.4 | 30.3 | 0 | 1 | 15 |
| degree-moment2 | 38 | 0 | 5 | 0 | 0 | 13 | 0 | 0 | 0 | 20 | 0.474 | 33 | 13 | 0.394 | 1.57 | 0 | 0 | 0 |
| all | 171 | 0 | 24 | 3 | 0 | 42 | 15 | 26 | 0 | 61 | 0.626 | 144 | 49 | 0.34 | inf | 0 | 1 | 15 |
