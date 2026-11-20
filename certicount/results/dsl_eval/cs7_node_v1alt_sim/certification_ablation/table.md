# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs7_node_v1alt_sim` (80 designs, 299 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 72 | 2 | 9 | 0 | 1 | 8 | 0 | 0 | 0 | 52 | 0.278 | 61 | 15 | 0.246 | 5.33 | 0 | 6 | 0 |
| 5-star | 64 | 1 | 9 | 2 | 0 | 10 | 0 | 0 | 0 | 42 | 0.312 | 52 | 10 | 0.192 | inf | 0 | 0 | 0 |
| triangle | 78 | 1 | 5 | 0 | 0 | 0 | 7 | 0 | 0 | 65 | 0.167 | 72 | 9 | 0.125 | 2.5 | 0 | 15 | 7 |
| degree-moment2 | 85 | 8 | 43 | 1 | 0 | 3 | 0 | 0 | 0 | 30 | 0.635 | 33 | 5 | 0.151 | 1.57 | 0 | 2 | 0 |
| all | 299 | 12 | 66 | 3 | 1 | 21 | 7 | 0 | 0 | 189 | 0.358 | 218 | 39 | 0.179 | inf | 0 | 23 | 7 |
