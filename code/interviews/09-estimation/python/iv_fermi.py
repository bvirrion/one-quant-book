"""Book 18, chapter 9: Fermi chains, intervals and calibration.

Reference values come from the chapter's source ledger (sources/interviews/09-estimation.md); each
constant names its row.
"""
from math import erf, exp, log, prod, sqrt

from scipy.stats import binom, norm

# Ledgered reference values
FX_TURNOVER_USD_PER_DAY = 9.6e12  # F1, BIS Triennial Survey, April 2025
OPRA_PEAK_MSGS_10MS = 0.89e6  # F2, OPRA metrics, July 2026
OPRA_PEAK_MSGS_1S = 63.9e6  # F2
OPRA_CAPACITY_GBITS_PER_100MS = 4.403  # F3, capacity projection for July 2026, one stream
CME_ADV_CONTRACTS_2025 = 28.129e6  # F4, CME Group Form 10-K for 2025
WORLD_POPULATION_2024 = 8.2e9  # F5, UN World Population Prospects 2024


def chain(*factors):
    return prod(factors)


def geometric_mean(lo, hi):
    return sqrt(lo * hi)


def product_log_sd(sds):
    """Log standard deviation of a product of independent factors with the given log standard deviations."""
    return sqrt(sum(s * s for s in sds))


def interval_factor(log_sd, coverage=0.9):
    """Multiplicative half-width of a central interval for a lognormal estimate."""
    return exp(norm.ppf(0.5 + coverage / 2) * log_sd)


def combine_log_estimates(estimates, log_sds):
    """Inverse-variance weighted geometric mean of independent estimates, and its log sd."""
    w = [1 / s**2 for s in log_sds]
    m = sum(wi * log(e) for wi, e in zip(w, estimates, strict=True)) / sum(w)
    return exp(m), sqrt(1 / sum(w))


def hit_rate(stated_coverage, sd_believed, sd_true):
    """Actual coverage of a central interval built with sd_believed when errors have sd_true."""
    z = norm.ppf(0.5 + stated_coverage / 2) * sd_believed / sd_true
    return erf(z / sqrt(2))


def calibration_p_value(hits, n, coverage):
    """Chance of at most `hits` hits in n intervals if each contains the truth with probability coverage."""
    return binom.cdf(hits, n, coverage)


def interval_score(lo, hi, x, alpha):
    """Gneiting and Raftery (2007) interval score for a central (1 - alpha) interval; lower is better."""
    s = hi - lo
    if x < lo:
        s += 2 / alpha * (lo - x)
    if x > hi:
        s += 2 / alpha * (x - hi)
    return s
