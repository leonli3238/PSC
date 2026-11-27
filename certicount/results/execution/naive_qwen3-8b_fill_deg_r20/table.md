Naive (LLM) on the CertiCount tasks: eps = 2, 20 runs per cell, model = Qwen3-8B, prompt = boxed. Mean relative error, lower is better.

| Task | Method | CU | Do | ML | CS | EE | Avg. |
|---|---|---|---|---|---|---|---|
| degree-ge3 | Naive (LLM) | 0.0988 | 0.1781 | 0.4675 | 1.4381 | 0.1818 | 0.4729 |
| degree-ge3 | GT-Naive (same runs) | 0.1395 | 0.3180 | 0.5375 | 1.4571 | 0.1818 | 0.5268 |
| degree-ge3 | Naive - GT-Naive | -0.0407 | -0.1400 | -0.0700 | -0.0190 | 0.0000 | -0.0539 |

Naive = the model answers from the RR noisy edge list only; GT-Naive = the exact count on the same noisy graph; Naive - GT-Naive > 0 means the model's execution is worse than perfect execution of the same mechanism.
