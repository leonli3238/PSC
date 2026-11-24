# Certificate fault injection (node-side verification)

833 distinct programs (accepted release candidates of cs9_node_generic_sim_tri_ow,cs9_node_generic_sim_ext,cs9_node_generic_sim_4cycle,cs9_node_v1alt_sim_ow and the library references) x n in {49,143,453} x D = dmax in {5,10,20} (0 program/parameter sets without a finite GS skipped). Regimes: `trust` = the node uses the claimed GS; `legacy` = node check before 2026-11-23 (re-derives with the certificate's facts); `hardened` = `binding.check_program` (finite nonnegative GS, the environment's own facts). `accepted_unsafe` = accepted with a noise GS below the GS derived under the true environment (privacy violation, `violation`) or with a NaN / infinite / negative noise scale (`invalid`, availability failure). `max_eps3_multiple` = true GS / used GS: the realised privacy loss of the count release in units of ε3. Relative to the deriver (supported by the falsifier and fuzz runs, not proven).

## Unsafe acceptances and rejections

| tampering | cases | trust_accepted_unsafe | legacy_accepted_unsafe | hardened_accepted_unsafe | trust_rejected | legacy_rejected | hardened_rejected |
|---|---|---|---|---|---|---|---|
| honest | 7497 | 0/7497 | 0/7497 | 0/7497 | 0 | 0 | 0 |
| overstate x2 | 7497 | 0/7497 | 0/7497 | 0/7497 | 0 | 0 | 0 |
| understate x0.5 | 7479 | 7479/7479 | 0/7479 | 0/7479 | 0 | 7479 | 7479 |
| understate x0.1 | 7479 | 7479/7479 | 0/7479 | 0/7479 | 0 | 7479 | 7479 |
| understate to 0 | 7479 | 7479/7479 | 0/7479 | 0/7479 | 0 | 7479 | 7479 |
| nan | 7497 | 7497/7497 | 7497/7497 | 0/7497 | 0 | 0 | 7497 |
| inf | 7497 | 7497/7497 | 7497/7497 | 0/7497 | 0 | 0 | 7497 |
| negative | 7497 | 7497/7497 | 0/7497 | 0/7497 | 0 | 7497 | 7497 |
| other program | 7497 | 2973/7497 | 0/7497 | 0/7497 | 0 | 7497 | 7497 |
| smaller bound D | 7497 | 5763/7497 | 0/7497 | 0/7497 | 0 | 7497 | 7497 |
| unguaranteed facts | 14994 | 18/14994 | 18/14994 | 0/14994 | 0 | 0 | 14994 |
| honest (reduced env) | 14994 | 0/14994 | 0/14994 | 0/14994 | 0 | 0 | 0 |

## Breakdown

| tampering | cases | trust_violation | trust_invalid | legacy_violation | legacy_invalid | hardened_violation | hardened_invalid | trust_max_eps3_multiple | legacy_max_eps3_multiple | hardened_max_eps3_multiple |
|---|---|---|---|---|---|---|---|---|---|---|
| honest | 7497 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | - |
| overstate x2 | 7497 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | - |
| understate x0.5 | 7479 | 7479 | 0 | 0 | 0 | 0 | 0 | 2.0000 | - | - |
| understate x0.1 | 7479 | 7479 | 0 | 0 | 0 | 0 | 0 | 10.0000 | - | - |
| understate to 0 | 7479 | 7479 | 0 | 0 | 0 | 0 | 0 | inf | - | - |
| nan | 7497 | 0 | 7497 | 0 | 7497 | 0 | 0 | - | - | - |
| inf | 7497 | 0 | 7497 | 0 | 7497 | 0 | 0 | - | - | - |
| negative | 7497 | 0 | 7497 | 0 | 0 | 0 | 0 | - | - | - |
| other program | 7497 | 2973 | 0 | 0 | 0 | 0 | 0 | inf | - | - |
| smaller bound D | 7497 | 5763 | 0 | 0 | 0 | 0 | 0 | inf | - | - |
| unguaranteed facts | 14994 | 18 | 0 | 18 | 0 | 0 | 0 | 1.2500 | 1.2500 | - |
| honest (reduced env) | 14994 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | - |

Node-side verification cost (hardened, per certificate): median 0.03 ms, p95 0.84 ms, max 43.8 ms over 104904 checks.

Hardened failures: 0 (listed in summary.json).
