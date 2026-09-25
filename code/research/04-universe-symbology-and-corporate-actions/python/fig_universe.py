"""Chart data for Book 7, chapter 4 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_universe import MONTHS, market, split_factor_today, ticker_file, universe

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

m = market()
plain, buf = universe(m, 500), universe(m, 500, 600)
with open(OUT / "churn.csv", "w") as f:
    f.write("month,plain,buffer\n")
    for t in range(1, MONTHS):
        f.write(f"{t},{len(plain[t] - plain[t - 1])},{len(buf[t] - buf[t - 1])}\n")


def splice_example():
    """Among reused tickers whose two holders both have at least a year in the file, the one with the
    shortest gap between the old holder's last month and the new holder's first (ties: sort order)."""
    tf = ticker_file(m)
    best = None
    for k in sorted(tf):
        rows = tf[k]
        holders = [p for _, p, _ in rows]
        if len(set(holders)) == 2 and min(holders.count(h) for h in set(holders)) >= 12:
            last_old = max(t for t, p, _ in rows if p == rows[0][1])
            first_new = min(t for t, p, _ in rows if p != rows[0][1])
            if best is None or first_new - last_old < best[0]:
                best = (first_new - last_old, k, rows)
    return best[1], best[2]


tick, rows = splice_example()
first = rows[0][1]
with open(OUT / "splice.csv", "w") as f:
    f.write("month,old,new\n")
    for t, p, c in rows:
        f.write(f"{t},{f'{c:.3f}' if p == first else 'nan'},{f'{c:.3f}' if p != first else 'nan'}\n")

adj = m["close"] / split_factor_today(m)
wrong = (m["close"] >= 5.0) & (adj < 5.0)
pid = int(np.flatnonzero(wrong.any(axis=0))[0])
with open(OUT / "adjfloor.csv", "w") as f:
    f.write("month,traded,adjusted\n")
    for t in range(MONTHS):
        if not np.isnan(m["close"][t, pid]):
            f.write(f"{t},{m['close'][t, pid]:.3f},{adj[t, pid]:.3f}\n")
print("splice ticker", tick, "holders", sorted({p for _, p, _ in rows}), "floor example pid", pid,
      "splits", [(t, r) for t, p, r in m["splits"] if p == pid])
