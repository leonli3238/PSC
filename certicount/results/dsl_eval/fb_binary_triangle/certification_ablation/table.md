# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/fb_binary_triangle` (90 designs, 446 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| triangle | 446 | 0 | 149 | 19 | 0 | 2 | 119 | 0 | 0 | 157 | 0.605 | 278 | 94 | 0.338 | 9.75 | 0 | 65 | 119 |
| all | 446 | 0 | 149 | 19 | 0 | 2 | 119 | 0 | 0 | 157 | 0.605 | 278 | 94 | 0.338 | 9.75 | 0 | 65 | 119 |
