"""firm.deskplan -- a desk's annual plan, its risk appetite and its chance of meeting its budget
(build of One Quant Book 16, chapter 6).

A desk runs several businesses, each with an expected annual revenue and a volatility, correlated. Revenue is
modelled as normal over the year (daily increments, so drawdowns can be read off the path). The plan sets a
revenue budget; the costs are the desk's direct fixed costs, costs allocated to it by the firm, and variable pay.
The risk-appetite cascade turns a loss the firm will bear in a bad year into a volatility budget, a daily
value-at-risk limit and stop limits by business. Amounts in one currency (the chapter uses $ millions a year).

API (stable):
    Business(name, mu, sigma); Plan(businesses, corr, direct_cost, allocated_cost, var_pay, budget)
    plan_stats(plan) -> dict(mu, sigma, sharpe)
    p_meet(plan) -> probability that revenue meets the budget (closed form)
    risk_multiple(plan, prob) -> scale of every position needed to meet the budget with probability prob
    simulate(plan, n, rng, days=252) -> dict(annual revenue (n,), max drawdown (n,), daily paths are not kept)
    cascade(plan, loss_tolerance, conf=0.95, var_conf=0.99, days=252) -> dict(vol_budget, daily_var, stops)
    plan_vs_actual(plan, actual_monthly) -> rows of month, plan, actual, lower, upper (one-sigma band)
"""
import math
from dataclasses import dataclass

import numpy as np


def _phi(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def _inv_phi(p: float) -> float:
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if _phi(mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


@dataclass(frozen=True)
class Business:
    name: str
    mu: float        # expected revenue a year
    sigma: float     # volatility of revenue a year


@dataclass(frozen=True)
class Plan:
    businesses: tuple
    corr: tuple                # correlation matrix as nested tuples
    direct_cost: float
    allocated_cost: float
    var_pay: float             # variable pay per unit of positive revenue after costs
    budget: float              # revenue budget


def _cov(plan: Plan) -> np.ndarray:
    s = np.array([b.sigma for b in plan.businesses])
    return np.outer(s, s) * np.array(plan.corr, float)


def plan_stats(plan: Plan) -> dict:
    mu = sum(b.mu for b in plan.businesses)
    sigma = math.sqrt(float(np.ones(len(plan.businesses)) @ _cov(plan) @ np.ones(len(plan.businesses))))
    return {"mu": mu, "sigma": sigma, "sharpe": mu / sigma}


def p_meet(plan: Plan) -> float:
    s = plan_stats(plan)
    return 1 - _phi((plan.budget - s["mu"]) / s["sigma"])


def risk_multiple(plan: Plan, prob: float) -> float:
    """Scale lambda of every position (mean and volatility both scale) so that P(revenue >= budget) = prob:
    lambda (mu - z sigma) = budget, possible only if the desk's Sharpe ratio exceeds z = Phi^-1(prob)."""
    s = plan_stats(plan)
    z = _inv_phi(prob)
    edge = s["mu"] - z * s["sigma"]
    if edge <= 0:
        return math.inf
    return plan.budget / edge


def simulate(plan: Plan, n: int, rng, days: int = 252) -> dict:
    """n simulated years of daily revenue for the whole desk: annual totals and maximum drawdowns."""
    s = plan_stats(plan)
    d = rng.normal(s["mu"] / days, s["sigma"] / math.sqrt(days), (n, days))
    path = np.cumsum(d, axis=1)
    peak = np.maximum.accumulate(np.maximum(path, 0.0), axis=1)
    return {"annual": path[:, -1], "max_drawdown": (peak - path).max(1)}


def cascade(plan: Plan, loss_tolerance: float, conf: float = 0.95, var_conf: float = 0.99, days: int = 252) -> dict:
    """The firm bears a loss of at most loss_tolerance in a 1-in-(1/(1-conf)) year. With the desk's expected
    revenue mu, the volatility budget is (mu + L) / z_conf; the daily VaR limit is z_var * vol_budget / sqrt(days);
    each business's stop is its share of the volatility budget (by its own sigma) times the loss tolerance."""
    s = plan_stats(plan)
    vol = (s["mu"] + loss_tolerance) / _inv_phi(conf)
    sig = np.array([b.sigma for b in plan.businesses])
    stops = {b.name: loss_tolerance * w for b, w in zip(plan.businesses, sig / sig.sum(), strict=True)}
    return {"vol_budget": vol, "scale": vol / s["sigma"], "daily_var": _inv_phi(var_conf) * vol / math.sqrt(days),
            "stops": stops}


def plan_vs_actual(plan: Plan, actual_monthly) -> list:
    """Cumulative plan (the budget spread evenly) against cumulative actual revenue, with a one-sigma band."""
    s = plan_stats(plan)
    rows, cum = [], 0.0
    for m, a in enumerate(actual_monthly, start=1):
        cum += a
        p = plan.budget * m / 12
        band = s["sigma"] * math.sqrt(m / 12)
        rows.append({"month": m, "plan": p, "actual": cum, "lower": p - band, "upper": p + band})
    return rows
