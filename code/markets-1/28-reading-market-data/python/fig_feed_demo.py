"""Chart data for Chapter 28 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from feed_demo import TRADES, clean, inversions, receive_times, replay, vwap

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/28-reading-market-data"
OUT.mkdir(parents=True, exist_ok=True)

book, l1 = replay()
t0 = l1[0][0]
with open(OUT / "l1.csv", "w") as f:
    f.write("seconds,bid,ask\n")
    for ts, bb, _, ba, _ in l1[60:700:4]:
        if bb is not None and ba is not None:
            f.write(f"{(ts - t0) / 1e9:.4f},{bb / 1e4:.2f},{ba / 1e4:.2f}\n")
with open(OUT / "tape.csv", "w") as f:
    f.write("seconds,price\n")
    last = l1[699][0]
    f.writelines(f"{(t.ts - t0) / 1e9:.4f},{t.price / 1e4:.2f}\n" for t in book.trades
                 if l1[60][0] <= t.ts <= last and t.price)

ex = np.array([x[0] for x in l1], dtype=float)
with open(OUT / "reorder.csv", "w") as f:
    f.write("jitter_us,inversions_pct\n")
    for j in (0, 50, 100, 250, 500, 1000, 2500, 5000):
        rx = receive_times(ex, 200_000.0, j * 1000.0, 28) if j else ex + 200_000.0
        f.write(f"{j},{inversions(ex, rx) / (len(ex) - 1) * 100:.2f}\n")

kept, dropped = clean(TRADES)
with open(OUT / "badtick.csv", "w") as f:
    f.write("seq,price,kept\n")
    f.writelines(f"{r[0]},{r[2]:.2f},{1 if r in kept else 0}\n" for r in TRADES)
print(len(dropped), round(vwap(TRADES), 4), round(vwap(kept), 4))
