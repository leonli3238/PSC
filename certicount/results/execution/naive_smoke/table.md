Naive (LLM) on the CertiCount tasks: eps = 2, 1 runs per cell, model = Qwen3-8B, prompt = paper. Mean relative error, lower is better.

| Task | Method | CU | Avg. |
|---|---|---|---|
| open-wedge | Naive (LLM) | 3.0960 | 3.0960 |
| open-wedge | GT-Naive (same runs) | 5.9040 | 5.9040 |
| open-wedge | Naive - GT-Naive | -2.8080 | -2.8080 |
| degree-ge3 | Naive (LLM) | 0.3023 | 0.3023 |
| degree-ge3 | GT-Naive (same runs) | 0.1395 | 0.1395 |
| degree-ge3 | Naive - GT-Naive | 0.1628 | 0.1628 |

Naive = the model answers from the RR noisy edge list only; GT-Naive = the exact count on the same noisy graph; Naive - GT-Naive > 0 means the model's execution is worse than perfect execution of the same mechanism.
