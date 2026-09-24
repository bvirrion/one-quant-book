"""Chart data for Chapter 21 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from basis_demo import DEC, DIVS, TODAY, basis_path, example_band, mispricing, rolled_index

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/fairvalue"))
from firm_fairvalue import fair_value

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/21-basis-roll-and-delivery"
OUT.mkdir(parents=True, exist_ok=True)

days, basis = basis_path(6000.0, 0.042, TODAY, DEC, DIVS)
with open(OUT / "basis.csv", "w") as f:
    f.write("days_to_expiry,basis\n")
    f.writelines(f"{(DEC - d).days},{b:.3f}\n" for d, b in zip(days, basis, strict=True))

lo, hi = example_band()
fv = fair_value(6000.0, 0.042, TODAY, DEC, DIVS)
x, _ = mispricing(400, lo - fv, hi - fv, 1.6, 0.05, 21)
with open(OUT / "mispricing.csv", "w") as f:
    f.write("t,mispricing,upper,lower\n")
    f.writelines(f"{i},{v:.3f},{hi - fv:.3f},{lo - fv:.3f}\n" for i, v in enumerate(x))

months = np.arange(1, 13)
with open(OUT / "curves.csv", "w") as f:
    f.write("month,contango,backwardation\n")
    f.writelines(f"{m},{70 * (1 + 0.012 * (m - 1)) :.2f},{70 * (1 - 0.010 * (m - 1)):.2f}\n" for m in months)

spot = np.full(25, 70.0)
cont = np.column_stack([spot, spot * 1.012])
back = np.column_stack([spot, spot * 0.990])
with open(OUT / "rolled.csv", "w") as f:
    f.write("month,contango,backwardation\n")
    a, b = rolled_index(cont), rolled_index(back)
    f.writelines(f"{i},{a[i]:.4f},{b[i]:.4f}\n" for i in range(25))
