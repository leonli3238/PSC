# CS7 summary (per-node architecture, PM, ε = 2, held-out tasks)

## Deriver fuzzing: programs that read A, own bounds D != dmax

- cs7_fuzz_matrix: 3000 programs, 0 refuted or failing
- cs7_fuzz_node_rows: 3000 programs, 0 refuted or failing

| campaign | n | dmax | D | graphs | programs | reads_matrix | derived | refuted | tight | median_gs_over_max | max_gs_over_max |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cs7_fuzz_matrix | 5 | 3 | 3 | every | 3000 | 2825 | 3000 | 0 | 730 | 2.0000 | 7565.0291 |
| cs7_fuzz_matrix | 7 | 4 | 4 | 200 random | 3000 | 2825 | 3000 | 0 | 742 | 1.9592 | 1389.2553 |
| cs7_fuzz_matrix | 7 | 4 | 2 | 200 random | 3000 | 2825 | 3000 | 0 | 876 | 2.0000 | 1.065e+04 |
| cs7_fuzz_matrix | 6 | 3 | 5 | 200 random | 3000 | 2825 | 3000 | 0 | 680 | 2.0000 | 962.3558 |
| cs7_fuzz_node_rows | 5 | 3 | 2 | every | 3000 | 0 | 2947 | 0 | 1694 | 1.0000 | 252.0000 |
| cs7_fuzz_node_rows | 7 | 4 | 2 | 200 random | 3000 | 0 | 2947 | 0 | 1680 | 1.0000 | 340.0000 |
| cs7_fuzz_node_rows | 6 | 3 | 5 | 200 random | 3000 | 0 | 2947 | 0 | 1480 | 1.1667 | 780.0000 |

## Offline replay of the CS4/CS5 per-node runs (no model call)

| task | designs | pairs | reference_re | recorded_accept | recorded_re | recorded_own_row | nogate_accept | single_accept | single_re | pair_accept | pair_first_re | pair_choice_re | pair_reads |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 40 | 20 | 0.0105 | 0.8250 | 0.0373 | 12 | 0.9000 | 0.5250 | 0.0105 | 0.7500 | 0.0105 | 0.0105 | P |
| 5-star | 30 | 15 | 0.0212 | 0.9000 | 0.0561 | 9 | 0.9333 | 0.6000 | 0.0212 | 0.8667 | 0.0212 | 0.0212 | P |
| triangle | 40 | 20 | 0.1497 | 0.6750 | 0.2526 | 0 | 0.6750 | 0.6750 | 0.2526 | 0.8500 | 0.1498 | 0.1498 | A |
| degree-moment2 | 30 | 15 | 0.0083 | 0.8333 | 0.0412 | 16 | 0.9667 | 0.3000 | 0.0083 | 0.4667 | 0.0083 | 0.0083 | P |

Design-time simulated score against the real error: 3-star 0.92 (260 program pairs); 5-star 1.00 (60 program pairs); triangle 1.00 (48 program pairs); degree-moment2 1.00 (88 program pairs)

## Online arms


