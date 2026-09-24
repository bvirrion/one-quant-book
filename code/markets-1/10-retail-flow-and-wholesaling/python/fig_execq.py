"""Chart data for Chapter 10 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from execq import EXCHANGE, HORIZONS_S, RETAIL, max_payment, simulate, stats

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/10-retail-flow-and-wholesaling"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "markout.csv", "w") as f:
    f.write("horizon_s,retail_realised,exchange_realised\n")
    sr, pr, mr = simulate(RETAIL, 400_000, 10)
    se, pe, me = simulate(EXCHANGE, 400_000, 11)
    for tau in HORIZONS_S:
        f.write(f"{tau},{stats(sr, pr, mr[tau])['realised']:.4f},{stats(se, pe, me[tau])['realised']:.4f}\n")

# where the quoted half-spread of one cent goes, for retail flow (cents a share)
cost = 0.10
pay = 0.25
impact = RETAIL.informed * RETAIL.drift_cents
margin = 1.0 * (1 - RETAIL.improvement) - impact - cost - pay
rows = [("Price improvement to the client", RETAIL.improvement), ("Adverse selection", impact),
        ("Wholesaler's costs", cost), ("Payment to the broker", pay), ("Wholesaler's margin", margin)]
with open(OUT / "halfspread.csv", "w") as f:
    f.write("k,label,cents\n")
    f.writelines(f"{i},{lab},{v:.2f}\n" for i, (lab, v) in enumerate(rows))
assert abs(sum(v for _, v in rows) - 1.0) < 1e-12 and max_payment(1.0, RETAIL, cost) > pay

with open(OUT / "maxpay.csv", "w") as f:
    f.write("informed_pct,max_payment\n")
    for k in range(0, 31):
        from execq import Flow
        fl = Flow("x", k / 100, 3.0, 0.20)
        f.write(f"{k},{max_payment(1.0, fl, cost):.3f}\n")
