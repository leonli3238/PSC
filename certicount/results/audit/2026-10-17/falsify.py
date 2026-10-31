"""Exhaustive sensitivity falsifier for PSC local-count functions (node 0, all G', all P, all flips)."""
import itertools, math, random, sys

def graphs(n, D, symmetric=True):
    pairs = list(itertools.combinations(range(n), 2))
    for mask in range(1 << len(pairs)):
        adj = [set() for _ in range(n)]
        for b, (u, v) in enumerate(pairs):
            if mask >> b & 1:
                adj[u].add(v); adj[v].add(u)
        if all(len(a) <= D for a in adj):
            yield adj

def tri(P, adj):  # c_0 = 1/2 * sum_{j in P ∩ N'(0)} |P ∩ N'(j)|
    return 0.5 * sum(len(P & adj[j]) for j in P & adj[0])

def max_delta(n, D, f, gen):
    best, arg = 0.0, None
    others = range(1, n)
    for adj in gen:
        for r in range(n):
            for P in itertools.combinations(others, r):
                P = set(P); y = f(P, adj)
                for v in others:
                    d = abs(f(P ^ {v}, adj) - y)
                    if d > best: best, arg = d, (P, v, [sorted(a) for a in adj])
    return best, arg

def asym(n, D, samples=20000, seed=0):
    # each node j keeps an arbitrary subset of size <= D of others: relation need not be symmetric
    rnd = random.Random(seed)
    for _ in range(samples):
        adj = [set(rnd.sample([u for u in range(n) if u != j], rnd.randint(0, D))) for j in range(n)]
        yield adj

if __name__ == "__main__":
    n = 6
    for D in (2, 3, 4):
        m, _ = max_delta(n, D, tri, graphs(n, D))
        print(f"triangle, symmetric G' maxdeg<= {D}: max Δ = {m}  (claimed GS d̂max-1 = {D-1}, paper d̂max = {D})")
    for D in (2, 3, 4):
        m, _ = max_delta(n, D, tri, asym(n, D))
        print(f"triangle, ASYMMETRIC projection D={D} (random search): max Δ = {m}  (d̂max-1 = {D-1})")
    m, _ = max_delta(n, n - 1, tri, graphs(n, n - 1))
    print(f"triangle, no projection: max Δ = {m}  (n-2 = {n-2})")
    # k-star: claimed GS C(D-1,k-1) is valid only if the REAL list is clipped to D
    for k, D in ((2, 3), (3, 3)):
        clipped = lambda P, adj, k=k, D=D: math.comb(min(len(P), D), k)
        raw = lambda P, adj, k=k: math.comb(len(P), k)
        one = [[set() for _ in range(n)]]
        print(f"{k}-star D={D}: clipped max Δ = {max_delta(n, D, clipped, one)[0]}, "
              f"unclipped max Δ = {max_delta(n, D, raw, one)[0]}, claimed GS C(D-1,k-1) = {math.comb(D-1, k-1)}")
