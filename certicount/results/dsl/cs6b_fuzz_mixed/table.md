# Deriver fuzz

3000 random programs (seed 1, depth 3, focus 0.5, shapes 0.3); GS derived at `PublicParams(n, D = dmax, dmax)` vs the falsifier's largest change on the same parameters (node 0, every P, every flip); 298s with 8 worker(s).

`refuted`: falsifier change > derived GS (a deriver bug, must be 0); `tight`: equal; `median_gs_over_max` / `max_gs_over_max` over programs with a nonzero change (> 1: possibly loose).

| n | dmax | graphs | programs | derived | rejected_by_deriver | interpreter_errors | falsified | refuted | tight | zero_change | median_gs_over_max | max_gs_over_max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 3 | every | 3000 | 2967 | 33 | 0 | 2967 | 0 | 1502 | 311 | 1.1818 | 226.4062 |
| 7 | 4 | 200 random | 3000 | 2967 | 33 | 0 | 2967 | 0 | 1377 | 305 | 1.2000 | 274.6667 |

## Refuted or failing programs: 0

## Loosest bounds (n = 5, dmax = 3)

| index | gs | max_delta | gs_over_max | program |
|---|---|---|---|---|
| 1741 | 1.174e+06 | 5184.0000 | 226.4062 | return sum(size(N(j) & P) * sum(size(N(k) & P) * sum(size(N(u) & P) * 3 * size(project((P & N(u)), 2)) * size(((P & N(u)) & N(self))) for u in (N(self) & P)) * size(((P & N(k)) & N(self))) for k in (P & N(self))) * comb(size((N(j) & P)), 2) for j in (P & N(self))) |
| 76 | 249.0000 | 2.0000 | 124.5000 | return min(sum((sum(size(P) for k in project(P, D)) * size((P - N(j)))) for j in P), -1 * sum(size(project(N(j), D - 1)) for j in project(P, D))) |
| 1736 | 4.123e+04 | 424.0000 | 97.2382 | return sum(size(P & N(j)) * sum(size((P & N(k))) * size(N(k) & P) * sum(size(P & N(u)) * comb(size(project((P & N(u)), 2)), 2) for u in N(self)) for k in project(P, D)) * comb(size((N(j) & N(self))), 2) for j in (P & N(self))) |
| 1371 | 231.0000 | 3.0000 | 77.0000 | S0 = ((P - P) & (P | (P & N(self)))) ; return sum((sum((size((N(k) - P)) * size((N(k) & P))) for k in S0) + D) for j in (P & N(self))) |
| 61 | 7.42e+04 | 1092.0000 | 67.9451 | return sum(sum(size(N(k) & P) * size(project((P & N(k)), 2)) * sum(size(((P & N(u)) & N(self))) * size(P & N(u)) for u in (N(j) & N(self))) for k in N(self)) * size(P & N(j)) * size((P & N(j))) for j in P) |
| 935 | 117.0000 | 2.0000 | 58.5000 | return min(sum((sum(size((P & N(self))) for k in N(self)) * size((N(j) & P))) for j in (P & (P & N(self)))), size((P - N(self)))) |
| 718 | 1.941e+05 | 3408.0000 | 56.9472 | S0 = P & N(self) ; return sum(size((P & N(j))) * size((N(j) & N(self))) * size(N(j) & P) * sum(sum(size(N(u) & P) * -1 * size(project((P & N(u)), 2)) for u in N(self)) * size(project((P & N(k)), 2)) * size(P & N(k)) for k in project(P, D)) for j in (P & N(self))) |
| 1629 | 2.069e+05 | 3992.0000 | 51.8357 | return sum(sum(size(P & N(k)) * sum(size(project((P & N(u)), 2)) + size(P & N(u)) + size(N(u)) for u in (P & N(k))) * size(project((P & N(k)), 2)) for k in project(P, D)) * size(N(j) & P) * size((N(j) & P)) * size((N(j) & N(self))) for j in (P & N(self))) |
| 236 | 8.367e+04 | 1712.0000 | 48.8744 | return sum(sum(sum(size((N(u) & P)) * size(P & N(u)) for u in (N(self) & P)) * size(N(k) & P) * size((N(k) & P)) for k in project(P, D)) * size((N(j) & N(self))) * size(N(j) & P) for j in (N(self) & P)) |
| 483 | 138.0000 | 3.0000 | 46.0000 | return min(size(project((P & N(self)), dmax)), sum(((size(N(self)) * size((P & N(self)))) * size((P & N(j)))) for j in (P & P))) |
