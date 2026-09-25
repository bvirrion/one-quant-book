"""Chart data for Book 7, chapter 13 (deterministic)."""
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_decay import BROKEN, DATA, HORIZONS, MONTH, YEAR, decay_table, monthly_ic, posterior_curve  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

d = decay_table()
with open(OUT / "decay.csv", "w") as f:
    f.write("h,reversal,momentum,surprise,bp\n")
    for h in HORIZONS:
        f.write(f"{h},{d['reversal']['ic'][h]:.5f},{d['momentum']['ic'][h]:.5f},{d['surprise']['ic'][h]:.5f},"
                f"{d['book-to-price']['ic'][h]:.5f}\n")

intact, broken = monthly_ic("surprise"), monthly_ic("surprise", cfg=BROKEN)
roll = lambda x: pd.Series(x).rolling(12).mean().to_numpy()  # noqa: E731
with open(OUT / "rolling_ic.csv", "w") as f:
    f.write("year,intact,broken\n")
    for k, (a, b) in enumerate(zip(roll(intact), roll(broken), strict=True)):
        if not np.isnan(a):
            f.write(f"{(2 * YEAR + k * MONTH) / YEAR:.3f},{a:.5f},{b:.5f}\n")

r = pd.read_csv(DATA / "ff_decay_rolling.csv").pivot(index="year", columns="factor", values="mean")
with open(OUT / "factors.csv", "w") as f:
    f.write("year,SMB,HML,Mom\n")
    for y, row in r.iterrows():
        f.write(f"{y},{100 * row.SMB:.4f},{100 * row.HML:.4f},{100 * row.Mom:.4f}\n")

with open(OUT / "posterior.csv", "w") as f:
    f.write("t,posterior\n")
    for t, p in posterior_curve().items():
        f.write(f"{t},{p:.4f}\n")
