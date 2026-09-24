"""Chart data for Book 2, Chapter 30 (deterministic, seeded)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mmgame_demo import curves, distribution, one_game

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "distribution.csv", "w") as f:
    f.write("sum,p\n")
    for s, p in distribution():
        f.write(f"{s},{p:.6f}\n")
value, mids, _ = one_game()
with open(OUT / "game.csv", "w") as f:
    f.write("round,mid,value\n")
    for k, m in enumerate(mids):
        f.write(f"{k},{m:.4f},{value}\n")
cs = curves()
with open(OUT / "pnl.csv", "w") as f:
    keys = list(cs)
    f.write("width," + ",".join(keys) + "\n")
    for i in range(len(cs[keys[0]])):
        f.write(f"{cs[keys[0]][i][0]:.1f}," + ",".join(f"{cs[k][i][1]:.4f}" for k in keys) + "\n")
