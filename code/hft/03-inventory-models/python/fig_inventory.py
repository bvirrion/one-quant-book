"""Chart data for Book 11, chapter 3 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from hf_inventory import as_table, depth_curves, frontier, one_path  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

p = one_path()
with open(OUT / "path.csv", "w") as f:
    f.write("t,s,r,bid,ask,q\n")
    for i in range(0, len(p["t"]), 2):
        f.write(f"{p['t'][i]:.3f},{p['s'][i]:.3f},{p['r'][i]:.3f},{p['bid'][i]:.3f},{p['ask'][i]:.3f},{int(p['q'][i])}\n")

d = depth_curves()
with open(OUT / "depths.csv", "w") as f:
    f.write("q,b05,a05,b5,a5,b50,a50\n")
    for i, q in enumerate(d["q"]):
        f.write(f"{q}," + ",".join(f"{d[phi][j][i]:.4f}" for phi in (0.5, 5.0, 50.0) for j in (0, 1)) + "\n")

fr = frontier()
with open(OUT / "frontier_cj.csv", "w") as f:
    f.write("phi,sd,profit\n")
    for phi, v in fr["cj"].items():
        f.write(f"{phi},{v['sd']:.2f},{v['profit']:.2f}\n")
with open(OUT / "frontier_sym.csv", "w") as f:
    f.write("half,sd,profit\n")
    for h, v in fr["symmetric"].items():
        f.write(f"{h},{v['sd']:.2f},{v['profit']:.2f}\n")
with open(OUT / "frontier_as.csv", "w") as f:
    f.write("gamma,sd,profit\n")
    for g, v in as_table().items():
        f.write(f"{g},{v['inventory']['sd']:.2f},{v['inventory']['profit']:.2f}\n")
