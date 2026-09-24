"""Chart data for Chapter 18 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from futures_basics import SPECS, Spec, hedge, roll_open_interest

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/18-futures-contracts-and-exchanges"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "specs.csv", "w") as f:
    f.write("root,currency,multiplier,tick_value,notional_k,tick_bp\n")
    for s in SPECS:
        f.write(f"{s.root},{s.currency},{s.multiplier:g},{s.tick_value:g},{s.notional / 1e3:.1f},{s.tick_bp:.3f}\n")

front, nxt = roll_open_interest(40, 22, 1.6, 2.4, 18)
with open(OUT / "roll.csv", "w") as f:
    f.write("day,front_m,next_m\n")
    f.writelines(f"{i - 30},{front[i]:.3f},{nxt[i]:.3f}\n" for i in range(40))

es = SPECS[0]
micro = Spec("MES", es.multiplier / 10, es.tick, "USD", es.ref_price)
with open(OUT / "residual.csv", "w") as f:
    f.write("portfolio_m,residual_pct_es,residual_pct_micro\n")
    for k in range(10, 301):
        v = k * 1e4                                    # 0.1m to 3m
        r1 = abs(hedge(v, 1.0, es)[1]) / v * 100
        r2 = abs(hedge(v, 1.0, micro)[1]) / v * 100
        f.write(f"{v / 1e6:.2f},{r1:.2f},{r2:.2f}\n")
