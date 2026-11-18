# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs5_eval_node_evolved` (40 designs, 76 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 18 | 0 | 7 | 0 | 0 | 0 | 0 | 3 | 0 | 8 | 0.556 | 11 | 0 | 0 | 1 | 0 | 0 | 0 |
| 5-star | 12 | 0 | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 9 | 0.25 | 11 | 1 | 0.0909 | inf | 0 | 0 | 0 |
| triangle | 26 | 0 | 20 | 0 | 0 | 0 | 3 | 0 | 0 | 3 | 0.885 | 6 | 1 | 0.167 | 2 | 0 | 0 | 3 |
| degree-moment2 | 20 | 0 | 9 | 0 | 0 | 0 | 0 | 3 | 0 | 8 | 0.6 | 11 | 4 | 0.364 | 3.24 | 0 | 8 | 0 |
| all | 76 | 0 | 37 | 0 | 1 | 0 | 3 | 7 | 0 | 28 | 0.632 | 39 | 6 | 0.154 | inf | 0 | 8 | 3 |
