# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs6c_psc_evolved` (40 designs, 58 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 0 | 10 | 0 | 0 | 1 | 0 | 0 | 0 |
| 5-star | 11 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 0.0909 | 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| triangle | 26 | 0 | 8 | 1 | 0 | 1 | 12 | 1 | 0 | 3 | 0.846 | 17 | 8 | 0.471 | 30.3 | 0 | 1 | 12 |
| degree-moment2 | 11 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 10 | 0.0909 | 11 | 1 | 0.0909 | 1.57 | 0 | 0 | 0 |
| all | 58 | 0 | 9 | 1 | 0 | 2 | 12 | 1 | 0 | 33 | 0.414 | 48 | 9 | 0.188 | 30.3 | 0 | 1 | 12 |
