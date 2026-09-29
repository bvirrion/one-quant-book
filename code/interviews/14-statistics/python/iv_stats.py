"""Book 18, chapter 14: statistics interview answers, in closed form and by simulation."""
from math import erf, exp, pi, sqrt

import numpy as np
from scipy.integrate import quad
from scipy.stats import binom, norm


def sharpe_se_annual(sr_annual: float, n_obs: int, periods_per_year: int = 252) -> float:
    """Lo (2002) standard error of an annualised Sharpe ratio estimated from n_obs i.i.d. returns."""
    sr = sr_annual / sqrt(periods_per_year)
    return sqrt((1 + sr * sr / 2) / n_obs) * sqrt(periods_per_year)


def expected_max_normal(k: int) -> float:
    def f(x):
        phi = exp(-x * x / 2) / sqrt(2 * pi)
        return k * x * phi * (0.5 * (1 + erf(x / sqrt(2)))) ** (k - 1)

    return quad(f, -12, 12, limit=200)[0]


def omitted_variable_slope(b1, b2, cov12, var1):
    return b1 + b2 * cov12 / var1


def years_for_power(sr: float, alpha: float = 0.05, power: float = 0.8) -> float:
    return ((norm.ppf(1 - alpha) + norm.ppf(power)) / sr) ** 2


def ar1_variance_inflation(phi: float) -> float:
    return (1 + phi) / (1 - phi)


def simulate_ar1_mean_se(phi, n, reps, seed):
    rng = np.random.default_rng(seed)
    e = rng.standard_normal((reps, n))
    x = np.empty_like(e)
    x[:, 0] = e[:, 0] / sqrt(1 - phi * phi)
    for t in range(1, n):
        x[:, t] = phi * x[:, t - 1] + e[:, t]
    return x.mean(axis=1).std() * sqrt(n) * sqrt(1 - phi * phi)  # relative to the iid se of a unit-variance series


def stopping_rule_p_values(heads: int, tosses: int):
    """One-sided p-values for 'too few heads' under a fixed number of tosses (binomial) and under tossing until
    `heads` heads (negative binomial): P(X <= heads | n) and P(N >= tosses) = P(at most heads-1 in tosses-1)."""
    p_bin = binom.cdf(heads, tosses, 0.5)
    p_nb = binom.cdf(heads - 1, tosses - 1, 0.5)
    return p_bin, p_nb


def outlier_r2(seed: int = 5, n: int = 250):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    y = rng.standard_normal(n)
    x2, y2 = np.append(x, -12.0), np.append(y, -12.0)
    r2_with = np.corrcoef(x2, y2)[0, 1] ** 2
    r2_without = np.corrcoef(x, y)[0, 1] ** 2
    return r2_with, r2_without
