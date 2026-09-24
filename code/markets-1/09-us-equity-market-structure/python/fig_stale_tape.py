"""Chart data for Chapter 9 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from stale_tape import Market, stale_fraction

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/09-us-equity-market-structure"
OUT.mkdir(parents=True, exist_ok=True)

m = Market()
with open(OUT / "stale.csv", "w") as f:
    f.write("sip_delay_us,stale_pct_quiet,stale_pct_busy\n")
    for d in (0, 50, 100, 200, 300, 500, 750, 1000, 1500, 2000):
        busy = Market(jumps_per_second=50.0)
        f.write(f"{d},{stale_fraction(m, d) * 100:.4f},{stale_fraction(busy, d) * 100:.4f}\n")

# 2025 US equity volume by where it traded (Cboe, 2025 U.S. Equities Year in Review; ledger row F5)
trf = 50.6
rows = [("Exchanges", 100 - trf), ("Off-exchange: principal dealers", trf * 0.813),
        ("Off-exchange: alternative trading systems", trf * 0.187)]
with open(OUT / "where_2025.csv", "w") as f:
    f.write("k,label,pct\n")
    f.writelines(f"{i},{lab},{v:.1f}\n" for i, (lab, v) in enumerate(rows))

# illustrative fee schedules within the 30-mil cap: all-in price of buying 1 share offered at 10.00
fees = [("Maker-taker venue (take fee 0.30c)", 0.0030), ("Flat-fee venue (0.09c)", 0.0009),
        ("Inverted venue (take rebate 0.15c)", -0.0015)]
with open(OUT / "fees.csv", "w") as f:
    f.write("k,label,net_cents_vs_quote\n")
    f.writelines(f"{i},{lab},{fee * 100:.2f}\n" for i, (lab, fee) in enumerate(fees))
