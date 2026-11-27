| Task | Method | CU | Do | Avg. |
|---|---|---|---|---|
| open-wedge | Naive (LLM) | 0.0000 | 0.0000 | 0.0000 |
| open-wedge | GT-Naive (same noisy graph) | 0.0000 | 0.0000 | 0.0000 |
| degree-ge3 | Naive (LLM) | 0.0000 | 0.2500 | 0.1250 |
| degree-ge3 | GT-Naive (same noisy graph) | 0.0000 | 0.2500 | 0.1250 |
| triangle-edge | Naive (LLM) | 0.0000 | 0.5000 | 0.2500 |
| triangle-edge | GT-Naive (same noisy graph) | 0.7500 | 0.5000 | 0.6250 |
| triangle-node | Naive (LLM) | 0.2500 | 0.2500 | 0.2500 |
| triangle-node | GT-Naive (same noisy graph) | 0.2500 | 0.5000 | 0.3750 |

Accuracy of the boolean tasks; 4 runs per cell, eps = 2. Graphs: CU(n=49,m=107), Do(n=62,m=159).

Relative error of the counting task (smaller is better):

| Task | Method | CU | Do | Avg. |
|---|---|---|---|---|
| open-wedge | Naive (LLM) | 2.5670 | 7.9491 | 5.2580 |
| open-wedge | GT-Naive (same noisy graph) | 5.4420 | 3.7543 | 4.5982 |
