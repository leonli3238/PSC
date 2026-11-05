# LLM-designed program pools + degree-first adaptive selection

eps = 2, 200 runs per cell (seed 0); selector: 1000 posterior samples (k-star), 4 simulations x 3 families (triangle), margin 0.1. Mean relative error (lower is better). `default` = PSC (library program, bound D, eps1 = r1 eps); every pool column is the adaptive selection over that pool on the same noise; `oracle-*` picks the best candidate of the pool on the real graph (not private).

## Pool design

Model requests (retries included): 12, made by the design run of `results/pool/pool_glm52_design_20261105/pools.json`; this evaluation made none. Public score: geometric mean over the public synthetic graphs of the best pool program on each.

| task | designer | calls | requests | proposed | certified | deployed | rejections | hand_score | pool_score | stopped |
|---|---|---|---|---|---|---|---|---|---|---|
| 2-star | llm | 3 | 3 | 12 | 2 | 0 | sensitivity=2, inexact=5, duplicate=3 | 0.0779 | 0.0779 | - |
| 2-star | random | 0 | - | 0 | 0 | 0 | - | 0.0779 | 0.0779 | - |
| 3-star | llm | 3 | 3 | 12 | 5 | 0 | inexact=2, sensitivity=1, parse=3, duplicate=1 | 0.2074 | 0.2074 | - |
| 3-star | random | 0 | - | 1 | 1 | 0 | - | 0.2074 | 0.2074 | - |
| triangle | llm | 3 | 3 | 12 | 5 | 1 | inexact=3, parse=1, duplicate=3 | 0.7853 | 0.6555 | - |
| triangle | random | 0 | - | 6 | 6 | 1 | - | 0.7853 | 0.6456 | - |
| 4-star | llm | 3 | 3 | 12 | 5 | 0 | parse=2, sensitivity=1, inexact=2, duplicate=2 | 0.3782 | 0.3782 | - |
| 4-star | random | 0 | - | 0 | 0 | 0 | - | 0.3782 | 0.3782 | - |

## Deployed pools

- **hand / 2-star**: `return comb(size(project(P, D)), 2) ; aggregate: total`
- **hand / 3-star**: `return comb(size(project(P, D)), 3) ; aggregate: total`
- **hand / triangle**: `S = P & N(self) ; return 0.5 * sum(size(P & N(j)) for j in S) ; aggregate: total / 3`
- **hand / 4-star**: `return comb(size(project(P, D)), 4) ; aggregate: total`
- **llm / 2-star**: `return comb(size(project(P, D)), 2) ; aggregate: total`
- **llm / 3-star**: `return comb(size(project(P, D)), 3) ; aggregate: total`
- **llm / triangle**: `S = P & N(self) ; return 0.5 * sum(size(P & N(j)) for j in S) ; aggregate: total / 3` · `S = project(P, D) ; return 0.5 * sum(size(N(self) & N(j)) for j in S) ; aggregate: total / 3`
- **llm / 4-star**: `return comb(size(project(P, D)), 4) ; aggregate: total`
- **random / 2-star**: `return comb(size(project(P, D)), 2) ; aggregate: total`
- **random / 3-star**: `return comb(size(project(P, D)), 3) ; aggregate: total`
- **random / triangle**: `S = P & N(self) ; return 0.5 * sum(size(P & N(j)) for j in S) ; aggregate: total / 3` · `return 0.5 * sum(size(P & N(j)) + size(project((P & N(j)), 2)) for j in P) ; aggregate: total / 6`
- **random / 4-star**: `return comb(size(project(P, D)), 4) ; aggregate: total`

## Averages over the datasets

`better/worse`: datasets with a significant paired difference (|z| > 1.96).

| task | default | hand | llm | random | oracle-hand | oracle-llm | oracle-random | GT-TriTR | hand_vs_default | llm_vs_default | random_vs_default | hand_better/worse | llm_better/worse | random_better/worse | llm_vs_hand | random_vs_hand | llm_vs_hand_better/worse | random_vs_hand_better/worse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2-star | 0.1093 | 0.1073 | 0.1073 | 0.1073 | 0.0521 | 0.0521 | 0.0521 | 0.2229 | -1.8% | -1.8% | -1.8% | 1/0 | 1/0 | 1/0 | +0.0% | +0.0% | 0/0 | 0/0 |
| 3-star | 0.3871 | 0.2962 | 0.2962 | 0.2962 | 0.1346 | 0.1346 | 0.1346 | 0.2383 | -23.5% | -23.5% | -23.5% | 3/0 | 3/0 | 3/0 | +0.0% | +0.0% | 0/0 | 0/0 |
| triangle | 0.9169 | 0.6692 | 0.6626 | 0.5527 | 0.3483 | 0.0728 | 0.2495 | 0.5374 | -27.0% | -27.7% | -39.7% | 4/0 | 5/0 | 4/1 | -1.0% | -17.4% | 1/0 | 4/1 |
| 4-star | 0.9901 | 0.5607 | 0.5607 | 0.5607 | 0.2354 | 0.2354 | 0.2354 | 0.3101 | -43.4% | -43.4% | -43.4% | 4/0 | 4/0 | 4/0 | +0.0% | +0.0% | 0/0 | 0/0 |

