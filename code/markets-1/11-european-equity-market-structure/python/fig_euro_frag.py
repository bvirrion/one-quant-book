"""Chart data for Chapter 11 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from euro_frag import ON_EXCHANGE_JULY_2026, effective_venues, simulate_cap

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/11-european-equity-market-structure"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "mechanisms.csv", "w") as f:
    f.write("k,label,pct\n")
    f.writelines(f"{i},{k},{v}\n" for i, (k, v) in enumerate(ON_EXCHANGE_JULY_2026.items()))

with open(OUT / "effective.csv", "w") as f:
    f.write("leader_pct,effective\n")
    for lead in range(20, 101, 2):
        rest = (100 - lead) / 5.0
        f.write(f"{lead},{effective_venues([lead] + [rest] * 5):.3f}\n")

s = simulate_cap()
with open(OUT / "cap.csv", "w") as f:
    f.write("month,usage_pct,dark_pct,periodic_pct\n")
    for m in range(len(s["total"])):
        u = "nan" if np.isnan(s["usage"][m]) else f"{s['usage'][m] * 100:.3f}"
        f.write(f"{m + 1},{u},{s['dark'][m] / s['total'][m] * 100:.3f},{s['periodic'][m] / s['total'][m] * 100:.3f}\n")
