# Confirm `random` — certicount-program:degree:6c7d10f2a71f19c2

pairs 60 (file:results/qwen/probe_pm_degree_qwen3-1.7b/confirm_random), family α = 0.05, per pair α/m = 8.33e-04, eval trials per side 300 (jittery pairs 500), extra selection trials 20

**violations (ε_lb > ε3 = 2.0): 0 / 60**, of which real-node count-error type 0; ε_lb max 1.39, median 0.94; max observed |Δ| 1 (descriptive); distinct inputs x among the pairs 60, among the violations 0

An audit only refutes: zero violations is no evidence of privacy.

## Violations by kind × bin × category

(none)

## By kind × bin × family

| kind | bin | family | pairs | tested | violations | eps_lb_max | eps_lb_median | max_delta_llm_over_gs | exec_error_rate_x | exec_error_rate_x2 | jitter_rate_x | failure_rate_x |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| real | 1-10 | C | 1 | 1 | 0 | 0.843 | 0.843 | 1 | 0 | 0 | 0 | 0 |
| real | 1-10 | R | 11 | 11 | 0 | 1.35 | 1.08 | 1 | 0 | 0 | 0 | 0 |
| real | 11-30 | R | 29 | 29 | 0 | 1.39 | 0.958 | 1 | 0 | 0 | 0 | 0 |
| real | 11-30 | S | 1 | 1 | 0 | 0.874 | 0.874 | 1 | 0 | 0 | 0 | 0 |
| real | 31-60 | E | 8 | 8 | 0 | 1.09 | 0.903 | 1 | 0 | 0 | 0 | 0 |
| real | 61-120 | E | 8 | 8 | 0 | 1.02 | 0.722 | 1 | 0 | 0 | 0 | 0 |
| real | >120 | E | 2 | 2 | 0 | 1.28 | 1.2 | 1 | 0 | 0 | 0 | 0 |

## Confirmed pairs

(none)
