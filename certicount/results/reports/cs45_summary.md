# CS4 + CS5 summary (PM, ε = 2, Qwen3-8B thinking curator)

qualified = accepted and noise-free bias within the gate (old-check runs: recorded only where available); RE over 100 paired code runs per accepted design; repairs = rejection stage of the draft before the accepted one; uncertified = drafts that would violate ε without certification; unsound = certificates refuted (must be 0).

## Design runs

| run | task | designs | accept | qualified | median RE | mean RE | reference RE | calls/design | repairs | uncertified | unsound |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CS2 (old checks) | degree | 10 | 1.000 | 1.000 | 0.003 | 0.003 | 0.003 | 1.100 | - | 0 | 0 |
| CS2 (old checks) | 2-star | 10 | 1.000 | 1.000 | 0.044 | 4.464 | 0.044 | 1.900 | - | 4 | 0 |
| CS2 (old checks) | 3-star | 10 | 0.900 | 0.900 | 0.124 | 14.750 | 0.123 | 1.300 | - | 2 | 0 |
| CS2 (old checks) | triangle | 10 | 0.800 | 0.800 | 100.773 | 63.619 | 1.029 | 2 | - | 1 | 0 |
| CS4 online, PSC arch | degree | 10 | 1.000 | 1.000 | 0.003 | 0.00305 | 0.003 | 1 | - | 0 | 0 |
| CS4 online, PSC arch | 2-star | 10 | 0.900 | 0.900 | 0.044 | 0.044 | 0.044 | 1.500 | gs_loose:1, parse:2 | 2 | 0 |
| CS4 online, PSC arch | 3-star | 10 | 1.000 | 1.000 | 0.123 | 0.123 | 0.123 | 2.100 | gs_loose:3, noisy:2, parse:3 | 4 | 0 |
| CS4 online, PSC arch | triangle | 10 | 0.200 | 0.200 | 1.693 | 1.693 | 1.029 | 2.800 | parse:1, semantic:1 | 3 | 0 |
| CS3 (old checks) | degree | 10 | 1.000 | 1.000 | 13.053 | 7.837 | 0.003 | 1.300 | - | 1 | 0 |
| CS3 (old checks) | 2-star | 10 | 1.000 | 1.000 | 0.030 | 13.280 | 0.00745 | 1.500 | - | 5 | 0 |
| CS3 (old checks) | 3-star | 10 | 1.000 | 1.000 | 0.074 | 8.847 | 0.00871 | 1.100 | - | 1 | 0 |
| CS3 (old checks) | triangle | 10 | 0.200 | 0.200 | 1.450 | 1.450 | 0.126 | 2.900 | - | 2 | 0 |
| CS4 online, per-node arch | degree | 10 | 0.700 | 0.700 | 0.00799 | 0.019 | 0.003 | 2 | noisy:1, semantic:2 | 4 | 0 |
| CS4 online, per-node arch | 2-star | 10 | 0.600 | 0.600 | 0.00749 | 0.015 | 0.00745 | 2.400 | gs_loose:2, noisy:1, parse:1 | 5 | 0 |
| CS4 online, per-node arch | 3-star | 10 | 0.900 | 0.900 | 0.00871 | 0.021 | 0.00871 | 1.700 | gs_failed:1, gs_loose:1, semantic:1 | 3 | 0 |
| CS4 online, per-node arch | triangle | 10 | 0.800 | 0.800 | 0.126 | 0.126 | 0.126 | 2.100 | gs_loose:1, semantic:3 | 0 | 0 |
| CS5 held-out, psc, v0 | 3-star | 10 | 0.900 | 0.900 | 0.124 | 0.123 | 0.123 | 1.700 | gs_loose:1, noisy:2, parse:2 | 1 | 0 |
| CS5 held-out, psc, v0 | 5-star | 10 | 0.900 | 0.900 | 0.287 | 0.287 | 0.287 | 1.800 | gs_loose:2, noisy:1, parse:2 | 3 | 0 |
| CS5 held-out, psc, v0 | triangle | 10 | 0.400 | 0.400 | 1.693 | 1.693 | 1.029 | 2.500 | gs_loose:1, semantic:1 | 4 | 0 |
| CS5 held-out, psc, v0 | degree-moment2 | 10 | 1.000 | 1.000 | 0.043 | 0.043 | 0.043 | 1.400 | gs_loose:1, parse:3 | 1 | 0 |
| CS5 held-out, psc, evolved | 3-star | 10 | 0.800 | 0.800 | 0.123 | 0.123 | 0.123 | 1.500 | noisy:1 | 0 | 0 |
| CS5 held-out, psc, evolved | 5-star | 10 | 1.000 | 1.000 | 0.287 | 0.287 | 0.287 | 1.400 | noisy:1, parse:3 | 0 | 0 |
| CS5 held-out, psc, evolved | triangle | 10 | 0.300 | 0.300 | 1.693 | 1.693 | 1.029 | 2.600 | parse:2 | 4 | 0 |
| CS5 held-out, psc, evolved | degree-moment2 | 10 | 0.800 | 0.800 | 0.043 | 0.043 | 0.043 | 1.600 | gs_loose:1, parse:1 | 1 | 0 |
| CS5 held-out, psc, v0-r2 | 3-star | 10 | 1.000 | 1.000 | 0.124 | 0.123 | 0.123 | 2.200 | gs_loose:4, parse:2 | 5 | 0 |
| CS5 held-out, psc, v0-r2 | 5-star | 10 | 1.000 | 1.000 | 0.287 | 0.287 | 0.287 | 1.800 | gs_loose:4, parse:1, semantic:1 | 4 | 0 |
| CS5 held-out, psc, v0-r2 | triangle | 10 | 0.600 | 0.600 | 1.693 | 1.694 | 1.029 | 3.800 | noisy:1, semantic:4 | 6 | 0 |
| CS5 held-out, psc, v0-r2 | degree-moment2 | 10 | 1.000 | 1.000 | 0.043 | 0.043 | 0.043 | 1.500 | gs_loose:3, parse:1 | 3 | 0 |
| CS5 held-out, node, v0 | 3-star | 10 | 0.600 | 0.600 | 0.041 | 0.041 | 0.00871 | 1.900 | noisy:1 | 2 | 0 |
| CS5 held-out, node, v0 | 5-star | 10 | 0.800 | 0.800 | 0.018 | 0.032 | 0.018 | 1.600 | parse:1 | 0 | 0 |
| CS5 held-out, node, v0 | triangle | 10 | 0.600 | 0.600 | 0.126 | 0.127 | 0.126 | 2 | semantic:1 | 1 | 0 |
| CS5 held-out, node, v0 | degree-moment2 | 10 | 0.800 | 0.800 | 0.052 | 0.035 | 0.00744 | 1.900 | gs_loose:1, noisy:3 | 6 | 0 |
| CS5 held-out, node, evolved | 3-star | 10 | 0.800 | 0.800 | 0.00871 | 0.025 | 0.00871 | 1.800 | noisy:3, parse:1 | 0 | 0 |
| CS5 held-out, node, evolved | 5-star | 10 | 0.900 | 0.900 | 0.133 | 0.082 | 0.018 | 1.200 | - | 1 | 0 |
| CS5 held-out, node, evolved | triangle | 10 | 0.300 | 0.300 | 0.126 | 0.126 | 0.126 | 2.600 | parse:1, semantic:1 | 1 | 0 |
| CS5 held-out, node, evolved | degree-moment2 | 10 | 0.800 | 0.800 | 0.030 | 0.030 | 0.00744 | 2 | noisy:2, parse:2 | 4 | 0 |
| CS5 held-out, node, v0-r2 | 3-star | 10 | 1.000 | 1.000 | 0.074 | 0.052 | 0.00871 | 2.300 | gs_failed:2, gs_loose:2, noisy:1, parse:1, semantic:1 | 5 | 0 |
| CS5 held-out, node, v0-r2 | 5-star | 10 | 1.000 | 1.000 | 0.018 | 0.052 | 0.018 | 2.400 | gs_failed:3, gs_loose:2, noisy:3 | 5 | 0 |
| CS5 held-out, node, v0-r2 | triangle | 10 | 1.000 | 1.000 | 0.126 | 0.407 | 0.126 | 2.500 | gs_loose:1, parse:3, semantic:2 | 1 | 0 |
| CS5 held-out, node, v0-r2 | degree-moment2 | 10 | 0.900 | 0.900 | 0.052 | 0.042 | 0.00744 | 3.300 | parse:5, semantic:1 | 8 | 0 |

