"""Book 18, chapter 3: leaderboards, the best of many backtests, and a recruiter's incentives.

The expected maximum of k independent standard normals is computed by numerical
integration of k * x * phi(x) * Phi(x)^(k-1).
"""
from math import erf, exp, pi, sqrt

from scipy.integrate import quad


def _phi(x: float) -> float:
    return exp(-x * x / 2) / sqrt(2 * pi)


def _cdf(x: float) -> float:
    return 0.5 * (1 + erf(x / sqrt(2)))


def expected_max_normal(k: int) -> float:
    """E[max of k iid N(0, 1)]."""
    val, _ = quad(lambda x: k * x * _phi(x) * _cdf(x) ** (k - 1), -12, 12, limit=200)
    return val


def leaderboard_inflation(k: int, noise: float) -> float:
    """Expected excess of the best public score over the common true score, k equally skilled teams."""
    return noise * expected_max_normal(k)


def null_best_sharpe(n_variants: int, years: float) -> float:
    """Expected best annualised Sharpe ratio among n independent zero-skill variants over `years` years
    (the estimate of each has standard deviation about 1/sqrt(years))."""
    return expected_max_normal(n_variants) / sqrt(years)


def recruiter_fee(base: float, rate: float) -> float:
    return base * rate


def recruiter_expected_fee(base: float, rate: float, p_close: float) -> float:
    return p_close * base * rate
