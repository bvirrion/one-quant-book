"""Distributed compute and schedulers (One Quant Book 15, chapter 13).

A sweep of 10,000 backtests on a simulated cluster of 24 nodes of 16 cores: durations lognormal around a median of
fifteen minutes, with the spread measured on real small backtests of chapter 11 run on this laptop through the same
scheduler interface (one worker), estimates known to within a lognormal error, and forty tasks thirty times the median
submitted last. One node is slow (four times), and running work fails at a small rate per core-hour. The sweep runs
under first-in-first-out, longest-first and work stealing, with and without speculative execution; a second team's
small sweep arrives an hour later under first-in-first-out and fair share; and a task graph with shared feature stages
runs with and without a content-addressed cache.
"""
from __future__ import annotations

import csv
import math
import pathlib
import random
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/jobgraph"))
import firm_jobgraph as J  # noqa: E402

FIG = ROOT / "figdata/platforms/13-distributed-compute-and-schedulers"
MEDIAN, N, LONG, EST_NOISE = 900.0, 10_000, 40, 0.3
SPEC = 2.5                                  # backup after 2.5 times the estimate (estimates err by e^(0.3 z))
H = 3600.0


def measured_sigma() -> float:
    """The spread of log durations of the measured small backtests (bench_jobgraph.py)."""
    rows = list(csv.DictReader(open(FIG / "measured_backtests.csv")))
    x = np.log([float(r["seconds"]) for r in rows])
    return float(np.std(x, ddof=1))


def sweep(sigma: float, n: int = N, n_long: int = LONG, seed: int = 13, team: str = "A", start: int = 0,
          release: float = 0.0) -> list[J.Task]:
    rng = random.Random(seed)
    out = []
    for i in range(n):
        d = MEDIAN * 30 if i >= n - n_long else MEDIAN * math.exp(sigma * rng.gauss(0, 1))
        out.append(J.Task(start + i, d, d * math.exp(EST_NOISE * rng.gauss(0, 1)), team, release=release))
    return out


def cluster(seed: int = 1, slow: tuple = (5,)) -> J.Cluster:
    return J.Cluster(24, 16, slow=slow, slowdown=4.0, fail_per_hour=0.002, seed=seed)


POLICIES = {"FIFO": J.FIFO, "LPT": J.LPT, "work stealing": lambda: J.WorkStealing(cluster().total)}


def policies(sigma: float) -> list[dict]:
    tasks, cl = sweep(sigma), cluster()
    lb = J.lower_bound(tasks, cl.total)
    rows = []
    for name, make in POLICIES.items():
        for spec in (None, SPEC):
            s = J.simulate(tasks, cl, make(), spec=spec)
            rows.append({"policy": name, "spec": spec is not None, "makespan_h": s.makespan / H,
                         "node_hours": s.node_hours, "wasted_core_h": s.wasted / H, "backups": s.backups,
                         "bound_h": lb / H})
    s = J.simulate(tasks, cluster(slow=()), J.LPT())
    rows.append({"policy": "LPT (no slow node)", "spec": False, "makespan_h": s.makespan / H,
                 "node_hours": s.node_hours, "wasted_core_h": s.wasted / H, "backups": 0, "bound_h": lb / H})
    return rows


def profile(sigma: float, grid_min: int = 10) -> dict:
    tasks, cl = sweep(sigma), cluster()
    out = {}
    for name in ("FIFO", "LPT"):
        s = J.simulate(tasks, cl, POLICIES[name](), spec=SPEC if name == "LPT" else None)
        grid = np.arange(0, s.makespan + grid_min * 60, grid_min * 60)
        out[name] = (grid / H, J.utilisation(s, grid))
    return out


def idle_after(grid_h, busy, share: float = 0.1) -> float:
    """First time after which fewer than `share` of the cores are ever busy again."""
    total = cluster().total
    busy = np.asarray(busy)
    above = np.flatnonzero(busy >= share * total)
    return float(grid_h[above[-1] + 1]) if len(above) and above[-1] + 1 < len(grid_h) else float(grid_h[-1])


def fair_share(sigma: float) -> list[dict]:
    """Team A's 10,000-task sweep at 18:00, team B's 500 tasks at 19:00."""
    a = sweep(sigma)
    b = sweep(sigma, n=500, n_long=0, seed=14, team="B", start=100_000, release=H)
    rows = []
    for name, pol in (("FIFO", J.FIFO()), ("fair share", J.FairShare({"A": 0.5, "B": 0.5}))):
        s = J.simulate(a + b, cluster(), pol)
        fb = sorted(s.finish[t.tid] for t in b)
        done_a = max(s.finish[t.tid] for t in a)
        rows.append({"policy": name, "team_b_half_h": (fb[len(fb) // 2] - H) / H, "team_b_done_h": (fb[-1] - H) / H,
                     "team_a_done_h": done_a / H})
    return rows


def graph(sigma: float, n_features: int = 100, feature_s: float = 1200.0) -> list[J.Task]:
    """100 feature stages (twenty minutes each), each followed by 100 backtests that read it."""
    rng = random.Random(21)
    tasks, bt = [], sweep(sigma, n_long=0)
    for f in range(n_features):
        tasks.append(J.Task(200_000 + f, feature_s, feature_s, key=f"features/{f}"))
    for i, t in enumerate(bt):
        tasks.append(J.Task(t.tid, t.duration, t.estimate, deps=(200_000 + i % n_features,), key=None))
    rng.shuffle(tasks)
    return tasks


def caching(sigma: float) -> dict:
    cl = cluster()
    inline = [J.Task(t.tid, t.duration + 1200.0, t.estimate + 1200.0) for t in sweep(sigma, n_long=0)]
    s_inline = J.simulate(inline, cl, J.LPT())
    cache: set = set()
    g = graph(sigma)
    s1 = J.simulate(g, cl, J.LPT(), cache=cache)
    s2 = J.simulate(graph(sigma), cl, J.LPT(), cache=cache)          # the next sweep, same features
    return {"inline_h": s_inline.makespan / H, "graph_h": s1.makespan / H, "cached_h": s2.makespan / H,
            "inline_core_h": s_inline.busy / H, "graph_core_h": s1.busy / H, "cached_core_h": s2.busy / H,
            "hits": len(cache)}


def long_tasks_first(sigma: float) -> dict:
    """Exercise 7: the same sweep with the forty long tasks submitted first."""
    t = sweep(sigma)
    t = t[-LONG:] + t[:-LONG]
    return {(name, spec is not None): J.simulate(t, cluster(), POLICIES[name](), spec=spec).makespan / H
            for name in ("FIFO", "LPT") for spec in (None, SPEC)}
