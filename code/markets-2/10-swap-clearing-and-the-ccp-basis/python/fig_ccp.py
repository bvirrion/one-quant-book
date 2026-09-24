"""Chart data for Book 2, Chapter 10 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ccp_demo import basis_table, im_profiles

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-2/10-swap-clearing-and-the-ccp-basis"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "im.csv", "w") as f:
    f.write("t,ten,thirty\n")
    for t, a, b in im_profiles():
        f.write(f"{t:.2f},{a:.4f},{b:.4f}\n")

with open(OUT / "basis.csv", "w") as f:
    f.write("maturity,f25,f50,f75\n")
    for row in basis_table():
        f.write(",".join(f"{v:.4f}" for v in row) + "\n")
