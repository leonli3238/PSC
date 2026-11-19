# Deriver fuzz

3000 random programs (seed 2, depth 3, focus 0.5, shapes 0.0, matrix 1.0); GS derived at `PublicParams(n, D, dmax)` (D = dmax unless the setting gives the node's own bound) vs the falsifier's largest change on the same parameters (node 0, every P, every flip); 304s with 4 worker(s).

`refuted`: falsifier change > derived GS (a deriver bug, must be 0); `tight`: equal; `median_gs_over_max` / `max_gs_over_max` over programs with a nonzero change (> 1: possibly loose).

| n | dmax | D | graphs | programs | reads_matrix | derived | rejected_by_deriver | interpreter_errors | falsified | refuted | tight | zero_change | median_gs_over_max | max_gs_over_max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 3 | 3 | every | 3000 | 2825 | 3000 | 0 | 0 | 3000 | 0 | 730 | 955 | 2.0000 | 7565.0291 |
| 7 | 4 | 4 | 200 random | 3000 | 2825 | 3000 | 0 | 0 | 3000 | 0 | 742 | 943 | 1.9592 | 1389.2553 |
| 7 | 4 | 2 | 200 random | 3000 | 2825 | 3000 | 0 | 0 | 3000 | 0 | 876 | 1070 | 2.0000 | 1.065e+04 |
| 6 | 3 | 5 | 200 random | 3000 | 2825 | 3000 | 0 | 0 | 3000 | 0 | 680 | 945 | 2.0000 | 962.3558 |

## Refuted or failing programs: 0

## Loosest bounds (n = 5, dmax = 3)

| index | gs | max_delta | gs_over_max | program |
|---|---|---|---|---|
| 1777 | 2.01e+04 | 2.6564 | 7565.0291 | Q = project(P, D - 1) ; T = project(P, 2) ; x = sum(sum(A(j, k) for k in (Q | T)) for j in (Q & T)) ; return x * (x - 1) * (x - 2) / 6 |
| 1948 | 2.01e+04 | 2.6564 | 7565.0291 | Q = project(P, D - 1) ; T = project(P, 2) ; x = sum(sum(A(j, k) for k in (Q | T)) for j in (Q & T)) ; return x * (x - 1) * (x - 2) / 6 |
| 2865 | 2.01e+04 | 2.6564 | 7565.0291 | Q = project(P, 2) ; T = project(P, D - 1) ; x = sum(sum(A(j, k) for k in (Q | T)) for j in (Q & T)) ; return x * (x - 1) * (x - 2) / 6 |
| 423 | 1.267e+04 | 8.1362 | 1556.6667 | Q = P ; T = project(P, D) ; x = sum(sum(A(j, k) for k in (Q - T)) for j in Q) ; return x * (x - 1) * (x - 2) / 6 |
| 1328 | 1.267e+04 | 8.1362 | 1556.6667 | Q = P ; T = project(P, dmax) ; x = sum(sum(A(j, k) for k in (Q - T)) for j in Q) ; return x * (x - 1) * (x - 2) / 6 |
| 1412 | 1.267e+04 | 8.1362 | 1556.6667 | Q = P ; T = project(P, dmax) ; x = sum(sum(A(j, k) for k in (Q - T)) for j in Q) ; return x * (x - 1) * (x - 2) / 6 |
| 1421 | 3.388e+04 | 24.3877 | 1389.2553 | Q = project(P, D) ; T = project(P, D - 1) ; x = sum(sum(A(j, k) for k in (Q | T)) for j in (Q & T)) ; return x * (x - 1) * (x - 2) / 6 |
| 1789 | 3.388e+04 | 24.3877 | 1389.2553 | Q = project(P, D - 1) ; T = project(P, dmax) ; x = sum(sum(A(j, k) for k in (Q | T)) for j in (Q & T)) ; return x * (x - 1) * (x - 2) / 6 |
| 2209 | 3.388e+04 | 24.3877 | 1389.2553 | Q = project(P, D) ; T = project(P, D - 1) ; x = sum(sum(A(j, k) for k in (Q | T)) for j in (Q & T)) ; return x * (x - 1) * (x - 2) / 6 |
| 655 | 6.382e+04 | 100.6185 | 634.2316 | Q = project(P, D) ; T = project(P, D) ; x = sum(sum(A(j, k) for k in (Q | T)) for j in (Q & T)) ; return x * (x - 1) * (x - 2) / 6 |
