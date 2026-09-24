"""Chart data for Book 2, Chapter 11 (deterministic, from data/markets-2)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from inflation_demo import accruals, load_tips10, seasonality

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-2/11-inflation-markets"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "tips10.csv", "w") as f:
    f.write("t,nominal,real,breakeven\n")
    for d, n, r, b in load_tips10():
        t = int(d[:4]) + (int(d[5:7]) - 0.5) / 12
        f.write(f"{t:.4f},{n:.2f},{r:.2f},{b:.2f}\n")

with open(OUT / "seasonal.csv", "w") as f:
    f.write("month,factor\n")
    for m, v in seasonality().items():
        f.write(f"{m},{v:.4f}\n")

with open(OUT / "accrual.csv", "w") as f:
    f.write("k,month,accrual\n")
    for k, (m, v) in enumerate(accruals()):
        f.write(f"{k},{m},{v:.4f}\n")
