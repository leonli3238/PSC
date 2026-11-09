# Confirm `random` — Qwen3-1.7B

pairs 60 (random), family α = 0.05, per pair α/m = 8.33e-04, eval trials per side 300 (jittery pairs 500), extra selection trials 20

**violations (ε_lb > ε3 = 2.0): 7 / 60**, of which real-node count-error type 7; ε_lb max 3.64, median 0.918; max observed |Δ| 395 (descriptive)

An audit only refutes: zero violations is no evidence of privacy.

## Violations by kind × bin × category

| kind | bin | category | violations |
|---|---|---|---|
| real | 11-30 | count | 5 |
| real | 61-120 | count | 2 |

## By kind × bin × family

| kind | bin | family | pairs | tested | violations | eps_lb_max | eps_lb_median | max_delta_llm_over_gs | exec_error_rate_x | exec_error_rate_x2 | jitter_rate_x | failure_rate_x |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| real | 1-10 | C | 1 | 1 | 0 | 0.984 | 0.984 | 1 | 0 | 0 | 0 | 0 |
| real | 1-10 | R | 11 | 11 | 0 | 1.29 | 0.933 | 1 | 0 | 0 | 0 | 0 |
| real | 11-30 | R | 29 | 29 | 5 | 2.84 | 1.12 | 2 | 0.379 | 0.311 | 0.069 | 0 |
| real | 11-30 | S | 1 | 1 | 0 | 0.664 | 0.664 | 1 | 0 | 0 | 0 | 0 |
| real | 31-60 | E | 8 | 8 | 0 | 1.31 | 0 | 4 | 0.75 | 0.875 | 0 | 0 |
| real | 61-120 | E | 8 | 8 | 2 | 3.64 | 0 | 395 | 0.875 | 1 | 0 | 0 |
| real | >120 | E | 2 | 2 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 |

## Confirmed pairs

| pair_id | kind | bin | family | category | eps_lb | delta_llm_max | exec_error | exec_error2 |
|---|---|---|---|---|---|---|---|---|
| n37-d63-5567428bd790|add124 | real | 61-120 | E | count | 3.64 | 395 | 1 | 1 |
| n50-d64-09502dea74cd|add364 | real | 61-120 | E | count | 3.55 | 36 | 0 | 1 |
| n65-d28-4a2742886ac8|add116 | real | 11-30 | R | count | 2.84 | 2 | 1 | 1 |
| n71-d15-a9357b884a83|add145 | real | 11-30 | R | count | 2.65 | 2 | 0 | 1 |
| n258-d13-e2ee03910ac4|add176 | real | 11-30 | R | count | 2.64 | 2 | 0.991 | 0 |
| n85-d24-270fecee5788|add435 | real | 11-30 | R | count | 2.35 | 2 | 1 | 1 |
| n182-d12-429eaccff126|add5 | real | 11-30 | R | count | 2.11 | 2 | 0 | 1 |
