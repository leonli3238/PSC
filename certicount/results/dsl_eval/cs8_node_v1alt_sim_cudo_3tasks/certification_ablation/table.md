# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs8_node_v1alt_sim_cudo_3tasks` (120 designs, 443 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| degree | 151 | 17 | 55 | 8 | 0 | 0 | 3 | 0 | 0 | 68 | 0.497 | 71 | 1 | 0.0141 | 2.16 | 0 | 1 | 3 |
| 2-star | 156 | 7 | 44 | 0 | 0 | 13 | 0 | 0 | 0 | 92 | 0.41 | 105 | 21 | 0.2 | 3.42 | 0 | 8 | 0 |
| 3-star | 136 | 5 | 23 | 1 | 1 | 17 | 0 | 0 | 0 | 89 | 0.338 | 107 | 20 | 0.187 | 5.33 | 0 | 2 | 0 |
| all | 443 | 29 | 122 | 9 | 1 | 30 | 3 | 0 | 0 | 249 | 0.418 | 283 | 42 | 0.148 | 5.33 | 0 | 11 | 3 |
