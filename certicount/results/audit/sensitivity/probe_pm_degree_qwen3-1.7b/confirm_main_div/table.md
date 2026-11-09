# Confirm `main_div` — Qwen3-1.7B

pairs 40 (top:40, per node ≤ 2), family α = 0.05, per pair α/m = 1.25e-03, eval trials per side 300 (jittery pairs 500), extra selection trials 20

**violations (ε_lb > ε3 = 2.0): 38 / 40**, of which real-node count-error type 27; ε_lb max 4.21, median 3.63; max observed |Δ| 449 (descriptive); distinct inputs x among the pairs 24, among the violations 23

An audit only refutes: zero violations is no evidence of privacy.

## Violations by kind × bin × category

| kind | bin | category | violations |
|---|---|---|---|
| constructed | 31-60 | count | 1 |
| constructed | 61-120 | count | 1 |
| constructed | >120 | count | 5 |
| real | 11-30 | count | 6 |
| real | 31-60 | count | 8 |
| real | 61-120 | count | 10 |
| real | 61-120 | number_fallback | 4 |
| real | >120 | count | 3 |

## By kind × bin × family

| kind | bin | family | pairs | tested | violations | eps_lb_max | eps_lb_median | max_delta_llm_over_gs | exec_error_rate_x | exec_error_rate_x2 | jitter_rate_x | failure_rate_x |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| constructed | 31-60 | L | 1 | 1 | 1 | 4.02 | 4.02 | 5 | 1 | 1 | 0 | 0 |
| constructed | 61-120 | L | 1 | 1 | 1 | 3.56 | 3.56 | 351 | 1 | 1 | 0 | 0 |
| constructed | >120 | L | 2 | 2 | 1 | 3.69 | 1.84 | 449 | 1 | 1 | 0.5 | 0 |
| constructed | >120 | X | 4 | 4 | 4 | 4.16 | 3.87 | 449 | 1 | 1 | 0.5 | 0 |
| real | 11-30 | P | 1 | 1 | 1 | 3.63 | 3.63 | 19 | 0 | 1 | 0 | 0 |
| real | 11-30 | R | 3 | 3 | 3 | 4.14 | 3.5 | 6 | 0.667 | 1 | 0 | 0 |
| real | 11-30 | S | 2 | 2 | 2 | 3.63 | 3.55 | 6 | 1 | 1 | 0 | 0 |
| real | 31-60 | E | 9 | 9 | 8 | 4.17 | 3.62 | 334 | 0.889 | 1 | 0 | 0 |
| real | 61-120 | E | 14 | 14 | 14 | 4.21 | 3.61 | 437 | 0.857 | 1 | 0 | 0 |
| real | >120 | E | 3 | 3 | 3 | 3.69 | 3.69 | 100 | 1 | 1 | 0 | 0 |

## Confirmed pairs

