"""firm.observe -- metrics, structured logs, traces, SLOs, error budgets and alert rules (Book 15, ch. 28).

Metrics are counters, gauges and latency histograms (Book 13's firm.lathist) in a registry keyed by name and labels.
Log records are dictionaries with a time, a level, a service, an event name and fields, written one JSON object per
line, carrying the trace and span identifiers of the work they describe. A span is one unit of work with its trace
identifier, its own identifier and its parent's, so that a message's path through capture, storage, positions and
risk can be rebuilt. A service-level objective states the share of good events (seconds, requests) required over a
window; the error budget is the bad share it allows. Alert rules are evaluated on a per-second series of good/bad
flags and of values: a static threshold pages when a value exceeds a level; a multi-window burn-rate rule pages when
the error budget is being consumed faster than a rate over both a long and a short window. An incident timeline
merges alerts, logs and spans in time order.

API (stable):
    Registry(): .counter(name, **labels).inc(n) ; .gauge(...).set(v) ; .histogram(...).observe(ns) -> firm.lathist
    log(stream, ts, level, service, event, trace=None, span=None, **fields) -> writes one JSON line
    Tracer(): .start(name, service, ts, parent=None) -> Span ; .finish(span, ts) ; .trace(trace_id) -> [Span]
    SLO(target, window_s).budget(n_events) ; .burn_rate(bad_share) ; error_budget_used(bad, n, target)
    threshold_pages(values, level, min_gap_s) -> [t] ; burn_rate_pages(bad, target, rules, min_gap_s) -> [t]
        rules: [(long_s, short_s, rate)], a page when any rule has both windows' bad share > rate x (1 - target)
    timeline(*event_lists) -> [(t, source, text)] sorted
"""
from __future__ import annotations

import itertools
import json
import pathlib
import sys
from dataclasses import dataclass, field

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lathist"))
from firm_lathist import LatHist  # noqa: E402


# ------------------------------------------------------------ metrics
class Counter:
    def __init__(self):
        self.value = 0

    def inc(self, n: int = 1) -> None:
        self.value += n


class Gauge:
    def __init__(self):
        self.value = 0.0

    def set(self, v: float) -> None:
        self.value = v


class Histogram:
    def __init__(self):
        self.h = LatHist()

    def observe(self, ns: int) -> None:
        self.h.record(int(ns))


class Registry:
    def __init__(self):
        self.metrics: dict = {}

    def _get(self, kind, name, labels):
        key = (name, tuple(sorted(labels.items())))
        if key not in self.metrics:
            self.metrics[key] = kind()
        m = self.metrics[key]
        if not isinstance(m, kind):
            raise TypeError(f"{name} is already a {type(m).__name__}")
        return m

    def counter(self, name, **labels) -> Counter:
        return self._get(Counter, name, labels)

    def gauge(self, name, **labels) -> Gauge:
        return self._get(Gauge, name, labels)

    def histogram(self, name, **labels) -> Histogram:
        return self._get(Histogram, name, labels)


# ------------------------------------------------------------ structured logs and traces
def log(stream, ts: float, level: str, service: str, event: str, trace=None, span=None, **fields) -> dict:
    rec = {"ts": ts, "level": level, "service": service, "event": event, "trace": trace, "span": span, **fields}
    stream.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_id: str | None
    name: str
    service: str
    start: float
    end: float | None = None
    attrs: dict = field(default_factory=dict)


class Tracer:
    def __init__(self, prefix: str = ""):
        self.spans: list[Span] = []
        self._ids = itertools.count(1)
        self.prefix = prefix

    def start(self, name: str, service: str, ts: float, parent: Span | None = None,
              **attrs) -> Span:
        n = next(self._ids)
        trace = parent.trace_id if parent else f"{self.prefix}t{n:06d}"  # a root: new trace
        parent_id = parent.span_id if parent else None
        s = Span(trace, f"{self.prefix}s{n:06d}", parent_id, name, service, ts, None, attrs)
        self.spans.append(s)
        return s

    def finish(self, span: Span, ts: float) -> None:
        span.end = ts

    def trace(self, trace_id: str) -> list[Span]:
        mine = (s for s in self.spans if s.trace_id == trace_id)
        return sorted(mine, key=lambda s: s.start)


# ------------------------------------------------------------ SLOs and alert rules
@dataclass(frozen=True)
class SLO:
    target: float          # share of good events required, e.g. 0.999
    window_s: float        # the period the target applies to

    def budget(self, n_events: int) -> float:
        return (1.0 - self.target) * n_events

    def burn_rate(self, bad_share: float) -> float:
        return bad_share / (1.0 - self.target)


def error_budget_used(bad: int, n: int, target: float) -> float:
    return bad / ((1.0 - target) * n)


def _pages(fire: np.ndarray, min_gap_s: float) -> list[int]:
    """Times at which a rule starts firing; a page is not repeated within min_gap_s."""
    out, last = [], -np.inf
    rising = np.flatnonzero(fire & ~np.concatenate(([False], fire[:-1])))
    for t in rising:
        if t - last >= min_gap_s:
            out.append(int(t))
            last = t
    return out


def threshold_pages(values, level: float, min_gap_s: float = 3600) -> list[int]:
    v = np.asarray(values, dtype=float)
    return _pages(v > level, min_gap_s)


def _window_share(bad: np.ndarray, w: int) -> np.ndarray:
    c = np.concatenate(([0], np.cumsum(bad)))
    t = np.arange(1, len(bad) + 1)
    lo = np.maximum(0, t - w)
    return (c[t] - c[lo]) / w           # share of bad seconds; the missing past counts good


def burn_rate_pages(bad, target: float, rules, min_gap_s: float = 3600) -> list[int]:
    """Multi-window burn-rate alerting: page when, for some rule (long, short, rate), the
    bad share over both the last `long` and `short` seconds exceeds rate x (1 - target)."""
    b = np.asarray(bad, dtype=float)
    fire = np.zeros(len(b), dtype=bool)
    for long_s, short_s, rate in rules:
        lim = rate * (1.0 - target)
        long_ok = _window_share(b, int(long_s)) > lim
        both = long_ok & (_window_share(b, int(short_s)) > lim)
        fire |= both
    return _pages(fire, min_gap_s)


def timeline(*event_lists) -> list[tuple]:
    return sorted(itertools.chain(*event_lists), key=lambda e: (e[0], e[1]))
