Naive (LLM) on the CertiCount tasks: eps = 2, 20 runs per cell, model = Qwen3-8B, prompt = boxed. Mean relative error, lower is better.

| Task | Method | EE | Avg. |
|---|---|---|---|
| open-wedge | Naive (LLM) | 1.1708 | 1.1708 |
| open-wedge | GT-Naive (same runs) | 6.0076 | 6.0076 |
| open-wedge | Naive - GT-Naive | -4.8368 | -4.8368 |
| degree-ge3 | Naive (LLM) | 0.7025 | 0.7025 |
| degree-ge3 | GT-Naive (same runs) | 0.1818 | 0.1818 |
| degree-ge3 | Naive - GT-Naive | 0.5207 | 0.5207 |
| triangle-node | Naive (LLM) | 0.1000 | 0.1000 |
| triangle-node | GT-Naive (same runs) | 0.1000 | 0.1000 |
| triangle-node | Naive - GT-Naive | 0.0000 | 0.0000 |
| triangle-edge | Naive (LLM) | 1.1153 | 1.1153 |
| triangle-edge | GT-Naive (same runs) | 1.8558 | 1.8558 |
| triangle-edge | Naive - GT-Naive | -0.7406 | -0.7406 |

Naive = the model answers from the RR noisy edge list only; GT-Naive = the exact count on the same noisy graph; Naive - GT-Naive > 0 means the model's execution is worse than perfect execution of the same mechanism.
