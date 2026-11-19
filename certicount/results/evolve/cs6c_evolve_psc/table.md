# Prompt self-evolution

start = v0 (898628ff51a8d8c9), training tasks = degree, 2-star, 4-star, open-wedge, n = 400, architecture = PSC, ε = 2.0, 8 designs per task and evaluation. Best: g1c3 (f4723269c9dad172). Falsifier refutations during evolution: 0 (must be 0: privacy does not depend on the prompt).

| generation | kind | name | parent | score | mean_score | se | qualified_rate | qualified_ci95 | accept_rate | mean_calls | refuted | patch |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | parent | v0 | - | 0.8869 | 0.8869 | 0.0443 | 0.9375 | [0.80, 0.98] | 0.9375 | 1.8125 | 0 | null |
| 1 | child | g1c1 | v0 | 0.8933 | 0.8933 | 0.0447 | 0.9375 | [0.80, 0.98] | 0.9375 | 1.4688 | 0 | {"module": "rules", "op": "add", "index": 0, "value": "Bound neighbor sets with project(P, D) before comb(), pow(), or size() to ensure sensitivity is minimized |
| 1 | child | g1c2 | v0 | 0.9182 | 0.9182 | 0.0324 | 0.9688 | [0.84, 0.99] | 0.9688 | 1.5625 | 0 | {"module": "repair_hints", "op": "add", "index": 0, "value": {"pattern": ".*comb\\(size\\(P\\), \\d+\\)|pow\\(size\\(P\\), \\d+\\).*$", "hint": "Bound neighbor  |
| 1 | child | g1c3 | v0 | 0.9282 | 0.9282 | 0.0325 | 0.9688 | [0.84, 0.99] | 0.9688 | 1.1875 | 0 | {"module": "rules", "op": "add", "index": 0, "value": "Always apply project(P, D) before using comb or pow on the size of P to ensure tight bounds and correct s |
| 1 | parent | v0 | - | 0.8853 | 0.8861 | 0.0311 | 0.9375 | [0.80, 0.98] | 0.9375 | 1.7812 | 0 | null |
| 1 | confirm | g1c3 | v0 | 0.9232 | 0.9257 | 0.0228 | 0.9688 | [0.84, 0.99] | 0.9688 | 1.2812 | 0 | null |
| 2 | child | g2c1 | v0 | 0.8941 | 0.8941 | 0.0447 | 0.9375 | [0.80, 0.98] | 0.9375 | 1.2812 | 0 | {"module": "rules", "op": "add", "index": 0, "value": "Always apply project(P, D) to sets before using comb or pow to bound their size and prevent loose sensiti |
| 2 | child | g2c2 | v0 | 0.8666 | 0.8666 | 0.0539 | 0.9062 | [0.76, 0.97] | 0.9062 | 1.3438 | 0 | {"module": "rules", "op": "add", "index": 0, "value": "Bound neighbor sets with project(..., D) before applying combinatorial functions like comb(...) or pow(.. |
| 2 | child | g2c3 | g1c3 | 0.8661 | 0.8661 | 0.0539 | 0.9062 | [0.76, 0.97] | 0.9062 | 1.3438 | 0 | {"module": "rules", "op": "replace", "index": 0, "value": "Always apply project(S, D) before using comb or pow on the size of any set S to ensure tight bounds a |
| 2 | parent | g1c3 | v0 | 0.8941 | 0.9152 | 0.0212 | 0.9375 | [0.80, 0.98] | 0.9375 | 1.4375 | 0 | null |
| 3 | child | g3c1 | v0 | 0.9247 | 0.9247 | 0.0326 | 0.9688 | [0.84, 0.99] | 0.9688 | 1.3438 | 0 | {"module": "rules", "op": "add", "index": 0, "value": "Bound all neighbor sets with project(..., D) before applying comb, size, or other functions that depend o |
| 3 | child | g3c2 | g2c3 | 0.9186 | 0.9186 | 0.0326 | 0.9688 | [0.84, 0.99] | 0.9688 | 1.4375 | 0 | {"module": "rules", "op": "add", "index": 1, "value": "Always project all sets used in set operations (intersection, union) or combinatorial functions (comb, po |
| 3 | child | g3c3 | v0 | 0.8973 | 0.8973 | 0.0448 | 0.9375 | [0.80, 0.98] | 0.9375 | 1.2500 | 0 | {"module": "rules", "op": "add", "index": 0, "value": "Bound all neighbor sets with project(..., D) before applying comb, pow, or any nonlinear function to ensu |
| 3 | parent | g1c3 | v0 | 0.8678 | 0.9033 | 0.0208 | 0.9062 | [0.76, 0.97] | 0.9062 | 1.1875 | 0 | null |
| 3 | confirm | g3c1 | v0 | 0.8640 | 0.8943 | 0.0315 | 0.9062 | [0.76, 0.97] | 0.9062 | 1.4688 | 0 | null |

## Best prompt modules

```json
{
  "name": "g1c3",
  "parent": "v0",
  "digest": "f4723269c9dad172",
  "core": "v1",
  "rules": [
    "Always apply project(P, D) before using comb or pow on the size of P to ensure tight bounds and correct sensitivity."
  ],
  "examples": [],
  "repair_hints": []
}
```
