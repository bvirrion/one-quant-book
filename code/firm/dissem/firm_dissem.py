"""firm.dissem -- unicast against multicast market-data dissemination (build of One Quant Book 14, chapter 12).

A labelled simulation of the two-level design that SEBI's 2019 order describes for NSE's TCP tick-by-tick feed: a
dissemination centre sends each tick to its distribution servers one after another, in the order in which the
servers logged in; each server runs a few sender ports, and each port sends to its members one after another, in
the order in which the members logged in. Multicast sends one copy that the network replicates to every member.
All costs are parameters, not measurements of any venue.

API (stable):
    Server(name, ports, speed=1.0)                 ports: members per port; speed > 1 is a slower (busier) server
    Member(server, port, rank)                     rank 0 is the first to log in on its port
    members(servers) -> [Member]
    unicast_us(servers, c_centre=5.0, c_send=10.0, jitter=1.0, rng=None, shuffle=False) -> {Member: us}
    multicast_us(servers, c_send=10.0, jitter=1.0, rng=None) -> {Member: us}
    fairness(times) -> dict(first, median, last, spread, first_vs_median)
    rank_stability(servers, ticks=50, seed=0, shuffle=False, **kw) -> mean rank correlation between ticks
    race_win(times, a, b, react_mean=20.0, react_sd=5.0, n=20000, seed=0) -> P(a's order beats b's)
"""
import statistics
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Server:
    name: str
    ports: tuple
    speed: float = 1.0


@dataclass(frozen=True)
class Member:
    server: str
    port: int
    rank: int


def members(servers):
    return [Member(s.name, p, r) for s in servers for p, n in enumerate(s.ports) for r in range(n)]


def _noise(rng, jitter, n):
    return rng.exponential(jitter, n) if jitter > 0 else np.zeros(n)


def unicast_us(servers, c_centre=5.0, c_send=10.0, jitter=1.0, rng=None, shuffle=False):
    """Receive time of one tick: the centre's copy to each server in server order, then each
    port's sends in login order. shuffle=True redraws both orders for this tick (a randomiser)."""
    rng = rng or np.random.default_rng(0)
    out = {}
    order = list(range(len(servers)))
    if shuffle:
        rng.shuffle(order)
    for q, i in enumerate(order):
        s = servers[i]
        at_server = (q + 1) * c_centre
        for p, n in enumerate(s.ports):
            ranks = rng.permutation(n) if shuffle else np.arange(n)
            noise = _noise(rng, jitter, n)
            for r in range(n):
                slot = int(ranks[r])
                out[Member(s.name, p, r)] = at_server + (slot + 1) * c_send * s.speed + noise[r]
    return out


def multicast_us(servers, c_send=10.0, jitter=1.0, rng=None):
    """One send; the switches replicate it, so every member waits one send plus its own jitter."""
    rng = rng or np.random.default_rng(0)
    ms = members(servers)
    noise = _noise(rng, jitter, len(ms))
    return {m: c_send + noise[k] for k, m in enumerate(ms)}


def fairness(times):
    v = sorted(float(x) for x in times.values())
    first, med, last = v[0], statistics.median(v), v[-1]
    return {"first": first, "median": med, "last": last, "spread": last - first, "first_vs_median": med - first}


def _ranks(times, keys):
    order = sorted(keys, key=lambda k: times[k])
    pos = {k: i for i, k in enumerate(order)}
    return np.array([pos[k] for k in keys], dtype=float)


def rank_stability(servers, ticks=50, seed=0, shuffle=False, **kw):
    """Mean Spearman correlation of members' arrival ranks between consecutive ticks (1: the same member is always
    first; near 0: the order is redrawn every tick)."""
    rng = np.random.default_rng(seed)
    keys = members(servers)
    prev, cors = None, []
    for _ in range(ticks):
        r = _ranks(unicast_us(servers, rng=rng, shuffle=shuffle, **kw), keys)
        if prev is not None:
            cors.append(float(np.corrcoef(prev, r)[0, 1]))
        prev = r
    return float(np.mean(cors))


def race_win(times, a, b, react_mean=20.0, react_sd=5.0, n=20000, seed=0):
    """Probability that member a's reaction reaches the engine before member b's, both reacting to the same tick
    with independent normal reaction times (a labelled model)."""
    rng = np.random.default_rng(seed)
    ta = times[a] + rng.normal(react_mean, react_sd, n)
    tb = times[b] + rng.normal(react_mean, react_sd, n)
    return float(np.mean(ta < tb))
