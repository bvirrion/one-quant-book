"""Chart data for Book 2, Chapter 6 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from futures_demo import REPO, delivery_value_per_cf, table

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-2/06-bond-futures"
OUT.mkdir(parents=True, exist_ok=True)

names = [n for n, _ in delivery_value_per_cf(0.0)]
with open(OUT / "switch.csv", "w") as f:
    f.write("shift," + ",".join(f"d{i}" for i in range(len(names))) + "\n")
    for k in range(-40, 51):
        s = k * 0.0005
        vals = [v for _, v in delivery_value_per_cf(s)]
        low = min(vals)
        f.write(f"{s * 1e4:.0f}," + ",".join(f"{v - low:.4f}" for v in vals) + "\n")

with open(OUT / "irr.csv", "w") as f:
    f.write("i,label,irr,repo\n")
    for i, r in enumerate(table()):
        label = str(r["name"]).split()[-1]
        f.write(f"{i},{label},{100 * float(r['irr']):.3f},{100 * REPO:.2f}\n")
