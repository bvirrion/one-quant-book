"""Chart data for Book 16, chapter 12 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_risk as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

c = m.compare()
names = {"desk": "head of desk approves", "committee": "risk committee approves",
         "committee_cut": "committee with cut while waiting"}
with open(OUT / "regimes.csv", "w") as f:
    f.write("pos,regime,cut,increase,model,open\n")
    for i, k in enumerate(m.REGIMES):
        sh = c[k]["share"]
        f.write(f"{i},{names[k]},{100 * sh['position cut']:.2f},{100 * sh['limit increase']:.2f},"
                f"{100 * sh['model change']:.2f},{100 * sh['open']:.2f}\n")

d, t, days, util, lim = m.model_change_window()
with open(OUT / "window.csv", "w") as f:
    f.write("day,utilisation,limit\n")
    for a, b, e in zip(days, util, lim, strict=True):
        f.write(f"{a - t},{b:.4f},{e:.4f}\n")

with open(OUT / "lehman.csv", "w") as f:
    f.write("month,limit\n")
    idx = {"2006-11": 0, "2006-12": 1, "2007-09": 10, "2007-12": 13}
    for ym, v in m.LEHMAN_LIMITS:
        f.write(f"{idx[ym]},{v}\n")
    f.write(f"15,{m.LEHMAN_LIMITS[-1][1]}\n")
