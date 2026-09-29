"""One Quant Book 16, chapter 27: seventy-two hours ($ million, hours; illustrative).

A volatility shock: prime brokers raise house margin by 60 per cent over the first day (firm.treasury.house_path with no
lock-up), the clearing house raises initial margin by 30 per cent at the first daily cycle and 50 per cent at the
second. Prime broker B fails at hour 6: 60 per cent of the collateral it holds is trapped, the rest comes back at hour
48, and its positions move to prime broker A. The firm has $30 million of unencumbered cash.
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/crisisdrill"))
sys.path.insert(0, str(ROOT / "code/firm/treasury"))
import firm_crisisdrill as cd  # noqa: E402
import firm_treasury as tr  # noqa: E402

HOURS = 72
ACCOUNTS = [cd.Account("PB A", 44.0, 40.0), cd.Account("PB B", 33.0, 30.0), cd.Account("FCM", 22.0, 20.0)]
CASH0 = 30.0


def scenario():
    ramp = np.minimum(1.0 + 0.6 * np.arange(HOURS) / 24, 1.6)
    house = tr.house_path(ramp, 0)
    clearing = np.where(np.arange(HOURS) >= 48, 1.5, np.where(np.arange(HOURS) >= 24, 1.3, 1.0))
    return cd.Scenario(tuple(house), tuple(clearing), "FCM", "PB B", 6, 0.6, 48, "PB A")


MENU = [cd.Action("draw the committed line", cash=20.0, delay=2, cost=0.3, deadline=12),
        cd.Action("sell money-market funds", cash=10.0, delay=4, cost=0.02),
        cd.Action("repo the bond portfolio", cash=10.0, delay=8, cost=0.1),
        cd.Action("cut 10% of positions", cut=0.10, delay=3, cost=1.0),
        cd.Action("cut a further 10%", cut=0.10, delay=3, cost=2.0),
        cd.Action("cut a further 10% (third)", cut=0.10, delay=3, cost=3.0)]


def baseline():
    return cd.run(ACCOUNTS, CASH0, scenario(), (), HOURS)


def plan():
    return cd.greedy(ACCOUNTS, CASH0, scenario(), MENU, HOURS, HOURS)


def no_failure():
    sc = scenario()
    sc2 = cd.Scenario(sc.house_mult, sc.clearing_mult, "FCM")
    return cd.run(ACCOUNTS, CASH0, sc2, (), HOURS)


def steps():
    """The greedy plan's actions in order, with the survival horizon and cumulative cost after each."""
    chosen, _ = plan()
    out = []
    for k in range(1, len(chosen) + 1):
        r = cd.run(ACCOUNTS, CASH0, scenario(), chosen[:k], HOURS)
        out.append((chosen[k - 1].name, r["horizon"], sum(a.cost for a in chosen[:k])))
    return out
