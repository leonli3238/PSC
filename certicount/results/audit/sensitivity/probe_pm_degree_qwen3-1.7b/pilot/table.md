# Pilot: Qwen3-1.7B

calls 200, wall 8s, completion tokens 50500, throughput 6026.3 tok/s, JSON rate 1

| bin | trials | inputs | exec_error | abs_err_mean | json | number | failed | length_cut | tok_mean | tok_p95 | tok_max | jitter_inputs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1-10 | 50 | 10 | 0 | 0 | 1 | 0 | 0 | 0 | 70.1 | 128 | 128 | 0 |
| 11-30 | 50 | 10 | 0.2 | 0.2 | 1 | 0 | 0 | 0 | 158 | 300 | 300 | 0 |
| 31-60 | 40 | 8 | 0.75 | 3 | 1 | 0 | 0 | 0 | 373 | 444 | 444 | 0 |
| 61-120 | 40 | 8 | 0.9 | 114 | 1 | 0 | 0 | 0 | 514 | 679 | 679 | 0.125 |
| >120 | 20 | 4 | 1 | 240 | 1 | 0 | 0 | 0 | 179 | 669 | 669 | 0 |

forecast screen: {'calls': 20112, 'completion_tokens': 7274837, 'hours': 0.34}

forecast confirm (upper): {'calls': 24000, 'completion_tokens': 4302000, 'hours': 0.2}
