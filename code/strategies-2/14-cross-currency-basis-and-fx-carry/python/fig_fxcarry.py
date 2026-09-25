"""Chart data for Book 9, chapter 14 (deterministic)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_fxcarry import DATA, cumulative  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(DATA / "g10_monthly.csv") as fh, open(OUT / "g10.csv", "w") as f:
    f.write("year,cum\n")
    for row in csv.DictReader(fh):
        y, m = int(row["month"][:4]), int(row["month"][5:7])
        f.write(f"{y + (m - 0.5) / 12:.3f},{100 * float(row['cum_log']):.2f}\n")

c = cumulative()
with open(OUT / "hedge.csv", "w") as f:
    f.write("year,raw,hedged\n")
    for s, a, b in zip(c["start"], c["raw"], c["hedged"], strict=True):
        f.write(f"{(s + 21) / 252:.3f},{100 * a:.2f},{100 * b:.2f}\n")
