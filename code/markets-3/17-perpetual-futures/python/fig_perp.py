"""Chart data for Book 3, Chapter 17 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_perp import funding_rate, funding_trade, inverse_curve, month_of_funding, regimes, yearly_funding

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "rule.csv", "w") as f:
    f.write("premium_bp,funding_bp\n")
    for k in range(-30, 31):
        f.write(f"{k},{1e4 * funding_rate(k / 1e4):.3f}\n")

with open(OUT / "month.csv", "w") as f:
    f.write("day,premium_bp,funding_bp\n")
    for i, p, r in month_of_funding(regimes()):
        f.write(f"{i / 3:.3f},{1e4 * p:.3f},{1e4 * r:.3f}\n")

with open(OUT / "inverse.csv", "w") as f:
    f.write("price,pnl_btc,tangent_btc\n")
    for s, p, t in inverse_curve():
        f.write(f"{s},{p:.5f},{t:.5f}\n")

with open(OUT / "years.csv", "w") as f:
    f.write("year,funding_pct,trade_pct\n")
    for y, v in yearly_funding().items():
        f.write(f"{y},{100 * v:.2f},{100 * funding_trade(v):.2f}\n")
