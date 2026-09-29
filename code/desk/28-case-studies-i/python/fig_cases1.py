"""Chart data for Book 16, chapter 28 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_cases1 as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

lt = m.ltcm()
with open(OUT / "ltcm.csv", "w") as f:
    f.write("pos,point,actual,half\n")
    labels = ["end 1997", "end July", "end August", "28 September"]
    for i, (lab, a, h) in enumerate(zip(labels, lt["actual"], lt["half"], strict=True)):
        f.write(f"{i},{lab},{a:.3f},{h:.3f}\n")

a = m.cb.AMARANTH
with open(OUT / "amaranth.csv", "w") as f:
    f.write("pos,contract,share\n")
    for i, (lab, k) in enumerate([("winter 2006-07", "share_winter_oi"), ("November 2006", "share_nov_2006"),
                                  ("January 2007", "share_jan_2007"), ("March 2007", "share_mar_2007")]):
        f.write(f"{i},{lab},{100 * a[k]:.0f}\n")

u = m.august()
with open(OUT / "august.csv", "w") as f:
    f.write("day,seller,holder\n")
    f.write("0,0.000,0.000\n")
    for d, (s, h) in enumerate(zip(u["seller"], u["holder"], strict=True), start=1):
        f.write(f"{d},{100 * s:.3f},{100 * h:.3f}\n")
