# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs5_eval_psc_v0` (40 designs, 74 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 17 | 0 | 5 | 0 | 0 | 1 | 0 | 2 | 0 | 9 | 0.471 | 12 | 1 | 0.0833 | 3.33 | 0 | 5 | 0 |
| 5-star | 18 | 0 | 5 | 0 | 0 | 3 | 0 | 1 | 0 | 9 | 0.5 | 13 | 3 | 0.231 | inf | 0 | 0 | 0 |
| triangle | 25 | 0 | 5 | 0 | 0 | 2 | 8 | 6 | 0 | 4 | 0.84 | 20 | 4 | 0.2 | 2 | 0 | 4 | 8 |
| degree-moment2 | 14 | 0 | 3 | 0 | 0 | 1 | 0 | 0 | 0 | 10 | 0.286 | 11 | 1 | 0.0909 | 1.57 | 0 | 10 | 0 |
| all | 74 | 0 | 18 | 0 | 0 | 7 | 8 | 9 | 0 | 32 | 0.568 | 56 | 9 | 0.161 | inf | 0 | 19 | 8 |
