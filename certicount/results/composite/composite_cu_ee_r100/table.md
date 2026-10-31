# Composite queries

ε = 2.0, 100 runs; relative error |est - truth| / max(|truth|, 1e-3).

| dataset | plan | part | task | truth | undefined_runs | mean_relative_error | median_relative_error |
|---|---|---|---|---|---|---|---|
| CU | clustering | T | triangle | 57.0000 | 0 | 1.6359 | 1.0000 |
| CU | clustering | W | 2-star | 421.0000 | 0 | 0.8586 | 0.8145 |
| CU | clustering | combined | 3 * T / W | 0.4062 | 22 | 2.7317 | 1.0000 |
| CU | degree_and_3star | deg | degree | 4.3673 | 0 | 0.1082 | 0.0957 |
| CU | degree_and_3star | S3 | 3-star | 494.0000 | 0 | 0.6632 | 0.4132 |
| CU | degree_and_3star | combined | S3 | 494.0000 | 0 | 0.6632 | 0.4132 |
| CU | star_profile | S2 | 2-star | 421.0000 | 0 | 0.4095 | 0.2969 |
| CU | star_profile | S3 | 3-star | 494.0000 | 0 | 1.3144 | 1.0000 |
| CU | star_profile | S4 | 4-star | 382.0000 | 0 | 6.0763 | 1.0000 |
| CU | star_profile | combined | S3 / S2 | 1.1734 | 3 | 1.4045 | 1.0000 |
| EE | clustering | T | triangle | 889.0000 | 0 | 0.5544 | 0.5554 |
| EE | clustering | W | 2-star | 7427.0000 | 0 | 0.1656 | 0.1220 |
| EE | clustering | combined | 3 * T / W | 0.3591 | 0 | 0.6061 | 0.5859 |
| EE | degree_and_3star | deg | degree | 8.7133 | 0 | 0.0284 | 0.0230 |
| EE | degree_and_3star | S3 | 3-star | 3.954e+04 | 0 | 0.1918 | 0.1481 |
| EE | degree_and_3star | combined | S3 | 3.954e+04 | 0 | 0.1918 | 0.1481 |
| EE | star_profile | S2 | 2-star | 7427.0000 | 0 | 0.1464 | 0.1226 |
| EE | star_profile | S3 | 3-star | 3.954e+04 | 0 | 0.5061 | 0.4319 |
| EE | star_profile | S4 | 4-star | 2.138e+05 | 0 | 1.1056 | 1.0000 |
| EE | star_profile | combined | S3 / S2 | 5.3241 | 0 | 0.5657 | 0.4576 |

## Ledgers

### clustering

| release | eps | note |
|---|---|---|
| rr_graph | 1.0000 | randomized response, lower triangle |
| noisy_degrees | 0.2000 | deg + Lap(1/eps2) per node |
| report:T | 0.4000 | triangle: Lap(GS/eps3), GS = 18 |
| report:W | 0.4000 | 2-star: Lap(GS/eps3), GS = 18 |

### degree_and_3star

| release | eps | note |
|---|---|---|
| noisy_degrees | 0.4000 | deg + Lap(1/eps2) per node |
| noisy_degrees | 0.0000 | reused by deg (post-processing) |
| report:S3 | 1.6000 | 3-star: Lap(GS/eps3), GS = 136 |

### star_profile

| release | eps | note |
|---|---|---|
| noisy_degrees | 0.4000 | deg + Lap(1/eps2) per node |
| report:S2 | 0.5333 | 2-star: Lap(GS/eps3), GS = 17 |
| report:S3 | 0.5333 | 3-star: Lap(GS/eps3), GS = 136 |
| report:S4 | 0.5333 | 4-star: Lap(GS/eps3), GS = 680 |
