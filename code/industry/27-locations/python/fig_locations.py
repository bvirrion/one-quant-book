"""Chart data for Book 17, chapter 27."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_locations as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
t = a.table()
with open(OUT / "split.csv", "w") as f:
    f.write("pos,city,disposable,rent,tax\n")
    for i, k in enumerate(reversed(a.ORDER)):
        x = t[k]
        tax = (a.PACKAGE - x["net"]) / 1000
        f.write(f"{i + 1},{k},{x['disposable'] / 1000:.2f},{x['rent'] / 1000:.2f},{tax:.2f}\n")
c = a.curves()
with open(OUT / "vs_london.csv", "w") as f:
    f.write("gross," + ",".join(k.replace(" ", "_") for k in a.ORDER[1:]) + "\n")
    for j, g in enumerate(a.GRID):
        f.write(f"{g / 1000:.0f}," + ",".join(f"{(c[k][j] - c['London'][j]) / 1000:.2f}" for k in a.ORDER[1:]) + "\n")
with open(OUT / "pli.csv", "w") as f:
    f.write("pos,country,pli\n")
    for i, (k, v) in enumerate(sorted(a.PLI_2024.items(), key=lambda x: x[1])):
        f.write(f"{i + 1},{k},{v}\n")
