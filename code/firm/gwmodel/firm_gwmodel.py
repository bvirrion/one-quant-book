"""firm.gwmodel -- order-entry gateways, sessions and fairness (build of One Quant Book 14, chapter 23).

A race at a market event: every competitor sends its order at the same instant, one copy per session. Under the
parallel design each copy crosses the network to one of several gateways with its own jitter, waits behind the
gateway's queue (background messages plus the race's copies that reached it first, a fixed service time each) and goes
on to the matching engine; the competitor's first copy to arrive counts. Under the segment design every copy enters one
gateway whose order is fixed at its network card, and connections are equal in length to a few nanoseconds, so
arrival order is decided by nanoseconds of cable and extra copies arrive with the first. All parameters are stated
assumptions; the results are a labelled simulation. The session planner prices sessions from dated fee rows
(data/eti_sessions.csv); drop copies are reconciled per session with Book 13's firm.ordergw (wrapped, unchanged).

API (stable):
    Design(kind="parallel"|"segment", gateways=16, net_us=20.0, net_sd_us=1.0, background=2.0, service_us=1.5,
           cable_ns=2.5)
    race(design, sessions, rng) -> (winner index, winning copy's arrival us, a bystander message's latency us)
    win_rate(design, k, others=9, other_sessions=1, n=20000, seed=0) -> (P(win), mean winning arrival, bystander)
    SessionType ; load_sessions(path) ; session_cost(stype, n) ; plan_sessions(tps, types) -> (cost, {type: n})
    both_lost(p_a, p_b, corr=0.0) -> probability a packet is lost on both A and B feeds
    reconcile_sessions(gateways, drop_copy) -> [str]   gateways {session: firm_ordergw.Gateway};
                                                       drop_copy [(session, kind, cl, qty)]
"""
import csv
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ordergw"))
import firm_ordergw as og  # noqa: E402


@dataclass(frozen=True)
class Design:
    kind: str = "parallel"
    gateways: int = 16
    net_us: float = 20.0
    net_sd_us: float = 1.0
    background: float = 2.0
    service_us: float = 1.5
    cable_ns: float = 2.5


def race(design, sessions, rng):
    """sessions: copies per competitor. Returns the winner, the arrival of its first copy (us) and the completion of a
    bystander message reaching a random gateway just after the race's copies (us)."""
    owner = np.repeat(np.arange(len(sessions)), sessions)
    if design.kind == "segment":
        arrive = design.net_us + rng.uniform(-design.cable_ns, design.cable_ns, len(sessions)) / 1000
        queue = rng.poisson(design.background) + int(np.sum(sessions))
        return (int(np.argmin(arrive)), float(arrive.min() + design.service_us),
                float(design.net_us + (queue + 1) * design.service_us))
    gw = np.concatenate([rng.choice(design.gateways, size=s, replace=False) for s in sessions])
    at_gw = design.net_us + design.net_sd_us * rng.standard_normal(len(gw))
    queue = rng.poisson(design.background, design.gateways).astype(float)
    done = np.empty(len(gw))
    for i in np.argsort(at_gw):
        queue[gw[i]] += 1
        done[i] = at_gw[i] + queue[gw[i]] * design.service_us
    best = np.full(len(sessions), np.inf)
    np.minimum.at(best, owner, done)
    by = design.net_us + (queue[rng.integers(design.gateways)] + 1) * design.service_us
    return int(np.argmin(best)), float(best.min()), float(by)


def win_rate(design, k, others=9, other_sessions=1, n=20000, seed=0):
    """P(the firm with k sessions wins), the mean arrival of the winning copy and a bystander's mean latency (us)."""
    rng = np.random.default_rng(seed)
    wins, t, by = 0, 0.0, 0.0
    for _ in range(n):
        w, a, b = race(design, [k] + [other_sessions] * others, rng)
        wins += w == 0
        t += a
        by += b
    return wins / n, t / n, by / n


@dataclass(frozen=True)
class SessionType:
    venue: str
    name: str
    max_tps: int
    first_n: int
    fee_first: float
    fee_after: float


def load_sessions(path=HERE / "data" / "eti_sessions.csv"):
    with open(path) as f:
        return [SessionType(r["venue"], r["session"], int(r["max_tps"]), int(r["first_n"]), float(r["fee_first_eur"]),
                            float(r["fee_after_eur"])) for r in csv.DictReader(f)]


def session_cost(stype, n):
    return min(n, stype.first_n) * stype.fee_first + max(0, n - stype.first_n) * stype.fee_after


def plan_sessions(tps, types, limit=80):
    """Cheapest mix of two session types carrying tps transactions a second, within the session limit."""
    a, b = types
    best = None
    for na in range(limit + 1):
        rest = max(0.0, tps - na * a.max_tps)
        nb = math.ceil(rest / b.max_tps)
        if na + nb <= limit:
            cost = session_cost(a, na) + session_cost(b, nb)
            if best is None or cost < best[0]:
                best = (cost, {a.name: na, b.name: nb})
    return best


def both_lost(p_a, p_b, corr=0.0):
    return p_a * p_b + corr * math.sqrt(p_a * (1 - p_a) * p_b * (1 - p_b))


def reconcile_sessions(gateways, drop_copy):
    """Reconcile each session's gateway with its part of the firm's drop copy (firm_ordergw.reconcile)."""
    breaks = []
    for s, gw in gateways.items():
        mine = [(k, cl, q) for (sess, k, cl, q) in drop_copy if sess == s]
        breaks += [f"session {s}: {b}" for b in og.reconcile(gw, mine)]
    unknown = sorted({sess for (sess, *_rest) in drop_copy} - set(gateways))
    breaks += [f"session {s}: in the drop copy, not in the firm" for s in unknown]
    return breaks
