"""Merger arbitrage (One Quant Book 8, chapter 11).

About fifty cash deals a year announced over the synthetic market's ten years (its cap-weighted market from Book 7
chapter 24), with premiums of 20% to 40%, a median of 110 trading days to resolution, a break price that moves with
the market, a spread that prices a 12% break probability, and a true break probability of 6% plus 1.5 times the
market's fall over the deal's life. An equal-weighted portfolio of the open deals, entered at each announcement's
close, years 3 to 10: its return, its return over the 4% rate the spreads discount at, volatility and Sharpe ratio;
its beta in months when the market fell more than 4% and in the other months; the completion probability implied at
entry against the realised completion rate; and the same portfolio when breaks do not depend on the market, and when
the spread prices the true break rate. NumPy only.
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

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3] / "firm" / "mergerarb"))
sys.path.insert(0, str(HERE.parents[3] / "research" / "24-risk-models" / "python"))
from firm_mergerarb import DealConfig, annualised, portfolio, simulate_deals, spread  # noqa: E402
from rs_riskmodel import START, market  # noqa: E402

YEAR, MONTH, DOWN, RATE = 252, 21, -0.04, 0.04


@functools.lru_cache(maxsize=8)
def run(crash_break: float = 1.5, q: float = 0.12, base_break: float = 0.06):
    mkt = market()[3]
    cfg = DealConfig(crash_break=crash_break, q=q, base_break=base_break)
    deals = simulate_deals(mkt, cfg, np.random.default_rng(11))
    r, c = portfolio(deals, len(mkt))
    r, m, c = r[START:], mkt[START:], c[START:]
    k = len(r) // MONTH
    rm = np.prod(1 + r[:k * MONTH].reshape(k, MONTH), axis=1) - 1
    mm = np.prod(1 + m[:k * MONTH].reshape(k, MONTH), axis=1) - 1
    down = mm < DOWN
    beta = lambda x, y: float(np.polyfit(x, y, 1)[0])  # noqa: E731
    ev = [d for d in deals if d["start"] >= START]
    x = r - RATE / YEAR                                      # in excess of the rate the spreads discount at
    return {"ret": float(r.mean() * YEAR), "excess": float(x.mean() * YEAR),
            "vol": float(r.std(ddof=1) * math.sqrt(YEAR)),
            "sr": float(x.mean() / x.std(ddof=1) * math.sqrt(YEAR)), "beta": beta(m, r),
            "beta_down": beta(mm[down], rm[down]), "beta_up": beta(mm[~down], rm[~down]),
            "down_months": int(down.sum()),
            "months": int(k), "worst_month": float(rm.min()), "mkt_worst": float(mm[rm.argmin()]),
            "active": float(c.mean()), "deals": len(ev), "implied": float(np.mean([d["implied"] for d in ev])),
            "completed": float(1 - np.mean([d["broke"] for d in ev])),
            "spread": float(np.mean([spread(d["price"][0], d["offer"]) for d in ev])),
            "spread_ann": float(np.mean([annualised(spread(d["price"][0], d["offer"]), d["end"] - d["start"])
                                        for d in ev])),
            "rm": rm, "mm": mm}


def break_rates():
    """Break rate of the deals whose market fell over their life against those whose market rose."""
    mkt = market()[3]
    lm = np.concatenate([[0.0], np.cumsum(np.log1p(mkt))])
    deals = simulate_deals(mkt, DealConfig(), np.random.default_rng(11))
    ev = [d for d in deals if d["start"] >= START]
    fell = np.array([lm[d["end"]] < lm[d["start"]] for d in ev])
    broke = np.array([d["broke"] for d in ev])
    return {"fell": float(broke[fell].mean()), "rose": float(broke[~fell].mean()), "n_fell": int(fell.sum())}
