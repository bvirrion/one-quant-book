"""Cloud against on-premises (One Quant Book 15, chapter 26).

Prices are the cited, dated ones (ledger F1-F6): a 96-thread compute instance in one cloud region on demand, reserved
for one or three years without upfront payment, and on the spot market; the data-transfer charges out of the region;
object storage from chapter 2; a server CPU's list price; the average commercial electricity price. What no public
list gives -- the rest of the server, space, staff, the building's overhead -- is stated below as the model's
assumptions. A year of the research cluster's hourly demand is bought four ways, cost per used thread-hour is traced
against utilisation, and chapter 13's sweep runs on spot capacity with preemption, with and without checkpoints.
"""
from __future__ import annotations

import math
import pathlib
import random
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("cloudcost", "jobgraph"):
    sys.path.insert(0, str(ROOT / "code/firm" / c))
import firm_cloudcost as C  # noqa: E402
import firm_jobgraph as J  # noqa: E402

# ---- cited prices (ledger), per hour for one c7i.24xlarge (96 threads), US East, Linux
PRICES = {
    "on_demand": C.PriceItem("on demand", 4.284, "USD/h", "AWS price list, published 2026-09-25", "2026-09"),
    "reserved_1y": C.PriceItem("reserved 1 year, no upfront", 2.83387, "USD/h", "AWS price list", "2026-09"),
    "reserved_3y": C.PriceItem("reserved 3 years, no upfront", 1.88608, "USD/h", "AWS price list", "2026-09"),
    "spot": C.PriceItem("spot", 1.7372, "USD/h", "AWS spot price feed, us-east-1", "2026-09"),
}
THREADS_CLOUD = 96
TRANSFER_TIERS = [(10_240, 0.09), (51_200, 0.085), (153_600, 0.07), (math.inf, 0.05)]   # USD/GB out, by GB tier
STORAGE = 0.023                                   # USD per GB-month, object storage standard (chapter 2)
CPU_PRICE, POWER_PRICE = 10_931.0, 0.1453         # one 128-core CPU at list (1kU); USD/kWh, US commercial average

# ---- the model's assumptions (not cited): a two-socket server of 256 cores, 512 threads
SERVER = C.OwnedServer(price=4 * CPU_PRICE,       # the two CPUs are half of the server's price
                       life_months=48, kw=1.3, pue=1.4, power_price=POWER_PRICE,
                       space=300.0,                # USD per server-month of rack space
                       staff=250_000 / 200 / 12)   # one engineer (USD 250k a year) per 200 servers
THREADS_OWNED = 512


def per_thread() -> dict:
    out = {k: v.value / THREADS_CLOUD for k, v in PRICES.items()}
    out["owned"] = SERVER.per_thread_hour(THREADS_OWNED)
    return out


def curves(us=None, spot_waste: float = 0.0) -> list[tuple]:
    """(u, owned, reserved 3y, reserved 1y, on demand, spot) cost per used thread-hour."""
    p = per_thread()
    us = us if us is not None else np.round(np.arange(0.05, 1.0001, 0.05), 2)
    return [(float(u), C.cost_per_used_hour("fixed", p["owned"], u), C.cost_per_used_hour("fixed", p["reserved_3y"], u),
             C.cost_per_used_hour("fixed", p["reserved_1y"], u), p["on_demand"],
             C.cost_per_used_hour("metered", p["spot"], u, spot_waste)) for u in us]


def break_evens(server_factor: float = 1.0) -> dict:
    p = per_thread()
    owned = C.OwnedServer(**{**SERVER.__dict__, "price": SERVER.price * server_factor}).per_thread_hour(THREADS_OWNED)
    return {"owned": owned, "vs_on_demand": C.break_even(owned, p["on_demand"]),
            "vs_spot": C.break_even(owned, p["spot"]), "reserved_3y_vs_on_demand": C.break_even(p["reserved_3y"],
                                                                                            p["on_demand"])}


def demand(seed: int = 26, spread_sweep: bool = False) -> np.ndarray:
    """A year of hourly demand in threads: interactive base, working hours, nightly batch on
    weekdays, a weekend sweep each week and twenty unplanned bursts. `spread_sweep` runs the
    sweep's thread-hours (12,000 x 8 a week) inside the five weeknight batch windows instead."""
    rng = np.random.default_rng(seed)
    h = np.arange(8760)
    day, hour = h // 24, h % 24
    weekday = (day % 7) < 5
    d = np.full(8760, 1_500.0)
    d += np.where(weekday & (hour >= 9) & (hour < 18), 1_000, 0)
    d += np.where(weekday & ((hour >= 22) | (hour < 6)), 4_000, 0)
    if spread_sweep:
        d += np.where(weekday & ((hour >= 22) | (hour < 6)), 12_000 * 8 / 40, 0)
    else:
        d += np.where(((day % 7) == 5) & (hour >= 8) & (hour < 16), 12_000, 0)
    for s in rng.choice(8760 - 4, 20, replace=False):
        d[s:s + 4] += 8_000
    return d


def plans(d=None) -> dict:
    d = demand() if d is None else d
    p = per_thread()
    inf = float("inf")
    return {"on demand only": C.plan_capacity(d, inf, inf, p["on_demand"]),
            "reserved + on demand": C.plan_capacity(d, inf, p["reserved_3y"], p["on_demand"]),
            "owned + on demand": C.plan_capacity(d, p["owned"], p["reserved_3y"], p["on_demand"]),
            "owned + spot bursts": C.plan_capacity(d, p["owned"], p["reserved_3y"], p["on_demand"], p["spot"],
                                                   spot_share=0.8)}


# ---- the burst: chapter 13's sweep (10,000 backtests, median 15 minutes, sigma 0.76, 40 long ones)
SIGMA, MEDIAN, N, LONG = 0.76, 900.0, 10_000, 40


def sweep(n: int = N, n_long: int = LONG, seed: int = 13) -> list:
    rng = random.Random(seed)
    out = []
    for i in range(n):
        d = MEDIAN * 30 if i >= n - n_long else MEDIAN * math.exp(SIGMA * rng.gauss(0, 1))
        out.append(J.Task(i, d, d * math.exp(0.3 * rng.gauss(0, 1))))
    return out


def burst(preempt: float, price: float, checkpoint: float | None = None, nodes: int = 24, n: int = N,
          n_long: int = LONG, seed: int = 1) -> dict:
    tasks = sweep(n, n_long)
    if checkpoint:
        tasks = C.checkpointed(tasks, checkpoint, overhead=10.0)
    s = J.simulate(tasks, J.Cluster(nodes, THREADS_CLOUD, preempt_per_hour=preempt, seed=seed), J.LPT())
    nh = C.billed_node_hours(s, THREADS_CLOUD)
    return {"makespan_h": s.makespan / 3600, "node_hours": nh, "cost": nh * price,
            "wasted_core_h": s.wasted / 3600, "busy_core_h": s.busy / 3600}


def monthly_to_hourly_rate(share_per_month: float) -> float:
    """The per-hour interruption rate that interrupts `share_per_month` of instances in 730 hours."""
    return -math.log(1 - share_per_month) / C.HOURS_PER_MONTH
