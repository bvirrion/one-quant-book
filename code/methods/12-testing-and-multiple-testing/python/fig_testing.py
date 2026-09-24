"""Chart data for Book 4, Chapter 12 (deterministic, seeded)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_testing import (
    LOOKBACKS,
    SEED,
    correlated_max_draws,
    fdr_experiment,
    max_survival,
    sharpe_power,
    tstats,
    variants,
)

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "power.csv", "w") as f:
    f.write("years,sr05,sr1,sr2\n")
    for y in np.linspace(0, 15, 61):
        f.write(f"{y:.2f}," + ",".join(f"{sharpe_power(s, y):.4f}" for s in (0.5, 1.0, 2.0)) + "\n")

t = tstats(variants(SEED))
with open(OUT / "variants.csv", "w") as f:
    f.write("lookback,t\n")
    for L, v in zip(LOOKBACKS, t, strict=True):
        f.write(f"{L},{v:.4f}\n")

mx = np.sort(correlated_max_draws())
with open(OUT / "maxt.csv", "w") as f:
    f.write("c,single,correlated,independent\n")
    for c in np.linspace(0, 4.5, 91):
        corr = 1 - np.searchsorted(mx, c, side="left") / mx.size
        f.write(f"{c:.2f},{max_survival(c, 1):.6f},{max(corr, 1e-6):.6f},{max_survival(c, 200):.6f}\n")

acc = fdr_experiment()
with open(OUT / "fdr.csv", "w") as f:
    f.write("k,rule,true,false,fdp\n")
    for k, rule in enumerate(("none", "bonferroni", "holm", "bh")):
        a = acc[rule]
        f.write(f"{k},{rule},{a['true']:.2f},{a['false']:.2f},{a['fdp']:.4f}\n")
