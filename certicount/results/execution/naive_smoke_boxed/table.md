Naive (LLM) on the CertiCount tasks: eps = 2, 2 runs per cell, model = Qwen3-8B, prompt = boxed. Mean relative error, lower is better.

| Task | Method | CU | Avg. |
|---|---|---|---|
| open-wedge | Naive (LLM) | 2.1540 | 2.1540 |
| open-wedge | GT-Naive (same runs) | 5.4740 | 5.4740 |
| open-wedge | Naive - GT-Naive | -3.3200 | -3.3200 |
| degree-ge3 | Naive (LLM) | 0.4767 | 0.4767 |
| degree-ge3 | GT-Naive (same runs) | 0.1395 | 0.1395 |
| degree-ge3 | Naive - GT-Naive | 0.3372 | 0.3372 |

Naive = the model answers from the RR noisy edge list only; GT-Naive = the exact count on the same noisy graph; Naive - GT-Naive > 0 means the model's execution is worse than perfect execution of the same mechanism.
