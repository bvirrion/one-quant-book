"""Alternative-data strategies (One Quant Book 8, chapter 16).

An alternative panel covers a tenth of the companies of firm.synthmkt (seed 1) and reads each of their earnings
surprises with noise twice the surprise's own spread (a correlation of about 0.45 with the surprise), delivered 10
trading days before the announcement. The nowcast is the reading times a slope estimated on the first two years'
events. A share phi of the market buys the same panel and moves each price by phi of the expected announcement jump
(three daily specific volatilities per unit of surprise, times the nowcast) on the delivery day. The book holds the
nowcast from the delivery day's close to the announcement's close (gross 1), at 10 basis points per unit traded, years
3 to 10, for phi from 0 to 0.9; and a book that also owns the data first, one day before the others. NumPy only.
"""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("altstrat", "synthmkt", "vecbt"):
    sys.path.insert(0, str(FIRM / c))
from firm_altstrat import diffuse, measure, nowcast_slope, pre_event_book  # noqa: E402
from firm_synthmkt import simulate  # noqa: E402
from firm_vecbt import backtest  # noqa: E402

YEAR, START, LEAD, NOISE, COST, COVER = 252, 504, 10, 2.0, 0.0010, 0.10
PHIS = (0.0, 0.25, 0.5, 0.75, 0.9)


@functools.lru_cache(maxsize=2)
def world(noise: float = NOISE):
    P = simulate()
    R = np.where(P.listed, P.ret, np.nan)
    covered = np.random.default_rng(3).random(R.shape[1]) < COVER          # the companies the panel reads
    events = [(t, p) for t, p, _ in P.earnings if t >= LEAD and covered[p]]
    s = np.array([x for t, p, x in P.earnings if t >= LEAD and covered[p]])
    m = measure(s, noise, np.random.default_rng(16))
    early = np.array([t < START for t, _ in events])
    b = nowcast_slope(m[early], s[early])
    jump = P.cfg.earn_jump * P.spec_vol
    return P, R, events, s, m, b, jump


@functools.lru_cache(maxsize=8)
def run(phi: float = 0.0, head_start: int = 0, noise: float = NOISE):
    """The book's statistics when a share phi of the market trades the panel on its delivery day; with a head start the
    firm receives the panel that many days earlier than the others."""
    P, R, events, s, m, b, jump = world(noise)
    Rd = diffuse(R, events, jump, phi, LEAD, m, b)
    W = pre_event_book(events, b * m, LEAD + head_start, *R.shape)
    res = backtest(W, Rd, lag=1, cost=COST)
    g, n = res.gross[START:], res.net[START:]
    sr = lambda x: float(x.mean() / x.std(ddof=1) * math.sqrt(YEAR))  # noqa: E731
    return {"sr_gross": sr(g), "sr_net": sr(n), "ret_gross": float(g.mean() * YEAR), "ret_net": float(n.mean() * YEAR),
            "turnover": float(res.turnover[START:].sum() / (len(n) / YEAR))}


def nowcast_quality():
    P, R, events, s, m, b, jump = world()
    return {"corr": float(np.corrcoef(m, s)[0, 1]), "slope": b, "events": len(events)}
