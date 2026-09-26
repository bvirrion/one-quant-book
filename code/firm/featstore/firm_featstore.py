"""firm.featstore -- one feature definition, computed offline and online, and the tests that they agree (Book 12,
chapter 24).

Features are declared as data: a name, the per-event input it reads, how it aggregates over a trailing window (the
last value, a sum, a count, or a change), the window in seconds, and a version. The offline store computes them for a
whole history at a list of decision times, vectorised over cumulative sums and as-of lookups (knowledge time = the
event's time; an event at the decision time is known). The online engine consumes the same events one at a time with
running windows and answers at any moment. A parity test compares the two on a sample of decision times; a freshness
check reports how old each online value's newest input is.

API (stable):
    FeatureDef(name, input, agg, window, version)          agg: 'last', 'sum', 'count', 'change'
    events_from_tape(tape, levels) -> dict of per-event arrays (t, mid, spread, imbalance, depth, wmid, ofi, trade_qty,
                                      trade_sign, one)      via Book 7's streaming firm.lobfeat engine
    offline(events, defs, times, lag_events=0) -> (n_times, n_defs) values; lag_events > 0 includes that many events
                                      after each decision (a look-ahead bug to plant)
    OnlineEngine(defs).on(i, events) ; .values(now) -> array ; .newest -> time of the last input seen
    stream(events, defs, times) -> the online values at each decision time
    parity(off, on, tol, sample, seed) -> dict(mismatch share, flagged)
"""
from __future__ import annotations

import pathlib
import sys
from collections import deque
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lobfeat"))
from firm_lobfeat import run as lob_run  # noqa: E402


@dataclass(frozen=True)
class FeatureDef:
    name: str
    input: str
    agg: str
    window: float = 0.0
    version: int = 1


def events_from_tape(tape, levels=5):
    """One row per message: the book's state after it (carried forward over messages that leave a side empty) and the
    message's own contributions (order-flow imbalance increment, traded quantity, signed traded quantity)."""
    m = tape.msgs
    f = lob_run(m, levels)
    ok = (f["bid"] > 0) & (f["ask"] > 0) & (f["ask"] > f["bid"])
    idx = np.maximum.accumulate(np.where(ok, np.arange(len(ok)), int(np.argmax(ok))))   # before the first two-sided
                                                                        # book, its first state
    mid = 0.5 * (f["bid"] + f["ask"]).astype(float)[idx]
    trade = m["kind"] == b"E"
    return {"t": m["t"].astype(float), "mid": mid, "spread": (f["ask"] - f["bid"]).astype(float)[idx],
            "imbalance": np.nan_to_num(f["imbalance"][idx]), "depth": np.nan_to_num(f["depth_imbalance"][idx]),
            "wmid": np.nan_to_num(f["wmid"][idx] - mid), "ofi": np.nan_to_num(f["ofi"].astype(float)),
            "trade_qty": np.where(trade, m["qty"], 0).astype(float),
            "trade_sign": np.where(trade, m["agg"] * m["qty"], 0).astype(float), "one": np.ones(len(m)),
            "is_trade": trade}


def offline(events, defs, times, lag_events=0):
    """Values at each decision time from the events with time <= t (plus lag_events more, to plant a look-ahead)."""
    t = events["t"]
    k = np.searchsorted(t, times, side="right") - 1 + lag_events       # index of the last event known
    k = np.clip(k, -1, len(t) - 1)
    out = np.zeros((len(times), len(defs)))
    for j, d in enumerate(defs):
        x = events[d.input]
        if d.agg == "last":
            out[:, j] = np.where(k >= 0, x[np.maximum(k, 0)], 0.0)
            continue
        if d.agg == "change":
            k0 = np.searchsorted(t, times - d.window, side="right") - 1
            out[:, j] = x[np.maximum(k, 0)] - x[np.maximum(k0, 0)]
            continue
        c = np.r_[0.0, np.cumsum(x if d.agg == "sum" else np.ones_like(x))]
        k0 = np.searchsorted(t, times - d.window, side="right")        # first event inside (t - w, t]
        out[:, j] = c[k + 1] - c[k0]
    return out


class OnlineEngine:
    """Running windows over a stream of events: a deque per windowed feature, the last value for the others."""

    def __init__(self, defs):
        self.defs = defs
        self.q = [deque() for _ in defs]
        self.s = np.zeros(len(defs))
        self.last = {}
        self.hist = {}
        self.newest = -np.inf

    def on(self, i, ev):
        t = ev["t"][i]
        self.newest = t
        for j, d in enumerate(self.defs):
            x = ev[d.input][i]
            if d.agg == "last":
                self.last[d.input] = x
            elif d.agg == "change":
                self.hist.setdefault(j, deque()).append((t, x))
                self.last[d.input] = x
            else:
                v = x if d.agg == "sum" else 1.0
                self.q[j].append((t, v))
                self.s[j] += v

    def values(self, now):
        out = np.zeros(len(self.defs))
        for j, d in enumerate(self.defs):
            if d.agg == "last":
                out[j] = self.last.get(d.input, 0.0)
            elif d.agg == "change":
                h = self.hist.get(j, deque())
                while len(h) > 1 and h[1][0] <= now - d.window:
                    h.popleft()
                base = h[0][1] if h and h[0][0] <= now - d.window else (h[0][1] if h else 0.0)
                out[j] = self.last.get(d.input, 0.0) - base
            else:
                q = self.q[j]
                while q and q[0][0] <= now - d.window:
                    self.s[j] -= q.popleft()[1]
                out[j] = self.s[j]
        return out


def stream(events, defs, times):
    """Feed every event to an OnlineEngine in order and read the values at each decision time, once every event stamped
    at or before it has been processed: what the production service would answer."""
    t = events["t"]
    eng = OnlineEngine(defs)
    out = np.zeros((len(times), len(defs)))
    j = 0
    for i in range(len(t)):
        eng.on(i, events)
        nxt = t[i + 1] if i + 1 < len(t) else np.inf
        while j < len(times) and times[j] < nxt:
            out[j] = eng.values(times[j])
            j += 1
    return out


def parity(off, on, tol=1e-9, sample=None, seed=0):
    """Share of decision times at which any feature differs by more than tol; with `sample`, the check a production
    job can afford: a random sample of that many times, flagged if any of them differs."""
    bad = np.any(np.abs(off - on) > tol, axis=1)
    out = {"mismatch share": float(bad.mean())}
    if sample:
        idx = np.random.default_rng(seed).choice(len(bad), min(sample, len(bad)), replace=False)
        out["flagged"] = bool(bad[idx].any())
    return out


def freshness(engine, now):
    """Seconds since the newest input the online engine has seen: a feature is only as fresh as its inputs."""
    return float(now - engine.newest)
