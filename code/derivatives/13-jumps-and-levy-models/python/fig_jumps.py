"""Chart data for Book 5, Chapter 13 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_jumps import (
    EVENT_STRIKES,
    TENORS,
    calibration,
    event_density,
    event_hedge,
    event_hedge_uncertain,
    event_smile,
    fit_bates,
    fit_models,
    hedge_experiment,
    heston_vols,
    implied_vols,
    market_vol,
    otm_put_decay,
    quotes,
    skew_terms,
)

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

xs, mix, logn = event_density()
with open(OUT / "event_density.csv", "w") as f:
    f.write("s,event,lognormal\n")
    for x, a, b in zip(xs, mix, logn, strict=True):
        f.write(f"{x:.3f},{a:.6f},{b:.6f}\n")
with open(OUT / "event_smile.csv", "w") as f:
    f.write("k,vol\n")
    for k, v in zip(EVENT_STRIKES, event_smile(), strict=True):
        f.write(f"{k:.1f},{100 * v:.3f}\n")

fits = fit_models()
t1 = 1 / 12
q = quotes(t1)
with open(OUT / "fit_market.csv", "w") as f:
    f.write("k,market\n")
    for k, v in zip(q[1], q[2], strict=True):
        f.write(f"{k:.3f},{100 * v:.4f}\n")
ks = np.linspace(87.0, 114.0, 55)
heston = calibration()[0]
curves = {name: implied_vols(fits[name][0], 100.0, ks, t1) for name in ("merton", "kou", "vg")}
curves["heston"] = heston_vols(heston, 100.0, ks, t1)
with open(OUT / "fit_models.csv", "w") as f:
    f.write("k,market,merton,kou,vg,heston\n")
    for i, k in enumerate(ks):
        f.write(f"{k:.3f},{100 * market_vol(k, t1):.4f}," + ",".join(f"{100 * curves[n][i]:.4f}"
                                                                   for n in ("merton", "kou", "vg", "heston")) + "\n")

od = otm_put_decay(fits["merton"][0])
with open(OUT / "otm_decay.csv", "w") as f:
    f.write("t,jump,bs,limit\n")
    for t, a, b in zip(od["t"], od["jump"], od["bs"], strict=True):
        bs = f"{b:.6g}" if b > 1e-9 else "nan"          # below the chart's floor
        f.write(f"{t:.6f},{a:.6g},{bs},{od['limit'] * t:.6g}\n")

bates = fit_bates()[0]
st = skew_terms(fits, bates)
with open(OUT / "skews.csv", "w") as f:
    f.write("t,market,merton,vg,heston,bates\n")
    for i, t in enumerate(TENORS):
        names = ("market", "merton", "vg", "heston", "bates")
        f.write(f"{t:.5f}," + ",".join(f"{-st[n][i]:.5f}" for n in names) + "\n")

he = hedge_experiment(fits["merton"][0])
edges = np.linspace(-5.0, 1.5, 27)
with open(OUT / "hedge_hist.csv", "w") as f:
    f.write("x,merton,diffusion\n")
    hm = np.histogram(he["merton"], edges)[0] / len(he["merton"])
    hd = np.histogram(he["diffusion"], edges)[0] / len(he["diffusion"])
    for i in range(len(hm)):
        f.write(f"{edges[i]:.3f},{hm[i]:.5f},{hd[i]:.5f}\n")
    f.write(f"{edges[-1]:.3f},{hm[-1]:.5f},{hd[-1]:.5f}\n")

eh, eu = event_hedge(), event_hedge_uncertain()
with open(OUT / "event_hedge.csv", "w") as f:
    f.write("i,name,sd\n")
    for i, name in enumerate(("none", "model", "black", "minvar")):
        f.write(f"{i},{name},{100 * eh['pnl'][name][2] / eh['premium']:.3f}\n")
    f.write(f"4,uncertain,{100 * eu['sd_rel']:.3f}\n")
