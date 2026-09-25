"""Chart data for Book 9, chapter 7 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_tailhedge import curves, real  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

x = real()
with open(OUT / "episodes.csv", "w") as f:
    f.write("x,PPUT,CLLZ,SPX\n")
    for i, k in enumerate(("oct_1987", "autumn_2008", "covid_2020", "max_dd")):
        f.write(f"{i + 1}," + ",".join(f"{100 * float(x[n][k]):.1f}" for n in ("PPUT", "CLLZ", "SPX")) + "\n")

c = curves()
with open(OUT / "paths.csv", "w") as f:
    f.write("year,index,puts,static,trend\n")
    for i, d in enumerate(c["day"]):
        f.write(f"{d / 252:.3f},{c['index'][i]:.4f},{c['5% monthly'][i]:.4f},{c['70% index, 30% cash'][i]:.4f},"
                f"{c['index + trend overlay'][i]:.4f}\n")
