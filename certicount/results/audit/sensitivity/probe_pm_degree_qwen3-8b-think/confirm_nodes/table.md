# Confirm `nodes` — Qwen3-8B

pairs 20 (file:results/audit/sensitivity/probe_pm_degree_qwen3-8b/confirm_nodes/pairs.jsonl), family α = 0.05, per pair α/m = 2.50e-03, eval trials per side 300 (jittery pairs 500), extra selection trials 20

**violations (ε_lb > ε3 = 2.0): 0 / 20**, of which real-node count-error type 0; ε_lb max 1.37, median 1.03; max observed |Δ| 1.02e+08 (descriptive); distinct inputs x among the pairs 20, among the violations 0

An audit only refutes: zero violations is no evidence of privacy.

## Violations by kind × bin × category

(none)

## By kind × bin × family

| kind | bin | family | pairs | tested | violations | eps_lb_max | eps_lb_median | max_delta_llm_over_gs | exec_error_rate_x | exec_error_rate_x2 | jitter_rate_x | failure_rate_x |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| real | 11-30 | S | 2 | 2 | 0 | 1.25 | 1.13 | 1 | 0 | 0 | 0 | 0 |
| real | 31-60 | E | 8 | 8 | 0 | 1.37 | 1.04 | 5 | 0.00195 | 0.0043 | 0.25 | 0 |
| real | 61-120 | E | 8 | 8 | 0 | 1.18 | 1.02 | 79 | 0.00352 | 0.00273 | 0.375 | 0 |
| real | >120 | E | 2 | 2 | 0 | 1 | 0.721 | 1.02e+08 | 0.108 | 0.169 | 1 | 0 |

## Confirmed pairs

(none)
