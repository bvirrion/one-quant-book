"""Chart data for Chapter 16 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from short_cost import carry_short, fee_from_utilisation, squeeze_return

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/16-stock-loan-and-short-selling"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "fee.csv", "w") as f:
    f.write("utilisation_pct,fee_pct\n")
    f.writelines(f"{u},{fee_from_utilisation(u / 100) * 100:.3f}\n" for u in range(0, 101))

rng = np.random.default_rng(16)
n = 250
ret = rng.normal(-0.30 / n, 0.025, n)
ret[0] = 0.0                                          # the short is opened at exactly 40
prices = 40.0 * np.cumprod(1 + ret)
util = np.clip(np.linspace(0.60, 0.99, n) + rng.normal(0, 0.01, n), 0, 1)
fees = np.array([fee_from_utilisation(u) for u in util])
pnl, cost = carry_short(prices, fees, 100_000)
with open(OUT / "carry.csv", "w") as f:
    f.write("day,price,fee_pct,price_pnl_k,cost_k,net_k\n")
    for i in range(n):
        f.write(f"{i + 1},{prices[i]:.2f},{fees[i] * 100:.2f},{pnl[i] / 1e3:.1f},{cost[i] / 1e3:.1f},"
                f"{(pnl[i] - cost[i]) / 1e3:.1f}\n")

with open(OUT / "squeeze.csv", "w") as f:
    f.write("shock_pct,k20,k40,k60\n")
    for s in np.arange(0.0, 0.401, 0.005):
        xs = [squeeze_return(float(s), k, 0.10, 0.60) * 100 for k in (0.2, 0.4, 0.6)]
        f.write(f"{s * 100:.1f},{xs[0]:.2f},{xs[1]:.2f},{xs[2]:.2f}\n")
