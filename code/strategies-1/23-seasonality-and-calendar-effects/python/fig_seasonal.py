"""Chart data for Book 8, chapter 23 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_seasonal import calendar_test, gas_profile, wti_months  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

c = calendar_test()
order = np.argsort(-np.abs(c["t"]))
with open(OUT / "rules.csv", "w") as f:
    f.write("rank,tom,pre,none\n")
    for k, i in enumerate(order):
        vals = [f"{abs(c['t'][i]):.3f}" if c["family"][i] == fam else "nan" for fam in ("tom", "pre", "none")]
        f.write(f"{k + 1}," + ",".join(vals) + "\n")

g = gas_profile()
w, _, _ = wti_months()
with open(OUT / "months.csv", "w") as f:
    f.write("month,gas_pct,wti_t\n")
    for m in range(12):
        f.write(f"{m + 1},{100 * g['dev'][m]:.2f},{w[m][2]:.3f}\n")
