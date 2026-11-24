# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs9_node_generic_sim_ext` (360 designs, 1551 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| degree-ge3 | 397 | 6 | 89 | 7 | 8 | 9 | 71 | 0 | 0 | 207 | 0.461 | 295 | 0 | 0 | 1 | 0 | 1 | 71 |
| triangle-edge | 703 | 3 | 229 | 31 | 0 | 0 | 284 | 0 | 0 | 156 | 0.734 | 440 | 353 | 0.802 | 33.5 | 0 | 101 | 284 |
| triangle-node | 451 | 0 | 118 | 7 | 0 | 0 | 103 | 0 | 0 | 223 | 0.49 | 326 | 7 | 0.0215 | 11 | 0 | 2 | 103 |
| all | 1551 | 9 | 436 | 45 | 8 | 9 | 458 | 0 | 0 | 586 | 0.593 | 1061 | 360 | 0.339 | 33.5 | 0 | 104 | 458 |
