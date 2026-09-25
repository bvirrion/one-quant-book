"""Chart data for Book 8, chapter 21 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_curve import book, wti  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

w = wti()
d = w["dates"]
start = next(i for i, x in enumerate(d) if x.year >= 1986)
end = next(i for i, x in enumerate(d) if x.year >= 2021)
a = np.cumsum(book(None)["net_series"][start:end])
b = np.cumsum(book(-0.2)["net_series"][start:end])
with open(OUT / "cumulative.csv", "w") as f:
    f.write("year,none,filter\n")
    for i in range(0, end - start, 5):
        x = d[start + i]
        f.write(f"{x.year + (x.timetuple().tm_yday - 1) / 365.25:.3f},{100 * a[i]:.2f},{100 * b[i]:.2f}\n")

with open(OUT / "carry2020.csv", "w") as f:
    f.write("n,carry_pct,long\n")
    p = book(None)["pos"]
    n = 0
    for i, x in enumerate(d):
        if x.year == 2020 and x.month <= 6:
            n += 1
            f.write(f"{n},{100 * w['carry'][i]:.1f},{100 * w['carry'][i] if p[i] > 0 else 'nan'}\n")
