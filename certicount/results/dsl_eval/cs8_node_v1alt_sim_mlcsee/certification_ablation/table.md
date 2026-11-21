# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs8_node_v1alt_sim_mlcsee` (240 designs, 935 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| degree | 236 | 26 | 94 | 18 | 0 | 0 | 13 | 0 | 0 | 85 | 0.564 | 98 | 2 | 0.0204 | 13 | 0 | 1 | 13 |
| 2-star | 247 | 14 | 68 | 7 | 0 | 27 | 0 | 0 | 0 | 131 | 0.441 | 158 | 39 | 0.247 | 3.42 | 0 | 12 | 0 |
| 3-star | 214 | 7 | 40 | 4 | 1 | 20 | 1 | 0 | 0 | 141 | 0.322 | 163 | 27 | 0.166 | 5.33 | 0 | 6 | 1 |
| triangle | 238 | 0 | 45 | 1 | 0 | 0 | 29 | 0 | 0 | 163 | 0.311 | 192 | 24 | 0.125 | 4 | 0 | 38 | 29 |
| all | 935 | 47 | 247 | 30 | 1 | 47 | 43 | 0 | 0 | 520 | 0.412 | 611 | 92 | 0.151 | 13 | 0 | 57 | 43 |
