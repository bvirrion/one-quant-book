"""firm.podshop -- the economics of a multi-manager platform (build of One Quant Book 16, chapter 3).

Pods trade on capital the platform allocates. Each pod's portfolio manager is paid a share of the pod's own
annual profit, losses carried forward against that pod's later profits and never netted against other pods'.
The fund bears every pod's costs and the platform's (pass-through), and pays the manager a performance
allocation on what is left. Netting risk is what the pods' payouts cost beyond the same rate applied to the
fund's total profit. A centre book can hedge the pods' summed exposure to shared factors (a factor overlay), and
a de-risking ladder can halve and then stop a pod after drawdowns.

All P&L is in fractions of each pod's allocated capital (1 = the pod's capital), daily or annual.
Self-contained NumPy; the drawdown statistics reuse firm.multistrat's stop_rate where a chapter needs them.

API (stable):
    pods(n, years, sr, vol, rho, rng, days=252, beta=None) -> dict(daily (T, n), factor (T,), beta (n,))
    annual(daily, days=252) -> (years, n)
    payouts(annual, rate, carry, fire) -> (years, n)      per-pod payout, losses carried forward (no clawback);
                                                          fire: a team losing more is replaced, its carry reset
    netting_cost(annual, rate, carry, fire) -> (years,)   pod payouts minus rate * max(fund profit, 0)
    expected_positive(mu, sigma) -> E[max(X, 0)], X ~ N(mu, sigma^2)
    Terms(payout_rate, pod_cost, platform_cost, mgr_perf); waterfall(annual, terms) -> dict of totals per pod-year
    classic(annual, mgmt=0.02, perf=0.20) -> dict      the same pods under a management plus performance fee
    ladder(daily, cut, stop, days=252) -> (daily after ladder, events)
    overlay(daily, beta, factor) -> daily fund P&L with the summed factor exposure hedged
"""
import math
from dataclasses import dataclass

import numpy as np


def pods(n: int, years: int, sr: float, vol: float, rho: float, rng, days: int = 252, beta=None) -> dict:
    """Daily pod returns: mean sr * vol / days, volatility vol / sqrt(days); pairwise correlation rho through one
    shared factor (each pod's loading sqrt(rho), or `beta` if given, in units of the pod's volatility)."""
    T = years * days
    d = vol / math.sqrt(days)
    b = np.full(n, math.sqrt(rho)) if beta is None else np.asarray(beta, float)
    f = rng.standard_normal(T)
    own = np.sqrt(np.maximum(1 - b ** 2, 0.0))
    daily = sr * vol / days + d * (np.outer(f, b) + own * rng.standard_normal((T, n)))
    return {"daily": daily, "factor": d * f, "beta": b}


def annual(daily: np.ndarray, days: int = 252) -> np.ndarray:
    T, n = daily.shape
    return daily[: (T // days) * days].reshape(T // days, days, n).sum(1)


def payouts(ann: np.ndarray, rate: float, carry: bool = True, fire: float | None = None) -> np.ndarray:
    """Each pod: rate * (profit above the losses it carries forward); carried losses are reduced by profits;
    nothing is clawed back and other pods' results do not count. carry=False pays on each year alone. With
    `fire`, a pod that loses more than `fire` in a year is replaced by a new team, whose carried loss starts at 0."""
    years, n = ann.shape
    c = np.zeros(n)
    out = np.zeros((years, n))
    for t in range(years):
        net = ann[t] - c if carry else ann[t]
        out[t] = rate * np.maximum(net, 0.0)
        c = np.maximum(-net, 0.0) if carry else c
        if fire is not None:
            c[ann[t] < -fire] = 0.0
    return out


def netting_cost(ann: np.ndarray, rate: float, carry: bool = True, fire: float | None = None) -> np.ndarray:
    """What the pods' payouts cost each year beyond rate * max(total profit, 0)."""
    return payouts(ann, rate, carry, fire).sum(1) - rate * np.maximum(ann.sum(1), 0.0)


def expected_positive(mu: float, sigma: float) -> float:
    """E[max(X, 0)] for X ~ N(mu, sigma^2): mu Phi(mu/sigma) + sigma phi(mu/sigma)."""
    z = mu / sigma
    return mu * 0.5 * (1 + math.erf(z / math.sqrt(2))) + sigma * math.exp(-z * z / 2) / math.sqrt(2 * math.pi)


@dataclass(frozen=True)
class Terms:
    payout_rate: float = 0.20      # share of each pod's own profit paid to its team
    pod_cost: float = 0.020        # pass-through costs of a pod a year (salaries, data, systems), per unit capital
    platform_cost: float = 0.010   # the platform's own passed-through costs a year, per unit capital
    mgr_perf: float = 0.20         # the manager's performance allocation on the fund's net profit


def waterfall(ann: np.ndarray, terms: Terms, fire: float | None = None) -> dict:
    """Totals per pod-year, in units of pod capital: gross, payouts, pass-through costs, manager, investor."""
    years, n = ann.shape
    gross = ann.sum(1)
    pay = payouts(ann, terms.payout_rate, True, fire).sum(1)
    costs = np.full(years, n * (terms.pod_cost + terms.platform_cost))
    pre = gross - pay - costs
    mgr = terms.mgr_perf * np.maximum(pre, 0.0)
    inv = pre - mgr
    k = years * n
    return {"gross": gross.sum() / k, "payouts": pay.sum() / k, "costs": costs.sum() / k, "manager": mgr.sum() / k,
            "investor": inv.sum() / k, "investor_years": inv / n, "loss_years": int((inv < 0).sum())}


def classic(ann: np.ndarray, mgmt: float = 0.02, perf: float = 0.20) -> dict:
    """The same pods inside a fund charging a management fee and a performance fee on the net (the manager pays
    the teams and the costs out of its fees)."""
    years, n = ann.shape
    gross = ann.sum(1) / n
    pre = gross - mgmt
    fee = perf * np.maximum(pre, 0.0)
    inv = pre - fee
    return {"gross": gross.mean(), "fees": mgmt + fee.mean(), "investor": inv.mean(), "investor_years": inv}


def ladder(daily: np.ndarray, cut: float, stop: float, days: int = 252):
    """Per pod: after a drawdown of `cut` (fraction of the pod's starting capital) from its peak within the year,
    capital is halved; after `stop` the pod is stopped until the next year, when it restarts at full size."""
    T, n = daily.shape
    out = np.zeros_like(daily)
    events = []
    size = np.ones(n)
    eq = np.zeros(n)
    peak = np.zeros(n)
    for t in range(T):
        if t % days == 0:
            size[:] = 1.0
            eq[:] = 0.0
            peak[:] = 0.0
        out[t] = size * daily[t]
        eq += out[t]
        peak = np.maximum(peak, eq)
        dd = peak - eq
        for i in np.flatnonzero((size == 1.0) & (dd > cut)):
            size[i] = 0.5
            events.append(("cut", i, t))
        for i in np.flatnonzero((size > 0) & (dd > stop)):
            size[i] = 0.0
            events.append(("stop", i, t))
    return out, events


def overlay(daily: np.ndarray, beta: np.ndarray, factor: np.ndarray) -> np.ndarray:
    """The fund's daily P&L (per unit of capital, equal-weighted pods) with its summed factor exposure hedged:
    the centre book holds -mean(beta) of the factor (in pod-volatility units, the factor path is its return)."""
    fund = daily.mean(1)
    return fund - float(np.mean(beta)) * factor
