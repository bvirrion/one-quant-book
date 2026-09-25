"""firm.perf -- performance measurement on a BacktestResult (build of One Quant Book 7, chapter 22).

Reads the net returns of a BacktestResult (or any array of periodic returns) and reports the Sharpe ratio with iid,
HAC and autocorrelation-adjusted (Lo) versions, drawdowns and their durations, Calmar, Sortino and Omega ratios, hit
rate and profit factor, turnover and holding period, alpha and beta against a benchmark with HAC errors, the
unsmoothing of returns reported through a moving average (Getmansky, Lo and Makarov), and a text tear sheet. The
Sharpe ratio's standard errors are firm.estim's (Book 4), the regression firm.linreg's.

API (stable):
    from_returns(r, periods)          a BacktestResult holding a return stream (one name, weight 1)
    returns_of(res)                   res.net
    sharpe(r, periods)                {'sr', 'se_iid', 'se_hac'} annualised (firm.estim.sharpe)
    lo_sharpe(r, q, lags)             Sharpe ratio annualised over q periods with Lo's autocorrelation correction
    drawdown(r, compound)             (T,) fall from the running peak of the wealth path, as a fraction (<= 0)
    max_drawdown(r, compound)         the most negative drawdown
    drawdown_spells(r, compound)      [(start, trough, end or None)] of each spell under water
    longest_drawdown(r, compound)     periods from a peak to the recovery (or the end), longest spell
    calmar(r, periods)                annualised return / |max drawdown|
    sortino(r, periods, mar)          annualised mean excess over the MAR / downside deviation
    omega(r, threshold)               E[(r - L)+] / E[(L - r)+]
    hit_rate(r), profit_factor(r)     share of positive periods; sum of gains / sum of losses
    holding_period(res)               mean gross exposure / mean one-way turnover, in periods
    alpha_beta(r, bench, periods, lags) {'alpha', 'alpha_t', 'beta', 'beta_se'}, alpha annualised, HAC errors
    smoothing_profile(r, k)           theta_0..theta_k (sum 1) matching the first k autocorrelations of an MA(k)
    unsmooth(r, theta)                true returns recovered by inverting the moving average
    tear_sheet(res, bench, name)      a dict of the measures and its text rendering
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

_FIRM = pathlib.Path(__file__).resolve().parents[1]
for _c in ("vecbt", "estim", "linreg"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_estim import long_run_variance  # noqa: E402
from firm_estim import sharpe as _sharpe  # noqa: E402
from firm_linreg import ols  # noqa: E402
from firm_vecbt import BacktestResult  # noqa: E402


def from_returns(r, periods: int = 252) -> BacktestResult:
    r = np.asarray(r, float)
    T = len(r)
    w = np.ones((T, 1))
    tr = np.zeros((T, 1))
    tr[0] = 1.0
    return BacktestResult(np.arange(T), np.array(["stream"]), w, tr, r.copy(), {"trading": np.zeros(T)}, r.copy(),
                          np.cumprod(1 + r), {"periods": periods, "compound": True})


def returns_of(res) -> np.ndarray:
    return np.asarray(res.net if isinstance(res, BacktestResult) else res, float)


def sharpe(r, periods: int = 252, lags: int | None = None) -> dict:
    return _sharpe(returns_of(r), periods, lags)


def lo_sharpe(r, q: int = 12, lags: int | None = None) -> float:
    """SR over q periods = q mu / sqrt(q gamma_0 + 2 sum_{k<q} (q - k) gamma_k): the per-period Sharpe ratio times
    q / sqrt(q + 2 sum (q - k) rho_k) instead of sqrt(q) (Lo 2002)."""
    x = returns_of(r)
    d = x - x.mean()
    n = len(x)
    L = q - 1 if lags is None else min(lags, q - 1)
    rho = [float(d[k:] @ d[:-k] / (d @ d)) for k in range(1, L + 1)]
    eta = q / math.sqrt(q + 2 * sum((q - k) * rho[k - 1] for k in range(1, L + 1)))
    return float(x.mean() / x.std(ddof=1) * eta) if n > 1 else float("nan")


def _wealth(x, compound):
    return np.cumprod(1 + x) if compound else 1 + np.cumsum(x)


def drawdown(r, compound: bool = True) -> np.ndarray:
    w = np.r_[1.0, _wealth(returns_of(r), compound)]
    peak = np.maximum.accumulate(w)
    return (w / peak - 1)[1:] if compound else (w - peak)[1:]


def max_drawdown(r, compound: bool = True) -> float:
    return float(drawdown(r, compound).min())


def drawdown_spells(r, compound: bool = True):
    dd = drawdown(r, compound)
    spells, start = [], None
    for t, v in enumerate(dd):
        if v < 0 and start is None:
            start = t
        elif v >= 0 and start is not None:
            spells.append((start, start + int(np.argmin(dd[start:t])), t))
            start = None
    if start is not None:
        spells.append((start, start + int(np.argmin(dd[start:])), None))
    return spells


def longest_drawdown(r, compound: bool = True) -> int:
    n = len(returns_of(r))
    return max([(e if e is not None else n) - s for s, _, e in drawdown_spells(r, compound)], default=0)


def calmar(r, periods: int = 252) -> float:
    x = returns_of(r)
    ann = float(np.prod(1 + x) ** (periods / len(x)) - 1)
    return ann / abs(max_drawdown(x))


def sortino(r, periods: int = 252, mar: float = 0.0) -> float:
    x = returns_of(r) - mar
    dd = math.sqrt(float(np.mean(np.minimum(x, 0.0) ** 2)))
    return float(x.mean() / dd * math.sqrt(periods))


def omega(r, threshold: float = 0.0) -> float:
    x = returns_of(r) - threshold
    return float(np.maximum(x, 0).mean() / np.maximum(-x, 0).mean())


def hit_rate(r) -> float:
    x = returns_of(r)
    return float(np.mean(x[x != 0] > 0))


def profit_factor(r) -> float:
    x = returns_of(r)
    return float(x[x > 0].sum() / -x[x < 0].sum())


def holding_period(res: BacktestResult) -> float:
    return float(res.gross_exposure.mean() / res.turnover.mean())


def alpha_beta(r, bench, periods: int = 252, lags: int | None = None) -> dict:
    x, b = returns_of(r), np.asarray(bench, float)
    fit = ols(np.column_stack([np.ones_like(b), b]), x, cov="hac", lags=lags)
    a, se_a = fit["beta"][0], fit["se"][0]
    return {"alpha": float(a * periods), "alpha_t": float(a / se_a), "beta": float(fit["beta"][1]),
            "beta_se": float(fit["se"][1])}


def _ma_acf(theta):
    th = np.asarray(theta, float)
    s = th @ th
    return np.array([th[k:] @ th[:-k] / s for k in range(1, len(th))])


def smoothing_profile(r, k: int = 2, grid: int = 201) -> np.ndarray:
    """The theta (theta_j >= 0, sum 1) of r_obs = sum_j theta_j r_{t-j} whose MA(k) autocorrelations best match the
    sample's first k (least squares on a grid of the simplex; k = 1 or 2), among invertible profiles (a profile and
    its reverse have the same autocorrelations)."""
    x = returns_of(r)
    d = x - x.mean()
    rho = np.array([d[j:] @ d[:-j] / (d @ d) for j in range(1, k + 1)])
    g = np.linspace(0.0, 1.0, grid)
    best, arg = np.inf, None
    if k == 1:
        cands = ((a, 1 - a) for a in g)
    else:
        cands = ((a, b, 1 - a - b) for a in g for b in g if a + b <= 1 + 1e-12)
    for th in cands:
        if th[0] <= 0.05 or np.any(np.abs(np.roots(th[::-1])) <= 1.0):
            continue                                                    # not invertible: time reversal of another
        e = float(((_ma_acf(th) - rho) ** 2).sum())
        if e < best:
            best, arg = e, th
    return np.array(arg)


def unsmooth(r, theta) -> np.ndarray:
    """r_t = (r_obs_t - sum_{j>=1} theta_j r_{t-j}) / theta_0, started from the observed mean (the start-up error
    decays geometrically when theta is invertible)."""
    x, th = returns_of(r), np.asarray(theta, float)
    out = np.full(len(x) + len(th) - 1, x.mean())
    k = len(th) - 1
    for t in range(len(x)):
        out[t + k] = (x[t] - th[1:] @ out[t + k - np.arange(1, k + 1)]) / th[0]
    return out[k:]


def tear_sheet(res, bench=None, name: str = "", periods: int | None = None):
    x = returns_of(res)
    p = periods or (res.meta.get("periods", 252) if isinstance(res, BacktestResult) else 252)
    s = sharpe(x, p)
    m = {"annual return": float(np.prod(1 + x) ** (p / len(x)) - 1), "annual volatility": float(x.std(ddof=1)) *
         math.sqrt(p), "Sharpe": s["sr"], "se (iid)": s["se_iid"], "se (HAC)": s["se_hac"],
         "max drawdown": max_drawdown(x), "longest drawdown": longest_drawdown(x), "Calmar": calmar(x, p),
         "Sortino": sortino(x, p), "Omega(0)": omega(x), "skewness": float(((x - x.mean()) ** 3).mean() / x.std() ** 3),
         "kurtosis": float(((x - x.mean()) ** 4).mean() / x.std() ** 4), "hit rate": hit_rate(x),
         "profit factor": profit_factor(x), "lrv / variance": long_run_variance(x) / float(x.var())}
    if isinstance(res, BacktestResult) and res.weights.shape[1] > 1:
        m["turnover"] = float(res.turnover.mean())
        m["holding period"] = holding_period(res)
    if bench is not None:
        m.update({f"{k}": v for k, v in alpha_beta(x, bench, p).items()})
    text = "\n".join([f"tear sheet {name}"] + [f"  {k:<18s} {v:10.4f}" for k, v in m.items()])
    return m, text
