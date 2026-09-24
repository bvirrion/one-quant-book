"""Chart data for Book 4, chapter 29: figdata/methods/29-games-auctions-and-information/."""
import pathlib

import numpy as np
from qm_games import best_response_curve, kelly_growth, pab_bid, reserve_curve, simulate_races

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "methods" / "29-games-auctions-and-information"
OUT.mkdir(parents=True, exist_ok=True)

br = best_response_curve()
with open(OUT / "bestresponse.csv", "w") as f:
    f.write("bid,payoff\n")
    for b, p in zip(br["b"], br["payoff"], strict=True):
        f.write(f"{b:.3f},{p:.5f}\n")

rc = reserve_curve()
with open(OUT / "reserve.csv", "w") as f:
    f.write("r,n2,n5\n")
    for i, r in enumerate(rc["r"]):
        f.write(f"{r:.3f},{rc[2][i]:.5f},{rc[5][i]:.5f}\n")

with open(OUT / "kelly.csv", "w") as f:
    f.write("q,mi,sim,simse\n")
    for q in np.round(np.linspace(0.25, 1.0, 16), 3):
        s = simulate_races(float(q))
        f.write(f"{q:.3f},{kelly_growth(float(q))['mi']:.5f},{s['gain']:.5f},{s['gain_se']:.5f}\n")

# revenue distributions of the two multi-unit formats (n = 5 dealers, k = 2 units), 100 bins on [0, 2]
rng = np.random.default_rng(1998)
V = rng.uniform(size=(400_000, 5))
uni = 2 * np.sort(V, axis=1)[:, 2]
grid = np.linspace(0.0, 1.0, 2001)
bids = np.interp(V, grid, pab_bid(grid, 5, 2))
pab = np.sort(bids, axis=1)[:, 3:].sum(axis=1)
edges = np.linspace(0.0, 2.0, 81)
hu, _ = np.histogram(uni, edges, density=True)
hp, _ = np.histogram(pab, edges, density=True)
with open(OUT / "multiunit.csv", "w") as f:
    f.write("revenue,uniform,payasbid\n")
    for i in range(len(hu)):
        f.write(f"{0.5 * (edges[i] + edges[i + 1]):.4f},{hu[i]:.4f},{hp[i]:.4f}\n")
