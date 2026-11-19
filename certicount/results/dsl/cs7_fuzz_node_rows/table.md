# Deriver fuzz

3000 random programs (seed 3, depth 3, focus 0.5, shapes 0.5, matrix 0.0); GS derived at `PublicParams(n, D, dmax)` (D = dmax unless the setting gives the node's own bound) vs the falsifier's largest change on the same parameters (node 0, every P, every flip); 615s with 4 worker(s).

`refuted`: falsifier change > derived GS (a deriver bug, must be 0); `tight`: equal; `median_gs_over_max` / `max_gs_over_max` over programs with a nonzero change (> 1: possibly loose).

| n | dmax | D | graphs | programs | reads_matrix | derived | rejected_by_deriver | interpreter_errors | falsified | refuted | tight | zero_change | median_gs_over_max | max_gs_over_max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 3 | 2 | every | 3000 | 0 | 2947 | 53 | 0 | 2947 | 0 | 1694 | 352 | 1.0000 | 252.0000 |
| 7 | 4 | 2 | 200 random | 3000 | 0 | 2947 | 53 | 0 | 2947 | 0 | 1680 | 352 | 1.0000 | 340.0000 |
| 6 | 3 | 5 | 200 random | 3000 | 0 | 2947 | 53 | 0 | 2947 | 0 | 1480 | 220 | 1.1667 | 780.0000 |

## Refuted or failing programs: 0

## Loosest bounds (n = 5, dmax = 3)

| index | gs | max_delta | gs_over_max | program |
|---|---|---|---|---|
| 1261 | 126.0000 | 0.5000 | 252.0000 | x0 = clip(D, 0, D) ; return min(sum(sum((size((N(j) - P)) * size((P & N(k)))) for k in P) for j in (P & N(self))), ((size(N(self)) - size(P))) / D) |
| 619 | 4.4e+05 | 3159.0000 | 139.2821 | return -1 * sum(sum(sum(size(P & N(u)) * size(N(u)) * comb(size((N(u) & N(self))), 2) for u in P) * size(P & N(k)) * size((P & N(k))) for k in (N(self) & P)) * size(N(j) & P) * comb(size((P & N(j))), 2) for j in P) |
| 2516 | 1.292e+06 | 1.118e+04 | 115.5105 | return sum(size((N(j) & P)) * sum(size(N(k) & P) * comb(size(((P & N(k)) & N(self))), 2) * sum(size(N(u) & P) * 3 * size((N(u) & P)) for u in (N(self) & P)) for k in N(j)) * size(N(j) & P) * size((N(j) & P)) for j in (P & N(self))) |
| 947 | 5.926e+04 | 864.0000 | 68.5833 | S0 = P & N(self) ; return sum(size(P & N(j)) * comb(size((P & N(j))), 2) * sum(sum(size(((P & N(u)) & N(self))) + size(N(u) & P) for u in (P & N(self))) * size(((P & N(k)) & N(self))) * size(P & N(k)) for k in P) for j in (P & N(self))) |
| 1486 | 186.0000 | 3.0000 | 62.0000 | return min(comb(size((P & N(self))), 2), sum((sum((size((P & N(self))) + size((N(k) & N(self)))) for k in (P & N(j))) * size((N(j) & P))) for j in (P & N(self)))) |
| 1189 | 5.2e+04 | 840.0000 | 61.9071 | return sum(size(project((P & N(j)), 2)) * size(P & N(j)) * sum(size((N(k) & P)) * size(P & N(k)) * sum(size(N(u) & P) * comb(size((N(u) & N(self))), 2) for u in (N(self) & P)) for k in N(self)) for j in (N(self) & P)) |
| 1632 | 5310.0000 | 96.0000 | 55.3125 | return 2 * sum(size(P & N(j)) * size(((P & N(j)) & N(self))) * sum(size(N(k) & P) * comb(size((P & N(k))), 2) for k in (N(j) & P)) for j in (P & N(self))) |
| 2140 | 1.6e+05 | 3408.0000 | 46.9489 | return 2 * sum(size((P & N(j))) * sum(size(P & N(k)) * size((P & N(k))) * sum(size(P & N(u)) * size((N(u) & P)) for u in (P & N(self))) for k in N(self)) * size(P & N(j)) for j in (N(self) & P)) |
| 1322 | 5.202e+04 | 1144.0000 | 45.4720 | return sum(size(project((P & N(j)), 2)) * sum(sum(comb(size(project((P & N(u)), 2)), 2) + size(N(u) & P) + comb(size((N(u) & N(self))), 2) for u in project(P, D)) * size((P & N(k))) * size(P & N(k)) for k in (P & N(self))) * size(N(j) & P) for j in (P & N(self))) |
| 1439 | 5316.0000 | 120.0000 | 44.3000 | S0 = P & N(self) ; return sum(size((P & N(j))) * sum(size(N(k)) + size(N(k) & P) for k in project(P, D)) * size(P & N(j)) * comb(size(((P & N(j)) & N(self))), 2) for j in S0) |
