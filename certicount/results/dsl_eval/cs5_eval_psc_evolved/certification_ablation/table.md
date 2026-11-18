# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs5_eval_psc_evolved` (40 designs, 71 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 15 | 0 | 6 | 0 | 0 | 0 | 0 | 1 | 0 | 8 | 0.467 | 9 | 0 | 0 | 1 | 0 | 0 | 0 |
| 5-star | 14 | 0 | 3 | 0 | 0 | 0 | 0 | 1 | 0 | 10 | 0.286 | 11 | 0 | 0 | 0 | 0 | 0 | 0 |
| triangle | 26 | 0 | 10 | 2 | 0 | 0 | 6 | 5 | 0 | 3 | 0.808 | 14 | 4 | 0.286 | 2 | 0 | 3 | 6 |
| degree-moment2 | 16 | 0 | 7 | 0 | 0 | 1 | 0 | 0 | 0 | 8 | 0.5 | 9 | 1 | 0.111 | 1.57 | 0 | 6 | 0 |
| all | 71 | 0 | 26 | 2 | 0 | 1 | 6 | 7 | 0 | 29 | 0.563 | 43 | 5 | 0.116 | 2 | 0 | 9 | 6 |
