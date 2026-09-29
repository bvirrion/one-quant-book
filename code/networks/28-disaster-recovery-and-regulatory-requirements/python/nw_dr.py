"""Chapter 28 of One Quant Book 14: the two-hour rule for a trading firm (firm.drplan, labelled simulation).

    SITES, CANDIDATES          the primary in Secaucus NY5 and candidate recovery sites, with their separation
    HOT, WARM                  two recovery designs: runbooks (stated durations), replication and yearly cost
    results()                  probability of resuming within two hours, recovery points, costs
    rto_hist()                 the recovery-time distributions for the figure
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "drplan"))
import firm_drplan as dr  # noqa: E402

SITES = {s.id: s for s in dr.gm.load_sites(ROOT / "data" / "networks" / "sites.csv")}
PRIMARY = "ny5"
CANDIDATES = ("ny4", "carteret", "mahwah", "aurora")
HAZARD_KM = 100.0                 # radius of a regional event around the primary (assumption)
TARGET_MIN = 120.0
PRIMARY_COST = 3190.0             # thousand USD a year: chapter 27's example stack
S = dr.Step
HOT = dr.Plan("hot", PRIMARY, "aurora",
              (S("detect and decide", 15, 0.5), S("switch sessions to recovery addresses", 10, 0.4),
               S("reconcile orders and positions", 20, 0.5), S("check venue connectivity", 10, 0.4),
               S("resume trading", 5, 0.3)),
              "async", lag_ms=50.0, annual_cost=0.70 * PRIMARY_COST)
WARM = dr.Plan("warm", PRIMARY, "aurora",
               (S("detect and decide", 15, 0.5), S("start servers and restore", 45, 0.6),
                S("load reference data and positions", 30, 0.5),
                S("reconnect and verify sessions", 20, 0.5),
                S("reconcile orders and positions", 20, 0.5), S("resume trading", 5, 0.3)),
               "snapshot", snapshot_min=15.0, annual_cost=0.25 * PRIMARY_COST)


def separations():
    return {c: dr.separation_km(PRIMARY, c, SITES) for c in CANDIDATES}


def results():
    out = {}
    for p in (HOT, WARM):
        x = dr.rto_samples(p)
        out[p.name] = {"p2h": float(np.mean(x <= TARGET_MIN)), "median": float(np.median(x)),
                       "p95": float(np.quantile(x, 0.95)), "rpo_s": dr.rpo(p, SITES), "cost": p.annual_cost}
    return out


def rto_hist(edges=tuple(range(0, 301, 10))):
    return {p.name: np.histogram(dr.rto_samples(p), bins=edges)[0] / 100000.0 for p in (HOT, WARM)}
