# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs7_node_v1alt_sim-noown` (80 designs, 253 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 58 | 3 | 9 | 1 | 0 | 4 | 0 | 0 | 0 | 41 | 0.276 | 45 | 9 | 0.2 | 16.2 | 0 | 5 | 0 |
| 5-star | 55 | 0 | 9 | 1 | 0 | 9 | 0 | 0 | 0 | 36 | 0.327 | 45 | 9 | 0.2 | inf | 0 | 0 | 0 |
| triangle | 62 | 1 | 6 | 0 | 0 | 0 | 11 | 0 | 0 | 44 | 0.29 | 55 | 7 | 0.127 | 3.05 | 0 | 8 | 11 |
| degree-moment2 | 78 | 14 | 26 | 3 | 0 | 8 | 1 | 0 | 0 | 26 | 0.628 | 35 | 14 | 0.4 | 3.24 | 0 | 5 | 1 |
| all | 253 | 18 | 50 | 5 | 0 | 21 | 12 | 0 | 0 | 147 | 0.399 | 180 | 39 | 0.217 | inf | 0 | 18 | 12 |
