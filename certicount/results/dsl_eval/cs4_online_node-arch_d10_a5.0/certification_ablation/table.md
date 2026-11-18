# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs4_online_node-arch_d10_a5.0` (40 designs, 82 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| degree | 20 | 0 | 6 | 0 | 0 | 0 | 5 | 2 | 0 | 7 | 0.65 | 14 | 4 | 0.286 | 2.16 | 0 | 3 | 5 |
| 2-star | 24 | 0 | 6 | 1 | 2 | 2 | 0 | 7 | 0 | 6 | 0.708 | 17 | 5 | 0.294 | 3.42 | 0 | 3 | 0 |
| 3-star | 17 | 0 | 3 | 0 | 1 | 1 | 1 | 2 | 0 | 9 | 0.471 | 14 | 3 | 0.214 | 7.74 | 0 | 2 | 1 |
| triangle | 21 | 0 | 7 | 0 | 0 | 2 | 4 | 0 | 0 | 8 | 0.619 | 14 | 0 | 0 | 1 | 0 | 0 | 4 |
| all | 82 | 0 | 22 | 1 | 3 | 5 | 10 | 11 | 0 | 30 | 0.622 | 59 | 12 | 0.203 | 7.74 | 0 | 8 | 10 |
