"""firm.crisisdrill -- an hourly liquidity drill: a volatility shock that raises margin everywhere, a prime broker that
fails with part of the firm's assets trapped, a credit line withdrawn, and the actions that buy time (build of One
Quant Book 16, chapter 27).

Each account holds collateral against a requirement that the scenario scales hour by hour; a shortfall is paid from
unencumbered cash when it arises (firm.treasury's rule, hour by hour). A failed broker's account stops: a share of
the collateral it held is trapped, the rest comes back after a delay, and its positions move to another account,
whose requirement rises accordingly. Actions add cash or cut requirements after a delay, at a cost; the survival
horizon is the first hour cash is negative. The greedy optimiser adds, one at a time, the action with the lowest
cost per hour of survival gained until the target is met.

API (stable):
    Account(name, held, base_req) ; Scenario(...) ; Action(name, hour_cash, cut, delay, cost, deadline)
    run(accounts, cash0, scenario, actions, hours) -> dict(cash, calls, horizon) ; greedy(accounts, cash0, scenario,
    menu, target, hours) -> (chosen actions, result)
"""
from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Account:
    name: str
    held: float
    base_req: float


@dataclass(frozen=True)
class Scenario:
    house_mult: tuple                   # multiplier on prime-broker requirements, one value per hour
    clearing_mult: tuple                # multiplier on the clearing account's requirement, per hour
    clearing: str = "FCM"
    failed: str | None = None           # the broker that fails
    fail_hour: int = 0
    trapped: float = 0.0                # share of the failed broker's collateral trapped
    return_hour: int = 0                # when the untrapped rest comes back
    moved_to: str | None = None         # the account that takes over the failed broker's positions


@dataclass(frozen=True)
class Action:
    name: str
    cash: float = 0.0                   # cash added when the action completes
    cut: float = 0.0                    # share of all requirements removed when it completes
    delay: int = 0                      # hours from the start of the drill to completion
    cost: float = 0.0                   # $ cost of the action
    deadline: int | None = None         # hour after which the action is no longer available (a withdrawn line)
    tags: tuple = field(default_factory=tuple)


def run(accounts, cash0, sc, actions=(), hours=72):
    held = {a.name: a.held for a in accounts}
    base = {a.name: a.base_req for a in accounts}
    alive = {a.name: True for a in accounts}
    cash, calls = cash0, 0.0
    path, callpath = [], []
    for h in range(hours):
        cut = sum(a.cut for a in actions if a.delay <= h and (a.deadline is None or a.delay <= a.deadline))
        for a in actions:
            if a.delay == h and (a.deadline is None or a.delay <= a.deadline):
                cash += a.cash
        if sc.failed and h == sc.fail_hour:
            alive[sc.failed] = False
            if sc.moved_to:
                base[sc.moved_to] += base[sc.failed]
        if sc.failed and h == sc.return_hour:
            cash += held[sc.failed] * (1 - sc.trapped)
        call_h = 0.0
        for n in held:
            if not alive[n]:
                continue
            mult = sc.clearing_mult[h] if n == sc.clearing else sc.house_mult[h]
            req = base[n] * mult * max(0.0, 1 - cut)
            short = req - held[n]
            if short > 0:
                held[n] += short
                cash -= short
                call_h += short
            elif short < -1e-9 and n == sc.clearing:
                held[n] += short                   # the clearing account returns excess daily variation
                cash -= short
        calls += call_h
        path.append(cash)
        callpath.append(call_h)
    path = np.array(path)
    neg = np.nonzero(path < 0)[0]
    return {"cash": path, "calls": np.array(callpath), "horizon": int(neg[0]) if len(neg) else hours,
            "total_calls": calls, "cost": sum(a.cost for a in actions)}


def greedy(accounts, cash0, sc, menu, target=72, hours=72):
    chosen = []
    res = run(accounts, cash0, sc, chosen, hours)
    while res["horizon"] < target:
        best, best_ratio, best_res = None, None, None
        for a in menu:
            if a in chosen:
                continue
            r = run(accounts, cash0, sc, chosen + [a], hours)
            gain = r["horizon"] - res["horizon"]
            if gain <= 0:
                continue
            ratio = a.cost / gain
            if best_ratio is None or ratio < best_ratio:
                best, best_ratio, best_res = a, ratio, r
        if best is None:
            break
        chosen.append(best)
        res = best_res
    return chosen, res
