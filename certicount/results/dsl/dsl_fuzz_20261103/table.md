# Deriver fuzz

10000 random programs (seed 0, depth 3, focus 0.5); GS derived at `PublicParams(n, D = dmax, dmax)` vs the falsifier's largest change on the same parameters (node 0, every P, every flip); 220s with 8 worker(s).

`refuted`: falsifier change > derived GS (a deriver bug, must be 0); `tight`: equal; `median_gs_over_max` / `max_gs_over_max` over programs with a nonzero change (> 1: possibly loose).

| n | dmax | graphs | programs | derived | rejected_by_deriver | interpreter_errors | falsified | refuted | tight | zero_change | median_gs_over_max | max_gs_over_max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 3 | every | 10000 | 10000 | 0 | 0 | 10000 | 0 | 4142 | 1366 | 1.5000 | 5960.7338 |
| 7 | 4 | 200 random | 10000 | 10000 | 0 | 0 | 10000 | 0 | 4154 | 1350 | 1.4000 | 2108.4809 |

## Refuted or failing programs: 0

## Loosest bounds (n = 5, dmax = 3)

| index | gs | max_delta | gs_over_max | program |
|---|---|---|---|---|
| 7959 | 4.091e+07 | 6864.0000 | 5960.7338 | return sum(size(((P & N(j)) & N(self))) * size(N(j) & P) * sum(sum(size(P & N(u)) * size((N(u) & P)) * 3 * size((N(u) & P)) for u in project(P, D)) * comb(size(((P & N(k)) & N(self))), 2) * comb(size(((P & N(k)) & N(self))), 2) * size(N(k) & P) for k in (N(j) & N(self))) * size((N(j) & N(self))) for j in P) |
| 6599 | 4.026e+05 | 576.0000 | 698.9062 | S0 = P & N(self) ; return sum(sum(size(N(k) & P) * comb(size((P & N(k))), 2) * sum(size(((P & N(u)) & N(self))) + size(N(u) & P) for u in (P & N(j))) for k in S0) * comb(size((N(j) & P)), 2) * size(((P & N(j)) & N(self))) * size(N(j) & P) for j in (N(self) & P)) |
| 6257 | 2.086e+07 | 3.213e+04 | 649.2992 | return 2 * sum(sum(size((N(k) & P)) * sum(size(((P & N(u)) & N(self))) * size(P & N(u)) * comb(size(((P & N(u)) & N(self))), 2) for u in project(P, D)) * size(N(k) & P) * -1 * size((P & N(k))) for k in (P & N(self))) * size(P & N(j)) * -1 * size((N(j) & P)) * size((N(j) & N(self))) for j in P) |
| 2470 | 2.231e+05 | 632.0000 | 352.9652 | return sum(size(N(j) & P) * comb(size((P & N(j))), 2) * sum(size(((P & N(k)) & N(self))) * sum(size(((P & N(u)) & N(self))) + -1 * size((N(u) & P)) + size(N(u) & P) for u in N(k)) * size(P & N(k)) for k in (P & N(j))) * size((N(j) & N(self))) for j in N(self)) |
| 6783 | 8194.5000 | 26.0000 | 315.1731 | return 0.5 * sum(sum(size(((P & N(k)) & N(self))) * sum(-1 * size((N(u) & N(self))) + size(P & N(u)) for u in (N(self) & P)) * size(P & N(k)) for k in N(j)) * size(P & N(j)) * comb(size((N(j) & N(self))), 2) for j in (P & N(self))) |
| 2076 | 263.0000 | 1.0000 | 263.0000 | S0 = project(P, n - 4) ; return max((sum((size((project(P, D) & N(j))) - size((project(P, D) & N(j)))) for j in (N(self) & P)) * sum(size(P) for j in S0)), min(sum((size(N(self)) * size((N(j) | P))) for j in (N(self) & P)), size(S0))) |
| 8011 | 6.855e+05 | 3456.0000 | 198.3438 | return -1 * sum(sum(2 * size((P & N(k))) * sum(size((N(u) & N(self))) + size(P & N(u)) for u in project(P, D)) * size(P & N(k)) for k in N(self)) * size(N(j) & P) * size((N(j) & P)) * comb(size((P & N(j))), 2) for j in (N(self) & P)) |
| 2850 | 540.0000 | 3.0000 | 180.0000 | S0 = (P & N(self)) ; return min(sum((sum((size(N(self)) * size((project(P, D) & N(k)))) for k in N(self)) * size((N(j) | P))) for j in S0), size((S0 & (P & N(self))))) |
| 4482 | 180.0000 | 1.0000 | 180.0000 | return min(comb(sum((size(P) * size((N(j) | P))) for j in P), 0), (sum((size((N(j) - P)) * size((P - N(j)))) for j in (P & N(self))) * size((P & N(self))))) |
| 1975 | 1.424e+05 | 824.0000 | 172.8131 | S0 = P & N(self) ; return sum(size(project((P & N(j)), 2)) * size(N(j) & P) * size(((P & N(j)) & N(self))) * sum(size(P & N(k)) * sum(size(P & N(u)) + -1 * size((N(u) & P)) + 0.5 * size((N(u) & N(self))) for u in project(P, D)) * size(project((P & N(k)), 2)) for k in (P & N(self))) for j in N(self)) |
