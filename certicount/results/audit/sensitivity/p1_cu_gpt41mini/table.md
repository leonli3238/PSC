# LLM node sensitivity audit

- model: `gpt-4.1-mini` (openai), temperature 0.0, 3 repeats per input, follow-up 50 samples on at most 20 pairs, family α = 0.05
- sources: `gpt41mini-node_gpt41-curator_exp1_CU_degree_r10_PSC`, `gpt41mini-node_gpt41-curator_exp1_CU_3-star_r10_PSC`, `gpt41mini-node_gpt41-curator_exp1_CU_triangle_r10_PSC`
- plan checks: {'roundtrip_ok': 294, 'neighbors_ok': 294}
- all losses are conditional on the logged public history of the run (ε3 step only)
- screened: plug-in loss of the main repeats above ε3 (a screening flag, not a violation; the screen rate CI is for the flag); excess = no jitter observed and |L(x) − L(x')| > GS; suspect = jitter observed
- confirmed: Clopper–Pearson ε_lb > ε3 on the follow-up samples, Bonferroni over the followed pairs (all bounds hold together with probability 1 − α); ε3 lb = largest ε_lb

## Summary by task (random = S1, targeted = S2–S4)

| dataset | task | group | pairs | nodes | GS | ε3 | screened (excess / suspect) | screen rate (95% CI) | confirmed / followed | screened, not followed | ε3 lb | max plug-in ε/ε3 | P95 plug-in ε/ε3 | exec err x / x' | jitter x / x' | parse fail x / x' |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 3-star | random | 222 | 98 | 45–136 | 1.6 | 0 (0 / 0) | 0.000 (0.000–0.017) | 0 / 0 | 0 | - | 0.622 | 0.333 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| CU | 3-star | targeted | 170 | 98 | 45–136 | 1.6 | 0 (0 / 0) | 0.000 (0.000–0.022) | 0 / 0 | 0 | - | 0.622 | 0.333 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| CU | 3-star | all | 392 | 98 | 45–136 | 1.6 | 0 (0 / 0) | 0.000 (0.000–0.010) | 0 / 0 | 0 | - | 0.622 | 0.333 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| CU | degree | random | 315 | 98 | 1 | 2 | 0 (0 / 0) | 0.000 (0.000–0.012) | 0 / 0 | 0 | - | 1.000 | 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| CU | degree | targeted | 77 | 77 | 1 | 2 | 0 (0 / 0) | 0.000 (0.000–0.048) | 0 / 0 | 0 | - | 1.000 | 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| CU | degree | all | 392 | 98 | 1 | 2 | 0 (0 / 0) | 0.000 (0.000–0.010) | 0 / 0 | 0 | - | 1.000 | 1.000 | 0.000 / 0.000 | 0.000 / 0.000 | 0.000 / 0.000 |
| CU | triangle | random | 142 | 59 | 15–19 | 0.8 | 0 (0 / 0) | 0.000 (0.000–0.026) | 0 / 0 | 0 | - | 0.167 | 0.133 | 0.009 / 0.007 | 0.014 / 0.014 | 0.000 / 0.000 |
| CU | triangle | targeted | 94 | 56 | 15–19 | 0.8 | 0 (0 / 0) | 0.000 (0.000–0.039) | 0 / 0 | 0 | - | 0.267 | 0.211 | 0.014 / 0.004 | 0.021 / 0.011 | 0.000 / 0.000 |
| CU | triangle | all | 236 | 59 | 15–19 | 0.8 | 0 (0 / 0) | 0.000 (0.000–0.016) | 0 / 0 | 0 | - | 0.267 | 0.200 | 0.011 / 0.006 | 0.017 / 0.013 | 0.000 / 0.000 |

## By strategy

| dataset | task | strategy | pairs | screened | confirmed | max plug-in ε/ε3 | mean |Δf|/GS | exec err x' |
|---|---|---|---|---|---|---|---|---|
| CU | 3-star | S1 | 222 | 0 | 0 | 0.622 | 0.103 | 0.000 |
| CU | 3-star | S2 | 96 | 0 | 0 | 0.622 | 0.128 | 0.000 |
| CU | 3-star | S3 | 52 | 0 | 0 | 0.467 | 0.113 | 0.000 |
| CU | 3-star | S4 | 22 | 0 | 0 | 0.022 | 0.015 | 0.000 |
| CU | degree | S1 | 315 | 0 | 0 | 1.000 | 1.000 | 0.000 |
| CU | degree | S3 | 77 | 0 | 0 | 1.000 | 1.000 | 0.000 |
| CU | triangle | S1 | 142 | 0 | 0 | 0.167 | 0.043 | 0.007 |
| CU | triangle | S2 | 55 | 0 | 0 | 0.267 | 0.142 | 0.006 |
| CU | triangle | S3 | 39 | 0 | 0 | 0.211 | 0.084 | 0.000 |

## Largest plug-in ε / ε3

| task | run | node | strategy | flip | |P| → |P'| | GS | f(x) → f(x') | L(x) | L(x') | plug-in ε/ε3 | ε_lb | confirmed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| degree | 1 | 0 | S1 | add 27 | 4 → 5 | 1 | 4 → 5 | 4, 4, 4 | 5, 5, 5 | 1.000 | - | - |
| degree | 1 | 0 | S1 | remove 2 | 4 → 3 | 1 | 4 → 3 | 4, 4, 4 | 3, 3, 3 | 1.000 | - | - |
| degree | 1 | 0 | S3 | remove 3 | 4 → 3 | 1 | 4 → 3 | 4, 4, 4 | 3, 3, 3 | 1.000 | - | - |
| degree | 1 | 0 | S1 | remove 1 | 4 → 3 | 1 | 4 → 3 | 4, 4, 4 | 3, 3, 3 | 1.000 | - | - |
| degree | 1 | 2 | S1 | add 40 | 5 → 6 | 1 | 5 → 6 | 5, 5, 5 | 6, 6, 6 | 1.000 | - | - |
| degree | 1 | 2 | S1 | add 47 | 5 → 6 | 1 | 5 → 6 | 5, 5, 5 | 6, 6, 6 | 1.000 | - | - |
| degree | 1 | 2 | S3 | remove 4 | 5 → 4 | 1 | 5 → 4 | 5, 5, 5 | 4, 4, 4 | 1.000 | - | - |
| degree | 1 | 2 | S1 | add 37 | 5 → 6 | 1 | 5 → 6 | 5, 5, 5 | 6, 6, 6 | 1.000 | - | - |
| degree | 1 | 1 | S1 | add 15 | 2 → 3 | 1 | 2 → 3 | 2, 2, 2 | 3, 3, 3 | 1.000 | - | - |
| degree | 1 | 1 | S1 | remove 2 | 2 → 1 | 1 | 2 → 1 | 2, 2, 2 | 1, 1, 1 | 1.000 | - | - |
| degree | 1 | 1 | S3 | add 3 | 2 → 3 | 1 | 2 → 3 | 2, 2, 2 | 3, 3, 3 | 1.000 | - | - |
| degree | 1 | 1 | S1 | add 28 | 2 → 3 | 1 | 2 → 3 | 2, 2, 2 | 3, 3, 3 | 1.000 | - | - |
| degree | 1 | 3 | S1 | add 2 | 4 → 5 | 1 | 4 → 5 | 4, 4, 4 | 5, 5, 5 | 1.000 | - | - |
| degree | 1 | 3 | S1 | remove 0 | 4 → 3 | 1 | 4 → 3 | 4, 4, 4 | 3, 3, 3 | 1.000 | - | - |
| degree | 1 | 3 | S3 | remove 5 | 4 → 3 | 1 | 4 → 3 | 4, 4, 4 | 3, 3, 3 | 1.000 | - | - |

## Pairs with an execution error (7)

| task | run | node | strategy | flip | f(x) → f(x') | L(x) | L(x') | |Δ_LLM| − |Δf| |
|---|---|---|---|---|---|---|---|---|
| triangle | 1 | 20 | S1 | remove 21 | 2 → 0 | 2, 2, 2 | 0, 0, 1 | 0 |
| triangle | 2 | 2 | S1 | add 27 | 7 → 8.5 | 7, 7, 7 | 8.5, 6.5, 8 | 0 |
| triangle | 2 | 3 | S1 | remove 5 | 3.5 → 1.5 | 4, 3.5, 4 | 1.5, 1.5, 1.5 | 0.5 |
| triangle | 2 | 3 | S1 | add 2 | 3.5 → 6.5 | 4, 3.5, 4 | 6.5, 6.5, 6.5 | 0 |
| triangle | 2 | 3 | S2 | add 1 | 3.5 → 6.5 | 4, 3.5, 4 | 6.5, 6.5, 6.5 | 0 |
| triangle | 2 | 3 | S3 | remove 0 | 3.5 → 1 | 4, 3.5, 4 | 1, 1, 1 | 0.5 |
| triangle | 2 | 5 | S2 | add 2 | 2 → 5 | 2, 2, 2 | 4.5, 5, 5 | 0 |
