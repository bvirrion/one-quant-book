"""Chart data for Book 2, Chapter 29 (deterministic, seeded)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from sizing_demo import coin_table, drawdown_table, growth_curve, uncertain_edge

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "growth.csv", "w") as f:
    f.write("f,g\n")
    for x, g in growth_curve():
        f.write(f"{x:.2f},{100 * g:.5f}\n")
with open(OUT / "coin.csv", "w") as f:
    f.write("k,c,p10,median,p90\n")
    for k, r in enumerate(coin_table()):
        f.write(f"{k},{r['c']},{r['p10']:.4f},{r['median']:.4f},{r['p90']:.4f}\n")
with open(OUT / "drawdown.csv", "w") as f:
    f.write("c,theory,sim\n")
    for c, t, s in drawdown_table():
        f.write(f"{c},{t:.5f},{s:.5f}\n")
with open(OUT / "uncertain.csv", "w") as f:
    f.write("c,g\n")
    for c, g in uncertain_edge():
        f.write(f"{c:.1f},{1e4 * g:.5f}\n")
