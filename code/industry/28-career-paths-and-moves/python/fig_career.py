"""Chart data for Book 17, chapter 28."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_career as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
s = a.surface()
with open(OUT / "surface.csv", "w") as f:
    f.write("month," + ",".join(f"q{round(100 * q)}" for q in a.QS) + "\n")
    for m in a.MONTHS:
        f.write(f"{m}," + ",".join(f"{100 * s[(m, q)]:.2f}" for q in a.QS) + "\n")
c = a.career()
with open(OUT / "fan.csv", "w") as f:
    f.write("year,mean,p10,p50,p90\n")
    for t in range(a.YEARS):
        f.write(f"{t + 1}," + ",".join(f"{c[k][t] / 1000:.1f}" for k in ("mean", "p10", "p50", "p90")) + "\n")
