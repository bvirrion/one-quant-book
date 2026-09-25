"""Chart data for Book 7, chapter 26 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_allocation import METHODS, RULES, backtest, multiperiod, redraw_turnover  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

SHORT = ("MV", "sample MV", "robust", "BL", "ERC", "HRP", "equal", "cap")
with open(OUT / "methods.csv", "w") as f:
    f.write("k,label,redraw,sr_net\n")
    for k, (m, lab) in enumerate(zip(METHODS, SHORT, strict=True)):
        f.write(f"{k},{lab},{redraw_turnover(m):.4f},{backtest(m)['sr_net']:.4f}\n")

with open(OUT / "lambda.csv", "w") as f:
    f.write("lam," + ",".join(r.replace(" ", "_") for r in RULES) + "\n")
    for lam in (10.0, 30.0, 100.0, 300.0, 1000.0, 3000.0, 10000.0):
        f.write(f"{lam:g}," + ",".join(f"{max(multiperiod(r, lam)['sr_net'], -3.5):.4f}" for r in RULES) + "\n")
