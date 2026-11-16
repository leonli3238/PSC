# Confirm `main` — Qwen3-1.7B

pairs 40 (top:40), family α = 0.05, per pair α/m = 1.25e-03, eval trials per side 300 (jittery pairs 500), extra selection trials 20

**violations (ε_lb > ε3 = 2.0): 38 / 40**, of which real-node count-error type 33; ε_lb max 4.2, median 4.11; max observed |Δ| 449 (descriptive)

An audit only refutes: zero violations is no evidence of privacy.

## Violations by kind × bin × category

| kind | bin | category | violations |
|---|---|---|---|
| constructed | >120 | count | 2 |
| real | 61-120 | count | 33 |
| real | 61-120 | number_fallback | 3 |

## By kind × bin × family

| kind | bin | family | pairs | tested | violations | eps_lb_max | eps_lb_median | max_delta_llm_over_gs | exec_error_rate_x | exec_error_rate_x2 | jitter_rate_x | failure_rate_x |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| constructed | >120 | L | 1 | 1 | 1 | 3.44 | 3.44 | 449 | 1 | 1 | 0 | 0 |
| constructed | >120 | X | 1 | 1 | 1 | 4.2 | 4.2 | 449 | 1 | 1 | 1 | 0 |
| real | 61-120 | E | 38 | 38 | 36 | 4.19 | 4.11 | 437 | 1 | 1 | 0 | 0 |

## Confirmed pairs

| pair_id | kind | bin | family | category | eps_lb | delta_llm_max | exec_error | exec_error2 |
|---|---|---|---|---|---|---|---|---|
| n14-d150-b1c54ece05d4|remove452 | constructed | >120 | X | count | 4.2 | 449 | 1 | 1 |
| n37-d63-5567428bd790|add103 | real | 61-120 | E | count | 4.19 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add138 | real | 61-120 | E | count | 4.19 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add133 | real | 61-120 | E | count | 4.18 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add120 | real | 61-120 | E | count | 4.18 | 437 | 1 | 1 |
| n37-d63-5567428bd790|add123 | real | 61-120 | E | count | 4.18 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add137 | real | 61-120 | E | count | 4.17 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add10 | real | 61-120 | E | count | 4.16 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add106 | real | 61-120 | E | count | 4.15 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add134 | real | 61-120 | E | count | 4.15 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add112 | real | 61-120 | E | count | 4.15 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add135 | real | 61-120 | E | count | 4.15 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add105 | real | 61-120 | E | number_fallback | 4.14 | 437 | 1 | 1 |
| n37-d63-5567428bd790|add126 | real | 61-120 | E | count | 4.14 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add136 | real | 61-120 | E | count | 4.14 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add13 | real | 61-120 | E | count | 4.13 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add142 | real | 61-120 | E | count | 4.13 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add132 | real | 61-120 | E | count | 4.13 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add131 | real | 61-120 | E | count | 4.12 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add140 | real | 61-120 | E | count | 4.12 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add116 | real | 61-120 | E | count | 4.11 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add122 | real | 61-120 | E | count | 4.11 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add125 | real | 61-120 | E | count | 4.11 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add141 | real | 61-120 | E | count | 4.11 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add145 | real | 61-120 | E | count | 4.11 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add124 | real | 61-120 | E | count | 4.1 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add312 | real | 61-120 | E | number_fallback | 4.08 | 437 | 1 | 1 |
| n37-d63-5567428bd790|add102 | real | 61-120 | E | count | 4.08 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add392 | real | 61-120 | E | number_fallback | 4.07 | 437 | 1 | 1 |
| n37-d63-5567428bd790|add117 | real | 61-120 | E | count | 4.07 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add139 | real | 61-120 | E | count | 4.04 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add443 | real | 61-120 | E | count | 4.03 | 437 | 1 | 1 |
| n37-d63-5567428bd790|add121 | real | 61-120 | E | count | 4.03 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add185 | real | 61-120 | E | count | 4 | 437 | 1 | 1 |
| n37-d63-5567428bd790|add144 | real | 61-120 | E | count | 4 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add104 | real | 61-120 | E | count | 4 | 395 | 1 | 1 |
| n37-d63-5567428bd790|add128 | real | 61-120 | E | count | 3.94 | 395 | 1 | 1 |
| n1-d199-3b53b6283c75|add223 | constructed | >120 | L | count | 3.44 | 449 | 1 | 1 |
