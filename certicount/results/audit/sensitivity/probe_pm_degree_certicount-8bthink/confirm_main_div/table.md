# Confirm `main_div` — certicount-program

pairs 40 (file:results/audit/sensitivity/probe_pm_degree_qwen3-8b/confirm_main_div/pairs.jsonl), family α = 0.05, per pair α/m = 1.25e-03, eval trials per side 300 (jittery pairs 500), extra selection trials 20

**violations (ε_lb > ε3 = 2.0): 0 / 40**, of which real-node count-error type 0; ε_lb max 1.47, median 0.956; max observed |Δ| 1 (descriptive); distinct inputs x among the pairs 23, among the violations 0

An audit only refutes: zero violations is no evidence of privacy.

## Violations by kind × bin × category

(none)

## By kind × bin × family

| kind | bin | family | pairs | tested | violations | eps_lb_max | eps_lb_median | max_delta_llm_over_gs | exec_error_rate_x | exec_error_rate_x2 | jitter_rate_x | failure_rate_x |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| constructed | 61-120 | L | 2 | 2 | 0 | 1.22 | 0.983 | 1 | 0 | 0 | 0 | 0 |
| constructed | >120 | L | 2 | 2 | 0 | 0.606 | 0.522 | 1 | 0 | 0 | 0 | 0 |
| constructed | >120 | X | 7 | 7 | 0 | 1.29 | 1.1 | 1 | 0 | 0 | 0 | 0 |
| real | 31-60 | E | 9 | 9 | 0 | 1.2 | 0.891 | 1 | 0 | 0 | 0 | 0 |
| real | 61-120 | E | 16 | 16 | 0 | 1.47 | 0.871 | 1 | 0 | 0 | 0 | 0 |
| real | >120 | E | 4 | 4 | 0 | 1.22 | 1.11 | 1 | 0 | 0 | 0 | 0 |

## Confirmed pairs

(none)