## Prompt evolution

### cs5_evolve_psc

Best prompt: g2c2 (243d5046cbd39614); falsifier refutations during evolution: 0 (must be 0).

| gen | kind | name | score | mean score | qualified | accepted | calls/design | patch |
|---|---|---|---|---|---|---|---|---|
| 0 | parent | v0 | 0.968 | 0.968 | 1 | 1 | 1.583 | - |
| 1 | child | g1c1 | 0.888 | 0.888 | 0.917 | 0.917 | 1.333 | {"module": "rules", "op": "add", "index": 0, "value": "Always apply project(P, D) to bound set sizes before using comb o |
| 1 | child | g1c2 | 0.888 | 0.888 | 0.917 | 0.917 | 1.333 | {"module": "rules", "op": "add", "index": 0, "value": "Bound degrees with project(P, D) before nonlinear functions like  |
| 1 | child | g1c3 | 0.803 | 0.803 | 0.833 | 0.833 | 1.417 | {"module": "rules", "op": "add", "index": 0, "value": "Always apply project(P, D) before comb or other size-dependent fu |
| 1 | parent | v0 | 0.796 | 0.882 | 0.833 | 0.833 | 1.833 | - |
| 1 | confirm | g1c1 | 0.977 | 0.932 | 1 | 1 | 1.083 | - |
| 2 | child | g2c1 | 0.713 | 0.713 | 0.750 | 0.750 | 1.667 | {"module": "rules", "op": "add", "index": 1, "value": "When using comb or other nonlinear functions on projected sets, a |
| 2 | child | g2c2 | 0.977 | 0.977 | 1 | 1 | 1 | {"module": "repair_hints", "op": "add", "index": 0, "value": {"pattern": "comb expects \\(num, num\\), got \\(set, num\\ |
| 2 | child | g2c3 | 0.891 | 0.891 | 0.917 | 0.917 | 1.167 | {"module": "rules", "op": "add", "index": 1, "value": "Use size(S) to get the numeric count before passing to comb or ot |
| 2 | parent | g1c1 | 0.977 | 0.947 | 1 | 1 | 1.083 | - |
| 2 | confirm | g2c2 | 0.975 | 0.976 | 1 | 1 | 1.083 | - |
| 3 | child | g3c1 | 0.803 | 0.803 | 0.833 | 0.833 | 1.333 | {"module": "rules", "op": "add", "index": 1, "value": "Use size(S) to get the count of a set for functions like comb; do |
| 3 | child | g3c2 | 0.967 | 0.967 | 1 | 1 | 1.417 | {"module": "rules", "op": "add", "index": 1, "value": "When passing a set to comb or other functions requiring a numeric |
| 3 | child | g3c3 | 0.976 | 0.976 | 1 | 1 | 1 | {"module": "rules", "op": "replace", "index": 0, "value": "Always apply project(P, D) to bound set sizes before using co |
| 3 | parent | g2c2 | 0.974 | 0.975 | 1 | 1 | 1.167 | - |
| 3 | confirm | g3c3 | 0.802 | 0.889 | 0.833 | 0.833 | 1.333 | - |
| 4 | child | g4c1 | 0.884 | 0.884 | 0.917 | 0.917 | 1.417 | {"module": "repair_hints", "op": "add", "index": 1, "value": {"pattern": "sensitivity GS.*loose.*apply project.*first",  |
| 4 | child | g4c2 | 0.801 | 0.801 | 0.833 | 0.833 | 1.417 | {"module": "repair_hints", "op": "add", "index": 1, "value": {"pattern": "comb expects \\(num, num\\), got \\(set, num\\ |
| 4 | child | g4c3 | 0.974 | 0.974 | 1 | 1 | 1.083 | {"module": "rules", "op": "add", "index": 1, "value": "Avoid using N(...) in calculations; use P (true neighbors) instea |
| 4 | parent | g2c2 | 0.889 | 0.954 | 0.917 | 0.917 | 1.250 | - |
| 4 | confirm | g4c3 | 0.884 | 0.929 | 0.917 | 0.917 | 1.417 | - |

Best prompt modules:

```json
{
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

### cs5_evolve_node

Best prompt: g2c1 (d32f1bda36412f26); falsifier refutations during evolution: 0 (must be 0).

| gen | kind | name | score | mean score | qualified | accepted | calls/design | patch |
|---|---|---|---|---|---|---|---|---|
| 0 | parent | v0 | 0.378 | 0.378 | 0.417 | 0.583 | 1.917 | - |
| 1 | child | g1c1 | 0.385 | 0.385 | 0.417 | 0.750 | 1.500 | {"module": "rules", "op": "add", "index": 0, "value": "Bound degrees with project(N(...), D) before nonlinear functions  |
| 1 | child | g1c2 | 0.458 | 0.458 | 0.500 | 0.833 | 2 | {"module": "rules", "op": "add", "index": 0, "value": "Use project(P, D) to bound degrees before applying comb or other  |
| 1 | parent | v0 | 0.370 | 0.374 | 0.417 | 0.667 | 2.333 | - |
| 1 | confirm | g1c2 | 0.546 | 0.502 | 0.583 | 0.750 | 1.750 | - |
| 2 | child | g2c1 | 0.803 | 0.803 | 0.833 | 1 | 1.333 | {"module": "rules", "op": "add", "index": 1, "value": "Avoid angle brackets and ensure all expressions use valid syntax; |
| 2 | child | g2c2 | 0.547 | 0.547 | 0.583 | 0.833 | 1.667 | {"module": "rules", "op": "add", "index": 1, "value": "Write function calls and set operations without spaces (e.g., siz |
| 2 | child | g2c3 | 0.543 | 0.543 | 0.583 | 0.917 | 1.833 | {"module": "repair_hints", "op": "add", "index": 0, "value": {"pattern": "syntax error: invalid syntax", "hint": "Ensure |
| 2 | parent | g1c2 | 0.378 | 0.461 | 0.417 | 0.667 | 1.833 | - |
| 2 | confirm | g2c1 | 0.380 | 0.591 | 0.417 | 0.917 | 1.667 | - |
| 3 | child | g3c1 | 0.631 | 0.631 | 0.667 | 1 | 1.500 | {"module": "rules", "op": "add", "index": 1, "value": "Avoid using comb or other nonlinear functions directly on the siz |
| 3 | child | g3c2 | 0.374 | 0.374 | 0.417 | 0.750 | 1.833 | {"module": "rules", "op": "add", "index": 1, "value": "Always apply project(N(self), D) before using size() or comb() on |
| 3 | child | g3c3 | 0.540 | 0.540 | 0.583 | 0.667 | 1.917 | {"module": "repair_hints", "op": "add", "index": 1, "value": {"pattern": ".*N\\(.+\\).*", "hint": "Use project(P, D) bef |
| 3 | parent | g2c1 | 0.463 | 0.548 | 0.500 | 0.750 | 1.667 | - |
| 3 | confirm | g3c1 | 0.458 | 0.544 | 0.500 | 0.750 | 1.833 | - |
| 4 | child | g4c1 | 0.541 | 0.541 | 0.583 | 0.750 | 1.833 | {"module": "rules", "op": "add", "index": 1, "value": "Avoid angle brackets and ensure all expressions use valid syntax; |
| 4 | child | g4c2 | -0.065 | -0.065 | 0 | 0 | 3 | {"module": "rules", "op": "add", "index": 2, "value": "Avoid angle brackets in code; use only valid syntax without <prog |
| 4 | child | g4c3 | 0.456 | 0.456 | 0.500 | 0.667 | 1.917 | {"module": "rules", "op": "add", "index": 1, "value": "Avoid angle brackets and ensure all expressions use valid syntax; |
| 4 | parent | g2c1 | 0.463 | 0.527 | 0.500 | 0.833 | 1.667 | - |
| 4 | confirm | g4c1 | 0.373 | 0.457 | 0.417 | 0.667 | 1.917 | - |

Best prompt modules:

```json
{
  "rules": [
    "Use project(P, D) to bound degrees before applying comb or other nonlinear functions, and avoid range() in loops; use only N(...) or A(...) but not both in a single program.",
    "Avoid angle brackets and ensure all expressions use valid syntax; use project(P, D) before comb or other nonlinear functions to tightly bound sensitivity."
  ],
  "examples": [],
  "repair_hints": []
}
```

## Offline replay

See results/dsl_eval/cs4_step1a_replay/table.md
