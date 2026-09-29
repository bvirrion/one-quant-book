"""firm.tokencomp -- what a grant of tokens is worth to the employee (build of One Quant Book 17, chapter 10).

A grant of tokens vests on a schedule (a cliff, then monthly); each vested tranche may be sold only after a lock-up, and
tax is due at vesting on the tranche's value then, paid in cash. The token's price follows a lognormal path with a
stated drift and volatility (parameters, not forecasts). The employee's net outcome is the sale proceeds, times one
minus a liquidity discount, minus the tax paid at vesting. The module simulates the distribution of that outcome,
compares it with the same grant value paid in cash on the same schedule, and reports how often a tranche's tax exceeds
its later proceeds.

API (stable):
    Grant(value0, months=48, cliff=12, lockup=6, tax=0.4, discount=0.0)
    schedule(grant) -> list of (month, fraction vested that month)
    simulate(grant, vol, drift, n, rng) -> dict(net, gross, tax, cash, tax_exceeds) arrays per path
    summary(sim) -> dict of median, p10, p90 of net, cash equivalent, share of paths where tax exceeds proceeds
"""
import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Grant:
    value0: float
    months: int = 48
    cliff: int = 12
    lockup: int = 6
    tax: float = 0.4
    discount: float = 0.0


def schedule(g):
    """A cliff tranche of cliff/months at the cliff, then 1/months each month to the end."""
    out = [(g.cliff, g.cliff / g.months)]
    out += [(m, 1 / g.months) for m in range(g.cliff + 1, g.months + 1)]
    return out


def simulate(g, vol, drift, n, rng):
    horizon = g.months + g.lockup
    dt = 1 / 12
    z = rng.standard_normal((n, horizon))
    logp = np.cumsum((drift - 0.5 * vol ** 2) * dt + vol * math.sqrt(dt) * z, axis=1)
    price = np.exp(np.concatenate([np.zeros((n, 1)), logp], axis=1))  # price relative to grant date, month 0..horizon
    net = np.zeros(n)
    gross = np.zeros(n)
    tax = np.zeros(n)
    exceeds = np.zeros(n)
    for m, frac in schedule(g):
        at_vest = g.value0 * frac * price[:, m]
        at_sale = g.value0 * frac * price[:, m + g.lockup] * (1 - g.discount)
        t = g.tax * at_vest
        gross += at_sale
        tax += t
        exceeds += t > at_sale
        net += at_sale - t
    cash = g.value0 * (1 - g.tax)
    return dict(net=net, gross=gross, tax=tax, cash=cash, tax_exceeds=exceeds / len(schedule(g)))


def summary(sim):
    net = sim["net"]
    return dict(median=float(np.median(net)), p10=float(np.quantile(net, 0.1)), p90=float(np.quantile(net, 0.9)),
                mean=float(net.mean()), cash=float(sim["cash"]), p_below_cash=float((net < sim["cash"]).mean()),
                p_any_tax_exceeds=float((sim["tax_exceeds"] > 0).mean()),
                tranche_tax_exceeds=float(sim["tax_exceeds"].mean()))
