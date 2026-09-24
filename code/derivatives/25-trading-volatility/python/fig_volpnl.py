"""Chart data for Book 5, Chapter 25 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_volpnl import DT, Option, SkewSurface, atm_term, book_explain, scalp, short_vol, value

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

s = scalp()
names = ("uniform", "wrong", "right")
with open(OUT / "scalp.csv", "w") as f:
    f.write("day," + ",".join(f"s_{n}" for n in names) + "," + ",".join(f"pnl_{n}" for n in names) + "\n")
    cum = {n: np.concatenate([[0.0], np.cumsum(s[n]["daily"])]) for n in names}
    for d in range(22):
        f.write(f"{d}," + ",".join(f"{s[n]['path'][d]:.3f}" for n in names) + ","
                + ",".join(f"{cum[n][d]:.4f}" for n in names) + "\n")

with open(OUT / "term.csv", "w") as f:
    f.write("months,vol\n")
    for m in np.linspace(0.5, 12, 24):
        f.write(f"{m:.2f},{100 * atm_term(m / 12):.3f}\n")
with open(OUT / "term_points.csv", "w") as f:
    f.write("months,vol\n")
    for m in (1, 2, 3):
        f.write(f"{m},{100 * atm_term(m / 12):.3f}\n")
book = [Option(100.0, 0.25, "C"), Option(100.0, 0.25, "P")]
surf, flat = SkewSurface(atm_term), SkewSurface(lambda tau: atm_term(0.25))
with open(OUT / "carry.csv", "w") as f:
    f.write("day,roll,flat\n")
    for d in range(22):
        f.write(f"{d},{value(book, 100.0, d * DT, surf):.4f},{value(book, 100.0, d * DT, flat):.4f}\n")

b = book_explain()
with open(OUT / "explain.csv", "w") as f:
    cols = ("gamma", "theta", "vega", "cross", "unexplained", "total")
    f.write("day," + ",".join(f"{c}_{r}" for r in ("ss", "sd") for c in cols) + "\n")
    series = {}
    for r, key in (("ss", "sticky_strike"), ("sd", "sticky_delta")):
        x = b[key]
        comp = {"gamma": x["gamma"], "theta": x["theta"], "vega": x["vega"], "cross": x["vanna"] + x["volga"],
                "unexplained": x["unexplained"], "total": x["total"]}
        for c in cols:
            series[f"{c}_{r}"] = np.concatenate([[0.0], np.cumsum(comp[c])])
    for d in range(len(b["spot"])):
        f.write(f"{d}," + ",".join(f"{series[f'{c}_{r}'][d]:.4f}" for r in ("ss", "sd") for c in cols) + "\n")

v = short_vol()
edges = np.arange(-6.0, 3.51, 0.5)
counts, _ = np.histogram(v["pnl"], bins=edges)
with open(OUT / "shortvol.csv", "w") as f:
    f.write("centre,count\n")
    for c, n in zip(0.5 * (edges[:-1] + edges[1:]), counts, strict=True):
        f.write(f"{c:.2f},{n}\n")
