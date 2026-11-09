# Confirm `nodes` — Qwen3-8B

pairs 20 (nodes), family α = 0.05, per pair α/m = 2.50e-03, eval trials per side 300 (jittery pairs 500), extra selection trials 20

**violations (ε_lb > ε3 = 2.0): 15 / 20**, of which real-node count-error type 15; ε_lb max 4.3, median 2.94; max observed |Δ| 332 (descriptive); distinct inputs x among the pairs 20, among the violations 15

An audit only refutes: zero violations is no evidence of privacy.

## Node level (one most suspicious pair per selected real node)

`confirmed_share` is a lower bound on the share of violating nodes among the selected nodes of the bin (unconfirmed nodes may still violate; hub nodes are all PM nodes of degree > 30, the other bins are samples).

| bin | nodes | with_candidate | tested | confirmed | confirmed_share |
|---|---|---|---|---|---|
| 1-10 | 12 | 0 | 0 | 0 | 0 |
| 11-30 | 30 | 2 | 2 | 2 | 0.0667 |
| 31-60 | 8 | 8 | 8 | 6 | 0.75 |
| 61-120 | 8 | 8 | 8 | 6 | 0.75 |
| >120 | 2 | 2 | 2 | 1 | 0.5 |
| all | 60 | 20 | 20 | 15 | 0.25 |

## Violations by kind × bin × category

| kind | bin | category | violations |
|---|---|---|---|
| real | 11-30 | count | 2 |
| real | 31-60 | count | 6 |
| real | 61-120 | count | 6 |
| real | >120 | count | 1 |

## By kind × bin × family

| kind | bin | family | pairs | tested | violations | eps_lb_max | eps_lb_median | max_delta_llm_over_gs | exec_error_rate_x | exec_error_rate_x2 | jitter_rate_x | failure_rate_x |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| real | 11-30 | S | 2 | 2 | 2 | 2.64 | 2.32 | 2 | 0 | 0.874 | 0 | 0 |
| real | 31-60 | E | 8 | 8 | 6 | 4.07 | 2.69 | 31 | 0.684 | 0.912 | 0.5 | 0 |
| real | 61-120 | E | 8 | 8 | 6 | 4.26 | 3.52 | 47 | 1 | 1 | 1 | 0 |
| real | >120 | E | 2 | 2 | 1 | 4.3 | 2.92 | 332 | 1 | 1 | 1 | 0 |

## Confirmed pairs

| pair_id | kind | bin | family | category | eps_lb | delta_llm_max | exec_error | exec_error2 |
|---|---|---|---|---|---|---|---|---|
| n14-d237-ef095c6ea966|remove113 | real | >120 | E | count | 4.3 | 332 | 1 | 1 |
| n8-d75-5331f4d88508|remove372 | real | 61-120 | E | count | 4.26 | 25 | 1 | 1 |
| n6-d75-3928d319423e|remove373 | real | 61-120 | E | count | 4.2 | 23 | 1 | 1 |
| n37-d63-5567428bd790|add435 | real | 61-120 | E | count | 4.14 | 47 | 1 | 1 |
| n46-d59-1a445ec952d4|add412 | real | 31-60 | E | count | 4.07 | 27 | 1 | 0.971 |
| n48-d59-b90250eaf8f2|add330 | real | 31-60 | E | count | 3.7 | 21 | 1 | 0.755 |
| n50-d64-09502dea74cd|add167 | real | 61-120 | E | count | 3.69 | 41 | 1 | 1 |
| n11-d57-d44a81f0ad2b|remove444 | real | 31-60 | E | count | 3.48 | 31 | 0.99 | 1 |
| n55-d64-b3f9d2395290|add139 | real | 61-120 | E | count | 3.35 | 39 | 1 | 0.998 |
| n4-d109-54d24c5ea66f|add19 | real | 61-120 | E | count | 3.14 | 35 | 1 | 1 |
| n12-d36-eb15d2acb744|add398 | real | 31-60 | E | count | 2.74 | 3 | 1 | 1 |
| n3-d38-f25134ffb4e0|add434 | real | 31-60 | E | count | 2.64 | 5 | 0 | 0.96 |
| n26-d30-8a5f81f990d9|add11 | real | 11-30 | S | count | 2.64 | 2 | 0 | 1 |
| n51-d35-f3b7b9f44ae0|add1 | real | 31-60 | E | count | 2.46 | 2 | 0 | 1 |
| n65-d28-4a2742886ac8|add275 | real | 11-30 | S | count | 2.01 | 2 | 0 | 0.748 |
