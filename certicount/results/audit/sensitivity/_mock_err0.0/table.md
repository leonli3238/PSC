# LLM node sensitivity audit

- model: `gpt-4.1-mini` (mock), temperature 0.0, 3 repeats per input, follow-up 50 samples on at most 20 pairs, α = 0.05
- sources: `gpt41mini-node_gpt41-curator_exp1_CU_degree_r10_PSC`, `gpt41mini-node_gpt41-curator_exp1_CU_3-star_r10_PSC`, `gpt41mini-node_gpt41-curator_exp1_CU_triangle_r10_PSC`
- plan checks: {'roundtrip_ok': 294, 'neighbors_ok': 294}
- robust violation: all repeats agree on both inputs and |L(x) − L(x')| > GS; ε_emp = ε3·|L(x) − L(x')|/GS (else the mixture loss of the repeats); confirmed: Clopper–Pearson ε_lb > ε3 on the follow-up samples

## Summary by task (random = S1, targeted = S2–S4)

| dataset | task | group | pairs | nodes | GS | ε3 | robust viol. | rate (95% CI) | suspect | confirmed / followed | max ε_emp/ε3 | P95 ε_emp/ε3 | exec err x / x' | jitter x / x' | parse fail x / x' |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 3-star | random | 222 | 98 | 45–136 | 1.6 | 0 | 0.000 (0.000–0.017) | 0 | 0 / 0 | 0.622 | 0.333 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| CU | 3-star | targeted | 170 | 98 | 45–136 | 1.6 | 0 | 0.000 (0.000–0.022) | 0 | 0 / 0 | 0.622 | 0.333 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| CU | 3-star | all | 392 | 98 | 45–136 | 1.6 | 0 | 0.000 (0.000–0.010) | 0 | 0 / 0 | 0.622 | 0.333 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| CU | degree | random | 315 | 98 | 1 | 2 | 0 | 0.000 (0.000–0.012) | 0 | 0 / 0 | 1.000 | 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| CU | degree | targeted | 77 | 77 | 1 | 2 | 0 | 0.000 (0.000–0.048) | 0 | 0 / 0 | 1.000 | 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| CU | degree | all | 392 | 98 | 1 | 2 | 0 | 0.000 (0.000–0.010) | 0 | 0 / 0 | 1.000 | 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| CU | triangle | random | 236 | 98 | 15–19 | 0.8 | 0 | 0.000 (0.000–0.016) | 0 | 0 / 0 | 0.167 | 0.132 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| CU | triangle | targeted | 156 | 95 | 15–19 | 0.8 | 0 | 0.000 (0.000–0.024) | 0 | 0 / 0 | 0.267 | 0.211 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| CU | triangle | all | 392 | 98 | 15–19 | 0.8 | 0 | 0.000 (0.000–0.010) | 0 | 0 / 0 | 0.267 | 0.184 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |

## By strategy

| dataset | task | strategy | pairs | robust viol. | suspect | max ε_emp/ε3 | mean |Δf|/GS | exec err x' |
|---|---|---|---|---|---|---|---|---|
| CU | 3-star | S1 | 222 | 0 | 0 | 0.622 | 0.103 | 0.000 |
| CU | 3-star | S2 | 96 | 0 | 0 | 0.622 | 0.128 | 0.000 |
| CU | 3-star | S3 | 52 | 0 | 0 | 0.467 | 0.113 | 0.000 |
| CU | 3-star | S4 | 22 | 0 | 0 | 0.022 | 0.015 | 0.000 |
| CU | degree | S1 | 315 | 0 | 0 | 1.000 | 1.000 | 0.000 |
| CU | degree | S3 | 77 | 0 | 0 | 1.000 | 1.000 | 0.000 |
| CU | triangle | S1 | 236 | 0 | 0 | 0.167 | 0.041 | 0.000 |
| CU | triangle | S2 | 93 | 0 | 0 | 0.267 | 0.139 | 0.000 |
| CU | triangle | S3 | 63 | 0 | 0 | 0.211 | 0.081 | 0.000 |

## Largest ε_emp / ε3

| task | run | node | strategy | flip | |P| → |P'| | GS | f(x) → f(x') | L(x) | L(x') | ε_emp/ε3 | ε_lb | robust |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| degree | 1 | 0 | S1 | add 27 | 4 → 5 | 1 | 4 → 5 | 4, 4, 4 | 5, 5, 5 | 1.000 | - | no |
| degree | 1 | 0 | S1 | remove 2 | 4 → 3 | 1 | 4 → 3 | 4, 4, 4 | 3, 3, 3 | 1.000 | - | no |
| degree | 1 | 0 | S3 | remove 3 | 4 → 3 | 1 | 4 → 3 | 4, 4, 4 | 3, 3, 3 | 1.000 | - | no |
| degree | 1 | 0 | S1 | remove 1 | 4 → 3 | 1 | 4 → 3 | 4, 4, 4 | 3, 3, 3 | 1.000 | - | no |
| degree | 1 | 2 | S1 | add 40 | 5 → 6 | 1 | 5 → 6 | 5, 5, 5 | 6, 6, 6 | 1.000 | - | no |
| degree | 1 | 2 | S1 | add 47 | 5 → 6 | 1 | 5 → 6 | 5, 5, 5 | 6, 6, 6 | 1.000 | - | no |
| degree | 1 | 2 | S3 | remove 4 | 5 → 4 | 1 | 5 → 4 | 5, 5, 5 | 4, 4, 4 | 1.000 | - | no |
| degree | 1 | 2 | S1 | add 37 | 5 → 6 | 1 | 5 → 6 | 5, 5, 5 | 6, 6, 6 | 1.000 | - | no |
| degree | 1 | 1 | S1 | add 15 | 2 → 3 | 1 | 2 → 3 | 2, 2, 2 | 3, 3, 3 | 1.000 | - | no |
| degree | 1 | 1 | S1 | remove 2 | 2 → 1 | 1 | 2 → 1 | 2, 2, 2 | 1, 1, 1 | 1.000 | - | no |
| degree | 1 | 1 | S3 | add 3 | 2 → 3 | 1 | 2 → 3 | 2, 2, 2 | 3, 3, 3 | 1.000 | - | no |
| degree | 1 | 1 | S1 | add 28 | 2 → 3 | 1 | 2 → 3 | 2, 2, 2 | 3, 3, 3 | 1.000 | - | no |
| degree | 1 | 3 | S1 | add 2 | 4 → 5 | 1 | 4 → 5 | 4, 4, 4 | 5, 5, 5 | 1.000 | - | no |
| degree | 1 | 3 | S1 | remove 0 | 4 → 3 | 1 | 4 → 3 | 4, 4, 4 | 3, 3, 3 | 1.000 | - | no |
| degree | 1 | 3 | S3 | remove 5 | 4 → 3 | 1 | 4 → 3 | 4, 4, 4 | 3, 3, 3 | 1.000 | - | no |

## Pairs with an execution error (0)