## Cells

`*_vs_hand`: paired mean difference to the hand pool ± 95% CI; `*_new_program`: share of runs in which the selector picked a program that is not the library program.

| dataset | task | default | hand | llm | random | oracle-hand | oracle-llm | oracle-random | GT-TriTR | llm_vs_hand | random_vs_hand | llm_new_program | random_new_program |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 2-star | 0.1638 | 0.1490 | 0.1490 | 0.1490 | 0.0607 | 0.0607 | 0.0607 | 0.3490 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| CU | 3-star | 0.7060 | 0.4225 | 0.4225 | 0.4225 | 0.1388 | 0.1388 | 0.1388 | 0.4080 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| CU | triangle | 1.0105 | 0.7975 | 0.7440 | 0.5821 | 0.5015 | 0.0720 | 0.3273 | 0.6576 | -0.0535 ± 0.0902 | -0.2153 ± 0.0341 | 0.8350 | 0.9700 |
| CU | 4-star | 2.3577 | 0.8913 | 0.8913 | 0.8913 | 0.2549 | 0.2549 | 0.2549 | 0.6640 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| Do | 2-star | 0.0978 | 0.0961 | 0.0961 | 0.0961 | 0.0450 | 0.0450 | 0.0450 | 0.2808 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| Do | 3-star | 0.3493 | 0.2552 | 0.2552 | 0.2552 | 0.1050 | 0.1050 | 0.1050 | 0.3204 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| Do | triangle | 0.8732 | 0.7353 | 0.7761 | 0.5542 | 0.4156 | 0.0681 | 0.2210 | 0.6198 | +0.0409 ± 0.0808 | -0.1811 ± 0.0375 | 0.7950 | 0.9250 |
| Do | 4-star | 0.9014 | 0.5209 | 0.5209 | 0.5209 | 0.1904 | 0.1904 | 0.1904 | 0.3797 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| ML | 2-star | 0.0866 | 0.0868 | 0.0868 | 0.0868 | 0.0572 | 0.0572 | 0.0572 | 0.1710 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| ML | 3-star | 0.2667 | 0.2712 | 0.2712 | 0.2712 | 0.1647 | 0.1647 | 0.1647 | 0.1641 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| ML | triangle | 0.4229 | 0.4345 | 0.3642 | 0.4228 | 0.3175 | 0.0467 | 0.2739 | 0.4375 | -0.0702 ± 0.0349 | -0.0117 ± 0.0194 | 0.7800 | 0.8550 |
| ML | 4-star | 0.4980 | 0.4762 | 0.4762 | 0.4762 | 0.2915 | 0.2915 | 0.2915 | 0.1672 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| CS | 2-star | 0.2128 | 0.2174 | 0.2174 | 0.2174 | 0.0968 | 0.0968 | 0.0968 | 0.3051 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| CS | 3-star | 0.6895 | 0.5174 | 0.5174 | 0.5174 | 0.2310 | 0.2310 | 0.2310 | 0.3223 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| CS | triangle | 1.6488 | 1.0461 | 1.1040 | 0.8245 | 0.5116 | 0.1283 | 0.4171 | 0.8174 | +0.0579 ± 0.1020 | -0.2217 ± 0.0729 | 0.7300 | 0.8650 |
| CS | 4-star | 1.5324 | 0.8814 | 0.8814 | 0.8814 | 0.3437 | 0.3437 | 0.3437 | 0.4386 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| EE | 2-star | 0.0495 | 0.0495 | 0.0495 | 0.0495 | 0.0299 | 0.0299 | 0.0299 | 0.1759 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| EE | 3-star | 0.1859 | 0.1860 | 0.1860 | 0.1860 | 0.1056 | 0.1056 | 0.1056 | 0.1810 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| EE | triangle | 0.4190 | 0.4357 | 0.4172 | 0.4673 | 0.3045 | 0.0829 | 0.2414 | 0.4193 | -0.0186 ± 0.0488 | +0.0316 ± 0.0252 | 0.7150 | 0.7200 |
| EE | 4-star | 0.4391 | 0.3826 | 0.3826 | 0.3826 | 0.2259 | 0.2259 | 0.2259 | 0.1755 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| PM | 2-star | 0.0451 | 0.0451 | 0.0451 | 0.0451 | 0.0227 | 0.0227 | 0.0227 | 0.0558 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| PM | 3-star | 0.1249 | 0.1249 | 0.1249 | 0.1249 | 0.0627 | 0.0627 | 0.0627 | 0.0339 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
| PM | triangle | 1.1272 | 0.5663 | 0.5698 | 0.4655 | 0.0388 | 0.0388 | 0.0162 | 0.2729 | +0.0035 ± 0.0056 | -0.1009 ± 0.0413 | 0.0300 | 0.9700 |
| PM | 4-star | 0.2116 | 0.2116 | 0.2116 | 0.2116 | 0.1058 | 0.1058 | 0.1058 | 0.0355 | +0.0000 ± 0.0000 | +0.0000 ± 0.0000 | 0.0000 | 0.0000 |
