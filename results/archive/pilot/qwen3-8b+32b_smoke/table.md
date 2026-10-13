| dataset | task | method | mechanism | runs | avg_relative_error | se_relative_error | rule_relative_error | delta | node_samples | node_update_acc | node_e2e_acc | send_acc | count_rel_diff | aggregate_acc | task_acc | parse_failures | api_retries | failed_calls | llm_calls_per_run |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | degree | PSC | floor_tight | 1 | 0.0046 | - | 0.0015 | 0.0031 | 49 | 1.0000 | 1.0000 | - | 0.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 52.0000 |
| CU | triangle | PSC | floor_tight | 1 | 3.7368 | - | 3.7977 | 0.0608 | 49 | 0.0000 | 0.0000 | 1.0000 | 5.0217 | 0.0000 | 1.0000 | 0 | 0 | 0 | 101.0000 |
| CU | 3-star | PSC | floor_tight | 1 | 3.9434 | - | 3.1494 | 0.7940 | 49 | 1.0000 | 1.0000 | - | 0.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 52.0000 |
| Do | degree | PSC | floor_tight | 1 | 0.0988 | - | 0.0061 | 0.0927 | 62 | 0.9839 | 0.9839 | - | 0.0346 | 0.0000 | 1.0000 | 0 | 0 | 0 | 65.0000 |
| Do | triangle | PSC | floor_tight | 1 | 0.1053 | - | 1.0000 | 0.8947 | 62 | 0.0161 | 0.0161 | 1.0000 | 1.4224 | 0.0000 | 1.0000 | 0 | 0 | 0 | 127.0000 |
| Do | 3-star | PSC | floor_tight | 1 | 0.6885 | - | 0.7157 | 0.0272 | 62 | 1.0000 | 1.0000 | - | 0.0000 | 0.0000 | 1.0000 | 0 | 0 | 0 | 65.0000 |
| CU | degree | Naive | floor_tight | 1 | 0.4019 | - | 0.8972 | 0.4953 | - | - | - | - | - | - | 1.0000 | 0 | 0 | 0 | 2.0000 |
| CU | triangle | Naive | floor_tight | 1 | 1.1579 | - | 0.8246 | 0.3333 | - | - | - | - | - | - | 1.0000 | 0 | 0 | 0 | 2.0000 |
| CU | 3-star | Naive | floor_tight | 1 | 2.1579 | - | 7.4798 | 5.3219 | - | - | - | - | - | - | 1.0000 | 0 | 0 | 0 | 2.0000 |
| Do | degree | Naive | floor_tight | 1 | 0.0566 | - | 1.1321 | 1.0755 | - | - | - | - | - | - | 1.0000 | 0 | 0 | 0 | 2.0000 |
| Do | triangle | Naive | floor_tight | 1 | 0.1789 | - | 1.7684 | 1.5895 | - | - | - | - | - | - | 1.0000 | 0 | 0 | 0 | 2.0000 |
| Do | 3-star | Naive | floor_tight | 1 | 1.2375 | - | 5.8974 | 4.6599 | - | - | - | - | - | - | 1.0000 | 0 | 0 | 0 | 2.0000 |
