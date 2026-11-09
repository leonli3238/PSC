# Confirm `nodes` — Qwen3-1.7B

pairs 36 (nodes), family α = 0.05, per pair α/m = 1.39e-03, eval trials per side 300 (jittery pairs 500), extra selection trials 20

**violations (ε_lb > ε3 = 2.0): 31 / 36**, of which real-node count-error type 29; ε_lb max 4.01, median 3.51; max observed |Δ| 437 (descriptive); distinct inputs x among the pairs 36, among the violations 31

An audit only refutes: zero violations is no evidence of privacy.

## Node level (one most suspicious pair per selected real node)

`confirmed_share` is a lower bound on the share of violating nodes among the selected nodes of the bin (unconfirmed nodes may still violate; hub nodes are all PM nodes of degree > 30, the other bins are samples).

| bin | nodes | with_candidate | tested | confirmed | confirmed_share |
|---|---|---|---|---|---|
| 1-10 | 12 | 0 | 0 | 0 | 0 |
| 11-30 | 30 | 19 | 19 | 14 | 0.467 |
| 31-60 | 8 | 8 | 8 | 8 | 1 |
| 61-120 | 8 | 7 | 7 | 7 | 0.875 |
| >120 | 2 | 2 | 2 | 2 | 1 |
| all | 60 | 36 | 36 | 31 | 0.517 |

## Violations by kind × bin × category

| kind | bin | category | violations |
|---|---|---|---|
| real | 11-30 | count | 14 |
| real | 31-60 | count | 8 |
| real | 61-120 | count | 5 |
| real | 61-120 | number_fallback | 2 |
| real | >120 | count | 2 |

## By kind × bin × family

| kind | bin | family | pairs | tested | violations | eps_lb_max | eps_lb_median | max_delta_llm_over_gs | exec_error_rate_x | exec_error_rate_x2 | jitter_rate_x | failure_rate_x |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| real | 11-30 | P | 12 | 12 | 8 | 3.68 | 2.26 | 19 | 0.333 | 0.75 | 0.0833 | 0 |
| real | 11-30 | R | 4 | 4 | 3 | 3.7 | 3.65 | 8 | 0.5 | 1 | 0.25 | 0 |
| real | 11-30 | S | 3 | 3 | 3 | 3.05 | 2.73 | 3 | 0.667 | 0.667 | 0 | 0 |
| real | 31-60 | E | 8 | 8 | 8 | 4.01 | 3.61 | 334 | 0.75 | 1 | 0.375 | 0 |
| real | 61-120 | E | 7 | 7 | 7 | 3.68 | 3.64 | 437 | 0.857 | 1 | 0 | 0 |
| real | >120 | E | 2 | 2 | 2 | 3.65 | 3.64 | 100 | 1 | 1 | 0 | 0 |

## Confirmed pairs

| pair_id | kind | bin | family | category | eps_lb | delta_llm_max | exec_error | exec_error2 |
|---|---|---|---|---|---|---|---|---|
| n48-d59-b90250eaf8f2|add69 | real | 31-60 | E | count | 4.01 | 36 | 1 | 1 |
| n51-d35-f3b7b9f44ae0|add0 | real | 31-60 | E | count | 3.7 | 5 | 0 | 1 |
| n65-d28-4a2742886ac8|add371 | real | 11-30 | R | count | 3.7 | 8 | 1 | 1 |
| n85-d24-270fecee5788|add242 | real | 11-30 | R | count | 3.69 | 5 | 1 | 1 |
| n6-d75-3928d319423e|remove38 | real | 61-120 | E | count | 3.68 | 349 | 1 | 1 |
| n143-d19-f81e8fc83ebc|remove390 | real | 11-30 | P | count | 3.68 | 19 | 0 | 1 |
| n37-d63-5567428bd790|add105 | real | 61-120 | E | number_fallback | 3.66 | 437 | 1 | 1 |
| n54-d37-d4e00c4184e5|add440 | real | 31-60 | E | count | 3.65 | 9 | 0.997 | 1 |
| n14-d237-ef095c6ea966|add2 | real | >120 | E | count | 3.65 | 100 | 1 | 1 |
| n57-d61-8edac2888720|add108 | real | 61-120 | E | count | 3.65 | 343 | 1 | 1 |
| n8-d75-5331f4d88508|remove261 | real | 61-120 | E | count | 3.64 | 284 | 1 | 1 |
| n96-d104-0de35713c8cd|add0 | real | 61-120 | E | count | 3.64 | 334 | 1 | 1 |
| n1-d123-6c2f4d763dd7|add128 | real | >120 | E | count | 3.63 | 100 | 1 | 1 |
| n24-d33-9f55cc6217f1|add0 | real | 31-60 | E | count | 3.62 | 4 | 1 | 1 |
| n137-d21-b230a5c2fdd8|add3 | real | 11-30 | R | count | 3.61 | 6 | 0 | 1 |
| n11-d57-d44a81f0ad2b|remove326 | real | 31-60 | E | count | 3.6 | 334 | 1 | 1 |
| n50-d64-09502dea74cd|add0 | real | 61-120 | E | count | 3.59 | 36 | 0 | 1 |
| n234-d21-47aaa5f8d82f|remove1 | real | 11-30 | P | count | 3.52 | 3 | 1 | 1 |
| n55-d64-b3f9d2395290|remove14 | real | 61-120 | E | number_fallback | 3.51 | 349 | 1 | 1 |
| n12-d36-eb15d2acb744|add315 | real | 31-60 | E | count | 3.47 | 4 | 1 | 1 |
| n46-d59-1a445ec952d4|add11 | real | 31-60 | E | count | 3.39 | 36 | 1 | 1 |
| n153-d16-aefc60ad9893|add0 | real | 11-30 | P | count | 3.35 | 2 | 0 | 1 |
| n3-d38-f25134ffb4e0|add10 | real | 31-60 | E | count | 3.22 | 4 | 0 | 1 |
| n113-d23-27eb52e63e64|add146 | real | 11-30 | S | count | 3.05 | 3 | 1 | 1 |
| n182-d12-429eaccff126|add0 | real | 11-30 | P | count | 2.77 | 2 | 0 | 1 |
| n64-d16-4625cbcdf2dc|remove11 | real | 11-30 | S | count | 2.73 | 2 | 1 | 0 |
| n119-d15-c792b023c859|add1 | real | 11-30 | P | count | 2.38 | 2 | 0 | 1 |
| n272-d15-771b3d8d7120|add290 | real | 11-30 | S | count | 2.28 | 2 | 0 | 1 |
| n244-d11-3a230ecbd82f|remove1 | real | 11-30 | P | count | 2.27 | 2 | 1 | 0 |
| n147-d16-ac255c1762d9|remove1 | real | 11-30 | P | count | 2.25 | 2 | 1 | 0 |
| n71-d15-a9357b884a83|add0 | real | 11-30 | P | count | 2.19 | 2 | 0 | 1 |
