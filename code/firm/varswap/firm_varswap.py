"""Variance and volatility swaps (build of Book 5, Chapter 14): strip replication, the index-style discrete
formula, realised variance, mark-to-market, the jump error of the log-contract hedge, and Heston's exact
variance-swap, volatility-swap and volatility-index-future values.

Conventions: variance in annualised units (sigma^2); a variance swap on variance notional N_var pays
N_var (sigma_realised^2 - K^2) at expiry; vega notional N_vega = 2 K N_var; realised variance is
(252 / n) sum ln(S_i / S_{i-1})^2 with no mean subtracted.
"""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "bs"))
from firm_bs import black  # noqa: E402


# ---------------------------------------------------------------- replication
def index_variance(strikes, calls, puts, fwd: float, t: float, rate: float = 0.0) -> float:
    """The volatility-index formula on one expiry: (2/T) sum dK_i / K_i^2 e^(RT) Q(K_i) - (1/T)(F/K0 - 1)^2,
    with Q the put below K0, the call above, their average at K0 (K0 = the strike at or below F), and dK_i
    half the distance between the neighbouring strikes (one-sided at the ends)."""
    k = np.asarray(strikes, float)
    c, p = np.asarray(calls, float), np.asarray(puts, float)
    i0 = int(np.searchsorted(k, fwd, side="right")) - 1
    q = np.where(np.arange(len(k)) < i0, p, c)
    q[i0] = 0.5 * (c[i0] + p[i0])
    dk = np.empty_like(k)
    dk[1:-1] = 0.5 * (k[2:] - k[:-2])
    dk[0], dk[-1] = k[1] - k[0], k[-1] - k[-2]
    return float(2 / t * np.sum(dk / k ** 2 * math.exp(rate * t) * q) - (fwd / k[i0] - 1) ** 2 / t)


