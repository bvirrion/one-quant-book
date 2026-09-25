"""Chart data for Book 8, chapter 6 (deterministic)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_factors import sml  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
DATA = HERE.parents[4] / "data" / "strategies-1"

with open(DATA / "beta_sml.csv") as f, open(OUT / "sml_french.csv", "w") as g:
    g.write("beta,ret_pct\n")
    for row in csv.DictReader(f):
        if row["portfolio"] != "BAB":
            g.write(f"{float(row['beta']):.4f},{100 * float(row['ann_excess']):.3f}\n")

with open(OUT / "sml_synth.csv", "w") as f:
    f.write("beta,ret_pct\n")
    for row in sml():
        f.write(f"{row['beta']:.4f},{100 * row['ret']:.3f}\n")

with open(DATA / "ff5_rolling.csv") as f, open(OUT / "rolling.csv", "w") as g:
    g.write("year,hml_pct,rmw_pct\n")
    for row in csv.DictReader(f):
        g.write(f"{row['year']},{100 * float(row['hml']):.3f},{100 * float(row['rmw']):.3f}\n")
