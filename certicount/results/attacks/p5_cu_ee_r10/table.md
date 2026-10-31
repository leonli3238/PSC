# P5 attack cases

ε = 2.0, 10 runs per dataset (run i uses the noise of seed [0, i]); undefended = obedient node, defended = binding + strict message validation.

| dataset | task | attack | defended | nodes | probed_edges | success_rate | false_positive_rate | advantage | eps3_claimed | eps3_actual_max | eps3_actual_median | frac_nodes_over_claim | rejections |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | triangle | malicious_rule | False | 490 | 500 | 0.8000 | 0.0909 | 0.7091 | - | - | - | - | - |
| CU | triangle | malicious_rule | True | 490 | 500 | 0.0000 | 0.0000 | 0.0000 | - | - | - | - | rule_tampered=490 |
| CU | degree | malicious_rule | False | 490 | 500 | 0.9980 | 0.0000 | 0.9980 | - | - | - | - | - |
| CU | degree | malicious_rule | True | 490 | 500 | 0.0000 | 0.0000 | 0.0000 | - | - | - | - | rule_tampered=490 |
| CU | triangle | task_mismatch | False | 490 | 0 | - | - | - | 0.8000 | 1.4933 | 0.2353 | 0.0347 | - |
| CU | triangle | task_mismatch | True | 490 | 0 | - | - | - | 0.8000 | 0.2667 | 0.0800 | 0.0000 | task_mismatch=490 |
| CU | triangle | text_injection | False | 599 | 54 | 1.0000 | 0.0000 | 1.0000 | - | - | - | - | - |
| CU | triangle | text_injection | True | 599 | 54 | 0.0000 | 0.0000 | 0.0000 | - | - | - | - | malformed_payload=599 |
| CU | triangle | forged_messages | False | 599 | 54 | 1.0000 | 0.2385 | 0.7615 | - | - | - | - | - |
| CU | triangle | forged_messages | True | 599 | 54 | 0.1667 | 0.2385 | -0.0719 | - | - | - | - | spoofed_sender_id=59900 |
| EE | triangle | malicious_rule | False | 1430 | 760 | 0.7882 | 0.0553 | 0.7329 | - | - | - | - | - |
| EE | triangle | malicious_rule | True | 1430 | 760 | 0.0000 | 0.0000 | 0.0000 | - | - | - | - | rule_tampered=1430 |
| EE | degree | malicious_rule | False | 1430 | 760 | 1.0000 | 0.0000 | 1.0000 | - | - | - | - | - |
| EE | degree | malicious_rule | True | 1430 | 760 | 0.0000 | 0.0000 | 0.0000 | - | - | - | - | rule_tampered=1430 |
| EE | triangle | task_mismatch | False | 1430 | 0 | - | - | - | 0.8000 | 23.7517 | 0.5501 | 0.3622 | - |
| EE | triangle | task_mismatch | True | 1430 | 0 | - | - | - | 0.8000 | 0.3391 | 0.0816 | 0.0000 | task_mismatch=1430 |
| EE | triangle | text_injection | False | 1342 | 96 | 1.0000 | 0.0000 | 1.0000 | - | - | - | - | - |
| EE | triangle | text_injection | True | 1342 | 96 | 0.0000 | 0.0000 | 0.0000 | - | - | - | - | malformed_payload=1342 |
| EE | triangle | forged_messages | False | 1342 | 96 | 0.9896 | 0.3989 | 0.5907 | - | - | - | - | - |
| EE | triangle | forged_messages | True | 1342 | 96 | 0.4792 | 0.3989 | 0.0803 | - | - | - | - | spoofed_sender_id=134200 |

## Defence cost on honest runs

| dataset | honest_messages | rejected | pass_rate | max_count_change |
|---|---|---|---|---|
| CU | 7204 | 0 | 1.0000 | 0.0000 |
| EE | 54952 | 0 | 1.0000 | 0.0000 |
