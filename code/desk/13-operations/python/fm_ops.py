"""One Quant Book 16, chapter 13: sizing an operations team for a settlement cycle (illustrative).

120 breaks a day arrive over an eight-hour day (15 an hour) and take 40 minutes of work each on average
(exponential): an M/M/c queue (firm.opsmetrics, on firm.queues). A break must be resolved within 10 working hours
under a two-day cycle and within 2.5 under a one-day cycle (before the evening affirmation cut-off). Half of the
late breaks become settlement fails, each on a $5 million trade, failing for two days, at a penalty of 1 basis
point a day (an input: the EU rate for liquid shares) plus an internal cost of $1,500 (claims, funding, handling).
A person costs $120,000 a year; 250 working days.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/opsmetrics"))
import firm_opsmetrics as om  # noqa: E402

BREAKS, HOURS, WORK_H = 120, 8.0, 40 / 60
LAM, MU = BREAKS / HOURS, 1 / WORK_H
DEADLINE = {"T+2": 10.0, "T+1": 2.5}
P_FAIL, VALUE, PENALTY_BP, FAIL_DAYS, INTERNAL = 0.5, 5e6, 1.0, 2, 1500.0
STAFF_COST, DAYS = 120e3, 250
EDGES = [0.0, 0.5, 1.0, 2.0, 4.0]


def year(c, cycle, lam=LAM, mu=MU):
    """Late share, fails a year, fail cost and total cost ($ million) for a team of c."""
    late = om.p_late(lam, mu, c, DEADLINE[cycle])
    fails = late * lam * HOURS * DAYS * P_FAIL
    fc = om.fail_cost(fails, VALUE, PENALTY_BP, FAIL_DAYS, INTERNAL) / 1e6
    return {"late": late, "fails": fails, "fail_cost": fc, "total": fc + c * STAFF_COST / 1e6}


def table(cycle, lam=LAM, mu=MU, extra=6):
    """Teams from the smallest stable one to `extra` more."""
    c0 = int(lam / mu) + 1
    return {c: year(c, cycle, lam, mu) for c in range(c0, c0 + extra)}


def staff95(cycle, lam=LAM, mu=MU):
    return om.staff_for(lam, mu, DEADLINE[cycle], 0.95)


def cheapest(cycle, lam=LAM, mu=MU):
    t = table(cycle, lam, mu)
    return min(t, key=lambda c: t[c]["total"])


def ageing(c):
    return om.ageing(LAM, MU, c, EDGES)


def collateral():
    csa = om.Csa(threshold=10.0, mta=0.5)
    ours, theirs, held = 25.3, 24.4, 14.6
    return om.call(ours, held, csa), om.call(theirs, held, csa), om.disputed(ours, theirs, 0.02)


def daily_report():
    metrics = {"breaks older than one day": 14, "fail rate (%)": 2.4, "affirmed on trade date (%)": 93.0,
               "disputed calls": 1}
    limits = {"breaks older than one day": (10, 25), "fail rate (%)": (2.0, 4.0),
              "affirmed on trade date (%)": (95.0, 90.0), "disputed calls": (2, 5)}
    return om.report(metrics, limits)


SCENARIOS = {"T+2": ("T+2", LAM, MU), "T+1": ("T+1", LAM, MU), "T+1, half the breaks": ("T+1", LAM / 2, MU),
             "T+1, 30-minute work": ("T+1", LAM, 2.0)}


def scenarios():
    """For each scenario: the cheapest team, its staff cost, fail cost and total ($ million)."""
    out = {}
    for name, (cy, lam, mu) in SCENARIOS.items():
        c = cheapest(cy, lam, mu)
        y = year(c, cy, lam, mu)
        out[name] = {"team": c, "staff": c * STAFF_COST / 1e6, "fail_cost": y["fail_cost"], "total": y["total"],
                     "staff95": staff95(cy, lam, mu)}
    return out
