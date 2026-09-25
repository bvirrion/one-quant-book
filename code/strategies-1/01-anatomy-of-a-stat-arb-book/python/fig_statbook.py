"""Chart data for Book 8, chapter 1 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_statbook import START, YEAR, run  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

a, b = run(neutral_styles=False), run(neutral_styles=True)
cum = {}
for name, rows in (("partial", a), ("full", b)):
    cum[name + "_factor"] = np.cumsum([r["factor"] for r in rows])
    cum[name + "_specific"] = np.cumsum([r["specific"] for r in rows])
    cum[name + "_total"] = np.cumsum([r["total"] for r in rows])
with open(OUT / "cum.csv", "w") as f:
    keys = list(cum)
    f.write("year," + ",".join(keys) + "\n")
    for i in range(0, len(a), 5):
        f.write(f"{(START + i) / YEAR:.3f}," + ",".join(f"{cum[k][i]:.4f}" for k in keys) + "\n")