| task | arm | designs | accept_rate | accept_ci95 | mean_llm_calls | relative_error | median_relative_error | gt_dsl_relative_error | design_error | gs_ratio | noise_ratio | mean_candidates | runs_matrix |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | cs5_eval_node_evolved | 10 | 0.8000 | - | 1.8000 | 0.0250 | 0.0087 | 0.0087 | 0.0162 | 0.7500 | 0.7500 | - | - |
| 3-star | cs5_eval_node_v0 | 10 | 0.6000 | - | 1.9000 | 0.0412 | 0.0412 | 0.0087 | 0.0325 | 0.5000 | 0.5000 | - | - |
| 3-star | cs5_eval_node_v0-r2 | 10 | 1.0000 | - | 2.3000 | 0.0524 | 0.0737 | 0.0087 | 0.0436 | 1.1852 | 1.4962 | - | - |
| 3-star | cs7_node_v1alt_gate | 20 | 0.9500 | [0.76, 0.99] | 1.8500 | 0.0190 | 0.0087 | 0.0087 | 0.0103 | 0.8421 | 0.8421 | - | - |
| 3-star | cs7_node_v1alt_sim | 20 | 1.0000 | [0.84, 1.00] | 3.6000 | 0.0087 | 0.0087 | 0.0087 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| 3-star | cs7_node_v1alt_sim-noown | 20 | 0.8500 | [0.64, 0.95] | 2.9000 | 0.0087 | 0.0087 | 0.0087 | 0.0000 | 1.0000 | 1.0000 | 1.5500 | 0.0000 |
| 5-star | cs5_eval_node_evolved | 10 | 0.9000 | - | 1.2000 | 0.0820 | 0.1335 | 0.0176 | 0.0644 | 0.4444 | 0.4444 | - | - |
| 5-star | cs5_eval_node_v0 | 10 | 0.8000 | - | 1.6000 | 0.0321 | 0.0176 | 0.0176 | 0.0145 | 0.8750 | 0.8750 | - | - |
| 5-star | cs5_eval_node_v0-r2 | 10 | 1.0000 | - | 2.4000 | 0.0523 | 0.0176 | 0.0176 | 0.0348 | 0.7000 | 0.7000 | - | - |
| 5-star | cs7_node_v1alt_gate | 20 | 0.9000 | [0.70, 0.97] | 2.1500 | 0.0691 | 0.0176 | 0.0176 | 0.0515 | 0.5556 | 0.5556 | - | - |
| 5-star | cs7_node_v1alt_sim | 20 | 1.0000 | [0.84, 1.00] | 3.2000 | 0.0176 | 0.0176 | 0.0176 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| 5-star | cs7_node_v1alt_sim-noown | 20 | 0.9500 | [0.76, 0.99] | 2.7500 | 0.0176 | 0.0176 | 0.0176 | 0.0000 | 1.0000 | 1.0000 | 1.4000 | 0.0000 |
| degree-moment2 | cs5_eval_node_evolved | 10 | 0.8000 | - | 2.0000 | 0.0297 | 0.0297 | 0.0074 | 0.0223 | 2.4776 | 3.9389 | - | - |
| degree-moment2 | cs5_eval_node_v0 | 10 | 0.8000 | - | 1.9000 | 0.0353 | 0.0519 | 0.0074 | 0.0278 | 2.8075 | 4.6720 | - | - |
| degree-moment2 | cs5_eval_node_v0-r2 | 10 | 0.9000 | - | 3.3000 | 0.0420 | 0.0519 | 0.0074 | 0.0346 | 3.2400 | 5.5693 | - | - |
| degree-moment2 | cs7_node_v1alt_gate | 20 | 0.6500 | [0.43, 0.82] | 2.2000 | 0.0109 | 0.0074 | 0.0074 | 0.0034 | 1.2192 | 1.4518 | - | - |
| degree-moment2 | cs7_node_v1alt_sim | 20 | 0.9500 | [0.76, 0.99] | 4.2500 | 0.0074 | 0.0074 | 0.0074 | 0.0000 | 1.0000 | 1.0000 | 0.9500 | 0.0000 |
| degree-moment2 | cs7_node_v1alt_sim-noown | 20 | 0.9000 | [0.70, 0.97] | 3.9000 | 0.0099 | 0.0074 | 0.0074 | 0.0025 | 1.1583 | 1.3263 | 1.1500 | 0.0556 |
| triangle | cs5_eval_node_evolved | 10 | 0.3000 | - | 2.6000 | 0.1263 | 0.1263 | 0.1263 | 0.0000 | 0.8333 | 1.0000 | - | - |
| triangle | cs5_eval_node_v0 | 10 | 0.6000 | - | 2.0000 | 0.1267 | 0.1263 | 0.1263 | 0.0003872 | 0.5880 | 1.0003 | - | - |
| triangle | cs5_eval_node_v0-r2 | 10 | 1.0000 | - | 2.5000 | 0.4069 | 0.1263 | 0.1263 | 0.2807 | 0.5719 | 0.9385 | - | - |
| triangle | cs7_node_v1alt_gate | 20 | 0.6000 | [0.39, 0.78] | 2.1500 | 1.1820 | 1.5339 | 0.1263 | 1.0557 | 0.5966 | 0.5955 | - | - |
| triangle | cs7_node_v1alt_sim | 20 | 1.0000 | [0.84, 1.00] | 3.9000 | 0.1967 | 0.1263 | 0.1263 | 0.0704 | 0.9731 | 0.9730 | 1.9000 | 0.9500 |
| triangle | cs7_node_v1alt_sim-noown | 20 | 1.0000 | [0.84, 1.00] | 3.1000 | 0.1263 | 0.1263 | 0.1263 | 0.0000 | 1.0000 | 1.0000 | 1.8000 | 1.0000 |
| triangle | cs7_node_v1alt_sim_cudo | 20 | 1.0000 | [0.84, 1.00] | 3.9000 | 0.5530 | 0.5233 | 1.0465 | -0.4935 | 0.4890 | 0.4689 | 1.8000 | 0.0500 |
| triangle | cs7_node_v1alt_sim_cudo | 20 | 1.0000 | [0.84, 1.00] | 4.1000 | 0.4721 | 0.4185 | 0.7280 | -0.2559 | 0.9193 | 0.5218 | 1.7000 | 0.1500 |

cs5_* rows: CS5 per-node arms (prompt v0 / evolved, gate on; their gs_ratio is the raw ratio of the local GS).
