"""Chart data for Book 3, Chapter 18 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_liq import MMR, cascade, drawdown_curve, liq_price_inverse, liq_price_linear, local_multiplier, population

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "liqprice.csv", "w") as f:
    f.write("leverage,long_linear,short_linear,long_inverse\n")
    for lev in [2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 75, 100]:
        m = 100 / lev
        f.write(f"{lev},{liq_price_linear(1, 100, m, MMR):.3f},{liq_price_linear(-1, 100, m, MMR):.3f},"
                f"{liq_price_inverse(100, 100, 1 / lev, MMR):.3f}\n")

pop = population()
with open(OUT / "kappa.csv", "w") as f:
    f.write("price,kappa\n")
    for p, k in local_multiplier(pop):
        f.write(f"{p:.1f},{k:.3f}\n")

shocks = [i / 400 for i in range(0, 41)]
base = drawdown_curve(pop, shocks)
cap = drawdown_curve(population(max_leverage=10), shocks)
deep = drawdown_curve(pop, shocks, impact=0.6e-5)
with open(OUT / "drawdown.csv", "w") as f:
    f.write("shock,base,cap10,depth2,noforced\n")
    for (s, b), (_, c), (_, d) in zip(base, cap, deep, strict=True):
        n = 1 - cascade(pop, s, forced_selling=False).price / 100
        f.write(f"{100 * s:.2f},{100 * b:.3f},{100 * c:.3f},{100 * d:.3f},{100 * n:.3f}\n")
