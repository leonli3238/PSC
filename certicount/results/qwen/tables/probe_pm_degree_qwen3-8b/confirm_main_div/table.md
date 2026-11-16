# Confirm `main_div` — Qwen3-8B

pairs 40 (top:40, per node ≤ 2), family α = 0.05, per pair α/m = 1.25e-03, eval trials per side 300 (jittery pairs 500), extra selection trials 20

**violations (ε_lb > ε3 = 2.0): 24 / 40**, of which real-node count-error type 20; ε_lb max 4.19, median 3.25; max observed |Δ| 406 (descriptive); distinct inputs x among the pairs 23, among the violations 16

An audit only refutes: zero violations is no evidence of privacy.

## Violations by kind × bin × category

| kind | bin | category | violations |
|---|---|---|---|
| constructed | >120 | count | 4 |
| real | 31-60 | count | 8 |
| real | 61-120 | count | 9 |
| real | >120 | count | 3 |

## By kind × bin × family

| kind | bin | family | pairs | tested | violations | eps_lb_max | eps_lb_median | max_delta_llm_over_gs | exec_error_rate_x | exec_error_rate_x2 | jitter_rate_x | failure_rate_x |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| constructed | 61-120 | L | 2 | 2 | 0 | 0.36 | 0.18 | 406 | 1 | 0.571 | 1 | 0 |
| constructed | >120 | L | 2 | 2 | 0 | 0.437 | 0.294 | 352 | 1 | 0.73 | 1 | 0 |
| constructed | >120 | X | 7 | 7 | 4 | 3.84 | 2.29 | 353 | 1 | 1 | 0.857 | 0 |
| real | 31-60 | E | 9 | 9 | 8 | 4.16 | 3.9 | 31 | 0.776 | 0.865 | 0.444 | 0 |
| real | 61-120 | E | 16 | 16 | 9 | 4.19 | 3.14 | 47 | 1 | 1 | 0.875 | 0 |
| real | >120 | E | 4 | 4 | 3 | 4.14 | 3.83 | 332 | 1 | 1 | 1 | 0 |

## Confirmed pairs

| pair_id | kind | bin | family | category | eps_lb | delta_llm_max | exec_error | exec_error2 |
|---|---|---|---|---|---|---|---|---|
| n37-d63-5567428bd790|add440 | real | 61-120 | E | count | 4.19 | 47 | 1 | 1 |
| n48-d59-b90250eaf8f2|add330 | real | 31-60 | E | count | 4.16 | 21 | 1 | 0.798 |
| n8-d75-5331f4d88508|remove372 | real | 61-120 | E | count | 4.16 | 25 | 1 | 1 |
| n8-d75-5331f4d88508|remove373 | real | 61-120 | E | count | 4.15 | 25 | 1 | 1 |
| n14-d237-ef095c6ea966|remove113 | real | >120 | E | count | 4.14 | 332 | 1 | 1 |
| n14-d237-ef095c6ea966|remove121 | real | >120 | E | count | 4.1 | 332 | 1 | 1 |
| n6-d75-3928d319423e|remove373 | real | 61-120 | E | count | 4.05 | 23 | 1 | 1 |
| n48-d59-b90250eaf8f2|add336 | real | 31-60 | E | count | 4.04 | 21 | 1 | 0.331 |
| n37-d63-5567428bd790|add435 | real | 61-120 | E | count | 4.03 | 47 | 1 | 1 |
| n46-d59-1a445ec952d4|add412 | real | 31-60 | E | count | 4.03 | 27 | 1 | 0.977 |
| n46-d59-1a445ec952d4|add178 | real | 31-60 | E | count | 4.03 | 21 | 1 | 0.994 |
| n11-d57-d44a81f0ad2b|add19 | real | 31-60 | E | count | 3.9 | 21 | 0.992 | 1 |
| n57-d61-8edac2888720|add173 | real | 61-120 | E | count | 3.84 | 16 | 1 | 1 |
| n1-d150-d5bb82f6fbb5|remove452 | constructed | >120 | X | count | 3.84 | 350 | 1 | 1 |
| n1-d450-12710aba289b|remove57 | constructed | >120 | X | count | 3.63 | 197 | 1 | 1 |
| n1-d123-6c2f4d763dd7|add110 | real | >120 | E | count | 3.56 | 28 | 1 | 1 |
| n1-d350-60cd3f4679ba|remove0 | constructed | >120 | X | count | 3.53 | 10 | 1 | 1 |
| n11-d57-d44a81f0ad2b|remove444 | real | 31-60 | E | count | 3.39 | 31 | 0.992 | 1 |
| n3-d38-f25134ffb4e0|add434 | real | 31-60 | E | count | 3.31 | 5 | 0 | 0.958 |
| n50-d64-09502dea74cd|add275 | real | 61-120 | E | count | 3.25 | 41 | 1 | 1 |
| n55-d64-b3f9d2395290|add144 | real | 61-120 | E | count | 3.24 | 39 | 1 | 1 |
| n50-d64-09502dea74cd|add167 | real | 61-120 | E | count | 3.04 | 41 | 1 | 1 |
| n1-d350-60cd3f4679ba|remove242 | constructed | >120 | X | count | 2.29 | 10 | 1 | 1 |
| n12-d36-eb15d2acb744|add398 | real | 31-60 | E | count | 2.13 | 3 | 1 | 1 |
