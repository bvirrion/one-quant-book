"""Short-term reversal (One Quant Book 8, chapter 2).

On firm.synthmkt (seed 1), years 3 to 10: the rank information coefficient of raw, industry-adjusted and residual
one-day reversal (the residual from Book 7 chapter 24's point-in-time risk model) against the next day's return, in all
names and in the 500 most liquid; the naive dollar-neutral book of each (gross 1, rebuilt every close) before and after
ten basis points per unit traded; then residual reversal traded as a forecast (Grinold's rule with the information
coefficient measured on year 2 only) by a mean-variance book neutral to the risk model's fifteen factors that ignores
costs and by one that has the costs inside (half spread 2 bp, square-root impact 0.7 sigma sqrt(Q / ADV)), at
$100 million, $1 billion and $10 billion; names announcing earnings that day can be skipped. NumPy only.
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
FIRM = HERE.parents[3] / "firm"
for c in ("reversal", "tcost", "vecbt", "predictor"):
    sys.path.insert(0, str(FIRM / c))
sys.path.insert(0, str(HERE.parents[3] / "research" / "24-risk-models" / "python"))
sys.path.insert(0, str(HERE.parents[3] / "research" / "16-vectorised-backtests" / "python"))
from firm_predictor import ic_series  # noqa: E402
from firm_reversal import book, forecast, industry_adjusted  # noqa: E402
from firm_tcost import trade_cost  # noqa: E402
from firm_vecbt import backtest, signal_to_weights  # noqa: E402
from rs_riskmodel import START, WARM, exposures, fundamental, market  # noqa: E402
from rs_vecbt import liquid  # noqa: E402

YEAR, FLAT, HALF_SPREAD, ETA, GAMMA = 252, 0.0010, 2e-4, 0.7, 1000.0
SIZES = (1e8, 1e9, 1e10)


@functools.lru_cache(maxsize=1)
def signals():
    """Signals known at each close (rows t), NaN where not listed: raw, industry-adjusted, residual; the truth."""
    P, R, _, _ = market()
    E = fundamental()["E"]
    raw = np.where(P.listed, -np.nan_to_num(R), np.nan)
    ind = np.vstack([industry_adjusted(np.nan_to_num(R[t]), P.industry, P.listed[t]) for t in range(R.shape[0])])
    res = np.where(P.listed & np.isfinite(E), -E, np.nan)
    spec = fundamental()["spec"]
    scaled = res / np.sqrt(np.where(np.isfinite(spec) & (spec > 0), spec, np.nan))     # in units of its own volatility
    return {"raw": raw, "industry": ind, "residual": res, "scaled": scaled,
            "truth": np.where(P.listed, P.alpha["reversal"], np.nan)}


@functools.lru_cache(maxsize=1)
def announced():
    """True where the name announced earnings that day (announcement dates are scheduled and public)."""
    P = market()[0]
    A = np.zeros(P.listed.shape, bool)
    for t, pid, _ in P.earnings:
        if t < A.shape[0] and pid < A.shape[1]:
            A[t, pid] = True
    return A


@functools.lru_cache(maxsize=1)
def liquid500():
    return liquid(market()[0])


def _next(R):
    return np.vstack([R[1:], np.full((1, R.shape[1]), np.nan)])


def ic(kind: str, top: bool = False, lo: int = START - 1, skip_earnings: bool = False):
    """Mean rank IC of the signal at close t against the return of t + 1, over the evaluation days."""
    P, R, _, _ = market()
    s = signals()[kind]
    if top:
        s = np.where(liquid500(), s, np.nan)
    if skip_earnings:
        s = np.where(announced(), np.nan, s)
    v = ic_series(s[lo:-1], _next(R)[lo:-1])
    return float(np.nanmean(v))


def sharpe(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(YEAR))


@functools.lru_cache(maxsize=8)
def naive(kind: str, cost: float = 0.0):
    """Gross-1 dollar-neutral book in the 500 most liquid, rebuilt at each close from the signal, held the next day."""
    P, R, _, _ = market()
    uni = liquid500() & np.isfinite(signals()[kind])
    w = signal_to_weights(np.nan_to_num(signals()[kind]), uni)
    res = backtest(w, np.where(P.listed, R, np.nan), lag=1, cost=cost)
    net = res.net[START:]
    return {"sr": sharpe(net), "ret": float(net.mean() * YEAR), "turnover": float(res.turnover[START:].mean())}


@functools.lru_cache(maxsize=1)
def inputs():
    """Point-in-time daily volatility (63 days) and ADV (21 days of dollar volume) known at each close."""
    P, R, _, _ = market()
    r = np.nan_to_num(R)
    c1, c2 = np.cumsum(r, axis=0), np.cumsum(r * r, axis=0)
    n = 63
    s1 = c1 - np.vstack([np.zeros((n, r.shape[1])), c1[:-n]])
    s2 = c2 - np.vstack([np.zeros((n, r.shape[1])), c2[:-n]])
    sig = np.sqrt(np.maximum(s2 / n - (s1 / n) ** 2, 1e-8))
    dv = np.where(P.listed, P.price * P.volume, 0.0)
    cd = np.cumsum(dv, axis=0)
    adv = (cd - np.vstack([np.zeros((21, dv.shape[1])), cd[:-21]])) / 21
    return sig, np.maximum(adv, 1e5)


@functools.lru_cache(maxsize=1)
def scale_ic() -> float:
    """The scaled residual signal's IC, measured on year 2 only (before the evaluation)."""
    return ic("scaled", lo=WARM)


