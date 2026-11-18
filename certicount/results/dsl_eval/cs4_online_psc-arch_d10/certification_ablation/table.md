# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs4_online_psc-arch_d10` (40 designs, 74 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| degree | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 0 | 10 | 0 | 0 | 1 | 0 | 0 | 0 |
| 2-star | 15 | 0 | 3 | 0 | 0 | 2 | 0 | 1 | 0 | 9 | 0.4 | 12 | 2 | 0.167 | 1.67 | 0 | 1 | 0 |
| 3-star | 21 | 0 | 3 | 0 | 0 | 4 | 0 | 4 | 0 | 10 | 0.524 | 18 | 4 | 0.222 | 3.33 | 0 | 4 | 0 |
| triangle | 28 | 0 | 15 | 0 | 0 | 3 | 4 | 4 | 0 | 2 | 0.929 | 13 | 3 | 0.231 | 3.67 | 0 | 2 | 4 |
| all | 74 | 0 | 21 | 0 | 0 | 9 | 4 | 9 | 0 | 31 | 0.581 | 53 | 9 | 0.17 | 3.67 | 0 | 7 | 4 |
