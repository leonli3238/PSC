import math
def tri(P, Np, i):  # c_i = 1/2 * sum_{j in P ∩ N'(i)} |P ∩ N'(j)|
    return 0.5 * sum(len(P & Np.get(j, set())) for j in P & Np[i])

# Example A: symmetric G', max degree 16, worst case Δ = 15
i, v, U = 'i', 'v', [f'u{k}' for k in range(15)]
Np = {i: set(U) | {v}, v: set(U) | {i}}
for u in U: Np[u] = {i, v}
assert all(len(s) <= 16 for s in Np.values())
P = set(U)
print('A symmetric  Δ =', tri(P | {v}, Np, i) - tri(P, Np, i))

# Example B: asymmetric rows (v's row omits i), max row length 16, Δ = 15.5
U2 = [f'w{k}' for k in range(16)]
Np = {i: set(U) | {v}, v: set(U) | {'w0'}}
for u in U: Np[u] = {i, v}
assert all(len(s) <= 16 for s in Np.values())
P = set(U) | {'w0'}
print('B asymmetric Δ =', tri(P | {v}, Np, i) - tri(P, Np, i))

# Example C: GS read as own degree-1, triangle, eps3=0.8
a, b = 'a', 'b'
Np = {i: {a, b, v}, a: {i, b, v}, b: {i, a, v}, v: {i, a, b}}
c, c2 = tri({a, b}, Np, i), tri({a, b, v}, Np, i)
s, s2 = (2 - 1) / 0.8, (3 - 1) / 0.8
print('C counts', c, c2, 'scales', s, s2)
for t in (20, 50):
    p, p2 = 0.5 * math.exp(-(t - c) / s), 0.5 * math.exp(-(t - c2) / s2)
    print(f'  P(report>{t}): x={p:.2e} x\'={p2:.2e} ln ratio={math.log(p2/p):.1f}')
# Example D: true max degree 8 -> 9 changes everyone's scale
for t in (50, 100):
    p, p2 = math.exp(-t / (7 / 0.8)), math.exp(-t / (8 / 0.8))
    print(f'D P(|noise|>{t}) per node: {p:.2e} vs {p2:.2e}, ln ratio {math.log(p2/p):.2f}, x49 nodes {49*math.log(p2/p):.1f}')
print('3-star CU deg 8->9 Δ', math.comb(9,3)-math.comb(8,3), 'worst within D=18', math.comb(18,3)-math.comb(17,3))
print('unclipped deg 30->31 Δ', math.comb(31,3)-math.comb(30,3), 'n=49 worst', math.comb(48,3)-math.comb(47,3))
print('PM hub', math.comb(238,3)-math.comb(237,3), 'GS D=236', math.comb(235,2), 'D=233', math.comb(232,2))
print('Laplace P(noisy deg<=18 | deg 30, eps2=0.4)', 0.5*math.exp(-12*0.4))
