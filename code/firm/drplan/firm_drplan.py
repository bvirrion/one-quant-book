"""firm.drplan -- a disaster-recovery plan as data, and its recovery time and point (build of One Quant Book 14,
chapter 28).

A plan has a primary and a recovery site (from data/networks/sites.csv through firm.geomap), a replication mode and a
runbook: steps with lognormal durations (median and spread, stated assumptions) run in sequence. The recovery time is
the sum of the steps; the recovery point is what replication loses: nothing if synchronous, the replication lag if
asynchronous, up to the snapshot interval if restored from snapshots. Checks: the recovery site outside a hazard
radius around the primary, the recovery time against a target, the last test within a period. The industry test
calendar is dated data (data/test_calendar.csv). Results are a labelled simulation.

API (stable):
    Step(name, median_min, sigma) ; Plan(name, primary, recovery, steps, replication, lag_ms=0.0, snapshot_min=0.0,
                                         annual_cost=0.0)
    separation_km(a, b, table) ; outside_hazard(plan, radius_km, table) -> bool
    rto_samples(plan, n=100000, seed=0) -> minutes ; p_within(plan, target_min, n, seed)
    rpo(plan, table) -> worst data loss in seconds (sync 0; async lag plus one-way floor; snapshot interval)
    sync_penalty_ms(plan, table, factor=1.5) -> round trip added to every write by synchronous replication
    tested_within(last_test, today, months=12) -> bool ; load_calendar(path)
"""
import csv
import datetime as dt
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "geomap"))
import firm_geomap as gm  # noqa: E402


@dataclass(frozen=True)
class Step:
    name: str
    median_min: float
    sigma: float


@dataclass(frozen=True)
class Plan:
    name: str
    primary: str
    recovery: str
    steps: tuple
    replication: str          # "sync", "async" or "snapshot"
    lag_ms: float = 0.0
    snapshot_min: float = 0.0
    annual_cost: float = 0.0


def separation_km(a, b, table):
    s, t = table[a], table[b]
    return gm.geodesic_m(s.lat, s.lon, t.lat, t.lon) / 1000.0


def outside_hazard(plan, radius_km, table):
    return separation_km(plan.primary, plan.recovery, table) > radius_km


def rto_samples(plan, n=100000, seed=0):
    rng = np.random.default_rng(seed)
    total = np.zeros(n)
    for s in plan.steps:
        total += s.median_min * np.exp(s.sigma * rng.standard_normal(n))
    return total


def p_within(plan, target_min, n=100000, seed=0):
    return float(np.mean(rto_samples(plan, n, seed) <= target_min))


def rpo(plan, table):
    if plan.replication == "sync":
        return 0.0
    if plan.replication == "async":
        d = separation_km(plan.primary, plan.recovery, table) * 1000.0
        return (plan.lag_ms + gm.floor_us(d, "fibre") / 1000.0) / 1000.0
    return plan.snapshot_min * 60.0


def sync_penalty_ms(plan, table, factor=1.5):
    d = separation_km(plan.primary, plan.recovery, table) * 1000.0
    return 2 * gm.floor_us(d, "fibre") * factor / 1000.0


def tested_within(last_test, today, months=12):
    y, m = today.year, today.month - months
    while m <= 0:
        y, m = y - 1, m + 12
    return last_test >= dt.date(y, m, min(today.day, 28))


def load_calendar(path=HERE / "data" / "test_calendar.csv"):
    with open(path) as f:
        return list(csv.DictReader(f))