def strip_from_vols(vol_of_k, fwd: float, t: float, strikes) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Call and put prices (zero rates) at the given strikes from a smile given in log-moneyness."""
    calls = np.array([black(fwd, k, t, 1.0, vol_of_k(math.log(k / fwd)), "C") for k in strikes])
    return np.asarray(strikes, float), calls, calls - (fwd - np.asarray(strikes, float))


def log_payoff_strip(s_t, fwd: float, strikes) -> np.ndarray:
    """Payoff of the discrete strip that replicates -2 ln(S_T / F): -2 (S_T - F) / F plus 2 dK / K^2 of each
    out-of-the-money option (puts below the forward, calls above, half of each at a strike equal to F)."""
    k = np.asarray(strikes, float)
    s = np.asarray(s_t, float)[..., None]
    dk = np.empty_like(k)
    dk[1:-1] = 0.5 * (k[2:] - k[:-2])
    dk[0], dk[-1] = k[1] - k[0], k[-1] - k[-2]
    put, call = np.maximum(k - s, 0.0), np.maximum(s - k, 0.0)
    opt = np.where(k < fwd, put, np.where(k > fwd, call, 0.5 * (put + call)))   # half each at K = F
    return -2 * (s[..., 0] - fwd) / fwd + np.sum(2 * dk / k ** 2 * opt, axis=-1)


# ---------------------------------------------------------------- realised variance and the swap's value
def realised_variance(prices, days_per_year: int = 252) -> float:
    r = np.diff(np.log(np.asarray(prices, float)))
    return float(days_per_year * np.mean(r * r))


def variance_notional(vega_notional: float, strike_vol: float) -> float:
    """N_var = N_vega / (2 K): a 1-point move in realised volatility near the strike pays about N_vega."""
    return vega_notional / (2 * strike_vol)


def mark_to_market(var_notional: float, strike_vol: float, realised_var: float, t_elapsed: float,
                   fair_var_remaining: float, t_remaining: float, df: float = 1.0) -> float:
    """Value of a long variance swap before expiry: the expected final variance is the time-weighted average of
    the realised part and the fair variance of the remaining part."""
    total = t_elapsed + t_remaining
    expected = (t_elapsed * realised_var + t_remaining * fair_var_remaining) / total
    return var_notional * df * (expected - strike_vol ** 2)


def jump_error(j):
    """Per-return shortfall of the log-contract hedge against the variance swap's leg: the hedge earns
    2 (e^r - 1 - r) for a log-return r and the swap pays r^2; for small r the difference is about r^3 / 3."""
    j = np.asarray(j, float)
    return 2 * (np.exp(j) - 1 - j) - j * j


def vol_swap_approx(mean_var: float, var_of_var: float) -> float:
    """Second-order convexity approximation of a volatility-swap strike: sqrt(V) - Var(V) / (8 V^(3/2))."""
    return math.sqrt(mean_var) - var_of_var / (8 * mean_var ** 1.5)


# ---------------------------------------------------------------- Heston's exact values
def heston_mean_variance(v0: float, kappa: float, vbar: float, t: float) -> float:
    """E[(1/T) int_0^T v dt], the fair variance-swap strike K^2 in Heston."""
    return vbar + (v0 - vbar) * (1 - math.exp(-kappa * t)) / (kappa * t)


def _sqrt_expectation(laplace, scale: float) -> float:
    """E[sqrt(X)] = (1 / (2 sqrt(pi))) int_0^inf (1 - E[e^(-s X)]) s^(-3/2) ds, on s = scale * e^y."""
    y = np.linspace(-25.0, 25.0, 4001)
    s = scale * np.exp(y)
    integrand = (1 - laplace(s)) * s ** -0.5          # s^(-3/2) ds = s^(-1/2) dy
    return float(np.trapezoid(integrand, y) / (2 * math.sqrt(math.pi)))


def integrated_cir_laplace(s, v0: float, kappa: float, vbar: float, eta: float, t: float):
    """E[exp(-s int_0^T v dt)] for the square-root process (the affine 'bond price' formula)."""
    s = np.asarray(s, float)
    g = np.sqrt(kappa * kappa + 2 * eta * eta * s)
    e = np.exp(-g * t)                                # written with e^(-g t) to stay finite for large s
    den = (g + kappa) * (1 - e) + 2 * g * e
    b = 2 * s * (1 - e) / den
    a = 2 * kappa * vbar / eta ** 2 * (np.log(2 * g / den) + 0.5 * (kappa - g) * t)
    return np.exp(a - b * v0)


def heston_vol_swap(v0: float, kappa: float, vbar: float, eta: float, t: float) -> float:
    """E[sqrt((1/T) int_0^T v dt)], the fair volatility-swap strike in Heston."""
    mean = heston_mean_variance(v0, kappa, vbar, t)
    return _sqrt_expectation(lambda s: integrated_cir_laplace(s / t, v0, kappa, vbar, eta, t), 1 / mean)


def cir_laplace(s, v0: float, kappa: float, vbar: float, eta: float, t: float):
    """E[exp(-s v_T)]: v_T is c times a non-central chi-square with d degrees of freedom and parameter lam."""
    s = np.asarray(s, float)
    c = eta * eta * (1 - math.exp(-kappa * t)) / (4 * kappa)
    d = 4 * kappa * vbar / eta ** 2
    lam = v0 * math.exp(-kappa * t) / c
    return (1 + 2 * s * c) ** (-d / 2) * np.exp(-lam * s * c / (1 + 2 * s * c))


def heston_vix_future(v0: float, kappa: float, vbar: float, eta: float, t: float,
                      window: float = 30 / 365) -> tuple[float, float]:
    """(future, forward variance-swap volatility) for the idealised index at T in Heston:
    VIX_T^2 = vbar + (v_T - vbar)(1 - e^(-kappa W)) / (kappa W), affine in v_T."""
    b = (1 - math.exp(-kappa * window)) / (kappa * window)
    a = vbar * (1 - b)
    mean_v = vbar + (v0 - vbar) * math.exp(-kappa * t)
    fwd_var = a + b * mean_v
    fut = _sqrt_expectation(lambda s: np.exp(-s * a) * cir_laplace(s * b, v0, kappa, vbar, eta, t), 1 / fwd_var)
    return fut, math.sqrt(fwd_var)
