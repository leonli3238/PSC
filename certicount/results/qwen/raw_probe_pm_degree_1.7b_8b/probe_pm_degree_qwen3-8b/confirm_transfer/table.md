# Confirm `transfer` — Qwen3-8B

pairs 38 (confirmed:results/audit/sensitivity/probe_pm_degree_qwen3-1.7b/confirm_main), family α = 0.05, per pair α/m = 1.32e-03, eval trials per side 300 (jittery pairs 500), extra selection trials 30

**violations (ε_lb > ε3 = 2.0): 8 / 38**, of which real-node count-error type 8; ε_lb max 2.42, median 0; max observed |Δ| 352 (descriptive)

An audit only refutes: zero violations is no evidence of privacy.

## Violations by kind × bin × category

| kind | bin | category | violations |
|---|---|---|---|
| real | 61-120 | count | 8 |

## By kind × bin × family

| kind | bin | family | pairs | tested | violations | eps_lb_max | eps_lb_median | max_delta_llm_over_gs | exec_error_rate_x | exec_error_rate_x2 | jitter_rate_x | failure_rate_x |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| constructed | >120 | L | 1 | 1 | 0 | 0 | 0 | 330 | 1 | 1 | 1 | 0 |
| constructed | >120 | X | 1 | 1 | 0 | 0 | 0 | 352 | 1 | 1 | 1 | 0 |
| real | 61-120 | E | 36 | 36 | 8 | 2.42 | 0.0144 | 40 | 1 | 1 | 1 | 0 |

## Confirmed pairs

| pair_id | kind | bin | family | category | eps_lb | delta_llm_max | exec_error | exec_error2 |
|---|---|---|---|---|---|---|---|---|
| n37-d63-5567428bd790|add102 | real | 61-120 | E | count | 2.42 | 30 | 1 | 1 |
| n37-d63-5567428bd790|add10 | real | 61-120 | E | count | 2.35 | 27 | 1 | 1 |
| n37-d63-5567428bd790|add13 | real | 61-120 | E | count | 2.34 | 27 | 1 | 1 |
| n37-d63-5567428bd790|add443 | real | 61-120 | E | count | 2.33 | 40 | 1 | 1 |
| n37-d63-5567428bd790|add134 | real | 61-120 | E | count | 2.24 | 27 | 1 | 1 |
| n37-d63-5567428bd790|add138 | real | 61-120 | E | count | 2.23 | 27 | 1 | 1 |
| n37-d63-5567428bd790|add139 | real | 61-120 | E | count | 2.15 | 27 | 1 | 1 |
| n37-d63-5567428bd790|add133 | real | 61-120 | E | count | 2.04 | 27 | 1 | 1 |
