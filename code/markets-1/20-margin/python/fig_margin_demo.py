"""Chart data for Chapter 20 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/margin"))
from firm_margin import Market, Params, Position, product_margin, risk_array, scenarios, value
from margin_demo import ewma_vol, fhs_var, hs_var, simulate_returns, with_floor

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/20-margin"
OUT.mkdir(parents=True, exist_ok=True)

P = Params(price_scan=345.0, vol_scan=0.04, multiplier=50.0, intermonth_charge=400.0, short_option_min=175.0)
MKT = Market({("ES", "Z"): 6000.0}, {("ES", "Z"): 0.18}, {("ES", "Z"): 0.25})
BOOK = [Position("ES", "Z", 2), Position("ES", "Z", -10, 5600.0, "P"), Position("ES", "Z", -10, 6400.0, "C")]

with open(OUT / "scenarios.csv", "w") as f:
    f.write("scenario,loss_k\n")
    losses = [sum(pos.qty * risk_array(pos, MKT, P)[i] for pos in BOOK) for i in range(16)]
    f.writelines(f"{i + 1},{x / 1e3:.2f}\n" for i, x in enumerate(losses))

with open(OUT / "profile.csv", "w") as f:
    f.write("move,vol_up_k,vol_down_k\n")
    base = sum(pos.qty * value(pos, MKT) for pos in BOOK)
    for dp in np.arange(-1100, 1101, 25):
        up = (sum(pos.qty * value(pos, MKT, dp, 0.04) for pos in BOOK) - base) * 50 / 1e3
        dn = (sum(pos.qty * value(pos, MKT, dp, -0.04) for pos in BOOK) - base) * 50 / 1e3
        f.write(f"{dp},{up:.2f},{dn:.2f}\n")
with open(OUT / "points.csv", "w") as f:
    f.write("move,pnl_k\n")
    for (dp, _dv, _cover), loss in zip(scenarios(P)[:14], losses[:14], strict=True):
        f.write(f"{dp:.0f},{-loss / 1e3:.2f}\n")

r = simulate_returns(900, 0.008, 0.035, 600, 25, 20)
vol = ewma_vol(r)
days = np.arange(300, 900)
hs = np.array([hs_var(r, t, 250, 0.99, 2) for t in days]) * 100
fhs = np.array([fhs_var(r, vol, t, 250, 0.99, 2) for t in days]) * 100
floored = with_floor(fhs, 9.0, 0.25)
with open(OUT / "procyclical.csv", "w") as f:
    f.write("day,hs,fhs,floored\n")
    f.writelines(f"{d - 600},{a:.3f},{b:.3f},{c:.3f}\n" for d, a, b, c in zip(days, hs, fhs, floored, strict=True))

legs = {"future": [BOOK[0]], "short put": [BOOK[1]], "short call": [BOOK[2]], "portfolio": BOOK}
with open(OUT / "offsets.csv", "w") as f:
    f.write("item,margin_k\n")
    f.writelines(f"{k},{product_margin(v, MKT, P).total / 1e3:.2f}\n" for k, v in legs.items())
