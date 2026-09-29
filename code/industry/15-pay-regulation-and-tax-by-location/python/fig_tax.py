"""Chart data for Book 17, chapter 15 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_tax as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

c = a.curve()
cols = list(a.at.LOCATIONS) + ["amsterdam expat"]
with open(OUT / "avg_rate.csv", "w") as f:
    f.write("gross," + ",".join(k.replace(" ", "_") for k in cols) + "\n")
    for i, g in enumerate(a.GRID):
        f.write(f"{g / 1000:.0f}," + ",".join(f"{100 * c[k][i]:.1f}" for k in cols) + "\n")

m = a.million()
order = sorted(cols, key=lambda k: m[k]["net"])
with open(OUT / "million.csv", "w") as f:
    f.write("pos,place,net,tax,social\n")
    for i, k in enumerate(order):
        name = a.NAMES.get(k, "Amsterdam (expat scheme)")
        f.write(f"{i + 1},{name},{m[k]['net'] / 1000:.0f},{m[k]['tax'] / 1000:.0f},{m[k]['social'] / 1000:.0f}\n")

mc = a.marginal_curve()
with open(OUT / "marginal.csv", "w") as f:
    f.write("gross," + ",".join(a.at.LOCATIONS) + "\n")
    for i, g in enumerate(a.MGRID):
        f.write(f"{g / 1000:.0f}," + ",".join(f"{100 * mc[k][i]:.1f}" for k in a.at.LOCATIONS) + "\n")
