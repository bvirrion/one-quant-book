"""firm.tailhedge -- rolling put programmes and portfolio-level evaluation (build of One Quant Book 9, chapter 7).

On firm.synthvol's index: a portfolio holds the index and one put per unit of index, bought `otm` below the spot with
`tenor` trading days to expiry at the surface's vol (the variance premium and the skew included), marked daily at the
surface and either held to expiry or monetised (sold and replaced at the new spot) once worth `monetise` times what
it cost. Each roll sets the index units so that the equity and the puts cover the same notional and the portfolio is
fully invested. Alternatives: a static mix of the index and cash (zero rate), and the index plus a trend overlay (a
futures position of `weight` times the sign of the trailing year's return). Evaluation: growth rate, volatility,
maximum drawdown and worst month of a value path. NumPy only.

API (stable):
    put_vol(S, K, tau, v, cfg)                       the surface's vol for a put (smile clipped, finite near expiry)
    put_programme(r, v, cfg, otm, tenor, monetise)   dict nav (T + 1,), hedge_pnl (T,), rolls, monetised count
    static_mix(r, weight, every)                     (T + 1,) value of weight in the index, rest cash, rebalanced
    trend_overlay(r, weight, lookback)               (T + 1,) value of the index plus a trend futures position
    evaluate(nav)                                    growth, vol, max drawdown, worst 21-day return
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "synthvol"))
from firm_synthvol import YEAR, atm_iv, bs_price  # noqa: E402


def put_vol(S, K, tau, v, cfg):
    """The surface's vol for a put: moneyness standardised at no less than a month's vol, the smile clipped to between
    half and three times the at-the-money vol, so that deep wings stay finite as expiry nears."""
    ts = max(tau, 21 / YEAR)
    atm = float(atm_iv(v, cfg, ts))
    x = math.log(K / S) / (atm * math.sqrt(ts))
    return atm * min(max(1 + cfg.skew * x + cfg.curv * x * x, 0.5), 3.0)


def _put(S, K, tau, v, cfg):
    return float(bs_price(S, K, max(tau, 1e-8), put_vol(S, K, tau, v, cfg), "P"))


def put_programme(r, v, cfg, otm: float = 0.05, tenor: int = 21, monetise: float | None = None) -> dict:
    T = len(r)
    S = np.concatenate([[1.0], np.exp(np.cumsum(r))])
    nav, pnl = np.ones(T + 1), np.zeros(T)
    q, K, expiry, n_mon, rolls = 0.0, 0.0, 0, 0, 0
    cost = 0.0
    for t in range(T + 1):
        if t == expiry or t == 0:                                   # roll: buy a new put
            K, expiry = S[t] * (1 - otm), t + tenor
            cost = _put(S[t], K, tenor / YEAR, v[min(t, T - 1)], cfg)
            q, rolls = nav[t] / (S[t] + cost), rolls + 1
        if t == T:
            break
        p0 = _put(S[t], K, (expiry - t) / YEAR, v[t], cfg)
        p1 = max(K - S[t + 1], 0.0) if t + 1 == expiry else _put(S[t + 1], K, (expiry - t - 1) / YEAR,
                                                                    v[min(t + 1, T - 1)], cfg)
        pnl[t] = q * (p1 - p0)
        nav[t + 1] = nav[t] + q * (S[t + 1] - S[t]) + pnl[t]
        if monetise and t + 1 < expiry and p1 >= monetise * cost:  # sell and replace at the new spot
            expiry, n_mon = t + 1, n_mon + 1
    return {"nav": nav, "hedge_pnl": pnl, "rolls": rolls, "monetised": n_mon, "S": S}


def static_mix(r, weight: float, every: int = 21):
    nav, w = np.ones(len(r) + 1), 0.0
    for t, x in enumerate(r):
        if t % every == 0:
            w = weight
        gross = w * math.expm1(x)
        nav[t + 1] = nav[t] * (1 + gross)
        w = w * (1 + math.expm1(x)) / (1 + gross)                   # the weight drifts until the next rebalance
    return nav


def trend_overlay(r, weight: float = 0.5, lookback: int = 252):
    r = np.asarray(r, float)
    trail = np.concatenate([[0.0], np.cumsum(r)])
    sig = np.zeros(len(r))
    for t in range(lookback, len(r)):
        sig[t] = np.sign(trail[t] - trail[t - lookback])
    daily = np.expm1(r) * (1 + weight * sig)
    return np.concatenate([[1.0], np.cumprod(1 + daily)])


def evaluate(nav) -> dict:
    nav = np.asarray(nav, float)
    years = (len(nav) - 1) / YEAR
    lr = np.diff(np.log(nav))
    peak = np.maximum.accumulate(nav)
    month = nav[21:] / nav[:-21] - 1
    return {"growth": float(math.log(nav[-1]) / years), "vol": float(lr.std() * math.sqrt(YEAR)),
            "max_dd": float((nav / peak - 1).min()), "worst_month": float(month.min())}
