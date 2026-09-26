"""Chart data for Book 10, chapter 27 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_agents import FACTS, LAGS, ablation, calibration, maker_study, sign_curves, target  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

t, c = target(), calibration()
with open(OUT / "facts.csv", "w") as f:
    f.write("k,fact,start,calibrated\n")
    for i, k in enumerate(FACTS):
        z0 = (c["start_facts"][k] - t["mean"][k]) / t["sd"][k]
        z1 = (c["fresh"][k] - t["mean"][k]) / t["sd"][k]
        f.write(f"{i},{k},{z0:.4f},{z1:.4f}\n")
with open(OUT / "surface.csv", "w") as f:
    f.write("chart,tail0,tail15,tail25\n")
    for ch in (0.0, 0.05, 0.1):
        f.write(f"{ch}," + ",".join(f"{c['surface'][(1.2, tl, ch)]:.4f}" for tl in (0.0, 1.5, 2.5)) + "\n")
s = sign_curves()
with open(OUT / "signs.csv", "w") as f:
    f.write("lag,runs,none,excess,law\n")
    for i, lag in enumerate(LAGS):
        law = s["excess"][0] * lag ** s["implied"]
        ex = s["excess"][i] if s["excess"][i] > 0 and lag <= 20 else float("nan")   # beyond lag 20: noise
        f.write(f"{lag},{s['runs'][i]:.5f},{s['none'][i]:.5f},{ex:.5f},{law:.5f}\n")
m = maker_study()
for k, name in ((0.0, "skew0"), (0.3, "skew3")):
    tt, pos = m[k]["path"]
    with open(OUT / f"inventory_{name}.csv", "w") as f:
        f.write("t,lots\n0,0\n")
        for a, b in zip(tt, pos, strict=True):
            f.write(f"{a:.2f},{b:.0f}\n")
a = ablation()
with open(OUT / "ablation.csv", "w") as f:
    f.write("drop," + ",".join(FACTS) + "\n")
    for d in ("runs", "chartists", "fundamentalists", "maker"):
        f.write(d + "," + ",".join(f"{a[d]['z'][k]:.4f}" for k in FACTS) + "\n")
