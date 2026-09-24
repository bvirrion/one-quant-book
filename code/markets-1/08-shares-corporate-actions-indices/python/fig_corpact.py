"""Chart data for Chapter 8 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from corpact import CapIndex, back_adjust, dividend_factor, split_factor, weights_cap, weights_price

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/08-shares-corporate-actions-indices"
OUT.mkdir(parents=True, exist_ok=True)

# 1. a simulated stock with two dividends and a 10-for-1 split
rng = np.random.default_rng(8)
n, split_day, div_days = 250, 150, (60, 200)
true = 400 * np.exp(np.cumsum(rng.normal(0.0012, 0.018, n)))        # total-return path
raw = true.copy()
events: dict[int, float] = {}
for d in div_days:
    dividend = 0.004 * raw[d - 1]
    events[d] = dividend_factor(raw[d - 1], dividend)
    raw[d:] *= events[d]
raw[split_day:] *= split_factor(10)
events[split_day] = split_factor(10)
adj = back_adjust(raw, events)
with open(OUT / "split.csv", "w") as f:
    f.write("day,raw,adjusted\n")
    f.writelines(f"{i},{raw[i]:.3f},{adj[i]:.3f}\n" for i in range(n))
assert np.allclose(adj[1:] / adj[:-1], true[1:] / true[:-1])

# 2. one universe, three weightings
prices = {"A": 480.0, "B": 35.0, "C": 120.0, "D": 900.0, "E": 60.0}
shares = {"A": 2.0e9, "B": 9.0e9, "C": 1.5e9, "D": 0.1e9, "E": 4.0e9}
floats = {"A": 1.0, "B": 0.6, "C": 0.9, "D": 1.0, "E": 0.8}
wc, wp = weights_cap(prices, shares, floats), weights_price(prices)
with open(OUT / "weights.csv", "w") as f:
    f.write("k,stock,cap,price,equal\n")
    f.writelines(f"{i},{s},{wc[s] * 100:.2f},{wp[s] * 100:.2f},20.00\n" for i, s in enumerate(prices))

# 3. a constituent change with and without divisor adjustment
idx = CapIndex(dict(shares), dict(floats), divisor=1.0)
idx.divisor = idx.market_value(prices) / 1000.0
path_p = {s: prices[s] * np.exp(np.cumsum(rng.normal(0, 0.01, 60))) for s in prices}
new_price = 250 * np.exp(np.cumsum(rng.normal(0, 0.01, 60)))
naive_div = idx.divisor
with open(OUT / "rebase.csv", "w") as f:
    f.write("day,maintained,naive\n")
    for t in range(60):
        px = {s: path_p[s][t] for s in prices}
        if t == 30:
            px_all = dict(px, F=new_price[t])

            def swap(ix):
                for d in (ix.shares, ix.floats):
                    d.pop("B")
                ix.shares["F"], ix.floats["F"] = 3.0e9, 1.0
            idx.rebase(px_all, swap)
        if t >= 30:
            px = {s: path_p[s][t] for s in prices if s != "B"} | {"F": new_price[t]}
        mv = idx.market_value(px)
        f.write(f"{t},{mv / idx.divisor:.2f},{mv / naive_div:.2f}\n")
