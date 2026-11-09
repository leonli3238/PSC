# Confirm `random` — Qwen3-8B

pairs 60 (random), family α = 0.05, per pair α/m = 8.33e-04, eval trials per side 300 (jittery pairs 500), extra selection trials 30

**violations (ε_lb > ε3 = 2.0): 4 / 60**, of which real-node count-error type 4; ε_lb max 3.51, median 1.09; max observed |Δ| 41 (descriptive)

An audit only refutes: zero violations is no evidence of privacy.

## Violations by kind × bin × category

| kind | bin | category | violations |
|---|---|---|---|
| real | 31-60 | count | 2 |
| real | 61-120 | count | 2 |

## By kind × bin × family

| kind | bin | family | pairs | tested | violations | eps_lb_max | eps_lb_median | max_delta_llm_over_gs | exec_error_rate_x | exec_error_rate_x2 | jitter_rate_x | failure_rate_x |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| real | 1-10 | C | 1 | 1 | 0 | 0.49 | 0.49 | 1 | 0 | 0 | 0 | 0 |
| real | 1-10 | R | 11 | 11 | 0 | 1.31 | 1.11 | 1 | 0 | 0 | 0 | 0 |
| real | 11-30 | R | 29 | 29 | 0 | 1.9 | 1.09 | 2 | 0.0345 | 0.069 | 0 | 0 |
| real | 11-30 | S | 1 | 1 | 0 | 1.14 | 1.14 | 1 | 0 | 0 | 0 | 0 |
| real | 31-60 | E | 8 | 8 | 2 | 3.51 | 1.19 | 18 | 0.685 | 0.719 | 0.625 | 0 |
| real | 61-120 | E | 8 | 8 | 2 | 3.21 | 0.0746 | 41 | 1 | 1 | 1 | 0 |
| real | >120 | E | 2 | 2 | 0 | 0 | 0 | 28 | 1 | 1 | 1 | 0 |

## Confirmed pairs

| pair_id | kind | bin | family | category | eps_lb | delta_llm_max | exec_error | exec_error2 |
|---|---|---|---|---|---|---|---|---|
| n48-d59-b90250eaf8f2|add40 | real | 31-60 | E | count | 3.51 | 11 | 1 | 0.679 |
| n46-d59-1a445ec952d4|add189 | real | 31-60 | E | count | 3.29 | 18 | 1 | 0.964 |
| n57-d61-8edac2888720|add167 | real | 61-120 | E | count | 3.21 | 6 | 1 | 1 |
| n50-d64-09502dea74cd|add364 | real | 61-120 | E | count | 2.78 | 41 | 1 | 1 |
