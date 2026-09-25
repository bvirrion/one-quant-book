"""Chart data for Book 8, chapter 19 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_trend import lookbacks, market, paths, smile  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "paths.csv", "w") as f:
    f.write("year,trend,equity\n")
    for y, a, b in paths():
        f.write(f"{y:.3f},{100 * a:.2f},{100 * b:.2f}\n")

with open(OUT / "crashes.csv", "w") as f:
    f.write("start,end\n")
    for s, e in market()["crashes"]:
        f.write(f"{s / 252:.3f},{e / 252:.3f}\n")

x, y, coef = smile()
with open(OUT / "smile.csv", "w") as f:
    f.write("equity,trend\n")
    for a, b in zip(x, y, strict=True):
        f.write(f"{100 * a:.3f},{100 * b:.3f}\n")
with open(OUT / "smile_fit.csv", "w") as f:
    f.write("equity,trend\n")
    for i in range(41):
        e = -0.30 + 0.015 * i
        f.write(f"{100 * e:.3f},{100 * (coef[0] * e * e + coef[1] * e + coef[2]):.3f}\n")

with open(OUT / "lookbacks.csv", "w") as f:
    f.write("months,sr\n")
    for m, s in lookbacks():
        f.write(f"{m},{s:.4f}\n")
