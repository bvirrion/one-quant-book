"""One Quant Book 16, chapter 24: an entry plan for a futures market in a new region ($ thousand, months; illustrative).

Workstreams and dependencies follow the hook: the clearing agreement cannot start before the legal entity has its
identifier, and the exchange will not certify the software before the clearing firm has set the firm's limits.
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/entryplan"))
import firm_entryplan as ep  # noqa: E402

TASKS = [
    ep.Task("legal entity", 2.0, 25.0),
    ep.Task("legal entity identifier", 0.5, 2.0, ("legal entity",)),
    ep.Task("regulatory registration", 4.0, 30.0, ("legal entity",)),
    ep.Task("clearing agreement", 5.0, 20.0, ("legal entity identifier",)),
    ep.Task("clearing limits set", 0.5, 5.0, ("clearing agreement",)),
    ep.Task("exchange membership", 3.0, 15.0, ("regulatory registration",)),
    ep.Task("connectivity", 3.0, 40.0, ("legal entity",)),
    ep.Task("market data licences", 2.0, 10.0, ("legal entity",)),
    ep.Task("hires", 4.0, 60.0),
    ep.Task("software adaptation", 3.0, 80.0, ("hires",)),
    ep.Task("certification", 1.0, 10.0, ("clearing limits set", "exchange membership", "connectivity",
                                         "software adaptation")),
    ep.Task("first trade", 0.0, 0.0, ("certification", "market data licences")),
]
PLAN_MONTHS = 8.0
HORIZON, RATE, TAU, RUN = 36, 0.10, 4.0, 250.0     # months; annual discount rate; ramp time constant; running cost
SCENARIOS = {"weak": 150.0, "base": 450.0, "strong": 800.0}   # steady-state monthly revenue
KILL_AFTER, THRESHOLD, NOISE = 6, 250.0, 0.25


def plan():
    return ep.schedule(TASKS), ep.critical_path(TASKS)


def first_trade():
    return plan()[0]["first trade"][1]


def scenario_npvs():
    ft = first_trade()
    return {k: ep.npv(ep.entry_cash(TASKS, ft, R, TAU, RUN, HORIZON), RATE) for k, R in SCENARIOS.items()}


def revenue_draws(n=4000, seed=24):
    """Steady-state monthly revenue: lognormal around the base case (median 400, dispersion 0.6)."""
    return 400.0 * np.exp(0.6 * np.random.default_rng(seed).standard_normal(n))


def staging(n=4000, seed=24):
    Rs = revenue_draws(n, seed)
    plain, staged, killed = ep.staged_npv(TASKS, first_trade(), Rs, TAU, RUN, HORIZON, RATE, KILL_AFTER, THRESHOLD,
                                          NOISE, seed + 1)
    return {"plain": plain, "staged": staged, "killed": killed, "R": Rs}


def threshold_curve(thresholds=tuple(range(0, 701, 50)), n=4000, seed=24):
    Rs = revenue_draws(n, seed)
    base = None
    out = []
    for th in thresholds:
        plain, staged, killed = ep.staged_npv(TASKS, first_trade(), Rs, TAU, RUN, HORIZON, RATE, KILL_AFTER, th,
                                              NOISE, seed + 1)
        base = plain.mean()
        out.append((th, staged.mean() - base, killed.mean()))
    return out
