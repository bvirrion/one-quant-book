"""Chart data for Book 3, Chapter 11 (deterministic, from data/markets-3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_weather import TICK, utility_put, winters

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/degreeday"))
from firm_degreeday import detrend, put_payoff

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

ws = winters()
with open(OUT / "hdd.csv", "w") as f:
    f.write("winter,hdd\n")
    for w, h, _ in ws:
        f.write(f"{w},{h:.1f}\n")
last = ws[-30:]
det = detrend([h for _, h, _ in last], [float(w) for w, _, _ in last], 2027.0)
k = utility_put()["strike"]
with open(OUT / "burn.csv", "w") as f:
    f.write("winter,hdd,payout\n")
    for (w, _, _), x in zip(last, det, strict=True):
        f.write(f"{w},{x:.1f},{put_payoff(x, k, TICK, 20e6) / 1e6:.3f}\n")
with open(OUT / "ffa.csv", "w") as f:
    f.write("day,index\n")
    for i in range(25):
        f.write(f"{i + 1},{(21_000 + 200 * i) / 1000:.1f}\n")
