"""Backward-looking caplets on compounded overnight rates (build of One Quant Book 6, chapter 10).

- Hull-White (constant sigma): closed-form caplet on the rate compounded over [S, E] (continuous
  compounding of the short rate), paid at E, and its forward-looking twin on a term rate fixed at S;
  the in-period variance that separates them; a Monte Carlo check;
- the generalised forward market model's Black formula with in-period volatility decay;
- a meeting-date model: the overnight rate moves only at scheduled meetings, and a Bachelier caplet on
  the period's average rate with the variance of the meetings that remain.
Rates decimal, times in years; the curve is any object with df_t.
"""
import math
from collections.abc import Sequence

import numpy as np

SQRT2 = math.sqrt(2.0)


def _cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / SQRT2)


def _B(kappa: float, tau: float) -> float:
    return tau if abs(kappa) < 1e-12 else (1 - math.exp(-kappa * tau)) / kappa


def _int_B2(kappa: float, d: float) -> float:
    """int_0^d B(tau)^2 dtau."""
    if abs(kappa) < 1e-12:
        return d**3 / 3
    k = kappa
    return (d - 2 * (1 - math.exp(-k * d)) / k + (1 - math.exp(-2 * k * d)) / (2 * k)) / (k * k)


def hw_period_variances(kappa: float, sigma: float, S: float, E: float) -> tuple[float, float]:
    """(variance of int_S^E r accumulated before S, variance accumulated during [S, E]) in Hull-White."""
    before = sigma**2 * _B(kappa, E - S) ** 2 * (1 - math.exp(-2 * kappa * S)) / (2 * kappa)
    during = sigma**2 * _int_B2(kappa, E - S)
    return before, during


def _lognormal_caplet(curve, S: float, E: float, K: float, var: float) -> float:
    """P(0,S) E[(1 - c L)^+] with L lognormal, mean P(0,E)/P(0,S), log-variance var, c = 1 + delta K."""
    delta = E - S
    c = 1 + delta * K
    ps, pe = curve.df_t(S), curve.df_t(E)
    m = pe / ps
    v = math.sqrt(var)
    d1 = (math.log(m * c) + 0.5 * var) / v
    return ps * (_cdf(-(d1 - v)) - c * m * _cdf(-d1))


def hw_backward_caplet(curve, kappa: float, sigma: float, S: float, E: float, K: float) -> float:
    """Caplet paying delta (R - K)^+ at E, R the overnight rate compounded over [S, E]."""
    b, d = hw_period_variances(kappa, sigma, S, E)
    return _lognormal_caplet(curve, S, E, K, b + d)


def hw_forward_caplet(curve, kappa: float, sigma: float, S: float, E: float, K: float) -> float:
    """The same on a forward-looking term rate for [S, E], fixed at S and paid at E."""
    b, _ = hw_period_variances(kappa, sigma, S, E)
    return _lognormal_caplet(curve, S, E, K, b)


def hw_backward_caplet_mc(curve, kappa: float, sigma: float, S: float, E: float, K: float, paths: int = 40000,
                          steps_per_year: int = 260, seed: int = 21) -> tuple[float, float]:
    """Monte Carlo under the risk-neutral measure: r = f(0,t) + x, dx = (y(t) - kappa x) dt + sigma dW."""
    rng = np.random.default_rng(seed)
    dt = 1.0 / steps_per_year
    n, n_start = int(round(E / dt)), int(round(S / dt))
    if abs(n * dt - E) > 1e-9 or abs(n_start * dt - S) > 1e-9:
        raise ValueError("S and E must lie on the time grid")          # a period cut short biases R
    x = np.zeros(paths)
    int_all, int_period = np.zeros(paths), np.zeros(paths)
    for i in range(n):
        t = i * dt
        f0 = -(math.log(curve.df_t(t + dt)) - math.log(curve.df_t(t))) / dt
        yt = sigma**2 * (1 - math.exp(-2 * kappa * t)) / (2 * kappa)
        r = f0 + x
        int_all += r * dt
        if i >= n_start:
            int_period += r * dt
        x = x + (yt - kappa * x) * dt + sigma * math.sqrt(dt) * rng.standard_normal(paths)
    delta = E - S
    rate = (np.exp(int_period) - 1) / delta
    pv = np.exp(-int_all) * delta * np.maximum(rate - K, 0.0)
    return float(pv.mean()), float(pv.std(ddof=1) / math.sqrt(paths))


# ---- generalised forward market model -------------------------------------------------------------------
def gfmm_effective_variance(sigma: float, S: float, E: float, t: float = 0.0) -> float:
    """int_t^E sigma^2 g(u)^2 du with g = 1 before S and decaying linearly to 0 at E."""
    before = max(S - t, 0.0)
    a = max(t, S)
    during = (E - a) ** 3 / (3 * (E - S) ** 2) if a < E else 0.0
    return sigma**2 * (before + during)


def black_caplet(f: float, k: float, total_var: float, annuity: float) -> float:
    v = math.sqrt(total_var)
    d1 = math.log(f / k) / v + 0.5 * v
    return annuity * (f * _cdf(d1) - k * _cdf(d1 - v))


# ---- meeting dates ---------------------------------------------------------------------------------------
def meeting_variance(meetings: Sequence[float], jump_sd: float, S: float, E: float, t: float = 0.0) -> float:
    """Variance, seen at t, of the average overnight rate over [S, E] when the rate moves only at meetings,
    by independent normal jumps of standard deviation jump_sd: a meeting at m moves the average by
    J * (E - max(m, S)) / (E - S) if m < E."""
    d = E - S
    return sum((jump_sd * (E - max(m, S)) / d) ** 2 for m in meetings if t < m < E)


def bachelier_caplet(f: float, k: float, total_var: float, annuity: float) -> float:
    s = math.sqrt(total_var)
    z = (f - k) / s
    return annuity * ((f - k) * _cdf(z) + s * math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi))
