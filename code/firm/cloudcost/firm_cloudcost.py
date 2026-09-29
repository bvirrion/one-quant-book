"""firm.cloudcost -- owned, reserved, on-demand and spot capacity, priced from dated lists (Book 15, ch. 26).

Every price is a PriceItem with its value, unit, source and date, so that a cost can say where each of its inputs
came from and when it will be stale. Owned hardware is a total cost of ownership per server-month: the purchase spread
over its life, power at the site's price with the building's overhead (PUE), space, and staff. Cloud capacity is
priced per hardware thread-hour (vCPU-hour): reserved and owned capacity is paid whether used or not, on-demand and
spot only when used, spot with the work that preemption wastes. The capacity planner reads a year of hourly demand as
a load-duration curve and buys each unit of capacity the cheapest way given the share of hours it is used; a burst
runs a task graph on firm.jobgraph's cluster with preemption, optionally split into checkpointed chunks, and bills
each node until its last task ends. Data leaving the cloud is priced with tiered data-transfer charges.

API (stable):
    PriceItem(name, value, unit, source, date)
    OwnedServer(price, life_months, kw, pue, power_price, space, staff) -> .monthly, .per_thread_hour(threads)
    cost_per_used_hour(kind, price, u, waste=0.0)       kind: 'fixed' (owned, reserved) or 'metered'
    break_even(fixed_full, metered)                     utilisation above which paying for fixed capacity is cheaper
    plan_capacity(demand, owned, reserved, on_demand, spot=None, spot_share=1.0) -> Plan
    checkpointed(tasks, chunk, overhead) -> tasks split into chained chunks
    billed_node_hours(schedule, cores_per_node) -> node-hours when each node is released after its last task
    transfer_out(gb, tiers) -> USD ; tiers [(upper GB, USD per GB)]
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, field

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "jobgraph"))
import firm_jobgraph as J  # noqa: E402

HOURS_PER_MONTH = 730.0


@dataclass(frozen=True)
class PriceItem:
    name: str
    value: float
    unit: str
    source: str
    date: str


@dataclass(frozen=True)
class OwnedServer:
    price: float              # purchase, USD
    life_months: int          # straight-line depreciation
    kw: float                 # average draw at load, kW
    pue: float                # facility overhead (power usage effectiveness)
    power_price: float        # USD per kWh
    space: float              # USD per server-month
    staff: float              # USD per server-month

    @property
    def monthly(self) -> float:
        power = self.kw * self.pue * HOURS_PER_MONTH * self.power_price
        return self.price / self.life_months + power + self.space + self.staff

    def per_thread_hour(self, threads: int) -> float:
        return self.monthly / (threads * HOURS_PER_MONTH)


def cost_per_used_hour(kind: str, price: float, u: float, waste: float = 0.0) -> float:
    """What one used thread-hour costs: fixed capacity divides its price by the utilisation,
    metered capacity pays its price (plus the share of work lost to preemption)."""
    if kind == "fixed":
        return price / u
    return price * (1.0 + waste)


def break_even(fixed_full: float, metered: float) -> float:
    return fixed_full / metered


@dataclass
class Plan:
    owned: int
    reserved: int
    metered_hours: float
    cost: dict = field(default_factory=dict)

    @property
    def total(self) -> float:
        return sum(self.cost.values())


def plan_capacity(demand, owned: float, reserved: float, on_demand: float,
                  spot: float | None = None, spot_share: float = 1.0) -> Plan:
    """Buy each unit of capacity the cheapest way: the k-th unit is needed in the share
    f(k) of hours with demand >= k; fixed options cost their price every hour, metered
    ones only f(k) of hours. `spot_share` of metered work may run on spot."""
    d = np.sort(np.asarray(demand, dtype=float))
    hours = len(d)
    metered = on_demand if spot is None else (
        spot_share * spot + (1 - spot_share) * on_demand)
    levels = np.arange(1, int(np.ceil(d[-1])) + 1)
    f = 1.0 - np.searchsorted(d, levels - 1e-9, side="left") / hours   # hours >= k
    n_own = int(np.sum(owned < np.minimum(reserved, metered * f)))
    n_res = int(np.sum((reserved <= owned) & (reserved < metered * f)))
    over = np.clip(d - (n_own + n_res), 0, None).sum()       # unit-hours bought hourly
    cost = {"owned": n_own * owned * hours if n_own else 0.0,
            "reserved": n_res * reserved * hours if n_res else 0.0,
            "metered": over * metered}
    return Plan(n_own, n_res, float(over), cost)


# ------------------------------------------------------------ bursts on the simulated cluster
def checkpointed(tasks: list, chunk: float, overhead: float) -> list:
    """Split each task into chunks of `chunk` seconds (plus `overhead` per checkpoint),
    chained so that a preempted chunk restarts from the last checkpoint."""
    out, nid = [], max(t.tid for t in tasks) + 1
    for t in tasks:
        k = max(1, int(np.ceil(t.duration / chunk)))
        prev = None
        for i in range(k):
            d = t.duration / k + (overhead if k > 1 else 0.0)
            tid = t.tid if i == 0 else nid
            if i > 0:
                nid += 1
            deps = (prev,) if prev is not None else ()
            out.append(J.Task(tid, d, t.estimate / k, t.team, deps=deps))
            prev = tid
    return out


def billed_node_hours(schedule, cores_per_node: int) -> float:
    last: dict = {}
    for _tid, core, _s, end, _outcome in schedule.runs:
        node = core // cores_per_node
        last[node] = max(last.get(node, 0.0), end)
    return sum(last.values()) / 3600.0


def transfer_out(gb: float, tiers) -> float:
    """Tiered per-GB charge; tiers are (upper bound in GB, USD per GB), ascending."""
    cost, lo = 0.0, 0.0
    for hi, price in tiers:
        take = max(0.0, min(gb, hi) - lo)
        cost += take * price
        lo = hi
        if gb <= hi:
            break
    return cost
