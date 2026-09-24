"""Chart data for Chapter 3 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from buyside import gross_nav, run_fees, tracking_error, years_to_significance

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/03-the-buy-side"
OUT.mkdir(parents=True, exist_ok=True)

# 1. the weekend problem's fund: gross NAV, net NAV, high-water mark
PATH = [0.20, -0.15, 0.10, 0.25, -0.05, 0.08, 0.30, -0.20, 0.15, 0.12]
r, g = run_fees(PATH), gross_nav(PATH)
with open(OUT / "hwm_path.csv", "w") as f:
    f.write("year,gross,net,hwm\n")
    f.writelines(f"{i},{g[i]:.4f},{r.nav[i]:.4f},{r.high_water[i]:.4f}\n" for i in range(len(g)))

# 2. years of track record needed against information ratio
with open(OUT / "years_needed.csv", "w") as f:
    f.write("ir,years\n")
    f.writelines(f"{ir:.2f},{years_to_significance(ir):.2f}\n" for ir in np.arange(0.2, 3.01, 0.05))

# 3. convexity of the performance fee: mean total fee against volatility, zero gross alpha
rng = np.random.default_rng(3)
with open(OUT / "fee_vs_vol.csv", "w") as f:
    f.write("vol_pct,fee_pct_per_year\n")
    for vol in range(0, 31, 2):
        draws = rng.normal(0.0, vol / 100, size=(4000, 10))
        fees = [sum(x.mgmt_fees) + sum(x.perf_fees) for x in (run_fees(list(row)) for row in draws)]
        f.write(f"{vol},{np.mean(fees) / 10 * 100:.3f}\n")

# 4. tutorial table: three funds on ten years of simulated monthly returns
rng = np.random.default_rng(33)
bench = rng.normal(0.07 / 12, 0.16 / np.sqrt(12), 120)
index_fund = bench - 0.0005 / 12 + rng.normal(0, 0.001 / np.sqrt(12), 120)
active = bench + 0.01 / 12 - 0.0075 / 12 + rng.normal(0, 0.04 / np.sqrt(12), 120)
with open(OUT / "three_funds.csv", "w") as f:
    f.write("fund,te_pct,active_return_pct\n")
    for name, x in (("index", index_fund), ("active", active)):
        f.write(f"{name},{tracking_error(x, bench) * 100:.2f},{(x - bench).mean() * 12 * 100:.2f}\n")
