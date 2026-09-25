"""Cross-asset lead-lag (One Quant Book 8, chapter 22).

Daily: firm.synthmkt's ten industry factor returns (ten years) follow firm.synthfut's ten commodities (the first ten
years) through planted slow diffusion: three industries receive 0.08 times the average of one commodity's returns
over the previous five days. The first half is scanned for lagged correlations, lag by lag (1 to 10 days, 1,000
tests) and over the five-day window (100 pairs), each with a Bonferroni threshold at 5%; the links found are traded
in the second half (position in each industry proportional to its commodity's five-day return in standard
deviations, capped at two, at 2 basis points per unit traded). Intraday: twenty sessions of 23,400 seconds in which
a follower sees the leader's efficient price two seconds late (both with tick noise, one tick a second on average);
the lead is estimated from the Hayashi-Yoshida cross-correlation, and a trader who sees the leader move more than
2 basis points in two seconds trades the follower after a latency of 0 to 3 seconds, holds two seconds and pays half
a basis point each way. NumPy only.
"""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys
from statistics import NormalDist

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
for p in ("synthmkt", "synthfut", "xasset", "leadlag", "hfvol"):
    sys.path.insert(0, str(ROOT / "firm" / p))
from firm_hfvol import previous_tick  # noqa: E402
from firm_leadlag import hy_ccf, lead_estimate  # noqa: E402
from firm_synthfut import simulate_futures  # noqa: E402
from firm_synthmkt import MarketConfig, simulate  # noqa: E402
from firm_xasset import detect, diffuse, lead_scan, lead_trades, signal, simulate_pair  # noqa: E402

LINKS = [(0, 0), (1, 3), (2, 7)]
BETA, WINDOW, COST = 0.08, 5, 2e-4
SESSION, SESSIONS, LEAD, VOL, NOISE, RATE = 23400, 20, 2, 1e-4, 1e-5, 1.0
LAGS = np.arange(-6, 7)


@functools.lru_cache(maxsize=2)
def panels(beta: float = BETA):
    ind = simulate(MarketConfig()).ind
    com = simulate_futures()["r"][: len(ind)]
    com = com[:, 30:40]                                            # the ten commodities
    return com, diffuse(ind, com, LINKS, beta, WINDOW)


def window_t(com, fol, end):
    c = np.cumsum(com, axis=0)
    W = np.zeros_like(com)
    W[WINDOW:] = c[WINDOW:] - c[:-WINDOW]
    t = np.zeros((com.shape[1], fol.shape[1]))
    for i in range(com.shape[1]):
        for j in range(fol.shape[1]):
            a, b = W[WINDOW:end - 1, i], fol[WINDOW + 1:end, j]
            t[i, j] = np.corrcoef(a, b)[0, 1] * math.sqrt(len(a))
    return t


@functools.lru_cache(maxsize=2)
def daily(beta: float = BETA):
    com, fol = panels(beta)
    T, half = len(fol), len(fol) // 2
    lag_t = lead_scan(com[:half], fol[:half], range(1, 11))
    lag_hits, lag_thr = detect(lag_t, lag_t.size)
    wt = window_t(com, fol, half)
    w_thr = NormalDist().inv_cdf(1 - 0.05 / (2 * wt.size))
    found = [(i, j) for i in range(10) for j in range(10) if abs(wt[i, j]) > w_thr]
    s = signal(com, found, WINDOW, fol.shape[1])
    w = np.zeros_like(s)
    for i, j in found:
        w[:, j] = np.sign(wt[i, j]) * s[:, j] / (com[:half, i].std() * math.sqrt(WINDOW))
    w = np.clip(w, -2, 2) * 0.1 / (fol[:half].std(0) * math.sqrt(252)) / max(len(found), 1)
    gross = np.zeros(T)
    gross[1:] = (w[:-1] * fol[1:]).sum(1)
    net = gross - (np.abs(np.diff(w, axis=0, prepend=0.0)) * COST).sum(1)
    sr = lambda x: float(x.mean() / x.std(ddof=1) * math.sqrt(252))  # noqa: E731
    return {"lag_hits": lag_hits, "lag_thr": lag_thr, "window_t": [float(wt[i, j]) for i, j in LINKS],
            "window_thr": w_thr, "found": found, "gross": sr(gross[half:]), "net": sr(net[half:]),
            "lag_t_max": [float(np.abs(lag_t[:, i, j]).max()) for i, j in LINKS],
            "lag_t_pairs": [[float(v) for v in lag_t[:, i, j]] for i, j in LINKS]}


@functools.lru_cache(maxsize=1)
def intraday():
    rng = np.random.default_rng(22)
    ccf, leads = np.zeros(len(LAGS)), []
    trades = {lat: [] for lat in range(4)}
    days = {lat: [] for lat in range(4)}
    g = np.arange(SESSION)
    for _ in range(SESSIONS):
        t1, x1, t2, x2 = simulate_pair(SESSION, LEAD, VOL, NOISE, RATE, rng)
        c = hy_ccf(t1, x1, t2, x2, LAGS, 60.0)
        ccf += c / SESSIONS
        leads.append(lead_estimate(LAGS, c))
        g1, g2 = previous_tick(t1, x1, g), previous_tick(t2, x2, g)
        for lat in range(4):
            tr = lead_trades(g1, g2, 2, lat, 2, 2e-4, 0.5e-4)
            trades[lat].append(tr)
            days[lat].append(tr.sum())
    out = {"ccf": ccf / ccf.max(), "leads": leads}
    for lat in range(4):
        tr, d = np.concatenate(trades[lat]), np.array(days[lat])
        out[lat] = {"n": len(tr) / SESSIONS, "bp": float(1e4 * tr.mean()), "hit": float((tr > 0).mean()),
                    "day_bp": float(1e4 * d.mean()), "days_up": int((d > 0).sum())}
    return out
