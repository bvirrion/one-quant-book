"""firm.entryplan -- an entry into a new market as workstreams with durations, costs and dependencies: the critical
path and slack, the cost schedule, revenue ramps, net present value, and the value of staging with a kill point
(build of One Quant Book 16, chapter 24).

Critical-path method: each task starts when all its predecessors finish (earliest start); the project's length is
the longest path; a task's slack is how late it can finish without delaying the end. Costs accrue evenly over each
task's months. After the first trade, revenue ramps as R (1 - exp(-t / tau)) against a running cost. Staging: at a
kill point after k months of trading the firm sees a noisy estimate of R and stops if it is below a threshold,
saving the remaining running costs.

API (stable):
    Task(name, months, monthly_cost, after) ; schedule(tasks) -> {name: (early start, early finish, slack)}
    critical_path(tasks) ; cost_by_month(tasks) ; npv(cash, annual_rate) ; irr(cash)
    entry_cash(tasks, first_trade, R, tau, run_cost, horizon) ; staged_npv(...) -> (values without, with)
"""
import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Task:
    name: str
    months: float
    monthly_cost: float = 0.0
    after: tuple = ()


def schedule(tasks):
    by = {t.name: t for t in tasks}
    es, ef = {}, {}

    def finish(n):
        if n not in ef:
            t = by[n]
            es[n] = max((finish(p) for p in t.after), default=0.0)
            ef[n] = es[n] + t.months
        return ef[n]

    end = max(finish(n) for n in by)
    lf = {n: end for n in by}
    for n in sorted(by, key=lambda x: -ef[x]):          # latest finish: min over successors' latest start
        for s in by.values():
            if n in s.after:
                lf[n] = min(lf[n], lf[s.name] - s.months)
    return {n: (es[n], ef[n], lf[n] - ef[n]) for n in by}


def critical_path(tasks):
    """Tasks with zero slack, in order of their earliest start."""
    sch = schedule(tasks)
    return [n for n, (s, _, sl) in sorted(sch.items(), key=lambda x: (x[1][0], x[1][1])) if abs(sl) < 1e-9]


def cost_by_month(tasks, horizon):
    sch = schedule(tasks)
    out = np.zeros(horizon)
    for t in tasks:
        s, f, _ = sch[t.name]
        for m in range(horizon):
            overlap = max(0.0, min(f, m + 1) - max(s, m))
            out[m] += overlap * t.monthly_cost
    return out


def npv(cash, annual_rate):
    r = (1 + annual_rate) ** (1 / 12) - 1
    return float(sum(c / (1 + r) ** (m + 1) for m, c in enumerate(cash)))


def irr(cash, lo=-0.99, hi=10.0, tol=1e-10):
    """Annual internal rate of return by bisection; None if the NPV does not change sign on [lo, hi]."""
    f = lambda a: npv(cash, a)  # noqa: E731
    if f(lo) * f(hi) > 0:
        return None
    while hi - lo > tol:
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(lo) * f(mid) > 0 else (lo, mid)
    return (lo + hi) / 2


def entry_cash(tasks, first_trade, R, tau, run_cost, horizon, stop=None):
    """Monthly cash: minus set-up costs, then after the first trade revenue R (1 - exp(-t/tau)) less running cost,
    until `stop` (a month index) if the entry is killed."""
    cash = -cost_by_month(tasks, horizon)
    for m in range(horizon):
        t = m + 1 - first_trade
        if t > 0 and (stop is None or m < stop):
            cash[m] += R * (1 - math.exp(-t / tau)) - run_cost
    return cash


def staged_npv(tasks, first_trade, Rs, tau, run_cost, horizon, rate, kill_after, threshold, noise, seed=0):
    """For each true steady-state revenue in Rs: the NPV without staging, and with a kill point after `kill_after`
    months of trading, where the firm observes R with multiplicative noise and stops if the estimate is below
    `threshold`. Returns (npv without, npv with, killed flags)."""
    rng = np.random.default_rng(seed)
    stop_month = int(math.ceil(first_trade)) + kill_after
    plain, staged, killed = [], [], []
    for R in Rs:
        plain.append(npv(entry_cash(tasks, first_trade, R, tau, run_cost, horizon), rate))
        est = R * math.exp(noise * rng.standard_normal())
        k = est < threshold
        killed.append(k)
        staged.append(npv(entry_cash(tasks, first_trade, R, tau, run_cost, horizon, stop_month if k else None), rate))
    return np.array(plain), np.array(staged), np.array(killed)
