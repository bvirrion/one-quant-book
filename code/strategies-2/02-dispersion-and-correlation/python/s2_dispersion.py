"""Dispersion and correlation (One Quant Book 9, chapter 2).

Synthetic: firm.synthvol's index as the equal-weighted average of its thirty members (twenty years, three crashes);
members' implied variance is expected variance (factor plus specific) times 1.10, the index's times 1.30, so implied
correlation carries a premium. Each month (21 days): implied and realised average correlation (firm.dispersion),
and three books of one-month variance swaps: short index variance against members' variance on notionals equal to
their weights, the same made vega-neutral, and a short correlation swap. Real: Cboe's 1-month implied correlation
index (COR1M, 2006-2026) and S&P 500 dispersion index (DSPX, 2014-2026), as derived statistics. NumPy.
"""
from __future__ import annotations

import csv
import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
for p in ("synthvol", "dispersion", "shortvol"):
    sys.path.insert(0, str(ROOT / "firm" / p))
from firm_dispersion import average_corr, corr_swap_pnl, dispersion_pnl, realised_var  # noqa: E402
from firm_shortvol import periods  # noqa: E402
from firm_synthvol import VolConfig, expected_var, simulate_vol  # noqa: E402

DATA = ROOT.parent / "data" / "strategies-2"
TENOR = 21


@functools.lru_cache(maxsize=2)
def monthly(member_vrp: float = 0.10):
    cfg = VolConfig(member_vrp=member_vrp)
    S = simulate_vol(cfg)
    R, spec = S["R"], S["spec"]
    N = R.shape[1]
    w = np.full(N, 1 / N)
    idx = R @ w
    tau = TENOR / 252
    out = {k: [] for k in ("ic", "rc", "weights", "vega", "corrswap", "start")}
    for s in periods(len(idx), TENOR):
        ev = expected_var(S["v"][s], cfg, tau)
        ivm = np.sqrt((ev + spec**2) * (1 + cfg.member_vrp))
        ivi = math.sqrt((ev + (w**2 * spec**2).sum()) * (1 + cfg.vrp))
        rvi, rvm = realised_var(idx[:, None], s, TENOR)[0], realised_var(R, s, TENOR)
        ic, rc = average_corr(ivi**2, ivm**2, w), average_corr(rvi, rvm, w)
        out["ic"].append(ic)
        out["rc"].append(rc)
        out["weights"].append(dispersion_pnl(ivi, ivm, rvi, rvm, w, False) * tau)
        out["vega"].append(dispersion_pnl(ivi, ivm, rvi, rvm, w, True) * tau)
        out["corrswap"].append(corr_swap_pnl(ic, rc))
        out["start"].append(s)
    out = {k: np.array(v, float) for k, v in out.items()}
    out["crash_periods"] = [s // TENOR for s, _ in S["crashes"]]
    return out


def stats(x):
    x = np.asarray(x, float)
    d = x - x.mean()
    return {"sr": float(x.mean() / x.std(ddof=1) * math.sqrt(12)), "skew": float((d**3).mean() / (d**2).mean() ** 1.5),
            "worst_sd": float(x.min() / x.std(ddof=1)), "share_up": float((x > 0).mean()), "worst_at": int(x.argmin())}


def crashes():
    m = monthly()
    return [(float(m["ic"][c]), float(m["rc"][c]), float(m["vega"][c] / m["vega"].std(ddof=1)),
             float(m["corrswap"][c])) for c in m["crash_periods"]]


def real():
    with open(DATA / "cor_summary.csv") as fh:
        return {r["index"]: r for r in csv.DictReader(fh)}
