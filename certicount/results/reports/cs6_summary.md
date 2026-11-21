# CS6 summary (PM, ε = 2, Qwen3-8B thinking curator, held-out tasks)

parse/draft: drafts that could not be parsed (after the run's format repairs) / all drafts; parse/fresh draft: the same over the first draft of every loop (no feedback yet). qualified: accepted and within the noise-free gate. RE: mean relative error over 100 paired code runs per accepted design.

## CS6a: prompt cores A / B / C

| run | task | designs | accept | accept 95% CI | qualified | drafts | parse/draft | parse/fresh draft | calls/design | gs_ratio | loose | noise_ratio | mean RE | median RE | reference RE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A v1 | 3-star | 20 | 0.800 | [0.58, 0.92] | 0.800 | 48 | 0.104 | 0.100 | 2.400 | 1.000 | 0 | 1.000 | 0.123 | 0.123 | 0.123 |
| A v1 | 5-star | 20 | 0.950 | [0.76, 0.99] | 0.950 | 30 | 0 | 0 | 1.500 | 1.000 | 0 | 1.000 | 0.287 | 0.287 | 0.287 |
| A v1 | triangle | 20 | 0.300 | [0.15, 0.52] | 0.300 | 55 | 0.255 | 0.350 | 2.750 | 1.167 | 1 | 1.000 | 1.587 | 1.587 | 1.029 |
| A v1 | degree-moment2 | 20 | 1.000 | [0.84, 1.00] | 1.000 | 38 | 0.132 | 0.250 | 1.900 | 1.000 | 0 | 1.000 | 0.043 | 0.043 | 0.043 |
| B v1-repeat3 | 3-star | 20 | 0.800 | [0.58, 0.92] | 0.800 | 41 | 0.146 | 0.150 | 2.050 | 1.000 | 0 | 1.000 | 0.123 | 0.123 | 0.123 |
| B v1-repeat3 | 5-star | 20 | 0.900 | [0.70, 0.97] | 0.900 | 37 | 0.054 | 0.050 | 1.850 | 1.000 | 0 | 1.000 | 0.287 | 0.287 | 0.287 |
| B v1-repeat3 | triangle | 20 | 0 | [0.00, 0.16] | 0 | 60 | 0.400 | 0.650 | 3 | - | 0 | - | - | - | - |
| B v1-repeat3 | degree-moment2 | 20 | 1.000 | [0.84, 1.00] | 1.000 | 32 | 0.031 | 0.050 | 1.600 | 1.000 | 0 | 1.000 | 0.043 | 0.043 | 0.043 |
| C v1-alt | 3-star | 20 | 0.900 | [0.70, 0.97] | 0.900 | 44 | 0.091 | 0.100 | 2.200 | 1.000 | 0 | 1.000 | 0.123 | 0.123 | 0.123 |
| C v1-alt | 5-star | 20 | 0.950 | [0.76, 0.99] | 0.950 | 33 | 0 | 0 | 1.650 | 1.000 | 0 | 1.000 | 0.287 | 0.287 | 0.287 |
| C v1-alt | triangle | 20 | 0.550 | [0.34, 0.74] | 0.550 | 46 | 0.109 | 0 | 2.300 | 0.879 | 0 | 1.000 | 1.587 | 1.587 | 1.029 |
| C v1-alt | degree-moment2 | 20 | 0.950 | [0.76, 0.99] | 0.950 | 36 | 0.111 | 0.100 | 1.800 | 1.000 | 0 | 1.000 | 0.043 | 0.043 | 0.043 |

Parse failures by category:

| run | parse failures | categories |
|---|---|---|
| A v1 | 24 | procedural_loop:5, unknown_function:4, literal_or_index:3, condition_in_sum:3, missing_return:3, set_as_number:2, power_operator:2, project_args:1, unknown_node_name:1 |
| B v1-repeat3 | 33 | unknown_function:8, unknown_node_name:7, other:6, set_as_number:4, procedural_loop:3, missing_return:3, name_reassigned:1, condition_in_sum:1 |
| C v1-alt | 13 | unknown_function:4, set_as_number:3, unknown_node_name:2, literal_or_index:2, missing_return:1, other:1 |

## CS6c: the four fixes online

| run | task | designs | accept | accept 95% CI | qualified | drafts | parse/draft | parse/fresh draft | calls/design | gs_ratio | loose | noise_ratio | mean RE | median RE | reference RE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CS5 v0 (recorded, old deriver) | 3-star | 10 | 0.900 | [0.60, 0.98] | 0.900 | 17 | 0.294 | 0.300 | 1.700 | 1.139 | 5 | 1.005 | 0.123 | 0.124 | 0.123 |
| CS5 v0 (recorded, old deriver) | 5-star | 10 | 0.900 | [0.60, 0.98] | 0.900 | 18 | 0.278 | 0.200 | 1.800 | 1.000 | 0 | 1.000 | 0.287 | 0.287 | 0.287 |
| CS5 v0 (recorded, old deriver) | triangle | 10 | 0.400 | [0.17, 0.69] | 0.400 | 25 | 0.200 | 0.300 | 2.500 | 1.944 | 4 | 1.502 | 1.693 | 1.693 | 1.029 |
| CS5 v0 (recorded, old deriver) | degree-moment2 | 10 | 1.000 | [0.72, 1.00] | 1.000 | 14 | 0.214 | 0.300 | 1.400 | 1.105 | 10 | 1.004 | 0.043 | 0.043 | 0.043 |
| CS5 v0-r2 (recorded, old deriver) | 3-star | 10 | 1.000 | [0.72, 1.00] | 1.000 | 22 | 0.227 | 0.364 | 2.200 | 1.150 | 6 | 1.005 | 0.123 | 0.124 | 0.123 |
| CS5 v0-r2 (recorded, old deriver) | 5-star | 10 | 1.000 | [0.72, 1.00] | 1.000 | 18 | 0.056 | 0.091 | 1.800 | 1.000 | 0 | 1.000 | 0.287 | 0.287 | 0.287 |
| CS5 v0-r2 (recorded, old deriver) | triangle | 10 | 0.600 | [0.31, 0.83] | 0.600 | 38 | 0.342 | 0.333 | 3.800 | 1.660 | 5 | 1.503 | 1.694 | 1.693 | 1.029 |
| CS5 v0-r2 (recorded, old deriver) | degree-moment2 | 10 | 1.000 | [0.72, 1.00] | 1.000 | 15 | 0.133 | 0.200 | 1.500 | 1.105 | 10 | 1.004 | 0.043 | 0.043 | 0.043 |
| CS5 evolved (recorded, old deriver) | 3-star | 10 | 0.800 | [0.49, 0.94] | 0.800 | 15 | 0.400 | 0.200 | 1.500 | 1.000 | 0 | 1.000 | 0.123 | 0.123 | 0.123 |
| CS5 evolved (recorded, old deriver) | 5-star | 10 | 1.000 | [0.72, 1.00] | 1.000 | 14 | 0.214 | 0.300 | 1.400 | 1.000 | 0 | 1.000 | 0.287 | 0.287 | 0.287 |
| CS5 evolved (recorded, old deriver) | triangle | 10 | 0.300 | [0.11, 0.60] | 0.300 | 26 | 0.385 | 0.700 | 2.600 | 2.074 | 3 | 1.502 | 1.693 | 1.693 | 1.029 |
| CS5 evolved (recorded, old deriver) | degree-moment2 | 10 | 0.800 | [0.49, 0.94] | 0.800 | 16 | 0.438 | 0.300 | 1.600 | 1.079 | 6 | 1.003 | 0.043 | 0.043 | 0.043 |
| legacy | 3-star | 10 | 0.900 | [0.60, 0.98] | 0.900 | 18 | 0.056 | 0.100 | 1.800 | 1.000 | 0 | 1.000 | 0.123 | 0.123 | 0.123 |
| legacy | 5-star | 10 | 0.900 | [0.60, 0.98] | 0.900 | 19 | 0.105 | 0.200 | 1.900 | 1.000 | 0 | 1.000 | 0.287 | 0.287 | 0.287 |
| legacy | triangle | 10 | 0.300 | [0.11, 0.60] | 0.300 | 26 | 0.538 | 0.600 | 2.600 | 1.000 | 0 | 1.000 | 1.587 | 1.587 | 1.029 |
| legacy | degree-moment2 | 10 | 1.000 | [0.72, 1.00] | 1.000 | 19 | 0.211 | 0.300 | 1.900 | 1.000 | 0 | 1.000 | 0.043 | 0.043 | 0.043 |
| v1 (= CS6a A) | 3-star | 20 | 0.800 | [0.58, 0.92] | 0.800 | 48 | 0.104 | 0.100 | 2.400 | 1.000 | 0 | 1.000 | 0.123 | 0.123 | 0.123 |
| v1 (= CS6a A) | 5-star | 20 | 0.950 | [0.76, 0.99] | 0.950 | 30 | 0 | 0 | 1.500 | 1.000 | 0 | 1.000 | 0.287 | 0.287 | 0.287 |
| v1 (= CS6a A) | triangle | 20 | 0.300 | [0.15, 0.52] | 0.300 | 55 | 0.255 | 0.350 | 2.750 | 1.167 | 1 | 1.000 | 1.587 | 1.587 | 1.029 |
| v1 (= CS6a A) | degree-moment2 | 20 | 1.000 | [0.84, 1.00] | 1.000 | 38 | 0.132 | 0.250 | 1.900 | 1.000 | 0 | 1.000 | 0.043 | 0.043 | 0.043 |
| v1, 4 restarts, first | 3-star | 10 | 1.000 | [0.72, 1.00] | 1.000 | 17 | 0 | 0 | 1.700 | 1.000 | 0 | 1.000 | 0.123 | 0.123 | 0.123 |
| v1, 4 restarts, first | 5-star | 10 | 1.000 | [0.72, 1.00] | 1.000 | 15 | 0.067 | 0.100 | 1.500 | 1.000 | 0 | 1.000 | 0.287 | 0.287 | 0.287 |
| v1, 4 restarts, first | triangle | 10 | 0.400 | [0.17, 0.69] | 0.400 | 96 | 0.396 | 0.618 | 9.600 | 1.000 | 0 | 1.000 | 1.587 | 1.587 | 1.029 |
| v1, 4 restarts, first | degree-moment2 | 10 | 1.000 | [0.72, 1.00] | 1.000 | 21 | 0.190 | 0.300 | 2.100 | 1.000 | 0 | 1.000 | 0.043 | 0.043 | 0.043 |
| v1, 4 restarts, min_gs | 3-star | 10 | 1.000 | [0.72, 1.00] | 1.000 | 74 | 0.014 | 0.025 | 7.400 | 1.000 | 0 | 1.000 | 0.123 | 0.123 | 0.123 |
| v1, 4 restarts, min_gs | 5-star | 10 | 1.000 | [0.72, 1.00] | 1.000 | 66 | 0.121 | 0.150 | 6.600 | 1.000 | 0 | 1.000 | 0.287 | 0.287 | 0.287 |
| v1, 4 restarts, min_gs | triangle | 10 | 0.500 | [0.24, 0.76] | 0.500 | 107 | 0.411 | 0.475 | 10.700 | 1.000 | 0 | 1.000 | 1.587 | 1.587 | 1.029 |
| v1, 4 restarts, min_gs | degree-moment2 | 10 | 1.000 | [0.72, 1.00] | 1.000 | 74 | 0.176 | 0.250 | 7.400 | 1.000 | 0 | 1.000 | 0.043 | 0.043 | 0.043 |
| evolved | 3-star | 10 | 1.000 | [0.72, 1.00] | 1.000 | 10 | 0 | 0 | 1 | 1.000 | 0 | 1.000 | 0.123 | 0.123 | 0.123 |
| evolved | 5-star | 10 | 1.000 | [0.72, 1.00] | 1.000 | 11 | 0.091 | 0.100 | 1.100 | 1.000 | 0 | 1.000 | 0.287 | 0.287 | 0.287 |
| evolved | triangle | 10 | 0.300 | [0.11, 0.60] | 0.300 | 26 | 0.308 | 0.400 | 2.600 | 1.333 | 1 | 1.000 | 1.587 | 1.587 | 1.029 |
| evolved | degree-moment2 | 10 | 1.000 | [0.72, 1.00] | 1.000 | 11 | 0 | 0 | 1.100 | 1.000 | 0 | 1.000 | 0.043 | 0.043 | 0.043 |
| evolved, 4 restarts, min_gs | 3-star | 10 | 1.000 | [0.72, 1.00] | 1.000 | 45 | 0.111 | 0.125 | 4.500 | 1.000 | 0 | 1.000 | 0.123 | 0.123 | 0.123 |
| evolved, 4 restarts, min_gs | 5-star | 10 | 1.000 | [0.72, 1.00] | 1.000 | 45 | 0.067 | 0.075 | 4.500 | 1.000 | 0 | 1.000 | 0.287 | 0.287 | 0.287 |
| evolved, 4 restarts, min_gs | triangle | 10 | 0.700 | [0.40, 0.89] | 0.700 | 107 | 0.393 | 0.375 | 10.700 | 1.000 | 0 | 1.000 | 1.587 | 1.587 | 1.029 |
| evolved, 4 restarts, min_gs | degree-moment2 | 10 | 1.000 | [0.72, 1.00] | 1.000 | 49 | 0.102 | 0.125 | 4.900 | 1.000 | 0 | 1.000 | 0.043 | 0.043 | 0.043 |

Parse failures by category:

| run | parse failures | categories |
|---|---|---|
| CS5 v0 (recorded, old deriver) | 18 | tag_line:6, set_as_number:6, unknown_node_name:4, name_reassigned:1, power_operator:1 |
| CS5 v0-r2 (recorded, old deriver) | 21 | floor_div_or_mod:3, condition_in_sum:3, unknown_node_name:3, tag_line:3, set_as_number:2, project_args:2, name_reassigned:1, unknown_function:1, other:1, literal_or_index:1, power_operator:1 |
| CS5 evolved (recorded, old deriver) | 26 | tag_line:12, unknown_node_name:4, set_as_number:3, floor_div_in_aggregate:3, condition_in_sum:1, procedural_loop:1, literal_or_index:1, power_operator:1 |
| legacy | 21 | set_as_number:5, tag_line:3, condition_in_sum:3, other:3, literal_or_index:2, procedural_loop:1, unknown_function:1, unknown_node_name:1, missing_return:1, power_operator:1 |
| v1 (= CS6a A) | 24 | procedural_loop:5, unknown_function:4, literal_or_index:3, condition_in_sum:3, missing_return:3, set_as_number:2, power_operator:2, project_args:1, unknown_node_name:1 |
| v1, 4 restarts, first | 43 | procedural_loop:14, condition_in_sum:9, unknown_function:6, literal_or_index:6, set_as_number:2, unknown_node_name:2, missing_return:2, other:1, power_operator:1 |
| v1, 4 restarts, min_gs | 66 | unknown_function:13, procedural_loop:9, set_as_number:8, floor_div_in_aggregate:7, missing_return:6, power_operator:6, unknown_node_name:4, other:4, literal_or_index:4, condition_in_sum:3, project_args:1, name_reassigned:1 |
| evolved | 9 | procedural_loop:4, literal_or_index:2, condition_in_sum:2, set_as_number:1 |
| evolved, 4 restarts, min_gs | 55 | missing_return:12, set_as_number:10, other:8, condition_in_sum:8, procedural_loop:6, name_reassigned:4, unknown_node_name:3, literal_or_index:2, unknown_function:2 |

## CS6c: prompt evolution

### cs6c_evolve_psc

Best prompt: g1c3 (f4723269c9dad172, core v1); falsifier refutations during the evolution: 0 (must be 0).

| gen | kind | name | mean score | se | evals | qualified | qualified 95% CI | accepted | calls/design | patch |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | parent | v0 | 0.887 | 0.044 | 1 | 0.938 | [0.80, 0.98] | 0.938 | 1.812 | - |
| 1 | child | g1c1 | 0.893 | 0.045 | 1 | 0.938 | [0.80, 0.98] | 0.938 | 1.469 | {"module": "rules", "op": "add", "index": 0, "value": "Bound neighbor sets with project(P, D) before |
| 1 | child | g1c2 | 0.918 | 0.032 | 1 | 0.969 | [0.84, 0.99] | 0.969 | 1.562 | {"module": "repair_hints", "op": "add", "index": 0, "value": {"pattern": ".*comb\\(size\\(P\\), \\d+ |
| 1 | child | g1c3 | 0.928 | 0.033 | 1 | 0.969 | [0.84, 0.99] | 0.969 | 1.188 | {"module": "rules", "op": "add", "index": 0, "value": "Always apply project(P, D) before using comb  |
| 1 | parent | v0 | 0.886 | 0.031 | 2 | 0.938 | [0.80, 0.98] | 0.938 | 1.781 | - |
| 1 | confirm | g1c3 | 0.926 | 0.023 | 2 | 0.969 | [0.84, 0.99] | 0.969 | 1.281 | - |
| 2 | child | g2c1 | 0.894 | 0.045 | 1 | 0.938 | [0.80, 0.98] | 0.938 | 1.281 | {"module": "rules", "op": "add", "index": 0, "value": "Always apply project(P, D) to sets before usi |
| 2 | child | g2c2 | 0.867 | 0.054 | 1 | 0.906 | [0.76, 0.97] | 0.906 | 1.344 | {"module": "rules", "op": "add", "index": 0, "value": "Bound neighbor sets with project(..., D) befo |
| 2 | child | g2c3 | 0.866 | 0.054 | 1 | 0.906 | [0.76, 0.97] | 0.906 | 1.344 | {"module": "rules", "op": "replace", "index": 0, "value": "Always apply project(S, D) before using c |
| 2 | parent | g1c3 | 0.915 | 0.021 | 3 | 0.938 | [0.80, 0.98] | 0.938 | 1.438 | - |
| 3 | child | g3c1 | 0.925 | 0.033 | 1 | 0.969 | [0.84, 0.99] | 0.969 | 1.344 | {"module": "rules", "op": "add", "index": 0, "value": "Bound all neighbor sets with project(..., D)  |
| 3 | child | g3c2 | 0.919 | 0.033 | 1 | 0.969 | [0.84, 0.99] | 0.969 | 1.438 | {"module": "rules", "op": "add", "index": 1, "value": "Always project all sets used in set operation |
| 3 | child | g3c3 | 0.897 | 0.045 | 1 | 0.938 | [0.80, 0.98] | 0.938 | 1.250 | {"module": "rules", "op": "add", "index": 0, "value": "Bound all neighbor sets with project(..., D)  |
| 3 | parent | g1c3 | 0.903 | 0.021 | 4 | 0.906 | [0.76, 0.97] | 0.906 | 1.188 | - |
| 3 | confirm | g3c1 | 0.894 | 0.031 | 2 | 0.906 | [0.76, 0.97] | 0.906 | 1.469 | - |

| gen | incumbent | mean | se | improved | Pareto front |
|---|---|---|---|---|---|
| 1 | g1c3 | 0.926 | 0.023 | True | v0, g1c1, g1c2, g1c3 |
| 2 | g1c3 | 0.915 | 0.021 | False | v0, g1c1, g1c2, g1c3, g2c1, g2c2, g2c3 |
| 3 | g1c3 | 0.903 | 0.021 | False | v0, g1c1, g1c2, g1c3, g2c1, g2c2, g2c3, g3c1, g3c2, g3c3 |

Best prompt modules:

```json
{
  "rules": [
    "Always apply project(P, D) before using comb or pow on the size of P to ensure tight bounds and correct sensitivity."
  ],
  "examples": [],
  "repair_hints": []
}
```

## CS6b: offline replay and fuzzing

See results/dsl_eval/cs6b_offline_replay/table.md
- cs6b_fuzz_shapes: {"count": 3000, "failures": 0}
- cs6b_fuzz_mixed: {"count": 3000, "failures": 0}
