"""Chart data for Chapter 2 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from blockbid import Block, breakeven_discount, impact_cost, simulate_unwind

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/02-the-sell-side"
OUT.mkdir(parents=True, exist_ok=True)

# 1. break-even discount against block size, three volatilities
with open(OUT / "discount_vs_size.csv", "w") as f:
    f.write("pct_adv,vol1,vol2,vol3,impact2\n")
    for pct in range(1, 51):
        row = [breakeven_discount(Block(pct / 100 * 1e7, 1e7, s)) * 100 for s in (0.01, 0.02, 0.03)]
        imp = impact_cost(Block(pct / 100 * 1e7, 1e7, 0.02)) * 100
        f.write(f"{pct},{row[0]:.4f},{row[1]:.4f},{row[2]:.4f},{imp:.4f}\n")

# 2. distribution of the unwind P&L at the 95 % break-even discount
b = Block(2e6, 1e7, 0.02)
pnl = simulate_unwind(b, breakeven_discount(b), 20_000, seed=2) * 100
hist, edges = np.histogram(pnl, bins=np.arange(-4, 9.01, 0.5))
with open(OUT / "pnl_hist.csv", "w") as f:
    f.write("centre,count\n")
    f.writelines(f"{lo + 0.25:.2f},{c}\n" for lo, c in zip(edges[:-1], hist, strict=True))
with open(OUT / "pnl_stats.csv", "w") as f:
    f.write("mean_pct,std_pct,share_losing\n")
    f.write(f"{pnl.mean():.3f},{pnl.std(ddof=1):.3f},{(pnl < 0).mean():.4f}\n")

# 3. Goldman Sachs 2025 Global Banking & Markets net revenues, USD billion
#    (source: 8-K earnings release of January 2026; ledger row F1)
rows = [("FICC intermediation", 10.271), ("FICC financing", 4.251),
        ("Equities intermediation", 9.340), ("Equities financing", 7.195),
        ("Advisory", 4.726), ("Equity underwriting", 1.784), ("Debt underwriting", 2.829)]
with open(OUT / "gs_gbm_2025.csv", "w") as f:
    f.write("k,label,usd_bn\n")
    f.writelines(f"{i},{lab},{v:.3f}\n" for i, (lab, v) in enumerate(rows))
