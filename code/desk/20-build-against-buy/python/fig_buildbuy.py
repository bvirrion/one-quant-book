"""Chart data for Book 16, chapter 20 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_buildbuy as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "horizon.csv", "w") as f:
    f.write("years,build,buy\n")
    for h, a, b in m.by_horizon():
        f.write(f"{h},{a:.4f},{b:.4f}\n")

base = m.diff(m.BASE)
with open(OUT / "tornado.csv", "w") as f:
    f.write("pos,input,low,high,base,lmid,lhalf,hmid,hhalf\n")
    for i, (k, lo, hi) in enumerate(m.tornado()):
        name = k.replace("_", " ")
        f.write(f"{i},{name},{lo:.4f},{hi:.4f},{base:.4f},{(lo + base) / 2:.4f},{abs(lo - base) / 2:.4f},"
                f"{(hi + base) / 2:.4f},{abs(hi - base) / 2:.4f}\n")

b, y = m.paths()
with open(OUT / "paths.csv", "w") as f:
    f.write("year,build,buy\n")
    for t, (a, c) in enumerate(zip(b, y, strict=True), start=1):
        f.write(f"{t},{a:.4f},{c:.4f}\n")
