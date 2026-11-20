# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs7_node_v1alt_gate` (80 designs, 167 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 37 | 0 | 2 | 1 | 0 | 5 | 1 | 9 | 0 | 19 | 0.46 | 34 | 5 | 0.147 | 3.33 | 0 | 0 | 1 |
| 5-star | 43 | 0 | 5 | 4 | 0 | 6 | 0 | 10 | 0 | 18 | 0.488 | 34 | 6 | 0.176 | inf | 0 | 0 | 0 |
| triangle | 43 | 0 | 10 | 0 | 0 | 6 | 3 | 12 | 0 | 12 | 0.721 | 33 | 4 | 0.121 | 1.5 | 0 | 0 | 3 |
| degree-moment2 | 44 | 0 | 14 | 0 | 1 | 9 | 0 | 7 | 0 | 13 | 0.705 | 30 | 11 | 0.367 | 3.24 | 0 | 1 | 0 |
| all | 167 | 0 | 31 | 5 | 1 | 26 | 4 | 38 | 0 | 62 | 0.599 | 131 | 26 | 0.199 | inf | 0 | 1 | 4 |
