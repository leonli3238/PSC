# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs5_eval_node_v0-r2` (40 designs, 105 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 23 | 0 | 3 | 0 | 2 | 2 | 1 | 5 | 0 | 10 | 0.565 | 20 | 5 | 0.25 | 16.2 | 0 | 2 | 1 |
| 5-star | 24 | 0 | 2 | 0 | 3 | 2 | 0 | 7 | 0 | 10 | 0.583 | 22 | 5 | 0.227 | inf | 0 | 0 | 0 |
| triangle | 25 | 0 | 8 | 0 | 0 | 1 | 4 | 2 | 0 | 10 | 0.6 | 17 | 1 | 0.0588 | 1.25 | 0 | 2 | 4 |
| degree-moment2 | 33 | 1 | 15 | 2 | 0 | 0 | 1 | 5 | 0 | 9 | 0.667 | 15 | 8 | 0.533 | 3.24 | 0 | 9 | 1 |
| all | 105 | 1 | 28 | 2 | 5 | 5 | 6 | 19 | 0 | 39 | 0.61 | 74 | 19 | 0.257 | inf | 0 | 13 | 6 |
