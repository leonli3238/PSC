# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs10_node_generic_gate_tri` (120 designs, 286 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| triangle | 286 | 3 | 117 | 2 | 0 | 12 | 82 | 6 | 0 | 64 | 0.769 | 164 | 27 | 0.165 | 8.67 | 0 | 1 | 82 |
| all | 286 | 3 | 117 | 2 | 0 | 12 | 82 | 6 | 0 | 64 | 0.769 | 164 | 27 | 0.165 | 8.67 | 0 | 1 | 82 |
