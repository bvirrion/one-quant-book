"""Chart data for Book 16, chapter 3 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_platform as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

w = m.waterfall()
with open(OUT / "waterfall.csv", "w") as f:
    f.write("k,bottom,cost,total\n")
    level = 100 * w["gross"]
    f.write(f"0,0.0,0.0,{level:.2f}\n")
    for k, key in enumerate(("payouts", "costs", "manager"), start=1):
        x = 100 * w[key]
        f.write(f"{k},{level - x:.2f},{x:.2f},0.0\n")
        level -= x
    f.write(f"4,0.0,0.0,{100 * w['investor']:.2f}\n")

with open(OUT / "netting.csv", "w") as f:
    f.write("sr,simulated,closed\n")
    for s, sim, cf in m.netting_vs_sr():
        f.write(f"{s:.2f},{100 * sim:.2f},{100 * cf:.2f}\n")

x = m.sim(1)
base = x["daily"].mean(1).cumsum()
hed = m.ps.overlay(x["daily"], x["beta"], x["factor"]).cumsum()
with open(OUT / "overlay.csv", "w") as f:
    f.write("year,base,hedged\n")
    for t in range(0, len(base), 21):
        f.write(f"{t / 252:.3f},{100 * base[t]:.2f},{100 * hed[t]:.2f}\n")
