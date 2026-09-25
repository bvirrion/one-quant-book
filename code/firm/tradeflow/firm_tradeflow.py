"""firm.tradeflow -- trade-flow features (build of One Quant Book 7, chapter 9).

Trade signing (tick rule, quote rule, Lee-Ready, bulk volume classification), order-sign autocorrelation and a Hurst
exponent by aggregated variance, VPIN on volume buckets, Kyle's lambda by rolling regression, and a mark-out
toxicity measure to compare VPIN with. Trades are arrays (times, prices, sizes); quotes are the prevailing bid and ask
at each trade (as-of), possibly lagged. NumPy only.

API (stable):
    tick_rule(price)                               +1 / -1 by the last price change (0 until the first change)
    quote_rule(price, bid, ask)                    +1 above the mid, -1 below, 0 at the mid
    lee_ready(price, bid, ask)                     quote rule, tick rule for trades at the mid
    bvc(price_change, volume, sigma)               buy fraction per bar: Phi(dP / sigma) (bulk volume classification)
    sign_acf(signs, lags)                          autocorrelation of trade signs at the given lags
    hurst_aggvar(x, scales)                        Hurst exponent from the variance of block sums across scales
    vpin(signs_or_buyfrac, volume, bucket, n)      VPIN over the last n volume buckets
    kyle_lambda(dmid, signed_volume)               OLS slope of mid changes on signed volume, with R^2
    markout_toxicity(sign, price, mid_later)       mean signed mark-out of trades against their resting side
    aggregate_orders(trade_id, t, qty, sign)       one row per aggressive order (a sweep is one order)
"""
from __future__ import annotations

import math

import numpy as np


def tick_rule(price) -> np.ndarray:
    p = np.asarray(price, float)
    out = np.zeros(len(p), int)
    last = 0
    for i in range(1, len(p)):
        if p[i] > p[i - 1]:
            last = 1
        elif p[i] < p[i - 1]:
            last = -1
        out[i] = last
    return out


def quote_rule(price, bid, ask, tol: float = 1e-9) -> np.ndarray:
    mid = 0.5 * (np.asarray(bid, float) + np.asarray(ask, float))
    d = np.asarray(price, float) - mid
    return np.where(np.abs(d) < tol, 0, np.sign(d)).astype(int)


def lee_ready(price, bid, ask) -> np.ndarray:
    q = quote_rule(price, bid, ask)
    t = tick_rule(price)
    return np.where(q != 0, q, t)


def _phi(x):
    return 0.5 * (1.0 + np.vectorize(math.erf)(np.asarray(x, float) / math.sqrt(2.0)))


def bvc(price_change, volume, sigma: float) -> np.ndarray:
    """Share of each bar's volume classified as buys: Phi(dP / sigma), sigma the standard deviation of dP."""
    return _phi(np.asarray(price_change, float) / sigma)


def sign_acf(signs, lags) -> np.ndarray:
    s = np.asarray(signs, float)
    s = s - s.mean()
    v = (s * s).mean()
    return np.array([(s[:-k] * s[k:]).mean() / v for k in lags])


def hurst_aggvar(x, scales=(1, 2, 4, 8, 16, 32, 64, 128, 256)) -> float:
    """Var(sum of m consecutive values) grows like m^(2H): regress log variance on log m."""
    x = np.asarray(x, float) - np.mean(x)
    v = []
    for m in scales:
        n = len(x) // m
        v.append(x[: n * m].reshape(n, m).sum(axis=1).var())
    slope = np.polyfit(np.log(scales), np.log(v), 1)[0]
    return float(slope / 2.0)


def vpin(buy_volume, volume, bucket: float, n: int) -> np.ndarray:
    """Cut the trade sequence into buckets of `bucket` shares (a trade may be split between buckets); VPIN at the end
    of each bucket is sum over the last n buckets of |V_buy - V_sell| / (n * bucket). buy_volume is the buy part of
    each trade's volume (the size itself for a buy, 0 for a sell, or a fraction of it under BVC)."""
    bv, v = np.asarray(buy_volume, float), np.asarray(volume, float)
    imb, fill, buys = [], 0.0, 0.0
    for b_i, v_i in zip(bv, v, strict=True):
        frac_b = b_i / v_i if v_i > 0 else 0.0
        left = v_i
        while left > 0:
            take = min(left, bucket - fill)
            fill += take
            buys += take * frac_b
            left -= take
            if fill >= bucket - 1e-9:
                imb.append(abs(2.0 * buys - bucket))
                fill, buys = 0.0, 0.0
    imb = np.array(imb)
    out = np.full(len(imb), np.nan)
    if len(imb) >= n:
        cs = np.cumsum(imb)
        out[n - 1:] = (cs[n - 1:] - np.r_[0.0, cs[:-n]]) / (n * bucket)
    return out


def kyle_lambda(dmid, signed_volume) -> dict:
    x, y = np.asarray(signed_volume, float), np.asarray(dmid, float)
    X = np.column_stack([np.ones(len(x)), x])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    res = y - X @ b
    return {"lambda": float(b[1]), "r2": float(1 - res.var() / y.var())}


def markout_toxicity(sign, price, mid_later) -> float:
    """Mean of sign * (later mid - trade price): what an aggressor gains, and the resting side loses, per share."""
    return float(np.mean(np.asarray(sign) * (np.asarray(mid_later, float) - np.asarray(price, float))))


def aggregate_orders(trade_id, t, qty, sign):
    """Collapse executions that belong to one aggressive order (same trade id) into one row."""
    trade_id = np.asarray(trade_id)
    first = np.r_[True, trade_id[1:] != trade_id[:-1]]
    idx = np.flatnonzero(first)
    q = np.add.reduceat(np.asarray(qty, float), idx)
    return np.asarray(t)[idx], q, np.asarray(sign)[idx]
