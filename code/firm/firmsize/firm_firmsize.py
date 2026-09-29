"""firm.firmsize -- size distributions from binned public counts (build of One Quant Book 17, chapter 6).

Regulators publish counts of firms in size bins, not firm sizes. A Pareto tail above x_min,
P(X > x) = (x / x_min)^-alpha, is fitted to the binned counts by maximum likelihood: bin i with integer bounds
[lo, hi] (hi None = open) has probability F(lo - 1/2) - F(hi + 1/2) of the continuous survival function F; the
standard error of alpha is the inverse square root of the observed information (a numerical second derivative). A
lognormal fit to the same bins is the comparison, and a chi-square statistic says how each fits.

API (stable):
    Bin(lo, hi, n)
    pareto_fit(bins, x_min) -> dict(alpha, se, loglik, n)
    lognormal_fit(bins, x_min) -> dict(mu, sigma, loglik, n)   conditional on X >= x_min
    expected_counts(bins, x_min, model) -> list ; chi2(bins, expected) -> float
    ccdf(bins) -> list of (x, share of firms of size >= x)
"""
import math
from dataclasses import dataclass

import numpy as np
from scipy import optimize, stats


@dataclass(frozen=True)
class Bin:
    lo: int
    hi: int | None
    n: int


def _edges(b):
    return b.lo - 0.5, (math.inf if b.hi is None else b.hi + 0.5)


def _pareto_p(b, x_min, alpha):
    a, c = _edges(b)
    s = lambda x: 0.0 if math.isinf(x) else (x / (x_min - 0.5)) ** (-alpha)  # noqa: E731
    return s(a) - s(c)


def _tail(bins, x_min):
    t = [b for b in bins if b.lo >= x_min]
    if not t:
        raise ValueError("no bin at or above x_min")
    return t


def _ll_pareto(alpha, bins, x_min):
    return sum(b.n * math.log(max(_pareto_p(b, x_min, alpha), 1e-300)) for b in bins)


def pareto_fit(bins, x_min):
    t = _tail(bins, x_min)
    res = optimize.minimize_scalar(lambda a: -_ll_pareto(a, t, x_min), bounds=(0.05, 5.0), method="bounded",
                                   options={"xatol": 1e-9})
    a = float(res.x)
    h = 1e-4
    d2 = (_ll_pareto(a + h, t, x_min) - 2 * _ll_pareto(a, t, x_min) + _ll_pareto(a - h, t, x_min)) / h ** 2
    return dict(alpha=a, se=float(1 / math.sqrt(-d2)), loglik=-float(res.fun), n=sum(b.n for b in t))


def _lognorm_p(b, x_min, mu, sigma):
    a, c = _edges(b)
    z = lambda x: 1.0 if math.isinf(x) else stats.norm.cdf((math.log(x) - mu) / sigma)  # noqa: E731
    base = 1 - z(x_min - 0.5)
    return (z(c) - z(a)) / base


def lognormal_fit(bins, x_min):
    t = _tail(bins, x_min)

    def nll(p):
        mu, ls = p
        return -sum(b.n * math.log(max(_lognorm_p(b, x_min, mu, math.exp(ls)), 1e-300)) for b in t)
    res = optimize.minimize(nll, x0=[math.log(x_min), 0.5], method="Nelder-Mead",
                            options={"xatol": 1e-8, "fatol": 1e-8})
    return dict(mu=float(res.x[0]), sigma=float(math.exp(res.x[1])), loglik=-float(res.fun), n=sum(b.n for b in t))


def expected_counts(bins, x_min, model):
    t = _tail(bins, x_min)
    n = sum(b.n for b in t)
    if "alpha" in model:
        return [n * _pareto_p(b, x_min, model["alpha"]) for b in t]
    return [n * _lognorm_p(b, x_min, model["mu"], model["sigma"]) for b in t]


def chi2(bins, expected):
    obs = [b.n for b in bins][-len(expected):]
    return float(sum((o - e) ** 2 / e for o, e in zip(obs, expected, strict=True)))


def ccdf(bins):
    tot = sum(b.n for b in bins)
    out, above = [], tot
    for b in sorted(bins, key=lambda b: b.lo):
        out.append((b.lo, above / tot))
        above -= b.n
    return out


def sample_pareto(n, x_min, alpha, rng):
    """Integer firm sizes from a Pareto tail (for tests of the fit)."""
    return np.floor((x_min - 0.5) * (1 - rng.random(n)) ** (-1 / alpha) + 0.5).astype(int)
