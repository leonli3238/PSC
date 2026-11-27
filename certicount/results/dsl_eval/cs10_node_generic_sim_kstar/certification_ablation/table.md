# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs10_node_generic_sim_kstar` (360 designs, 1182 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| degree | 377 | 18 | 89 | 38 | 0 | 0 | 22 | 0 | 0 | 210 | 0.342 | 232 | 4 | 0.0172 | 2.16 | 0 | 4 | 22 |
| 2-star | 395 | 4 | 45 | 3 | 2 | 75 | 1 | 0 | 0 | 265 | 0.322 | 343 | 82 | 0.239 | 5 | 0 | 5 | 1 |
| 3-star | 410 | 10 | 42 | 4 | 0 | 51 | 5 | 0 | 0 | 298 | 0.263 | 354 | 70 | 0.198 | 7.74 | 0 | 18 | 5 |
| all | 1182 | 32 | 176 | 45 | 2 | 126 | 28 | 0 | 0 | 773 | 0.308 | 929 | 156 | 0.168 | 7.74 | 0 | 27 | 28 |
