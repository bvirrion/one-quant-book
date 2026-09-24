"""Chart data for Book 5, Chapter 16 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_pathdep import (
    FWD_KS,
    asian_by_fixings,
    asian_scatter,
    cliquet_by_cap,
    forward_smiles,
    lookback_table,
    model_paths,
)

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "asian_fixings.csv", "w") as f:
    f.write("n,ratio,volfactor\n")
    for n, ratio, vf in asian_by_fixings():
        f.write(f"{n},{ratio:.5f},{vf:.5f}\n")

g, a = asian_scatter()
with open(OUT / "asian_scatter.csv", "w") as f:
    f.write("geometric,arithmetic\n")
    for x, y in zip(g, a, strict=True):
        f.write(f"{x:.4f},{y:.4f}\n")

lb = lookback_table((4, 12, 52, 252))
with open(OUT / "lookback.csv", "w") as f:
    f.write("n,mc,shifted,cont,vanilla\n")
    for r in lb["rows"]:
        f.write(f"{r['n']},{r['mc']:.4f},{r['shifted']:.4f},{lb['cont']:.4f},{lb['vanilla']:.4f}\n")

paths = model_paths()
fs = forward_smiles(paths)
with open(OUT / "forward_smiles.csv", "w") as f:
    f.write("k,today,lv,heston\n")
    for i, k in enumerate(FWD_KS):
        f.write(f"{100 * k:.0f},{100 * fs['today'][i]:.3f},{100 * fs['lv'][i]:.3f},{100 * fs['heston'][i]:.3f}\n")

with open(OUT / "cliquet_caps.csv", "w") as f:
    f.write("cap,lv,heston,bs\n")
    for cap, lv, hs, b in cliquet_by_cap(paths):
        f.write(f"{100 * cap:.1f},{100 * lv:.4f},{100 * hs:.4f},{100 * b:.4f}\n")
