# CS7 offline replay: own-row check, no gate, simulated choice (per-node architecture)

Runs: cs4_online_node-arch_d10_a5.0, cs5_eval_node_v0, cs5_eval_node_evolved, cs5_eval_node_v0-r2; 50 paired code runs per program (seed [run seed, i]). The replay accepts a design at its first recorded draft that passes the new checks; pairs of recorded designs of one run stand in for the two design rounds.

`recorded_*`: the run's own outcome (old checks, gate on); `nogate_accept`: new checks without the own-row check; `single_*`: one loop with the own-row check, no gate; `pair_*`: two loops, `first_re` keeps the first accepted program, `choice_re` the simulated choice; `pair_reads`: what the chosen programs read (P only, N rows, A matrix; several letters: run-time choice).

| task | designs | pairs | reference_re | recorded_accept | recorded_re | recorded_own_row | nogate_accept | single_accept | single_re | pair_accept | pair_first_re | pair_choice_re | pair_reads |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3-star | 40 | 20 | 0.0105 | 0.8250 | 0.0373 | 12 | 0.9000 | 0.5250 | 0.0105 | 0.7500 | 0.0105 | 0.0105 | P |
| 5-star | 30 | 15 | 0.0212 | 0.9000 | 0.0561 | 9 | 0.9333 | 0.6000 | 0.0212 | 0.8667 | 0.0212 | 0.0212 | P |
| triangle | 40 | 20 | 0.1497 | 0.6750 | 0.2526 | 0 | 0.6750 | 0.6750 | 0.2526 | 0.8500 | 0.1498 | 0.1498 | A |
| degree-moment2 | 30 | 15 | 0.0083 | 0.8333 | 0.0412 | 16 | 0.9667 | 0.3000 | 0.0083 | 0.4667 | 0.0083 | 0.0083 | P |

## Design-time simulated score against the real error

