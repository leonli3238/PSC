# Prompt self-evolution

start = v0 (c214aa50ed8714f0), training tasks = degree, 2-star, 4-star, n = 400, architecture = PSC, ε = 2.0, 4 designs per task and evaluation. Best: g2c2 (243d5046cbd39614). Falsifier refutations during evolution: 0 (must be 0: privacy does not depend on the prompt).

| generation | kind | name | parent | score | mean_score | qualified_rate | accept_rate | mean_calls | refuted | patch |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | parent | v0 | - | 0.9678 | 0.9678 | 1 | 1 | 1.5833 | 0 | null |
| 1 | child | g1c1 | v0 | 0.8883 | 0.8883 | 0.9167 | 0.9167 | 1.3333 | 0 | {"module": "rules", "op": "add", "index": 0, "value": "Always apply project(P, D) to bound set sizes before using comb or other nonlinear functions; use size(S) |
| 1 | child | g1c2 | v0 | 0.8880 | 0.8880 | 0.9167 | 0.9167 | 1.3333 | 0 | {"module": "rules", "op": "add", "index": 0, "value": "Bound degrees with project(P, D) before nonlinear functions like comb() or pow() to ensure tight sensitiv |
| 1 | child | g1c3 | v0 | 0.8028 | 0.8028 | 0.8333 | 0.8333 | 1.4167 | 0 | {"module": "rules", "op": "add", "index": 0, "value": "Always apply project(P, D) before comb or other size-dependent functions, and use size(S) instead of S di |
| 1 | parent | v0 | - | 0.7962 | 0.8820 | 0.8333 | 0.8333 | 1.8333 | 0 | null |
| 1 | confirm | g1c1 | v0 | 0.9766 | 0.9324 | 1 | 1 | 1.0833 | 0 | null |
| 2 | child | g2c1 | g1c1 | 0.7133 | 0.7133 | 0.7500 | 0.7500 | 1.6667 | 0 | {"module": "rules", "op": "add", "index": 1, "value": "When using comb or other nonlinear functions on projected sets, always apply size(S) to convert the set t |
| 2 | child | g2c2 | g1c1 | 0.9770 | 0.9770 | 1 | 1 | 1 | 0 | {"module": "repair_hints", "op": "add", "index": 0, "value": {"pattern": "comb expects \\(num, num\\), got \\(set, num\\)", "hint": "Use size(S) instead of the  |
| 2 | child | g2c3 | g1c1 | 0.8906 | 0.8906 | 0.9167 | 0.9167 | 1.1667 | 0 | {"module": "rules", "op": "add", "index": 1, "value": "Use size(S) to get the numeric count before passing to comb or other functions expecting numbers", "reaso |
| 2 | parent | g1c1 | v0 | 0.9766 | 0.9471 | 1 | 1 | 1.0833 | 0 | null |
| 2 | confirm | g2c2 | g1c1 | 0.9754 | 0.9762 | 1 | 1 | 1.0833 | 0 | null |
| 3 | child | g3c1 | g2c2 | 0.8026 | 0.8026 | 0.8333 | 0.8333 | 1.3333 | 0 | {"module": "rules", "op": "add", "index": 1, "value": "Use size(S) to get the count of a set for functions like comb; do not pass sets directly as numeric argum |
| 3 | child | g3c2 | g2c2 | 0.9673 | 0.9673 | 1 | 1 | 1.4167 | 0 | {"module": "rules", "op": "add", "index": 1, "value": "When passing a set to comb or other functions requiring a numeric count, use size(S) to explicitly conver |
| 3 | child | g3c3 | g2c2 | 0.9755 | 0.9755 | 1 | 1 | 1 | 0 | {"module": "rules", "op": "replace", "index": 0, "value": "Always apply project(P, D) to bound set sizes before using comb or other nonlinear functions. Use siz |
| 3 | parent | g2c2 | g1c1 | 0.9737 | 0.9754 | 1 | 1 | 1.1667 | 0 | null |
| 3 | confirm | g3c3 | g2c2 | 0.8022 | 0.8889 | 0.8333 | 0.8333 | 1.3333 | 0 | null |
| 4 | child | g4c1 | g2c2 | 0.8842 | 0.8842 | 0.9167 | 0.9167 | 1.4167 | 0 | {"module": "repair_hints", "op": "add", "index": 1, "value": {"pattern": "sensitivity GS.*loose.*apply project.*first", "hint": "Apply project(P, D) before comb |
| 4 | child | g4c2 | g2c2 | 0.8007 | 0.8007 | 0.8333 | 0.8333 | 1.4167 | 0 | {"module": "repair_hints", "op": "add", "index": 1, "value": {"pattern": "comb expects \\(num, num\\), got \\(set, num\\)", "hint": "Use project(P, D) first to  |
| 4 | child | g4c3 | g2c2 | 0.9744 | 0.9744 | 1 | 1 | 1.0833 | 0 | {"module": "rules", "op": "add", "index": 1, "value": "Avoid using N(...) in calculations; use P (true neighbors) instead to ensure accurate results", "reason": |
| 4 | parent | g2c2 | g1c1 | 0.8887 | 0.9537 | 0.9167 | 0.9167 | 1.2500 | 0 | null |
| 4 | confirm | g4c3 | g2c2 | 0.8844 | 0.9294 | 0.9167 | 0.9167 | 1.4167 | 0 | null |

## Best prompt modules

```json
{
  "name": "g2c2",
  "parent": "g1c1",
  "digest": "243d5046cbd39614",
  "rules": [
    "Always apply project(P, D) to bound set sizes before using comb or other nonlinear functions; use size(S) to get the count."
  ],
  "examples": [],
  "repair_hints": [
    [
      "comb expects \\(num, num\\), got \\(set, num\\)",
      "Use size(S) instead of the set directly as the first argument to comb"
    ]
  ]
}
```