@functools.lru_cache(maxsize=8)
def traded(aum: float, costs: bool, round_trip: float = 1.0, skip_earnings: bool = False):
    """Residual reversal as a forecast, traded daily; costs always charged, inside the optimiser only if `costs`."""
    P, R, _, _ = market()
    spec = fundamental()["spec"]
    s = signals()["scaled"]
    if skip_earnings:
        s = np.where(announced(), 0.0, s)                  # no reversal bet on an announcement day's move
    sig, adv = inputs()
    k = scale_ic()
    T, M = R.shape
    w0 = np.zeros(M)
    gross, cost, turn, gx = [], [], [], []
    for t in range(START - 1, T - 1):
        ok = P.listed[t] & P.listed[t + 1] & np.isfinite(s[t]) & np.isfinite(spec[t])
        z = np.zeros(M)
        z[ok] = (s[t, ok] - s[t, ok].mean()) / s[t, ok].std()
        alpha = forecast(z, k, sig[t])
        var = np.where(ok, np.nan_to_num(spec[t]), 1.0)
        w = np.zeros(M)
        w[ok] = book(alpha[ok], var[ok], w0[ok], GAMMA, aum, sig[t, ok], adv[t, ok], HALF_SPREAD, ETA, costs,
                     round_trip, exposures(t + 1)[ok])
        dw = w - w0
        cost.append(trade_cost(dw, aum, sig[t], adv[t], HALF_SPREAD, ETA))
        gross.append(float(np.nansum(w * np.nan_to_num(R[t + 1]))))
        turn.append(float(np.abs(dw).sum()) / 2)
        gx.append(float(np.abs(w).sum()))
        w0 = w * (1 + np.nan_to_num(R[t + 1]))
    g, c = np.array(gross), np.array(cost)
    return {"sr_gross": sharpe(g), "sr_net": sharpe(g - c), "ret_gross": float(g.mean() * YEAR),
            "cost": float(c.mean() * YEAR), "ret_net": float((g - c).mean() * YEAR),
            "turnover": float(np.mean(turn[1:])), "gross": float(np.mean(gx)),
            "vol": float((g - c).std(ddof=1) * math.sqrt(YEAR)), "net": g - c}


def breakeven(kind: str = "residual") -> float:
    """Cost per unit of weight traded (fraction) at which the naive book's net return is zero: g / (2 tau)."""
    n = naive(kind)
    return n["ret"] / (2 * n["turnover"] * YEAR)
