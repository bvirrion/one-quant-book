"""Chart data for Chapter 30 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from futures_access import ES, MICRO, ROUTES, cost_curve, exchange_round_trip_in_ticks

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/30-getting-access-futures-options"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "per_side.csv", "w") as f:
    f.write("status,exchange,regulatory,commission\n")
    for a, label in zip(ROUTES, ("non-member", "lessee", "owner"), strict=True):
        f.write(f"{label},{ES.exchange_fee[a.status]:.2f},{ES.regulatory_fee[a.status]:.2f},{a.broker_commission:.2f}\n")

with open(OUT / "monthly.csv", "w") as f:
    f.write("sides_k,non_member_k,lessee_k,owner_k\n")
    for s, a, b, c in cost_curve([k * 500.0 for k in range(0, 61)]):
        f.write(f"{s / 1e3:.1f},{a / 1e3:.3f},{b / 1e3:.3f},{c / 1e3:.3f}\n")

with open(OUT / "ticks.csv", "w") as f:
    f.write("status,es_pct,micro_pct\n")
    e, m = exchange_round_trip_in_ticks(ES, 12.5), exchange_round_trip_in_ticks(MICRO, 1.25)
    for k, label in (("non_member", "non-member"), ("lessee", "lessee"), ("owner", "owner")):
        f.write(f"{label},{e[k] * 100:.1f},{m[k] * 100:.1f}\n")
