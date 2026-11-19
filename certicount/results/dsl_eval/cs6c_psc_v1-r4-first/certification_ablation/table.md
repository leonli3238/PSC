# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs6c_psc_v1-r4-first` (40 designs, 149 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 17 | 0 | 0 | 0 | 0 | 6 | 0 | 1 | 0 | 10 | 0.412 | 17 | 6 | 0.353 | 3.33 | 0 | 0 | 0 |
| 5-star | 15 | 0 | 1 | 1 | 0 | 2 | 0 | 1 | 0 | 10 | 0.267 | 13 | 2 | 0.154 | inf | 0 | 0 | 0 |
| triangle | 96 | 0 | 39 | 1 | 0 | 23 | 22 | 7 | 0 | 4 | 0.948 | 56 | 32 | 0.571 | 71.3 | 0 | 0 | 22 |
| degree-moment2 | 21 | 0 | 4 | 0 | 0 | 7 | 0 | 0 | 0 | 10 | 0.524 | 17 | 7 | 0.412 | 1.57 | 0 | 0 | 0 |
| all | 149 | 0 | 44 | 2 | 0 | 38 | 22 | 9 | 0 | 34 | 0.758 | 103 | 47 | 0.456 | inf | 0 | 0 | 22 |
