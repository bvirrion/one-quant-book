"""Chart data for Book 3, Chapter 13 (deterministic, illustrative inputs)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_access import routes

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "routes.csv", "w") as f:
    f.write("i,route,collateral,annual\n")
    for i, r in enumerate(routes(), start=1):
        f.write(f"{i},{r['route']},{r['collateral'] / 1e6:.3f},{r['annual'] / 1e6:.3f}\n")
