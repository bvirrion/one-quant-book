"""Chart data for Book 9, chapter 9 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_capstruct import YEAR, cumulative, curve  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

c = curve()
with open(OUT / "curve.csv", "w") as f:
    f.write("E,d40,d80\n")
    for i, e in enumerate(c["E"]):
        f.write(f"{e:.1f},{c[40.0][i]:.1f},{c[80.0][i]:.1f}\n")

cum = cumulative()
with open(OUT / "book.csv", "w") as f:
    f.write("year,base,shifts\n")
    for t in range(YEAR, len(cum[0.05]), 5):
        f.write(f"{t / YEAR:.3f},{100 * cum[0.05][t]:.2f},{100 * cum[0.2][t]:.2f}\n")
