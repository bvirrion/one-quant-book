"""Chart data for Book 2, Chapter 12 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mbs_demo import load_fed_mbs, price_yield, psa_curves

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-2/12-mortgages-and-agencies"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "psa.csv", "w") as f:
    f.write("age,psa50,psa100,psa200\n")
    for row in psa_curves():
        f.write(f"{row[0]}," + ",".join(f"{v:.2f}" for v in row[1:]) + "\n")

with open(OUT / "priceyield.csv", "w") as f:
    f.write("y,mbs,static\n")
    for y, a, b in price_yield():
        f.write(f"{y:.2f},{a:.4f},{b:.4f}\n")

with open(OUT / "fedmbs.csv", "w") as f:
    f.write("t,bn\n")
    for d, v in load_fed_mbs():
        if d >= "2007-01":
            f.write(f"{int(d[:4]) + (int(d[5:7]) - 0.5) / 12:.4f},{v:.1f}\n")
