"""Chart data for Book 2, Chapter 24 (deterministic, seeded)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from index_demo import SPREADS, loss_histograms, skew_pnl_curve, tranche_table

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "constituents.csv", "w") as f:
    f.write("rank,spread\n")
    for k, s in enumerate(SPREADS, start=1):
        f.write(f"{k},{1e4 * s:.3f}\n")
with open(OUT / "skewpnl.csv", "w") as f:
    f.write("skew,pnl\n")
    for x, p in skew_pnl_curve():
        f.write(f"{x},{p:.4f}\n")
with open(OUT / "tranches.csv", "w") as f:
    f.write("rho,equity,mezz,senior,super\n")
    for rho, *el in tranche_table():
        f.write(f"{rho:.2f}," + ",".join(f"{100 * x:.5f}" for x in el) + "\n")
hs = loss_histograms()
with open(OUT / "losses.csv", "w") as f:
    f.write("defaults,loss," + ",".join(f"r{int(100 * r)}" for r, _ in hs) + "\n")
    for i in range(len(hs[0][1])):
        k, loss, _ = hs[0][1][i]
        f.write(f"{k},{loss:.3f}," + ",".join(f"{h[i][2]:.5f}" for _, h in hs) + "\n")
