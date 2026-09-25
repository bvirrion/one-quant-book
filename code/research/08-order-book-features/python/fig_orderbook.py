"""Chart data for Book 7, chapter 8 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_orderbook import (  # noqa: E402
    CFG,
    best_level_rates,
    data,
    forecast_errors,
    model_up_probability,
    up_probability,
)

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

up = up_probability()
b, d = best_level_rates()
with open(OUT / "updown.csv", "w") as f:
    f.write("centre,empirical,model\n")
    for k, u in enumerate(up):
        f.write(f"{-0.9 + 0.2 * k:.1f},{u['p_up']:.4f},{model_up_probability(u['qb'], u['qa'], b, d):.4f}\n")

tp, feats, mid = data()
g = np.searchsorted(tp.msgs["t"], np.arange(10.0, CFG.seconds, 10.0))
dm, do = np.diff(mid[g]), np.diff(feats["ofi_cum"][g]) / (np.nanmean(feats["bid_qty"] + feats["ask_qty"]) / 2)
order = np.argsort(do)
with open(OUT / "ofi.csv", "w") as f:
    f.write("ofi,dmid\n")
    for chunk in np.array_split(order, 20):
        f.write(f"{do[chunk].mean():.4f},{dm[chunk].mean():.4f}\n")

fe, _ = forecast_errors()
with open(OUT / "forecast.csv", "w") as f:
    f.write("k,h,wmid,micro\n")
    for k, (h, v) in enumerate(fe.items()):
        f.write(f"{k},{h:.0f},{v['wmid'] / v['mid']:.4f},{v['micro'] / v['mid']:.4f}\n")
