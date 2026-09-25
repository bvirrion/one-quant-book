"""Performance measurement (One Quant Book 7, chapter 22).

Four synthetic return streams and what their numbers hide. A trend-like stream (normal daily returns, 25% volatility,
true Sharpe ratio 0.7); a short-volatility stream (one-month puts 5% out of the money sold every 21 trading days on a
GJR-GARCH index with Student-t shocks, priced at 1.3 times the index's conditional volatility and marked to market
daily, notional twice the capital); an illiquid book whose true monthly returns (Sharpe ratio 0.6) are reported through
a moving average with weights 0.5, 0.3, 0.2 (Getmansky, Lo and Makarov); a market maker (daily P&L with a Sharpe ratio
of 4 and rare adverse-selection days). And chapter 16's momentum book as a BacktestResult. The probability of a 30%
drawdown within five years, by simulation. NumPy only.
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys
import warnings

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "perf"))
from firm_perf import from_returns, lo_sharpe, max_drawdown, sharpe, smoothing_profile, unsmooth  # noqa: E402

YEAR, YEARS, MONTH = 252, 5, 21
ALPHA, GAMMA, BETA, NU = 0.02, 0.12, 0.90, 5.0
VOL, DRIFT = 0.16, 0.07
STRIKE, IV_MULT, NOTIONAL = 0.95, 1.3, 3.4
THETA = np.array([0.5, 0.3, 0.2])

_ERFC = np.frompyfunc(math.erfc, 1, 1)


def ncdf(x):
    return 0.5 * _ERFC(-np.asarray(x, float) / math.sqrt(2.0)).astype(float)


def put(S, K, tau, vol):
    """Black-Scholes put with zero rates; tau in years (0: intrinsic value)."""
    S, K, tau, vol = (np.asarray(a, float) for a in (S, K, tau, vol))
    live = tau > 0
    st = np.where(live, vol * np.sqrt(np.where(live, tau, 1.0)), 1.0)
    d1 = (np.log(S / K) + 0.5 * st * st) / st
    return np.where(live, K * ncdf(-(d1 - st)) - S * ncdf(-d1), np.maximum(K - S, 0.0))


def market(days: int, paths: int, seed: int):
    """Daily log returns and annualised conditional volatilities of the GJR-GARCH-t index, (days, paths)."""
    rng = np.random.default_rng(seed)
    v_bar = VOL * VOL / YEAR
    omega = v_bar * (1 - ALPHA - GAMMA / 2 - BETA)
    z = rng.standard_t(NU, size=(days, paths)) / math.sqrt(NU / (NU - 2))
    v = np.full(paths, v_bar)
    r = np.empty((days, paths))
    s = np.empty((days, paths))
    for t in range(days):
        s[t] = np.sqrt(v * YEAR)
        r[t] = DRIFT / YEAR - 0.5 * v + np.sqrt(v) * z[t]
        v = omega + (ALPHA + GAMMA * (r[t] < 0)) * r[t] ** 2 + BETA * v
    return r, s


def short_vol(days: int, paths: int, seed: int):
    """Daily returns of the put seller and of the index, (days, paths): sell puts at STRIKE of the level with MONTH
    days to expiry, notional NOTIONAL times capital, mark daily at IV_MULT times the conditional volatility."""
    r, s = market(days, paths, seed)
    S = np.exp(np.cumsum(r, axis=0))
    S_prev = np.vstack([np.ones(paths), S[:-1]])
    s_prev = np.vstack([s[:1], s[:-1]])
    out = np.empty((days, paths))
    cap = np.ones(paths)
    for m0 in range(0, days, MONTH):
        K = STRIKE * S_prev[m0]
        n = NOTIONAL * cap / S_prev[m0]
        v_old = put(S_prev[m0], K, MONTH / YEAR, IV_MULT * s_prev[m0])
        for t in range(m0, min(m0 + MONTH, days)):
            tau = (m0 + MONTH - t - 1) / YEAR
            v_new = put(S[t], K, tau, IV_MULT * s[t])
            pnl = -n * (v_new - v_old)
            out[t] = pnl / cap
            cap = cap + pnl
            v_old = v_new
    return out, np.expm1(r)


def trend(days: int, paths: int, seed: int, vol: float = 0.15, sr: float = 0.75):
    rng = np.random.default_rng(seed)
    return sr * vol / YEAR + vol / math.sqrt(YEAR) * rng.standard_normal((days, paths))


def market_maker(days: int, paths: int, seed: int, vol: float = 0.05, sr: float = 4.0):
    """Daily P&L on capital: a Student-t(4) day-to-day noise and, one day in 250 on average, an adverse-selection loss
    of 1.5%; the mean is set so that the long-run Sharpe ratio is `sr`."""
    rng = np.random.default_rng(seed)
    jump = -0.015 * (rng.random((days, paths)) < 1 / 250)
    noise = rng.standard_t(4, size=(days, paths)) / math.sqrt(2.0)
    base = math.sqrt(max(vol * vol / YEAR - 0.015**2 * (1 / 250) * (1 - 1 / 250), 1e-12))
    return sr * vol / YEAR + 0.015 / 250 + base * noise + jump


def smoothed(months: int, paths: int, seed: int, vol: float = 0.035, sr: float = 0.6):
    """(reported, true) monthly returns: true normal, reported = THETA-weighted average of the last three."""
    rng = np.random.default_rng(seed)
    true = sr * vol * math.sqrt(12) / 12 + vol * rng.standard_normal((months + 2, paths))
    rep = THETA[0] * true[2:] + THETA[1] * true[1:-1] + THETA[2] * true[:-2]
    return rep, true[2:]


def pick(streams, periods: int, target: float = 1.0):
    """The path whose annualised Sharpe ratio is closest to `target` (the displayed history)."""
    sr = streams.mean(axis=0) / streams.std(axis=0, ddof=1) * math.sqrt(periods)
    j = int(np.argmin(np.abs(sr - target)))
    return j, float(sr[j])


@functools.lru_cache(maxsize=1)
def histories():
    """The displayed five-year histories: for each stream, the path (of 400 simulated) with a Sharpe ratio nearest
    1.0 (the market maker: its own median path); the short-volatility path also has no losing quarter."""
    n = YEARS * YEAR
    tr = trend(n, 400, 1)
    sv, idx = short_vol(n, 400, 2)
    q = (1 + sv).reshape(YEARS * 4, 63, -1).prod(axis=1) - 1
    clean = np.all(q > 0, axis=0)
    srs = sv.mean(axis=0) / sv.std(axis=0, ddof=1) * math.sqrt(YEAR)
    j_sv = int(np.flatnonzero(clean)[np.argmin(np.abs(srs[clean] - 1.0))])
    rep, true = smoothed(YEARS * 12, 400, 3)
    j_sm, _ = pick(rep, 12)
    mm = market_maker(n, 400, 4)
    srm = mm.mean(axis=0) / mm.std(axis=0, ddof=1) * math.sqrt(YEAR)
    j_mm = int(np.argsort(srm)[len(srm) // 2])
    j_tr, _ = pick(tr, YEAR)
    return {"trend": tr[:, j_tr], "short vol": sv[:, j_sv], "index": idx[:, j_sv], "smoothed": rep[:, j_sm],
            "smoothed true": true[:, j_sm], "market maker": mm[:, j_mm], "clean share": float(clean.mean())}


def dd_probability(kind: str, level: float = 0.30, years=(1, 2, 3, 5, 10), paths: int = 4000, seed: int = 11):
    """Share of simulated paths whose drawdown reaches `level` within each horizon."""
    n = max(years) * YEAR
    x = trend(n, paths, seed) if kind == "trend" else short_vol(n, paths, seed)[0]
    w = np.cumprod(1 + x, axis=0)
    dd = w / np.maximum.accumulate(np.maximum(w, 1.0), axis=0) - 1
    worst = np.minimum.accumulate(dd, axis=0)
    return {y: float(np.mean(worst[y * YEAR - 1] <= -level)) for y in years}


def long_run(kind: str, years: int = 200, seed: int = 12):
    """The long-run Sharpe ratio, maximum drawdown and annual volatility of one very long path."""
    n = years * YEAR
    x = trend(n, 1, seed)[:, 0] if kind == "trend" else short_vol(n, 1, seed)[0][:, 0]
    return sharpe(x, YEAR)["sr"], max_drawdown(x), float(x.std() * math.sqrt(YEAR))


def smoothed_report():
    """The displayed smoothed book: naive, Lo-adjusted and true Sharpe ratios, standard errors, the estimated
    smoothing profile, and the unsmoothed series' Sharpe ratio."""
    h = histories()
    rep, true = h["smoothed"], h["smoothed true"]
    s = sharpe(rep, 12, lags=3)
    theta = smoothing_profile(rep, 2)
    un = unsmooth(rep, theta)
    d = rep - rep.mean()
    rho = [float(d[k:] @ d[:-k] / (d @ d)) for k in (1, 2, 3)]
    return {"sr": s["sr"], "se_iid": s["se_iid"], "se_hac": s["se_hac"], "lo": lo_sharpe(rep, 12, lags=2),
            "true": sharpe(true, 12)["sr"], "theta": theta, "unsmoothed": sharpe(un, 12)["sr"], "rho": rho,
            "vol_rep": float(rep.std(ddof=1) * math.sqrt(12)), "vol_true": float(true.std(ddof=1) * math.sqrt(12)),
            "vol_un": float(un.std(ddof=1) * math.sqrt(12))}


