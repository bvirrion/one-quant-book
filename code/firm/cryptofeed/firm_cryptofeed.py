"""firm.cryptofeed -- running market data and orders against a crypto venue's limits (build of One Quant Book 14,
chapter 20).

A shard planner assigns streams to connections and connections to addresses under a venue's documented limits (rows
of LIMITS, each with its ledger row). A resynchronisation model compares per-symbol and per-connection recovery from a
sequence gap when every snapshot costs request weight under Book 3's firm.ratelimit governor (wrapped). A budget
allocator splits one weight budget among strategies. A clock-skew estimator applies a minimum-delay filter to pairs of
(venue event time, local receive time).

API (stable):
    Limits(venue, streams_per_conn, conns_per_window, window_s, in_msgs_per_s, lifetime_h, source, as_of) ; LIMITS
    plan_shards(n_streams, limits, max_streams_per_conn=None, reconnect_window_s=None) -> dict(connections, addresses)
    resync_staleness(symbols_hit, snapshot_weight, governor_rules, rtt_ms=100) -> dict(done_ms, symbol_seconds)
    allocate(total, demands, weights) -> {strategy: share}      water-filling of a budget by priority weights
    skew(event_ms, recv_ms, window) -> [(t, offset_ms)]         minimum of recv - event over sliding windows
"""
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ratelimit"))
import firm_ratelimit as frl  # noqa: E402


@dataclass(frozen=True)
class Limits:
    venue: str
    streams_per_conn: int
    conns_per_window: int
    window_s: float
    in_msgs_per_s: float
    lifetime_h: float
    source: str
    as_of: str


LIMITS = {
    "binance-spot": Limits("Binance spot", 1024, 300, 300.0, 5.0, 24.0, "networks/20:F1", "2026-09-28"),
}


def plan_shards(n_streams, limits, max_streams_per_conn=None, reconnect_window_s=None):
    """Connections to carry the streams at the venue's cap or the firm's lower one; addresses
    so that reconnecting them all within reconnect_window_s respects the per-address limit."""
    cap = min(limits.streams_per_conn, max_streams_per_conn or limits.streams_per_conn)
    conns = math.ceil(n_streams / cap)
    window = reconnect_window_s or limits.window_s
    per_addr = limits.conns_per_window * min(1.0, window / limits.window_s)
    addresses = max(1, math.ceil(conns / per_addr))
    return {"connections": conns, "addresses": addresses, "streams_per_conn": cap}


def resync_staleness(symbols_hit, snapshot_weight, governor_rules, rtt_ms=100.0):
    """One snapshot per hit symbol, admitted by the governor's weight (one a millisecond at most);
    a symbol is stale until its snapshot returns. The last return and the stale symbol-seconds."""
    gov = frl.Governor([frl.Rule(r.kind, r.interval_ms, r.limit) for r in governor_rules])
    t, done = 0, []
    for _ in range(symbols_hit):
        while True:
            ok, wait = gov.try_send(t, snapshot_weight, False)
            if ok:
                break
            t += wait
        done.append(t + rtt_ms)
        t += 1
    return {"done_ms": max(done) if done else 0.0, "symbol_seconds": sum(done) / 1000.0}


def allocate(total, demands, weights):
    """Water-filling: each strategy gets up to its demand, in proportion to its weight."""
    left, share, active = float(total), {k: 0.0 for k in demands}, set(demands)
    while active and left > 1e-12:
        wsum = sum(weights[k] for k in active)
        offer = {k: left * weights[k] / wsum for k in active}
        full = {k for k in active if demands[k] - share[k] <= offer[k]}
        if not full:
            for k in active:
                share[k] += offer[k]
            break
        for k in full:
            left -= demands[k] - share[k]
            share[k] = demands[k]
        active -= full
    return share


def skew(event_ms, recv_ms, window):
    """Minimum one-way delay minus the venue's clock offset: min(receive - event) per window."""
    e, r = np.asarray(event_ms, float), np.asarray(recv_ms, float)
    d = r - e
    starts = range(0, len(d) - window + 1, window)
    return [(float(r[i + window - 1]), float(d[i:i + window].min())) for i in starts]
