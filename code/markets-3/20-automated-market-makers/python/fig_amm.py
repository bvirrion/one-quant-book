"""Chart data for Book 3, Chapter 20 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_amm import breakeven_turnover, impermanent_loss, impermanent_loss_range, lvr_mean, stableswap_curve

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "invariants.csv", "w") as f:
    f.write("x,cp,csum,ss\n")
    for x, y in stableswap_curve():
        f.write(f"{x:.2f},{25 / x:.4f},{max(10 - x, 0):.4f},{y:.4f}\n")

with open(OUT / "il.csv", "w") as f:
    f.write("r,full,w50,w10\n")
    for k in range(-30, 31):
        r = 2 ** (k / 30)
        f.write(f"{r:.4f},{100 * impermanent_loss(r):.3f},{100 * impermanent_loss_range(r, 0.5):.3f},"
                f"{100 * impermanent_loss_range(r, 0.1):.3f}\n")

acc, _ = lvr_mean()
with open(OUT / "lvr.csv", "w") as f:
    f.write("day,measured_bp,theory_bp\n")
    f.write("0,0,0\n")
    for d, a in enumerate(acc, 1):
        f.write(f"{d},{1e4 * a:.3f},{1e4 * 0.36 / 8 * d / 365:.3f}\n")

with open(OUT / "turnover.csv", "w") as f:
    f.write("vol,f5,f30,f100\n")
    for v in range(20, 121, 5):
        s = v / 100
        f.write(f"{v}," + ",".join(f"{100 * breakeven_turnover(s, fee):.3f}" for fee in (0.0005, 0.003, 0.01)) + "\n")
