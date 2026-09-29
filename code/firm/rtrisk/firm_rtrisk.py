"""firm.rtrisk -- real-time risk: incremental aggregation, a sensitivity cache, limits, what-if (Book 15, ch. 18).

Trades sit in books, books in desks, desks in the firm (a risk hierarchy, Book 6). Each trade's sensitivities come
from Book 5's pricing library (firm.pricing: delta, gamma, vega by bump and reprice) and are kept in a cache, valid
around the spot at which they were computed. On a fill the trade's delta-dollars are added to every ancestor; on a
market tick the cached deltas are carried forward with their gammas (delta + gamma dS), and when the spot has moved
more than a threshold since the cache was filled, every trade is repriced and the aggregates are corrected by the
difference -- the aggregation is incremental in both cases, never a full recomputation of the tree. Limits (absolute
delta-dollars per node, in the firm.riskctl hierarchy: a desk's limit never above the firm's) are checked on every
update. A what-if check answers what a proposed trade would do to every ancestor before it is sent. A snapshot carries
its market time, the time of the sensitivities it used and their age.

API (stable):
    Hierarchy(parents {node: parent})            .ancestors(node) -> [node, parent, ..., root]
    SensitivityCache(md, threshold=0.005)        .greeks(inst) -> {'delta', 'gamma', 'vega'} ; .stale(spot) -> bool
                                                  .refresh(md) ; .asof_spot
    Aggregator(hierarchy, cache, limits {node: max |delta-dollars|})
        .on_fill(t, book, key, inst, qty) ; .on_tick(t, spot) ; .exposure(node) ; .snapshot(t) -> Snapshot
        .what_if(book, inst, qty) -> ({node: exposure after}, [breached nodes]) ; .alerts [(t, node, exposure, limit)]
    Future(id, underlying)                        a linear instrument: delta 1, no gamma, priced at the spot
    delta_gamma_pnl(greeks, qty, s0, s1) ; full_pnl(inst, qty, md0, md1)
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "pricing"))
import firm_pricing as FP  # noqa: E402


@dataclass(frozen=True)
class Future:
    id: str
    underlying: str


class Hierarchy:
    def __init__(self, parents: dict):
        self.parents = dict(parents)

    def ancestors(self, node) -> list:
        out = [node]
        while self.parents.get(out[-1]) is not None:
            out.append(self.parents[out[-1]])
        return out


class SensitivityCache:
    """Greeks per instrument, computed at one snapshot, valid while the spot stays near it."""

    def __init__(self, md: FP.MarketData, underlying: str, threshold: float = 0.005):
        self.md, self.und, self.threshold = md, underlying, threshold
        self.asof_spot = md.spots[underlying]
        self.cache: dict = {}
        self.refreshes = 0

    def greeks(self, inst) -> dict:
        if inst.id not in self.cache:
            if isinstance(inst, Future):
                self.cache[inst.id] = {"delta": 1.0, "gamma": 0.0, "vega": 0.0}
            else:
                g = FP.greeks(inst, self.md, which=("delta", "gamma", "vega"))
                s = self.asof_spot
                gamma = g["gamma"] * 100.0 / (s * s)          # per unit of spot, squared
                self.cache[inst.id] = {"delta": g["delta"], "gamma": gamma, "vega": g["vega"]}
        return self.cache[inst.id]

    def stale(self, spot: float) -> bool:
        return abs(spot / self.asof_spot - 1.0) > self.threshold

    def refresh(self, md: FP.MarketData) -> None:
        self.md, self.asof_spot, self.cache = md, md.spots[self.und], {}
        self.refreshes += 1


@dataclass
class Snapshot:
    t: float
    spot: float
    cache_spot: float
    cache_age: float                            # seconds since the sensitivities were computed
    exposures: dict
    breaches: list = field(default_factory=list)


class Aggregator:
    def __init__(self, hierarchy: Hierarchy, cache: SensitivityCache, limits: dict):
        self.h, self.cache, self.limits = hierarchy, cache, limits
        self.trades: dict = {}                  # key -> (book, inst, qty)
        self.contrib: dict = {}                 # key -> delta-dollars currently counted
        self.expo: dict = {}                    # node -> delta-dollars
        self.spot = cache.asof_spot
        self.cache_t = 0.0
        self.alerts: list = []
        self.updates = 0

    def _dd(self, inst, qty: float) -> float:
        """Delta-dollars of a trade now, from the cache: (delta + gamma dS) qty S."""
        g = self.cache.greeks(inst)
        ds = self.spot - self.cache.asof_spot
        return (g["delta"] + g["gamma"] * ds) * qty * self.spot

    def _add(self, book, amount: float) -> None:
        for node in self.h.ancestors(book):
            self.expo[node] = self.expo.get(node, 0.0) + amount
        self.updates += 1

    def _check(self, t: float) -> None:
        for node, lim in self.limits.items():
            e = self.expo.get(node, 0.0)
            if abs(e) > lim and not any(a[1] == node for a in self.alerts):
                self.alerts.append((t, node, e, lim))

    def on_fill(self, t: float, book, key, inst, qty: float) -> None:
        old = self.trades.get(key)
        qty_total = qty + (old[2] if old else 0.0)
        self.trades[key] = (book, inst, qty_total)
        new = self._dd(inst, qty_total)
        self._add(book, new - self.contrib.get(key, 0.0))
        self.contrib[key] = new
        self._check(t)

    def on_tick(self, t: float, md: FP.MarketData) -> None:
        self.spot = md.spots[self.cache.und]
        if self.cache.stale(self.spot):
            self.cache.refresh(md)
            self.cache_t = t
        for key, (book, inst, qty) in self.trades.items():
            new = self._dd(inst, qty)
            self._add(book, new - self.contrib[key])
            self.contrib[key] = new
        self._check(t)

    def exposure(self, node) -> float:
        return self.expo.get(node, 0.0)

    def snapshot(self, t: float) -> Snapshot:
        breaches = [n for n, lim in self.limits.items() if abs(self.expo.get(n, 0.0)) > lim]
        return Snapshot(t, self.spot, self.cache.asof_spot, t - self.cache_t, dict(self.expo),
                        breaches)

    def what_if(self, book, inst, qty: float) -> tuple[dict, list]:
        d = self._dd(inst, qty)
        after = {n: self.expo.get(n, 0.0) + d for n in self.h.ancestors(book)}
        breached = [n for n, e in after.items() if n in self.limits and abs(e) > self.limits[n]]
        return after, breached


def delta_gamma_pnl(g: dict, qty: float, s0: float, s1: float) -> float:
    ds = s1 - s0
    return qty * (g["delta"] * ds + 0.5 * g["gamma"] * ds * ds)


def full_pnl(inst, qty: float, md0: FP.MarketData, md1: FP.MarketData) -> float:
    if isinstance(inst, Future):
        return qty * (md1.spots[inst.underlying] - md0.spots[inst.underlying])
    return qty * (FP.price(inst, md1).pv - FP.price(inst, md0).pv)
