| Task | Method | CU | Avg. |
|---|---|---|---|
| degree | Naive | 1.1522 | 1.1522 |
| degree | *Naive (paper)* | *1.1020* | *1.1020* |
| degree | GT-Naive | 1.0684 | 1.0684 |
| degree | *GT-Naive (paper)* | *1.0707* | *1.0707* |
| degree | GT-PSC | 0.0182 | 0.0182 |
| degree | *GT-PSC (paper)* | *0.0187* | *0.0187* |
| 2-star | Naive | 5.0741 | 5.0741 |
| 2-star | *Naive (paper)* | *10.4517* | *10.4517* |
| 2-star | GT-Naive | 3.5982 | 3.5982 |
| 2-star | *GT-Naive (paper)* | *3.6030* | *3.6030* |
| 2-star | GT-PSC | 0.1545 | 0.1545 |
| 2-star | *GT-PSC (paper)* | *0.1062* | *0.1062* |
| 3-star | Naive | 16.1192 | 16.1192 |
| 3-star | *Naive (paper)* | *109.3320* | *109.3320* |
| 3-star | GT-Naive | 10.0666 | 10.0666 |
| 3-star | *GT-Naive (paper)* | *10.1186* | *10.1186* |
| 3-star | GT-PSC | 0.6954 | 0.6954 |
| 3-star | *GT-PSC (paper)* | *0.8035* | *0.8035* |
| triangle | Naive | 9.0544 | 9.0544 |
| triangle | *Naive (paper)* | *9.1228* | *9.1228* |
| triangle | GT-Naive | 1.4433 | 1.4433 |
| triangle | *GT-Naive (paper)* | *1.4545* | *1.4545* |
| triangle | GT-PSC | 1.0028 | 1.0028 |
| triangle | *GT-PSC (paper)* | *0.9612* | *0.9612* |

LLM error decomposition (same noise, per run):

| dataset | task | eps | method | runs | avg_relative_error | rule_relative_error | delta | delta_signed | se_delta_signed | exec_exact | exec_deviation | lucky_gain | lucky_runs | llm_harm | harm_runs | conservative_relative_error | optimistic_relative_error | rule_not_better_than_zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | degree | 2.0000 | Naive | 10 | 1.1522 | 1.0991 | 0.0532 | 0.0532 | 0.0501 | 0.3000 | 0.0965 | 0.0217 | 2 | 0.0749 | 5 | 1.1739 | 1.0774 | 0.9000 |
| CU | 2-star | 2.0000 | Naive | 10 | 5.0741 | 3.7404 | 1.3337 | 1.3337 | 0.9824 | 0.0000 | 2.3399 | 0.5031 | 4 | 1.8368 | 6 | 5.5772 | 3.2373 | 1.0000 |
| CU | 3-star | 2.0000 | Naive | 10 | 16.1192 | 10.5680 | 5.5512 | 5.5512 | 1.9572 | 0.0000 | 6.6800 | 0.5644 | 2 | 6.1156 | 8 | 16.6836 | 10.0036 | 1.0000 |
| CU | triangle | 2.0000 | Naive | 10 | 9.0544 | 1.5596 | 7.4947 | 7.4947 | 1.0133 | 0.0000 | 7.4947 | 0.0000 | 0 | 7.4947 | 10 | 9.0544 | 1.5596 | 0.9000 |