| task | programs | rank_agreement | sim_score | real_re | program |
|---|---|---|---|---|---|
| 3-star | 32 | 0.9231 | - | - | - |
| 3-star |  | - | 0.0216 | 0.0105 | d = size(project(P, D)) ; return comb(d, 3) ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | deg = size(project(P, D)) ; return comb(deg, 3) ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | degree = size(project(P, D)) ; return comb(degree, 3) ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | degree = size(project(P, D)) ; return degree * (degree - 1) * (degree - 2) / 6 ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | k = size(project(P, D)) ; return comb(k, 3) ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | name = project(P, D) ; degree = size(name) ; return comb(degree, 3) ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | name = size(project(P, D)) ; return comb(name, 3) ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | name = size(project(P, D)) ; stars = comb(name, 3) ; return stars ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | neighbors = project(P, D) ; degree = size(neighbors) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | projected = project(P, D) ; count = comb(size(projected), 3) ; return count ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | projected = project(P, D) ; degree = size(projected) ; count = comb(degree, 3) ; return count ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | projected = project(P, D) ; degree = size(projected) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | projected = project(P, D) ; return comb(size(projected), 3) ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | projected_P = project(P, D) ; degree = size(projected_P) ; count = comb(degree, 3) ; return count ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | projected_P = project(P, D) ; degree = size(projected_P) ; return comb(degree, 3) ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | projected_P = project(P, D) ; degree = size(projected_P) ; return degree * (degree - 1) * (degree - 2) / 6 ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | projected_P = project(P, D) ; degree = size(projected_P) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | projected_P = project(P, D) ; return comb(size(projected_P), 3) ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | projected_neighbors = project(P, D) ; degree = size(projected_neighbors) ; report = comb(degree, 3) ; return report ; aggregate: total |
| 3-star |  | - | 0.0216 | 0.0105 | projected_neighbors = project(P, D) ; degree = size(projected_neighbors) ; stars = comb(degree, 3) ; return stars ; aggregate: total |
| 3-star |  | - | 0.1856 | 0.1367 | projected_neighbors = project(P, D) ; degree_estimate = sum(A(self, v) for v in projected_neighbors) ; count = degree_estimate * (degree_estimate - 1) * (degree_estimate - 2) / 6 ; return count ; aggregate: total |
| 3-star |  | - | 0.1856 | 0.1367 | return (sum(A(self, j) for j in project(P, D)) * (sum(A(self, j) for j in project(P, D)) - 1) * (sum(A(self, j) for j in project(P, D)) - 2)) / 6 ; aggregate: total |
| 3-star |  | - | 0.8369 | 0.0739 | count = comb(size(project(N(self), D)), 3) ; return count ; aggregate: total |
| 3-star |  | - | 0.8369 | 0.0739 | name = clip(size(N(self)), 0, D) ; return comb(name, 3) ; aggregate: total |
| 3-star |  | - | 0.8369 | 0.0739 | name = comb(size(project(N(self), D)), 3) ; return name ; aggregate: total |
| 3-star |  | - | 0.8369 | 0.0739 | name = project(N(self), D) ; return comb(size(name), 3) ; aggregate: total |
| 3-star |  | - | 0.8369 | 0.0739 | name = size(project(N(self), D)) * (size(project(N(self), D)) - 1) * (size(project(N(self), D)) - 2) / 6 ; return name ; aggregate: total |
| 3-star |  | - | 0.8369 | 0.0739 | name = size(project(N(self), D)) ; return comb(name, 3) ; aggregate: total |
| 3-star |  | - | 0.8369 | 0.0739 | projected = project(N(self), D) ; d = size(projected) ; count = comb(d, 3) ; return count ; aggregate: total |
| 3-star |  | - | 0.8369 | 0.0739 | projected = project(N(self), D) ; d = size(projected) ; return d * (d - 1) * (d - 2) / 6 ; aggregate: total |
| 3-star |  | - | 0.8369 | 0.0739 | projected_neighbors = project(N(self), D) ; degree = size(projected_neighbors) ; return comb(degree, 3) ; aggregate: total |
| 3-star |  | - | 0.8369 | 0.0739 | report = comb(size(project(N(self), D)), 3) ; return report ; aggregate: total |
| 5-star | 16 | 1 | - | - | - |
| 5-star |  | - | 0.0487 | 0.0212 | degree = size(project(P, D)) ; count = comb(degree, 5) ; return count ; aggregate: total |
| 5-star |  | - | 0.0487 | 0.0212 | name = comb(size(project(P, D)), 5) ; return name ; aggregate: total |
| 5-star |  | - | 0.0487 | 0.0212 | name = size(project(P, D)) ; return comb(name, 5) ; aggregate: total |
| 5-star |  | - | 0.0487 | 0.0212 | projected = project(P, D) ; return comb(size(projected), 5) ; aggregate: total |
| 5-star |  | - | 0.0487 | 0.0212 | projected = project(P, D) ; size_p = size(projected) ; return comb(size_p, 5) ; aggregate: total |
| 5-star |  | - | 0.0487 | 0.0212 | projected = project(P, D) ; size_projected = size(projected) ; return comb(size_projected, 5) ; aggregate: total |
| 5-star |  | - | 0.0487 | 0.0212 | projected_P = project(P, D) ; count = comb(size(projected_P), 5) ; return count ; aggregate: total |
| 5-star |  | - | 0.0487 | 0.0212 | projected_P = project(P, D) ; degree = size(projected_P) ; return comb(degree, 5) ; aggregate: total |
| 5-star |  | - | 0.0487 | 0.0212 | return comb(size(project(P, D)), 5) ; aggregate: total |
| 5-star |  | - | 0.0487 | 0.0212 | size_proj = size(project(P, D)) ; return comb(size_proj, 5) ; aggregate: total |
| 5-star |  | - | 0.3814 | 0.1260 | name = comb(size(project(N(self), D)), 5) ; return name ; aggregate: total |
| 5-star |  | - | 0.3814 | 0.1260 | name = project(N(self), D) ; result = comb(size(name), 5) ; return result ; aggregate: total |
| 5-star |  | - | 0.3814 | 0.1260 | name = size(project(N(self), D)) ; return comb(name, 5) ; aggregate: total |
| 5-star |  | - | 0.3814 | 0.1260 | projected = project(N(self), D) ; count = comb(size(projected), 5) ; return count ; aggregate: total |
| 5-star |  | - | 0.3814 | 0.1260 | projected = project(N(self), D) ; size_projected = size(projected) ; return comb(size_projected, 5) ; aggregate: total |
| 5-star |  | - | 0.3814 | 0.1260 | size_n = size(N(self)) ; projected_size = min(size_n, D) ; count = comb(projected_size, 5) ; return count ; aggregate: total |
| triangle | 26 | 1 | - | - | - |
| triangle |  | - | 0.4533 | 0.1497 | P_proj = project(P, D) ; return sum( A(v, w) for v in P_proj for w in P_proj ) ; aggregate: total / 6 |
| triangle |  | - | 0.4533 | 0.1497 | S = project(P, D) ; edges_between_neighbors = sum( sum( A(v, w) for w in S ) for v in S ) / 2 ; return edges_between_neighbors ; aggregate: total / 3 |
| triangle |  | - | 0.4533 | 0.1497 | S = project(P, D) ; return sum(A(v, w) for v in S for w in S) / 2 ; aggregate: total / 3 |
| triangle |  | - | 0.4533 | 0.1497 | S = project(P, D) ; sum_A = sum( A(v, w) for v in S for w in S ) ; return sum_A / 2 ; aggregate: total / 3 |
| triangle |  | - | 0.4533 | 0.1497 | S = project(P, D) ; sum_A = sum( A(y, z) for y in S for z in S ) ; return sum_A ; aggregate: total / 6 |
| triangle |  | - | 0.4533 | 0.1497 | S = project(P, D) ; sum_ordered = sum( sum( A(v, w) for w in S ) for v in S ) ; sum_unordered = sum_ordered / 2 ; return sum_unordered ; aggregate: total / 3 |
| triangle |  | - | 0.4533 | 0.1497 | S = project(P, D) ; sum_pairs = sum( A(v, w) for v in S for w in S ) ; count = sum_pairs / 2 ; return count ; aggregate: total / 3 |
| triangle |  | - | 0.4533 | 0.1497 | S = project(P, D) ; sum_pairs = sum(A(v, w) for v in S for w in S) ; return sum_pairs ; aggregate: total / 6 |
| triangle |  | - | 0.4533 | 0.1497 | name = project(P, D) ; sum_A = sum( A(v, w) for v in name for w in name ) ; return sum_A / 2 ; aggregate: total / 3 |
| triangle |  | - | 0.4533 | 0.1497 | name = sum( A(v, w) for v in project(P, D) for w in project(P, D) ) ; return name / 2 ; aggregate: total / 3 |
| triangle |  | - | 0.4533 | 0.1497 | name = sum( A(v, w) for v in project(P, D) for w in project(P, D) ) ; return name ; aggregate: total / 6 |
| triangle |  | - | 0.4533 | 0.1497 | name = sum( A(y, z) for y in project(P, D) for z in project(P, D) ) ; return name ; aggregate: total / 6 |
| triangle |  | - | 0.4533 | 0.1497 | name = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) / 2 ; return name ; aggregate: total / 3 |
| triangle |  | - | 0.4533 | 0.1497 | name = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return name ; aggregate: total / 6 |
| triangle |  | - | 0.4533 | 0.1497 | name = sum(A(v, w) for v in project(P, D) for w in project(P, D)) / 2 ; return name ; aggregate: total / 3 |
| triangle |  | - | 0.4533 | 0.1497 | neighbors = project(P, D) ; sum_pairs = sum( A(v, w) for v in neighbors for w in neighbors ) ; return sum_pairs ; aggregate: total / 6 |
| triangle |  | - | 0.4533 | 0.1497 | proj = project(P, D) ; sum_A = sum(A(j, k) for j in proj for k in proj) ; edges = sum_A / 2 ; return edges ; aggregate: total / 3 |
| triangle |  | - | 0.4533 | 0.1497 | projected = project(P, D) ; sum_A = sum( A(v, w) for v in projected for w in projected ) ; edges = sum_A / 2 ; return edges ; aggregate: total / 3 |
| triangle |  | - | 0.4533 | 0.1497 | projected = project(P, D) ; sum_edges = sum( sum( A(i, k) for k in projected ) for i in projected ) / 2 ; return sum_edges ; aggregate: total / 3 |
| triangle |  | - | 0.4533 | 0.1497 | projected_neighbors = project(P, D) ; sum_pairs = sum(A(v, w) for v in projected_neighbors for w in projected_neighbors) ; return sum_pairs / 2 ; aggregate: total / 3 |
| triangle |  | - | 0.4533 | 0.1497 | return sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) / 2 ; aggregate: total / 3 |
| triangle |  | - | 0.4533 | 0.1497 | sum_pairs = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return sum_pairs / 2 ; aggregate: total / 3 |
| triangle |  | - | 0.4533 | 0.1497 | sum_pairs = sum( sum( A(v, w) for w in project(P, D) ) for v in project(P, D) ) ; return sum_pairs ; aggregate: total / 6 |
| triangle |  | - | 0.4633 | 0.1519 | S = project(P, D) ; sum_A = sum(A(v, w) for v in S for w in S) ; sum_diag = sum(A(v, v) for v in S) ; return (sum_A - sum_diag) / 2 ; aggregate: total / 3 |
| triangle |  | - | 0.9050 | 1.5371 | S = project(P, D) ; sum_size = sum( size(N(v) & S) for v in S ) ; return sum_size / 2 ; aggregate: total / 3 |
| triangle |  | - | 0.9050 | 1.5371 | name = project(P, D) ; count = sum( size(N(v) & name) for v in name ) ; return count / 2 ; aggregate: total / 3 |
| degree-moment2 | 19 | 1 | - | - | - |
| degree-moment2 |  | - | 0.0158 | 0.0083 | degree = size(project(P, D)) ; return degree * degree ; aggregate: total |
| degree-moment2 |  | - | 0.0158 | 0.0083 | name = size(project(P, D)) ; return name * name ; aggregate: total |
| degree-moment2 |  | - | 0.0158 | 0.0083 | projected = project(P, D) ; degree = size(projected) ; return degree * degree ; aggregate: total |
| degree-moment2 |  | - | 0.0158 | 0.0083 | projected_P = project(P, D) ; size_projected = size(projected_P) ; report = size_projected * size_projected ; return report ; aggregate: total |
| degree-moment2 |  | - | 0.0158 | 0.0083 | projected_P = project(P, D) ; size_projected = size(projected_P) ; squared = size_projected * size_projected ; return squared ; aggregate: total |
| degree-moment2 |  | - | 0.0158 | 0.0083 | projected_neighbors = project(P, D) ; degree_estimate = size(projected_neighbors) ; return degree_estimate * degree_estimate ; aggregate: total |
| degree-moment2 |  | - | 0.0158 | 0.0083 | return pow(size(project(P, D)), 2) ; aggregate: total |
| degree-moment2 |  | - | 0.0158 | 0.0083 | s = size(project(P, D)) ; return s * s ; aggregate: total |
| degree-moment2 |  | - | 0.0894 | 0.0598 | degree = sum(A(self, j) for j in project(P, D)) ; return degree * degree ; aggregate: total |
| degree-moment2 |  | - | 0.0894 | 0.0598 | degree = sum(A(self, y) for y in project(P, D)) ; return degree * degree ; aggregate: total |
| degree-moment2 |  | - | 0.0894 | 0.0598 | degree_est = sum(A(self, j) for j in project(P, D)) ; return degree_est * degree_est ; aggregate: total |
| degree-moment2 |  | - | 0.0894 | 0.0598 | name = sum(A(self, j) for j in project(P, D)) ; return name * name ; aggregate: total |
| degree-moment2 |  | - | 0.0894 | 0.0598 | name = sum(A(self, y) for y in project(P, D)) ; return name * name ; aggregate: total |
| degree-moment2 |  | - | 0.0894 | 0.0598 | projected = project(P, D) ; degree = sum(A(self, j) for j in projected) ; return degree * degree ; aggregate: total |
| degree-moment2 |  | - | 0.0894 | 0.0598 | projected_neighbors = project(P, D) ; degree_estimate = sum( A(self, y) for y in projected_neighbors ) ; squared_degree = degree_estimate * degree_estimate ; return squared_degree ; aggregate: total |
| degree-moment2 |  | - | 0.0894 | 0.0598 | s = sum(A(self, j) for j in project(P, D)) ; return s * s ; aggregate: total |
| degree-moment2 |  | - | 0.0894 | 0.0598 | s = sum(A(self, y) for y in project(P, D)) ; return s * s ; aggregate: total |
| degree-moment2 |  | - | 0.0894 | 0.0598 | sum_A = sum(A(self, j) for j in project(P, D)) ; return sum_A * sum_A ; aggregate: total |
| degree-moment2 |  | - | 0.0894 | 0.0598 | sum_A = sum(A(self, y) for y in project(P, D)) ; return sum_A * sum_A ; aggregate: total |

Own-row rejection text: the program reads this node's own entries of the release (N(self), A(self, ...) or A(..., self)). In this architecture they are only randomized copies of this node's own edges, which it knows exactly as P: they add noise and no information. Use P (bounded: project(P, D)) for this node's own neighbors and read the release only for edges between other nodes
