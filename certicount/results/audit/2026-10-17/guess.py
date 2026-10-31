"""Attacker's best guessing accuracy for 'edge present or not' (50/50 prior)."""
import numpy as np
rng = np.random.default_rng(0)
def lap_acc(delta, b):            # same scale: optimal test accuracy
    return 1 - 0.5 * np.exp(-delta / (2 * b))
def tv_acc(c0, b0, c1, b1):       # different scales: 0.5 + 0.5*TV, numeric
    z = np.linspace(-400, 400, 2_000_001); dz = z[1] - z[0]
    p = np.exp(-abs(z - c0) / b0) / (2 * b0); q = np.exp(-abs(z - c1) / b1) / (2 * b1)
    return 0.5 + 0.25 * np.abs(p - q).sum() * dz
pct = lambda x: f"{100*x:.1f}%"
print("① 3-star deg8→9: correct", pct(lap_acc(28, 136/1.6)), " broken", pct(lap_acc(28, 18/1.6)))
print("① 3-star deg17→18: correct", pct(lap_acc(136, 136/1.6)), " broken", pct(lap_acc(136, 18/1.6)))
print("② own degree: correct", pct(lap_acc(2, 15/0.8)), " broken", pct(tv_acc(1, 1.25, 3, 2.5)))
# ③ 49 reports, scale 8.75 vs 10, attacker knows true local counts (DP worst case)
N = 200_000
def sim(b): return rng.laplace(0, b, (N, 49))
llr = lambda x: (np.abs(x).sum(1) * (1/8.75 - 1/10) - 49*np.log(10/8.75))
a, bb = llr(sim(8.75)), llr(sim(10))
print("③ true max degree, 49 reports: broken", pct(0.5*((a < 0).mean() + (bb > 0).mean())))
print("④ rounding: correct", pct(lap_acc(15, 15/0.8)), " broken", pct(lap_acc(15, 14/0.8)))
print("⑤ no clip deg30→31: clipped", "50.0%", " unclipped", pct(lap_acc(435, 136/1.6)))
print("⑥ asym: correct-bound", pct(lap_acc(15, 15/0.8)), " asym worst", pct(lap_acc(15.5, 15/0.8)))
print("CU triangle noise Lap(18.75): median |noise| =", round(18.75*np.log(2), 2))
