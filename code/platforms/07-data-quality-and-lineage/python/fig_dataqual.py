"""Chart data for One Quant Book 15, chapter 7 (deterministic: the chapter 4 week's second day, seed 0 of planting)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_dataqual import base, plant, rules, run  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

tables, truth, busted = plant(0)
_e, _q, ref, halts = base()
t = tables["trades"]
aware = {f.row for f in run(rules(ref, busted, halts, True), tables) if f.rule == "price spike"}
naive = {f.row for f in run(rules(ref, busted, halts, False), tables) if f.rule == "price spike"}
g = t[t["symbol"] == "SIM2"].sort_values("seq")
with open(OUT / "sim2_prices.csv", "w") as f:
    f.write("n,price,flagged,naive_only\n")
    for n, (i, row) in enumerate(g.iterrows()):
        f.write(f"{n},{row['price'] / 1e4:.4f},{int(i in aware)},{int(i in naive and i not in aware)}\n")
x = np.log(g["price"].to_numpy(dtype=float))
back = np.array([np.median(x[max(0, k - 50):k]) if k >= 5 else np.nan for k in range(len(x))])
ahead = np.array([np.median(x[k + 1:k + 51]) if k + 6 <= len(x) else np.nan for k in range(len(x))])
rows = list(g.index)
first_naive = min(rows.index(i) for i in naive - aware)
with open(OUT / "jump.csv", "w") as f:
    f.write("n,price,behind,ahead,naive_only\n")
    for k in range(max(0, first_naive - 40), min(len(x), first_naive + 60)):
        if rows[k] in aware:
            continue
        f.write(f"{k},{np.exp(x[k]) / 1e4:.4f},{np.exp(back[k]) / 1e4:.4f},{np.exp(ahead[k]) / 1e4:.4f},"
                f"{int(rows[k] in naive)}\n")
