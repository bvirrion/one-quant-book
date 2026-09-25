"""Chart data for Book 9, chapter 15 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_fxflows import real, results  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

x = real()
with open(OUT / "real.csv", "w") as f:
    f.write("k,bp\n")
    for k in (2, 3, 5):
        f.write(f"{k},{float(x[f'k{k}_trade_bp']):.2f}\n")

r = results()
with open(OUT / "quintiles.csv", "w") as f:
    f.write("q,est,realised\n")
    for i, g in enumerate(r["quintiles"]):
        f.write(f"{i + 1},{g['est_bp']:.2f},{g['mean']:.2f}\n")