def stream_results():
    h = histories()
    return {"trend": from_returns(h["trend"]), "short vol": from_returns(h["short vol"]),
            "smoothed": from_returns(h["smoothed"], 12), "market maker": from_returns(h["market maker"])}


@functools.lru_cache(maxsize=1)
def momentum():
    """Chapter 16's momentum book at its last step (the 500 most liquid names, 12-1 momentum rebuilt monthly, 10 bp
    costs, 50 bp borrow, traded at the next close) as a BacktestResult, and the synthetic market's daily return."""
    root = pathlib.Path(__file__).resolve().parents[3] / "firm"
    for c in ("vecbt", "synthmkt", "features"):
        sys.path.insert(0, str(root / c))
    from firm_features import past_return
    from firm_synthmkt import simulate
    from firm_vecbt import backtest, signal_to_weights
    P = simulate()
    dv = np.where(P.listed, P.price * P.volume, 0.0)
    c = np.cumsum(dv, axis=0)
    avg = (c - np.vstack([np.zeros((21, dv.shape[1])), c[:-21]])) / 21
    top = (np.argsort(np.argsort(-avg, axis=1), axis=1) < 500) & P.listed
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)                 # the first year has no signal: empty rows
        w = signal_to_weights(past_return(P.ret, YEAR - 21, 21), top)
    w = w[(np.arange(len(w)) // 21) * 21]
    res = backtest(w, P.ret, lag=2, cost=0.0010, borrow=0.005)
    return res, np.asarray(P.mkt, float)


def updown_beta(r, bench):
    """Betas estimated on the benchmark's down periods and on its up periods separately (with an intercept each)."""
    r, b = np.asarray(r, float), np.asarray(bench, float)
    out = []
    for m in (b < 0, b > 0):
        X = np.column_stack([np.ones(m.sum()), b[m]])
        out.append(float(np.linalg.lstsq(X, r[m], rcond=None)[0][1]))
    return tuple(out)


def monthly_scatter(years: int = 100, seed: int = 12):
    """Monthly (index, short-volatility) returns on a long path, and the down/up betas of the daily returns."""
    sv, idx = short_vol(years * YEAR, 1, seed)
    m = lambda x: (1 + x[:, 0]).reshape(-1, MONTH).prod(axis=1) - 1  # noqa: E731
    return m(idx), m(sv), updown_beta(sv[:, 0], idx[:, 0])


def long_run_shape(years: int = 100, seed: int = 12):
    """Skewness and kurtosis of the short-volatility stream's daily returns over a long path."""
    x = short_vol(years * YEAR, 1, seed)[0][:, 0]
    d = x - x.mean()
    return float((d**3).mean() / x.std() ** 3), float((d**4).mean() / x.std() ** 4)
