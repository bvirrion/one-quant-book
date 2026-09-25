"""Chart data for Book 7, chapter 12 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_altdata import breakeven_curve, live_fit, trial, trial_report  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

d = trial()
rng = np.random.default_rng(0)
for name, mask in (("backfill", d["backfilled"]), ("live", ~d["backfilled"])):
    idx = np.sort(rng.choice(np.flatnonzero(mask), 600, replace=False))
    with open(OUT / f"{name}.csv", "w") as f:
        f.write("s,m\n")
        for i in idx:
            f.write(f"{d['s'][i]:.4f},{d['m'][i]:.4f}\n")
b, a = live_fit()
with open(OUT / "fitline.csv", "w") as f:
    f.write("s,m\n")
    for x in (-3.5, 3.5):
        f.write(f"{x:.1f},{a + b * x:.4f}\n")

r = trial_report()
with open(OUT / "ic.csv", "w") as f:
    f.write("year,ic\n")
    for y, v in sorted(r["ic_year"].items()):
        f.write(f"{y},{v:.4f}\n")
with open(OUT / "icref.csv", "w") as f:
    f.write("year,inc,own\n")
    for x in (2.5, 5.5):
        f.write(f"{x},{r['inc'][0]:.4f},{r['ic_old_live']:.4f}\n")

with open(OUT / "breakeven.csv", "w") as f:
    f.write("half_life,back,live,inc\n")
    for h, v in breakeven_curve().items():
        f.write(f"{h},{v['ls_back'] / 1e6:.4f},{v['ls_new'] / 1e6:.4f},{v['ls_inc'] / 1e6:.4f}\n")
