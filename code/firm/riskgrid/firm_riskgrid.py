"""firm.riskgrid -- planning, running and checking the nightly revaluation grid (build of One Quant Book 15, ch. 20).

The nightly risk batch revalues every trade under every scenario. Its work is a grid of (trade batch, scenario batch)
tasks; this module plans the grid from each trade's cost estimate, runs it on chapter 13's scheduler and simulated
cluster (firm.jobgraph), and reports what failed. A plan fixes the trade batches (trades grouped until their summed
cost per scenario reaches a target) and the scenario batch size; each task costs a fixed overhead (loading the
snapshot and the trades, writing results) plus its trades' costs times its scenarios. A cost-aware plan isolates the
trades whose cost per task would exceed a bound and fans their scenarios out into smaller tasks. Failures are handled
per task (a failing trade fails its task, which is retried and then lost) or per trade (the trade is quarantined with
a report and the task completes). Sensitivities of swaps come from the adjoint of Book 4's tape (firm.aad) in one
sweep, where bumping needs two repricings per pillar; results are cached by (trade, trade version, market version), so
an intraday rerun reprices only what changed.

API (stable):
    GridTrade(trade_id, kind, est, cost=None, fails=False)        est and cost in seconds per scenario
    plan(trades, n_scen, trade_target, scen_batch, overhead, isolate_above=None) -> [TaskSpec]
    run(tasks, nodes, cores, failures='trade', retries=2, seed=0) -> GridRun(makespan, core_seconds, wasted, lost_cells,
        quarantined, n_tasks)
    swap_pv_adjoint(zeros, tenors, years, fixed, payer=True) -> (pv, dpv/dzero per pillar, tape stats)
    ResultCache(): .needed(trades {id: version}, md_version) -> ids to reprice ; .store(id, version, md_version, value)
"""
from __future__ import annotations

import math
import pathlib
import sys
from dataclasses import dataclass, field

FIRM = pathlib.Path(__file__).resolve().parents[1]
for _c in ("jobgraph", "aad"):
    sys.path.insert(0, str(FIRM / _c))
import firm_aad as AD  # noqa: E402
import firm_jobgraph as J  # noqa: E402


@dataclass(frozen=True)
class GridTrade:
    trade_id: str
    kind: str
    est: float                  # estimated seconds per scenario (what the planner sees)
    cost: float | None = None   # true seconds per scenario (default: the estimate)
    fails: bool = False

    @property
    def true(self) -> float:
        return self.est if self.cost is None else self.cost


@dataclass
class TaskSpec:
    tid: int
    trades: list
    scenarios: int
    overhead: float

    @property
    def estimate(self) -> float:
        return self.overhead + self.scenarios * sum(t.est for t in self.trades)

    @property
    def duration(self) -> float:
        return self.overhead + self.scenarios * sum(t.true for t in self.trades)


def _batches(trades, target):
    batch, acc = [], 0.0
    for t in trades:
        batch.append(t)
        acc += t.est
        if acc >= target:
            yield batch
            batch, acc = [], 0.0
    if batch:
        yield batch


def plan(trades, n_scen: int, trade_target: float, scen_batch: int, overhead: float,
         isolate_above: float | None = None) -> list[TaskSpec]:
    """Trade batches of about `trade_target` seconds per scenario times scenario batches of
    `scen_batch`; a trade costing more than `isolate_above` a task gets finer tasks."""
    big = isolate_above is not None
    heavy = [t for t in trades if big and t.est * scen_batch > isolate_above]
    light = [t for t in trades if t not in heavy]
    out = []
    for group in _batches(light, trade_target):
        for s0 in range(0, n_scen, scen_batch):
            out.append(TaskSpec(len(out), group, min(scen_batch, n_scen - s0), overhead))
    for t in heavy:
        fine = max(1, int(isolate_above // t.est))
        for s0 in range(0, n_scen, fine):
            out.append(TaskSpec(len(out), [t], min(fine, n_scen - s0), overhead))
    return out


@dataclass
class GridRun:
    makespan: float
    core_seconds: float
    wasted: float
    lost_cells: int
    quarantined: list = field(default_factory=list)
    n_tasks: int = 0


def run(tasks: list[TaskSpec], nodes: int, cores: int, failures: str = "trade",
        retries: int = 2, seed: int = 0) -> GridRun:
    """Longest estimate first on the simulated cluster. failures='task': a task with a failing
    trade runs 1 + retries times and loses its cells; 'trade': the trade is quarantined."""
    jobs, wasted, lost, quarantined = [], 0.0, 0, []
    for spec in tasks:
        bad = [t for t in spec.trades if t.fails]
        d = spec.duration
        if bad and failures == "task":
            wasted += retries * d
            d *= 1 + retries
            lost += len(spec.trades) * spec.scenarios
        elif bad:
            quarantined += [t.trade_id for t in bad]
            lost += len(bad) * spec.scenarios
        jobs.append(J.Task(spec.tid, d, spec.estimate))
    s = J.simulate(jobs, J.Cluster(nodes, cores, seed=seed), J.LPT())
    return GridRun(s.makespan, s.busy, wasted, lost, sorted(set(quarantined)), len(tasks))


# ------------------------------------------------------------ adjoint sensitivities of a swap
def swap_pv_adjoint(zeros, tenors, years: int, fixed: float, payer: bool = True):
    """PV of a spot-starting annual swap (unit notional) on pillar zero rates, linear between
    pillars, flat outside, and its derivative to every pillar, in one reverse sweep."""
    def pv(z):
        def zero(t):
            if t <= tenors[0]:
                return z[0]
            if t >= tenors[-1]:
                return z[-1]
            i = next(k for k in range(1, len(tenors)) if t < tenors[k])
            w = (t - tenors[i - 1]) / (tenors[i] - tenors[i - 1])
            return z[i - 1] * (1 - w) + z[i] * w
        dfs = [AD.exp(-zero(t) * t) for t in [_act365(k) for k in range(1, years + 1)]]
        value = (1.0 - dfs[-1]) - fixed * sum(dfs[1:], dfs[0])
        return value if payer else -value
    return AD.gradient(pv, list(zeros))


def _act365(years: int) -> float:
    """The year fraction the library uses for a date `years` whole years ahead (round(365 x years) days / 365)."""
    return round(365.0 * years) / 365.0


class ResultCache:
    """Scenario P&L vectors keyed by (trade, trade version, market-data version)."""

    def __init__(self):
        self.store_: dict = {}

    def needed(self, trades: dict, md_version: str) -> list:
        return [t for t, v in trades.items() if (t, v, md_version) not in self.store_]

    def store(self, trade_id: str, version: int, md_version: str, value) -> None:
        self.store_[(trade_id, version, md_version)] = value


def cells(tasks: list[TaskSpec]) -> int:
    return sum(len(t.trades) * t.scenarios for t in tasks)


def lower_bound(tasks: list[TaskSpec], total_cores: int) -> float:
    return max(sum(t.duration for t in tasks) / total_cores, max(t.duration for t in tasks))


def hours(seconds: float) -> str:
    h = int(seconds // 3600)
    return f"{h}:{int(math.floor((seconds - 3600 * h) / 60)):02d}"
