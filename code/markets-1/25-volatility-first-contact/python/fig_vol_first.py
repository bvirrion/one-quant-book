"""Chart data for Chapter 25 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from vol_first import RATE, YEARS, chain, read_chain, true_forward

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/parity"))
from firm_parity import price

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/25-volatility-first-contact"
OUT.mkdir(parents=True, exist_ok=True)

strikes = [float(k) for k in range(80, 121, 5)]
rows = chain(strikes)
forwards, f, div, vols = read_chain(rows)
with open(OUT / "chain.csv", "w") as fh:
    fh.write("strike,call,put,implied_forward,implied_vol_pct\n")
    for (k, c, p), fw, v in zip(rows, forwards, vols, strict=True):
        fh.write(f"{k:.0f},{c:.2f},{p:.2f},{fw:.3f},{v * 100:.2f}\n")

with open(OUT / "price_vs_vol.csv", "w") as fh:
    fh.write("vol_pct,call_100,put_90\n")
    for v in range(2, 61):
        fh.write(f"{v},{price(true_forward(), 100.0, YEARS, RATE, v / 100, 'C'):.4f},"
                 f"{price(true_forward(), 90.0, YEARS, RATE, v / 100, 'P'):.4f}\n")

with open(OUT / "weights.csv", "w") as fh:
    fh.write("strike,weight\n")
    total = sum(1.0 / (k * k) for k in range(60, 141))
    fh.writelines(f"{k},{1.0 / (k * k) / total * 100:.3f}\n" for k in range(60, 141, 5))

with open(OUT / "term.csv", "w") as fh:          # two stylised futures curves on a volatility index
    fh.write("month,calm,stress\n")
    calm = [14.0, 15.6, 16.7, 17.5, 18.1, 18.5, 18.8, 19.0]
    stress = [37.0, 30.5, 27.0, 25.0, 23.8, 23.0, 22.5, 22.2]
    fh.writelines(f"{i},{a:.1f},{b:.1f}\n" for i, (a, b) in enumerate(zip(calm, stress, strict=True)))
