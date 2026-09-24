"""Convexity adjustments and constant-maturity products (build of One Quant Book 6, chapter 6).

- timing adjustment of a forward rate paid at the start of its period (Black and normal forms);
- the linear terminal swap-rate model: P(T, Tp) / A(T) = a0 + a1 S(T);
- CMS rate expectation and CMS caplets by static replication with swaptions priced on any smile
  (a function strike -> normal volatility), integrated numerically;
- quanto adjustment of a rate paid in another currency;
- CMS spread options in a normal model of the spread.
Rates and volatilities are decimals; option values per unit notional.
"""
import math
from collections.abc import Callable

import numpy as np

SQRT_2PI = math.sqrt(2 * math.pi)


def _phi(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT_2PI


def _cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2))


def bachelier_call(f: float, k: float, t: float, vol: float) -> float:
    s = vol * math.sqrt(t)
    if s <= 0.0:
        return max(f - k, 0.0)
    d = (f - k) / s
    return (f - k) * _cdf(d) + s * _phi(d)


def bachelier_put(f: float, k: float, t: float, vol: float) -> float:
    return bachelier_call(f, k, t, vol) - (f - k)


# ---- timing ---------------------------------------------------------------------------------------
def timing_adjustment_black(f: float, delta: float, t: float, vol: float) -> float:
    """E^{T_{k-1}}[F_k(T_{k-1})] - F_k(0) for a lognormal forward paid at the start of its period."""
    return f * f * vol * vol * t * delta / (1 + delta * f)


def timing_adjustment_normal(f: float, delta: float, t: float, vol_n: float) -> float:
    """Same with a normal forward: delta * vol_n^2 * t / (1 + delta * F)."""
    return delta * vol_n * vol_n * t / (1 + delta * f)


# ---- linear terminal swap-rate model and CMS -------------------------------------------------------------
def linear_tsr(annuity0: float, df_pay: float, fwd: float, accruals: list[float]) -> tuple[float, float]:
    """(a0, a1) with P(T,Tp)/A(T) = a0 + a1 S(T): a0 from the zero-rate limit, a1 matching today."""
    a0 = 1.0 / sum(accruals)
    a1 = (df_pay / annuity0 - a0) / fwd
    return a0, a1


def _grid(fwd: float, t: float, smile: Callable[[float], float], width: float = 8.0, n: int = 800):
    s = smile(fwd) * math.sqrt(t)
    return np.linspace(fwd - width * s, fwd + width * s, n + 1)


def otm_integral(fwd: float, t: float, smile: Callable[[float], float], lo: float | None = None) -> float:
    """Integral over strikes of out-of-the-money options per unit annuity (receivers below the
    forward, payers above), from `lo` (default: far below) to far above: Var^A(S) / 2 when lo is None."""
    ks = _grid(fwd, t, smile)
    if lo is not None:
        ks = np.concatenate([[lo], ks[ks > lo]])
    vals = [bachelier_put(fwd, k, t, smile(k)) if k < fwd else bachelier_call(fwd, k, t, smile(k)) for k in ks]
    return float(np.trapezoid(vals, ks))


def cms_rate(fwd: float, t: float, annuity0: float, df_pay: float, accruals: list[float],
             smile: Callable[[float], float], lo: float | None = None) -> float:
    """E^{Tp}[S(T)] by replication: [F(a0 + a1 F) + 2 a1 * integral of OTM options] / (a0 + a1 F).
    `lo`: lowest strike of the smile's model (a shifted model has no mass below minus its shift)."""
    a0, a1 = linear_tsr(annuity0, df_pay, fwd, accruals)
    num = fwd * (a0 + a1 * fwd) + 2 * a1 * otm_integral(fwd, t, smile, lo)
    return num / (a0 + a1 * fwd)


def cms_caplet(strike: float, fwd: float, t: float, annuity0: float, df_pay: float, accruals: list[float],
               smile: Callable[[float], float]) -> float:
    """Value (per unit notional and accrual) of max(S(T) - K, 0) paid at Tp:
    A(0) [ (a0 + a1 K) Pay(K) + 2 a1 * integral_K^inf Pay(L) dL ]."""
    a0, a1 = linear_tsr(annuity0, df_pay, fwd, accruals)
    ks = _grid(fwd, t, smile)
    ks = np.concatenate([[strike], ks[ks > strike]])
    tail = float(np.trapezoid([bachelier_call(fwd, k, t, smile(k)) for k in ks], ks))
    return annuity0 * ((a0 + a1 * strike) * bachelier_call(fwd, strike, t, smile(strike)) + 2 * a1 * tail)


def cms_rate_hagan(fwd: float, t: float, vol_n: float, annuity0: float, df_pay: float, accruals: list[float]) -> float:
    """Closed form with a flat normal smile: F + a1 vol^2 t / (a0 + a1 F)."""
    a0, a1 = linear_tsr(annuity0, df_pay, fwd, accruals)
    return fwd + a1 * vol_n * vol_n * t / (a0 + a1 * fwd)


# ---- quanto and spread -----------------------------------------------------------------------------------
def quanto_adjustment_normal(vol_rate_n: float, vol_fx: float, rho: float, t: float) -> float:
    """Drift of a normal rate under the measure of another currency: -rho * vol_rate * vol_fx * t,
    for FX quoted as units of the payment currency per unit of the rate's currency."""
    return -rho * vol_rate_n * vol_fx * t


def spread_vol(v1: float, v2: float, rho: float) -> float:
    return math.sqrt(max(v1 * v1 + v2 * v2 - 2 * rho * v1 * v2, 0.0))


def cms_spread_option(cms1: float, cms2: float, strike: float, t: float, v1: float, v2: float, rho: float,
                      df_pay: float) -> float:
    """max(S1 - S2 - K, 0) paid at Tp, with (S1, S2) jointly normal around their CMS rates."""
    return df_pay * bachelier_call(cms1 - cms2, strike, t, spread_vol(v1, v2, rho))
