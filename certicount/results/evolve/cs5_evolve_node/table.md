# Prompt self-evolution

start = v0 (c214aa50ed8714f0), training tasks = degree, 2-star, 4-star, n = 400, architecture = per-node (α = 5), ε = 2.0, 4 designs per task and evaluation. Best: g2c1 (d32f1bda36412f26). Falsifier refutations during evolution: 0 (must be 0: privacy does not depend on the prompt).

| generation | kind | name | parent | score | mean_score | qualified_rate | accept_rate | mean_calls | refuted | patch |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | parent | v0 | - | 0.3778 | 0.3778 | 0.4167 | 0.5833 | 1.9167 | 0 | null |
| 1 | child | g1c1 | v0 | 0.3846 | 0.3846 | 0.4167 | 0.7500 | 1.5000 | 0 | {"module": "rules", "op": "add", "index": 0, "value": "Bound degrees with project(N(...), D) before nonlinear functions to minimize sensitivity and noise. Use ' |
| 1 | child | g1c2 | v0 | 0.4578 | 0.4578 | 0.5000 | 0.8333 | 2 | 0 | {"module": "rules", "op": "add", "index": 0, "value": "Use project(P, D) to bound degrees before applying comb or other nonlinear functions, and avoid range() i |
| 1 | parent | v0 | - | 0.3695 | 0.3737 | 0.4167 | 0.6667 | 2.3333 | 0 | null |
| 1 | confirm | g1c2 | v0 | 0.5461 | 0.5019 | 0.5833 | 0.7500 | 1.7500 | 0 | null |
| 2 | child | g2c1 | g1c2 | 0.8028 | 0.8028 | 0.8333 | 1 | 1.3333 | 0 | {"module": "rules", "op": "add", "index": 1, "value": "Avoid angle brackets and ensure all expressions use valid syntax; use project(P, D) before comb or other  |
| 2 | child | g2c2 | g1c2 | 0.5467 | 0.5467 | 0.5833 | 0.8333 | 1.6667 | 0 | {"module": "rules", "op": "add", "index": 1, "value": "Write function calls and set operations without spaces (e.g., size(N(self)) instead of size( N(self) ))", |
| 2 | child | g2c3 | g1c2 | 0.5426 | 0.5426 | 0.5833 | 0.9167 | 1.8333 | 0 | {"module": "repair_hints", "op": "add", "index": 0, "value": {"pattern": "syntax error: invalid syntax", "hint": "Ensure proper spacing around operators and use |
| 2 | parent | g1c2 | v0 | 0.3778 | 0.4605 | 0.4167 | 0.6667 | 1.8333 | 0 | null |
| 2 | confirm | g2c1 | g1c2 | 0.3795 | 0.5912 | 0.4167 | 0.9167 | 1.6667 | 0 | null |
| 3 | child | g3c1 | g2c1 | 0.6309 | 0.6309 | 0.6667 | 1 | 1.5000 | 0 | {"module": "rules", "op": "add", "index": 1, "value": "Avoid using comb or other nonlinear functions directly on the size of projected neighbors; instead, use l |
| 3 | child | g3c2 | g2c1 | 0.3745 | 0.3745 | 0.4167 | 0.7500 | 1.8333 | 0 | {"module": "rules", "op": "add", "index": 1, "value": "Always apply project(N(self), D) before using size() or comb() on noisy neighbor sets; use project(P, D)  |
| 3 | child | g3c3 | g2c1 | 0.5396 | 0.5396 | 0.5833 | 0.6667 | 1.9167 | 0 | {"module": "repair_hints", "op": "add", "index": 1, "value": {"pattern": ".*N\\(.+\\).*", "hint": "Use project(P, D) before N(...) to bound the degree and reduc |
| 3 | parent | g2c1 | g1c2 | 0.4628 | 0.5484 | 0.5000 | 0.7500 | 1.6667 | 0 | null |
| 3 | confirm | g3c1 | g2c1 | 0.4576 | 0.5443 | 0.5000 | 0.7500 | 1.8333 | 0 | null |
| 4 | child | g4c1 | g2c1 | 0.5413 | 0.5413 | 0.5833 | 0.7500 | 1.8333 | 0 | {"module": "rules", "op": "add", "index": 1, "value": "Avoid angle brackets and ensure all expressions use valid syntax; use project(P, D) before comb or other  |
| 4 | child | g4c2 | g2c1 | -0.0648 | -0.0648 | 0 | 0 | 3 | 0 | {"module": "rules", "op": "add", "index": 2, "value": "Avoid angle brackets in code; use only valid syntax without <program> or </program> tags.", "reason": "Pr |
| 4 | child | g4c3 | g2c1 | 0.4563 | 0.4563 | 0.5000 | 0.6667 | 1.9167 | 0 | {"module": "rules", "op": "add", "index": 1, "value": "Avoid angle brackets and ensure all expressions use valid syntax; use project(P, D) before comb or other  |
| 4 | parent | g2c1 | g1c2 | 0.4628 | 0.5270 | 0.5000 | 0.8333 | 1.6667 | 0 | null |
| 4 | confirm | g4c1 | g2c1 | 0.3729 | 0.4571 | 0.4167 | 0.6667 | 1.9167 | 0 | null |

## Best prompt modules

```json
{
  "name": "g2c1",
  "parent": "g1c2",
  "digest": "d32f1bda36412f26",
  "rules": [
    "Use project(P, D) to bound degrees before applying comb or other nonlinear functions, and avoid range() in loops; use only N(...) or A(...) but not both in a single program.",
    "Avoid angle brackets and ensure all expressions use valid syntax; use project(P, D) before comb or other nonlinear functions to tightly bound sensitivity."
  ],
  "examples": [],
  "repair_hints": []
}
```
