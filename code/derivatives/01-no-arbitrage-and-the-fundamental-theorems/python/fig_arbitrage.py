"""Chart data for Book 5, Chapter 1 (deterministic)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_arbitrage import FWD, K1, K2, PRICES, RATE, TRINOMIAL, YEARS, _vol, black, call_payoff, price_bounds

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

S = TRINOMIAL[:, 1]
with open(OUT / "bounds.csv", "w") as f:
    f.write("strike,lower,upper,complete\n")
    q = np.array([0.3, 0.48, 0.2])          # state prices once the 100 call trades at 6.00
    for k in range(80, 121, 2):
        lo, hi = price_bounds(TRINOMIAL, PRICES, call_payoff(S, k))
        f.write(f"{k},{lo:.4f},{hi:.4f},{q @ call_payoff(S, k):.4f}\n")

with open(OUT / "box_payoff.csv", "w") as f:
    f.write("s,longcall,shortcall,shortput,longput,total\n")
    for s in range(4000, 7001, 50):
        lc, sc = max(s - K1, 0.0), -max(s - K2, 0.0)
        sp, lp = -max(K1 - s, 0.0), max(K2 - s, 0.0)
        f.write(f"{s},{lc:.1f},{sc:.1f},{sp:.1f},{lp:.1f},{lc + sc + sp + lp:.1f}\n")

df = math.exp(-RATE * YEARS)
with open(OUT / "call_region.csv", "w") as f:
    f.write("strike,lower,upper,call\n")
    for k in range(3000, 8001, 100):
        f.write(f"{k},{df * max(FWD - k, 0.0):.2f},{df * FWD:.2f},{black(FWD, k, YEARS, RATE, _vol(k), 'C'):.2f}\n")
