# A4: certification ablation of the curator's drafts

Source `results/dsl_eval/cs9_node_generic_sim_tri_ow` (60 designs, 302 drafts). Stage = first failed check of the design loop. `uncertified_violations`: runnable drafts whose largest flip change on small public graphs exceeds the task's reference GS, i.e. drafts that would break ε-edge LDP if executed with PSC-style noise Lap(GS_ref/ε3) without certification (as PSC's rule-calibrated controller would); `max_eps_ratio` = Δ / GS_ref = privacy loss / ε3 (lower bound). `certificate_unsound`: drafts whose measured change exceeds the GS the system itself derived — **must be 0**, otherwise the deriver is wrong. `accepted_looser_than_reference`: accepted drafts certified with a looser GS than the task's ideal bound (valid but less accurate, a cost of the design step, not a privacy break). `semantic_errors_published_without_check`: drafts the utility test rejects, i.e. wrong statistics that would be published if the test were skipped.

**Partial:** 180 design(s) without complete transcripts are not analysed (cells CS/triangle, CU/open-wedge, CU/triangle, Do/open-wedge, Do/triangle, ML/open-wedge, ML/triangle, PM/open-wedge, PM/triangle; list in `missing_transcripts.json`).

| task | drafts | truncated | parse | duplicate | gs_failed | gs_loose | semantic | noisy | refuted | accepted | rejected_share | runnable | uncertified_violations | uncertified_violation_share | max_eps_ratio | certificate_unsound | accepted_looser_than_reference | semantic_errors_published_without_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| open-wedge | 217 | 0 | 35 | 35 | 0 | 19 | 18 | 0 | 0 | 110 | 0.332 | 147 | 94 | 0.639 | 7 | 0 | 100 | 18 |
| triangle | 85 | 1 | 28 | 2 | 0 | 0 | 22 | 0 | 0 | 32 | 0.6 | 54 | 13 | 0.241 | 28.7 | 0 | 6 | 22 |
| all | 302 | 1 | 63 | 37 | 0 | 19 | 40 | 0 | 0 | 142 | 0.407 | 201 | 107 | 0.532 | 28.7 | 0 | 106 | 40 |
