"""The risk grid (One Quant Book 15, chapter 20).

A nightly batch revalues a book of 105,000 trades -- swaps, swaptions and equity options from Books 5 and 6, and
autocallables priced by Monte Carlo -- under 1,000 historical scenarios, on a small simulated grid of 16 cores
(firm.jobgraph), in a window from 04:00 to 06:00. The cost of each kind of trade is measured on this laptop with the
real pricing library (bench_riskgrid.py). One autocallable prices two hundred times slower than its estimate (its
engine falls back to daily steps), and one swaption fails every time (its volatility is missing). The chapter
measures the makespan against the task granularity and the cluster size, the difference between a naive and a
cost-aware plan and between failing tasks and quarantined trades, the pricing calls an adjoint saves on swap deltas,
and those an intraday rerun saves by repricing only what changed.
"""
from __future__ import annotations

import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/riskgrid"))
import firm_riskgrid as G  # noqa: E402

FIG = ROOT / "figdata/platforms/20-the-risk-grid"
COUNTS = {"swap": 60_000, "swaption": 20_000, "option": 20_000, "autocallable": 5_000}
N_SCEN, OVERHEAD, WINDOW, START = 1_000, 5.0, 5_400.0, 4.5 * 3600
SLOW_FACTOR, NODES, CORES = 220.0, 8, 4
TRADE_TARGET = 0.5


def costs() -> dict:
    rows = {r["kind"]: r for r in csv.DictReader(open(FIG / "measured_costs.csv"))}
    return {k: float(rows[k]["seconds"]) for k in COUNTS}


def book(slow: bool = True, failing: bool = True) -> list[G.GridTrade]:
    c = costs()
    out = []
    for kind, n in COUNTS.items():
        out += [G.GridTrade(f"{kind}-{i}", kind, c[kind]) for i in range(n)]
    if slow:
        k = next(i for i, t in enumerate(out) if t.kind == "autocallable")
        out[k] = G.GridTrade(out[k].trade_id, "autocallable", c["autocallable"], c["autocallable"] * SLOW_FACTOR)
    if failing:
        k = next(i for i, t in enumerate(out) if t.kind == "swaption")
        out[k] = G.GridTrade(out[k].trade_id, "swaption", c["swaption"], fails=True)
    return out


def grid(scen_batch: int, cores: int = CORES, nodes: int = NODES, cost_aware: bool = False, failures: str = "trade",
         trades=None, slow_known: bool = True) -> G.GridRun:
    trades = trades if trades is not None else book()
    if cost_aware and slow_known:                           # last night's measured cost replaces the estimate
        trades = [G.GridTrade(t.trade_id, t.kind, t.true, t.cost, t.fails) for t in trades]
    tasks = G.plan(trades, N_SCEN, TRADE_TARGET, scen_batch, OVERHEAD, 600.0 if cost_aware else None)
    return G.run(tasks, nodes, cores, failures)


BATCHES = (1000, 500, 250, 100, 50, 20, 10, 5)


def sweep(cores_list=(32, 64)) -> list[dict]:
    rows = []
    for total in cores_list:
        for b in BATCHES:
            for aware in (False, True):
                r = grid(b, nodes=total // CORES, cost_aware=aware)
                rows.append({"cores": total, "scen_batch": b, "cost_aware": aware, "makespan": r.makespan,
                             "tasks": r.n_tasks, "core_seconds": r.core_seconds})
    return rows


def failure_policies(scen_batch: int = 100) -> dict:
    out = {}
    for pol in ("task", "trade"):
        r = grid(scen_batch, cost_aware=True, failures=pol)
        out[pol] = {"makespan": r.makespan, "wasted": r.wasted, "lost": r.lost_cells, "quarantined": r.quarantined}
    return out


def pricing_calls(n_pillars: int = 8) -> dict:
    swaps = COUNTS["swap"]
    return {"bump": swaps * (2 * n_pillars + 1), "adjoint_runs": swaps,
            "full_grid": sum(COUNTS.values()) * (N_SCEN + 1)}


def intraday(changed: int = 1_500) -> dict:
    """Morning results cached; intraday, `changed` trades are amended: only they are repriced."""
    cache = G.ResultCache()
    versions = {f"t{i}": 1 for i in range(sum(COUNTS.values()))}
    for t, v in versions.items():
        cache.store(t, v, "EOD-2026-09-27", None)
    for i in range(changed):
        versions[f"t{i}"] = 2
    need = cache.needed(versions, "EOD-2026-09-27")
    return {"repriced": len(need), "calls": len(need) * N_SCEN, "full_calls": len(versions) * N_SCEN}
