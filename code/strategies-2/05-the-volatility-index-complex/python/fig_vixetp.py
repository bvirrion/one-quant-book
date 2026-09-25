"""Chart data for Book 9, chapter 5 (deterministic)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_vixetp import DATA, paths  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(DATA / "vx_yearly.csv") as fh, open(OUT / "yearly.csv", "w") as f:
    f.write("year,long,vix\n")
    for row in csv.DictReader(fh):
        f.write(f"{row['year']},{100 * float(row['long']):.1f},{100 * float(row['vix_change']):.1f}\n")

p = paths()
with open(OUT / "products.csv", "w") as f:
    f.write("year,vix,inverse,quarter\n")
    for d, x, inv, q in zip(p["day"], p["vix"], p["inverse"], p["quarter"], strict=True):
        inv_s = f"{inv:.4f}" if inv > 0 else "nan"
        f.write(f"{d / 252:.3f},{x:.2f},{inv_s},{q:.4f}\n")
