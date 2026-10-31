"""Degree task (GS=1, eps3=2, Laplace scale 0.5): which kinds of LLM counting error break eps3-DP.
x has 30 real neighbors, x' has 31 (one edge added). Reports empirical eps = max_z |log p(z)/q(z)|
and the attacker's best guessing accuracy 0.5 + 0.5*TV."""
import numpy as np

b, eps3 = 0.5, 2.0
z = np.linspace(-60, 100, 1_600_001); dz = z[1] - z[0]
def density(outcomes):  # outcomes: list of (LLM value, probability)
    return sum(p * np.exp(-np.abs(z - y) / b) / (2 * b) for y, p in outcomes)
def report(name, ox, ox2):
    p, q = density(ox), density(ox2)
    mask = (p > 1e-300) & (q > 1e-300)
    eps = np.max(np.abs(np.log(p[mask] / q[mask])))
    acc = 0.5 + 0.25 * np.abs(p - q).sum() * dz
    print(f"{name:<44} eps_emp={eps:5.2f} (claimed {eps3})  attacker accuracy={acc:.1%}")

report("a. LLM always correct: 30 / 31", [(30, 1)], [(31, 1)])
report("b. always one short: 29 / 30", [(29, 1)], [(30, 1)])
report("c. random ±1 w.p. 10%, same for any list", [(30, .9), (29, .05), (31, .05)], [(31, .9), (30, .05), (32, .05)])
report("d. correct on 30, says 33 on 31", [(30, 1)], [(33, 1)])
report("e. correct on 30, says 29 on 31 (under)", [(30, 1)], [(29, 1)])
report("f. errs (+2) only on the longer list w.p. 20%", [(30, 1)], [(31, .8), (33, .2)])
