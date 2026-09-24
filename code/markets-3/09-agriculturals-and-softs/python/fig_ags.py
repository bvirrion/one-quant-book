"""Chart data for Book 3, Chapter 9 (deterministic, from data/markets-3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_ags import load_ags, monthly_mm_vs_maize, report_day

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)


def t(m: str) -> float:
    return int(m[:4]) + (int(m[5:]) - 0.5) / 12


with open(OUT / "mm.csv", "w") as f:
    f.write("t,mm,maize\n")
    for m, s, z in monthly_mm_vs_maize():
        f.write(f"{t(m):.4f},{100 * s:.2f},{z:.2f}\n")
with open(OUT / "cocoa.csv", "w") as f:
    f.write("t,cocoa\n")
    for m, c, _ in load_ags():
        f.write(f"{t(m):.4f},{c / 1000:.3f}\n")
with open(OUT / "limits.csv", "w") as f:
    f.write("day,settle,fair\n")
    f.write("0,4.50,4.50\n")
    for i, d in enumerate(report_day()["path"], start=1):
        f.write(f"{i},{d.settle:.2f},3.70\n")
