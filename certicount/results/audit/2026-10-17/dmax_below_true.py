"""How often the noisy max degree D falls below the true max degree (k-star: eps2=0.4, floor;
triangle: eps2=0.2, ceil), and how many nodes get clipped. Run from the repo root."""
import glob, json, re
import numpy as np

rng = np.random.default_rng(0)
DATA = __import__("pathlib").Path(__file__).resolve().parents[4] / "psc-reproduction" / "data"  # moved 2026-10-24
for path in sorted(glob.glob(str(DATA / "*.json"))):
    data = json.load(open(path))
    rec = data[0] if isinstance(data, list) else data
    n = rec["vertex_num"]
    deg = np.zeros(n, int)
    for u, v in re.findall(r"\((\d+),\s*(\d+)\)", rec["edges"]):
        deg[int(u)] += 1; deg[int(v)] += 1
    row = []
    for eps2, rounding in ((0.4, "floor"), (0.2, "ceil")):
        mx = (deg + rng.laplace(0, 1 / eps2, (20000, n))).max(1)
        D = np.floor(mx) if rounding == "floor" else np.maximum(1, np.ceil(mx))
        row.append(f"eps2={eps2}: P(D<maxdeg)={(D < deg.max()).mean():.1%}, "
                   f"clipped nodes={(deg[None] > D[:, None]).sum(1).mean():.2f}, mean D={D.mean():.1f}")
    print(path.split("/")[-1], f"n={n} maxdeg={deg.max()} |", " ; ".join(row))
