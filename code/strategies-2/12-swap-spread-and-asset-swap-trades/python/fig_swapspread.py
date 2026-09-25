"""Chart data for Book 9, chapter 12 (deterministic)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_swapspread import DATA, YEAR, market  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(DATA / "swaps_monthly.csv") as fh, open(OUT / "real.csv", "w") as f:
    f.write("year,s10,s30\n")
    for row in csv.DictReader(fh):
        y, m = int(row["month"][:4]), int(row["month"][5:7])
        s30 = f"{float(row['s30']):.1f}" if row["s30"] not in ("", "nan") else "nan"
        f.write(f"{y + (m - 0.5) / 12:.3f},{float(row['s10']):.1f},{s30}\n")

cfg, s = market()
with open(OUT / "synthetic.csv", "w") as f:
    f.write("year,spread,cost\n")
    for t in range(0, len(s["spread"]), 2):
        f.write(f"{t / YEAR:.3f},{s['spread'][t]:.2f},{-s['cost'][t]:.2f}\n")