| pair_id | kind | bin | family | category | eps_lb | delta_llm_max | exec_error | exec_error2 |
|---|---|---|---|---|---|---|---|---|
| n8-d75-5331f4d88508|remove20 | real | 61-120 | E | count | 4.21 | 248 | 1 | 1 |
| n8-d75-5331f4d88508|remove261 | real | 61-120 | E | count | 4.2 | 284 | 1 | 1 |
| n37-d63-5567428bd790|add185 | real | 61-120 | E | number_fallback | 4.2 | 437 | 1 | 1 |
| n11-d57-d44a81f0ad2b|remove326 | real | 31-60 | E | count | 4.17 | 334 | 1 | 1 |
| n14-d150-b1c54ece05d4|remove452 | constructed | >120 | X | count | 4.16 | 449 | 1 | 1 |
| n14-d150-b1c54ece05d4|add295 | constructed | >120 | X | count | 4.15 | 99 | 1 | 1 |
| n65-d28-4a2742886ac8|add371 | real | 11-30 | R | count | 4.14 | 6 | 1 | 1 |
| n48-d59-b90250eaf8f2|add69 | real | 31-60 | E | count | 4.12 | 36 | 1 | 1 |
| n14-d49-59129e905aba|add81 | constructed | 31-60 | L | count | 4.02 | 5 | 1 | 1 |
| n48-d59-b90250eaf8f2|add8 | real | 31-60 | E | count | 4.01 | 26 | 1 | 1 |
| n37-d63-5567428bd790|add105 | real | 61-120 | E | number_fallback | 3.99 | 437 | 1 | 1 |
| n55-d64-b3f9d2395290|remove8 | real | 61-120 | E | number_fallback | 3.69 | 349 | 1 | 1 |
| n1-d123-6c2f4d763dd7|add208 | real | >120 | E | count | 3.69 | 100 | 1 | 1 |
| n1-d199-3b53b6283c75|add223 | constructed | >120 | L | count | 3.69 | 449 | 1 | 1 |
| n14-d237-ef095c6ea966|add2 | real | >120 | E | count | 3.69 | 100 | 1 | 1 |
| n1-d123-6c2f4d763dd7|add128 | real | >120 | E | count | 3.67 | 100 | 1 | 1 |
| n50-d64-09502dea74cd|add0 | real | 61-120 | E | count | 3.65 | 36 | 0 | 1 |
| n54-d37-d4e00c4184e5|add441 | real | 31-60 | E | count | 3.64 | 9 | 1 | 1 |
| n143-d19-f81e8fc83ebc|remove390 | real | 11-30 | P | count | 3.63 | 19 | 0 | 1 |
| n96-d104-0de35713c8cd|add0 | real | 61-120 | E | count | 3.63 | 334 | 1 | 1 |
| n85-d24-270fecee5788|add249 | real | 11-30 | S | count | 3.63 | 5 | 1 | 1 |
| n46-d59-1a445ec952d4|add130 | real | 31-60 | E | count | 3.62 | 36 | 1 | 1 |
| n51-d35-f3b7b9f44ae0|add0 | real | 31-60 | E | count | 3.62 | 5 | 0 | 1 |
| n46-d59-1a445ec952d4|add11 | real | 31-60 | E | count | 3.61 | 36 | 1 | 1 |
| n57-d61-8edac2888720|add213 | real | 61-120 | E | count | 3.59 | 343 | 1 | 1 |
| n6-d75-3928d319423e|remove38 | real | 61-120 | E | count | 3.58 | 349 | 1 | 1 |
| n55-d64-b3f9d2395290|remove14 | real | 61-120 | E | number_fallback | 3.58 | 349 | 1 | 1 |
| n1-d450-12710aba289b|remove228 | constructed | >120 | X | count | 3.58 | 159 | 1 | 1 |
| n50-d64-09502dea74cd|add10 | real | 61-120 | E | count | 3.57 | 36 | 0 | 1 |
| n14-d99-60495914b2a7|add76 | constructed | 61-120 | L | count | 3.56 | 351 | 1 | 1 |
| n57-d61-8edac2888720|add108 | real | 61-120 | E | count | 3.55 | 343 | 1 | 1 |
| n96-d104-0de35713c8cd|add10 | real | 61-120 | E | count | 3.55 | 334 | 1 | 1 |
| n54-d37-d4e00c4184e5|add440 | real | 31-60 | E | count | 3.52 | 9 | 1 | 1 |
| n85-d24-270fecee5788|add242 | real | 11-30 | R | count | 3.5 | 5 | 1 | 1 |
| n65-d28-4a2742886ac8|add444 | real | 11-30 | S | count | 3.48 | 6 | 1 | 1 |
| n1-d450-12710aba289b|remove208 | constructed | >120 | X | count | 3.45 | 159 | 1 | 1 |
| n6-d75-3928d319423e|remove45 | real | 61-120 | E | count | 3.42 | 349 | 1 | 1 |
| n137-d21-b230a5c2fdd8|add3 | real | 11-30 | R | count | 3.38 | 5 | 0 | 1 |
