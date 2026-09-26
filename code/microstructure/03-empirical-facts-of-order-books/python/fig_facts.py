"""Chart data for Book 10, chapter 3 (deterministic; MIDAS figures from the derived files in data/microstructure)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_facts import (  # noqa: E402
    POINTS,
    day,
    intraday_mean,
    lifetable,
    midas_lifetimes,
    midas_yearly,
    spread_vs_vol,
    spread_vs_vol_zi,
)

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

m, sim = midas_lifetimes(), lifetable(day())
with open(OUT / "lifetimes.csv", "w") as f:
    f.write("k,large,mid,small,sim\n")
    for k in range(len(POINTS)):
        f.write(f"{k},{m[('large', 'cancel')][k]:.4f},{m[('mid', 'cancel')][k]:.4f},"
                f"{m[('small', 'cancel')][k]:.4f},{sim[k]:.4f}\n")

with open(OUT / "yearly.csv", "w") as f:
    f.write("year,hidden,oddlot,ctt\n")
    for y, v in midas_yearly().items():
        f.write(f"{y},{v['hidden_rate']:.2f},{v['oddlot_rate']:.2f},{v['cancel_to_trade']:.2f}\n")

zi, tp = spread_vs_vol_zi(), spread_vs_vol()
with open(OUT / "spreadvol.csv", "w") as f:
    f.write("vol,spread,kind\n")
    for s, v in zi["points"]:
        f.write(f"{v:.4f},{s:.4f},0\n")
    for s, v in tp["points"]:
        f.write(f"{v:.4f},{s:.4f},1\n")
with open(OUT / "spreadvol_fit.csv", "w") as f:
    f.write("vol,spread\n")
    for v in (0.0, 5.5):
        f.write(f"{v:.2f},{zi['intercept'] + zi['slope'] * v:.4f}\n")

with open(OUT / "intraday.csv", "w") as f:
    f.write("bin,volume,messages\n")
    for r in intraday_mean():
        f.write(f"{r['bin'] + 1},{r['volume'] / 1000:.1f},{r['messages'] / 1000:.2f}\n")
