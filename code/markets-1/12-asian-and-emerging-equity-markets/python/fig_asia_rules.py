"""Chart data for Chapter 12 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from asia_rules import TAXES, autocorr, locked_days, round_trip_tax_bp, truncate

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/12-asian-and-emerging-equity-markets"
OUT.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(12)
true = rng.standard_t(3, 60_000) * 0.035 / np.sqrt(3)           # heavy-tailed, about 3.5 % a day
obs = truncate(true, 0.10)
edges = np.arange(-0.135, 0.1351, 0.01)          # bins centred on whole percentages: +/-10 % each get one bin
ht, _ = np.histogram(true, bins=edges)
ho, _ = np.histogram(obs, bins=edges)
with open(OUT / "limit_hist.csv", "w") as f:
    f.write("centre_pct,true,observed\n")
    f.writelines(f"{(lo + 0.005) * 100:.1f},{a},{b}\n" for lo, a, b in zip(edges[:-1], ht, ho, strict=True))
with open(OUT / "limit_stats.csv", "w") as f:
    f.write("series,std_pct,autocorr,share_at_limit_pct\n")
    f.write(f"true,{true.std() * 100:.3f},{autocorr(true):.4f},0\n")
    f.write(f"observed,{obs.std() * 100:.3f},{autocorr(obs):.4f},{(np.abs(obs) > 0.0999).mean() * 100:.3f}\n")

with open(OUT / "locked.csv", "w") as f:
    f.write("shock_pct,l5,l10,l20\n")
    for s in range(0, 81, 2):
        f.write(f"{s}," + ",".join(str(locked_days(s / 100, L)) for L in (0.05, 0.10, 0.20)) + "\n")

with open(OUT / "taxes.csv", "w") as f:
    f.write("k,label,bp\n")
    f.writelines(f"{i},{k},{round_trip_tax_bp(*v):.0f}\n" for i, (k, v) in enumerate(TAXES.items()))
