"""Chart data for Book 3, Chapter 10 (deterministic, from data/markets-3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_curves import convenience_monthly, index_series, samuelson

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "samuelson.csv", "w") as f:
    f.write("contract,vol\n")
    for i, v in enumerate(samuelson(), start=1):
        f.write(f"{i},{100 * v:.1f}\n")
with open(OUT / "convenience.csv", "w") as f:
    f.write("t,back,ycu\n")
    for m, b, y in convenience_monthly():
        f.write(f"{int(m[:4]) + (int(m[5:]) - 0.5) / 12:.4f},{100 * b:.1f},{100 * y:.2f}\n")
s = index_series()
with open(OUT / "index.csv", "w") as f:
    f.write("t,excess,spot\n")
    for k, (d, lvl, near) in enumerate(s):
        if k % 5 == 0 or k == len(s) - 1:
            f.write(f"{d.year + (d.timetuple().tm_yday - 0.5) / 366:.4f},{lvl:.4f},{near / s[0][2]:.4f}\n")
