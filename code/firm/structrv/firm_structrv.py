"""firm.structrv -- structural relative value (build of One Quant Book 8, chapter 12).

Securities whose value is tied by a structure to other securities: a closed-end fund or a holding company and the assets
it holds, two share classes of one company, a SPAC and the cash in its trust. The discount (the log of price over the
value of what stands behind it) follows a mean-reverting process with a long-run level below zero, and can be closed at
once by a catalyst (a tender, a liquidation, an activist) arriving at a Poisson rate. The trade buys the discounted
security and sells what stands behind it: it earns the discount's narrowing less carry. A SPAC unit is worth the trust
(which grows at the rate the trust earns) with a call on the merged company. NumPy only.

API (stable):
    simulate_discount(d0, mean, half_life, vol, days, catalyst_rate, catalyst_level, paths, rng)
                                                 (discount paths (paths, days + 1), catalyst day or -1 per path)
    discount_trade(paths, catalyst_day, close_level, carry, horizon)
                                                 per path: log return of the hedged trade at exit, and the exit day (the
                                                 first day the discount reaches close_level or a catalyst, else horizon)
    spac_payoff(trust_at_vote, merged_value)     per share: max(redeem at trust, keep the merged share)
    spac_return(price, trust, rate, days, merged_value)
                                                 return of buying at price and choosing at the vote
"""
from __future__ import annotations

import math

import numpy as np


def simulate_discount(d0: float, mean: float, half_life: float, vol: float, days: int, catalyst_rate: float = 0.0,
                      catalyst_level: float = -0.02, paths: int = 10000, rng=None):
    rng = rng or np.random.default_rng(12)
    phi = 0.5 ** (1 / half_life)
    sd = vol / math.sqrt(252)
    D = np.empty((paths, days + 1))
    D[:, 0] = d0
    hit = rng.random((paths, days)) < catalyst_rate / 252
    cat = np.where(hit.any(axis=1), hit.argmax(axis=1) + 1, -1)
    for t in range(1, days + 1):
        D[:, t] = mean + phi * (D[:, t - 1] - mean) + sd * rng.standard_normal(paths)
        done = cat == t
        D[done, t] = catalyst_level
        after = (cat > 0) & (cat < t)
        D[after, t] = catalyst_level
    return D, cat


def discount_trade(paths, catalyst_day, close_level: float, carry: float, horizon: int):
    D = np.asarray(paths, float)
    reach = D[:, 1:horizon + 1] >= close_level
    first = np.where(reach.any(axis=1), reach.argmax(axis=1) + 1, horizon)
    cat = np.asarray(catalyst_day)
    exit_day = np.where((cat > 0) & (cat < first), cat, first)
    ret = D[np.arange(len(D)), exit_day] - D[:, 0] - carry * exit_day / 252
    return ret, exit_day


def spac_payoff(trust_at_vote: float, merged_value):
    return np.maximum(trust_at_vote, np.asarray(merged_value, float))


def spac_return(price: float, trust: float, rate: float, days: int, merged_value):
    return spac_payoff(trust * math.exp(rate * days / 252), merged_value) / price - 1
