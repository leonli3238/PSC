# Deriver fuzz

3000 random programs (seed 0, depth 3, focus 0.5, shapes 1.0); GS derived at `PublicParams(n, D = dmax, dmax)` vs the falsifier's largest change on the same parameters (node 0, every P, every flip); 180s with 8 worker(s).

`refuted`: falsifier change > derived GS (a deriver bug, must be 0); `tight`: equal; `median_gs_over_max` / `max_gs_over_max` over programs with a nonzero change (> 1: possibly loose).

| n | dmax | graphs | programs | derived | rejected_by_deriver | interpreter_errors | falsified | refuted | tight | zero_change | median_gs_over_max | max_gs_over_max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 3 | every | 3000 | 2891 | 109 | 0 | 2891 | 0 | 1940 | 82 | 1.0000 | 4.6667 |
| 7 | 4 | 200 random | 3000 | 2891 | 109 | 0 | 2891 | 0 | 1704 | 84 | 1.0000 | 6.0000 |

## Refuted or failing programs: 0

## Loosest bounds (n = 5, dmax = 3)

| index | gs | max_delta | gs_over_max | program |
|---|---|---|---|---|
| 151 | 14.0000 | 3.0000 | 4.6667 | Q = project(P, 2) ; return -1 * sum(size((Q - N(j))) + size(P & N(j)) for j in Q) |
| 671 | 14.0000 | 3.0000 | 4.6667 | Q = project(P, D - 1) ; return -1 * sum(size((Q - N(j))) + size(P & N(j)) for j in Q) |
| 1163 | 14.0000 | 3.0000 | 4.6667 | Q = project(P, 2) ; return -1 * sum(size((Q - N(j))) + size(P & N(j)) for j in Q) |
| 1340 | 14.0000 | 3.0000 | 4.6667 | Q = project(P, D - 1) ; return sum(size((Q - N(j))) + size(P & N(j)) for j in Q) |
| 1846 | 7.0000 | 1.5000 | 4.6667 | Q = project(P, D - 1) ; return 0.5 * sum(size((Q - N(j))) + size(P & N(j)) for j in Q) |
| 2651 | 7.0000 | 1.5000 | 4.6667 | Q = project(P, D - 1) ; return 0.5 * sum(size((Q - N(j))) + size(P & N(j)) for j in Q) |
| 266 | 4.0000 | 1.0000 | 4.0000 | Q = (project(P, D) - N(self)) ; return sum(size((N(j) & Q & N(self))) - 1 for j in Q) |
| 610 | 2.0000 | 0.5000 | 4.0000 | Q = (project(P, D) - N(self)) ; return 0.5 * sum(size((N(j) & Q & N(self))) - 1 for j in Q) |
| 1840 | 2.0000 | 0.5000 | 4.0000 | Q = (project(P, D) - N(self)) ; return 0.5 * sum(size((N(j) & Q & N(self))) - 1 for j in Q) |
| 2487 | 2.0000 | 0.5000 | 4.0000 | Q = (project(P, D) - N(self)) ; return 0.5 * sum(size((N(j) & Q & N(self))) - 1 for j in Q) |
