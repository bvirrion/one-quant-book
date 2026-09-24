"""Chart data for Chapter 14 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from etf_demo import ArbCosts, leveraged_path, rebalance_trade, simulate_premium, stale_nav

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/14-exchange-traded-funds"
OUT.mkdir(parents=True, exist_ok=True)

costs = ArbCosts(4.0, 1.5, 1.0, 0.5)
prem, _ = simulate_premium(costs, 300, 14)
with open(OUT / "premium.csv", "w") as f:
    f.write("t,premium_bp\n")
    f.writelines(f"{i},{p:.2f}\n" for i, p in enumerate(prem))

rng = np.random.default_rng(141)
ret = rng.normal(0.0, 0.004, 60)
ret[20:30] += -0.012                                   # a ten-day sell-off
ret[30:40] += 0.006
true = 100 * np.cumprod(1 + ret)
nav = stale_nav(true, 0.75)
with open(OUT / "stale.csv", "w") as f:
    f.write("day,true,nav,premium_pct\n")
    f.writelines(f"{i},{true[i]:.3f},{nav[i]:.3f},{(true[i] / nav[i] - 1) * 100:.3f}\n" for i in range(60))

rng = np.random.default_rng(142)
r = rng.normal(0.0, 0.02, 252)
r -= r.mean()                 # daily returns sum to zero: the index is 'flat' in arithmetic terms
idx = np.cumprod(1 + r)
with open(OUT / "leveraged.csv", "w") as f:
    f.write("day,index,three_x,naive_three_x,inverse\n")
    l3, inv = leveraged_path(r, 3.0), leveraged_path(r, -1.0)
    for i in range(252):
        f.write(f"{i + 1},{idx[i]:.4f},{l3[i]:.4f},{1 + 3 * (idx[i] - 1):.4f},{inv[i]:.4f}\n")

with open(OUT / "rebalance.csv", "w") as f:
    f.write("beta,trade_pct_nav\n")
    f.writelines(f"{b},{rebalance_trade(b, 100.0, 0.01):.1f}\n" for b in (-3, -2, -1, 1, 2, 3))
