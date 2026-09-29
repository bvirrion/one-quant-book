"""Observability and incident response (One Quant Book 15, chapter 28).

The chain capture -> tick store -> position service -> real-time risk is observed through one service-level indicator:
each second of the trading day is good if the market data the risk service is using is at most five seconds old. On
a quiet day the age is the chain's latency (tens of milliseconds) plus rare pauses -- a burst, a collection, a slow
disk -- during which it grows one second per second until the pause ends; pauses arrive 0.8 an hour with Pareto
durations (minimum one second, tail 1.5). Three incidents are replayed on a quiet day: a feed stall at 12:03 lasting 21
minutes, intermittent stalls of 20 seconds every minute from 11:48 to 12:03, and a slow consumer from 14:00 whose lag
grows by 0.05 seconds each second. Alert rules -- a process heartbeat, static thresholds on the age, and multi-window
burn-rate alerts on a 99.9% objective -- are compared on time to detect each incident and on false pages over thirty
quiet days. A traced message shows where the time goes.
"""
from __future__ import annotations

import io
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/observe"))
import firm_observe as O  # noqa: E402

DAY = 23_400                                   # 09:30 to 16:00, in seconds
OPEN_H = 9.5
FRESH = 5.0                                    # a second is good if the data is at most 5 s old
TARGET = 0.999
BURN_RULES = [(3600, 300, 14.4), (21_600, 1800, 6.0)]
RULES = {"process heartbeat": None, "age above 5 s": 5.0, "age above 30 s": 30.0, "age above 60 s": 60.0,
         "burn rate (1 h and 6 h)": "burn"}


def clock(t: float) -> str:
    s = int(round(OPEN_H * 3600 + t))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def at(hh: int, mm: int) -> int:
    return int((hh + mm / 60 - OPEN_H) * 3600)


def quiet_day(seed: int, pauses_per_hour: float = 0.8) -> np.ndarray:
    """Seconds of one day: the age of the risk service's market data."""
    rng = np.random.default_rng(seed)
    age = np.exp(np.log(0.05) + 0.5 * rng.standard_normal(DAY))
    for s in rng.uniform(0, DAY, rng.poisson(pauses_per_hour * DAY / 3600)).astype(int):
        d = min(600, int(np.ceil((1 - rng.random()) ** (-1 / 1.5))))
        e = min(DAY, s + d)
        age[s:e] += np.arange(1, e - s + 1)
    return age


INCIDENTS = {"feed stall": (at(12, 3), 21 * 60), "intermittent stalls": (at(11, 48), 15 * 60),
             "slow consumer": (at(14, 0), 60 * 60)}


def incident(kind: str, seed: int = 999) -> np.ndarray:
    age = quiet_day(seed)
    start, length = INCIDENTS[kind]
    t = np.arange(length)
    if kind == "feed stall":
        age[start:start + length] = np.maximum(age[start:start + length], t + 1)
    elif kind == "intermittent stalls":
        j = t % 60
        age[start:start + length] = np.maximum(age[start:start + length], np.where(j < 20, j + 1, 0))
    else:
        age[start:start + length] = np.maximum(age[start:start + length], 0.05 * (t + 1))
    return age


def pages(rule, age: np.ndarray) -> list[int]:
    if rule is None:
        return []                                  # the process never stopped
    if rule == "burn":
        return O.burn_rate_pages(age > FRESH, TARGET, BURN_RULES)
    return O.threshold_pages(age, rule)


def time_to_detect(rule, kind: str) -> float | None:
    start, length = INCIDENTS[kind]
    after = [p for p in pages(rule, incident(kind)) if start <= p < start + length + 3600]
    return float(after[0] - start) if after else None


def month(days: int = 30, pauses_per_hour: float = 0.8) -> np.ndarray:
    return np.concatenate([quiet_day(d, pauses_per_hour) for d in range(1, days + 1)])


def false_pages(pauses_per_hour: float, days: int = 30) -> dict:
    """Exercise 7: pages a month on quiet days with more frequent pauses."""
    q = month(days, pauses_per_hour)
    return {name: len(pages(rule, q)) * 30 / days for name, rule in RULES.items()}


def compare(days: int = 30) -> list[dict]:
    quiet = month(days)
    rows = []
    for name, rule in RULES.items():
        rows.append({"rule": name, **{k: time_to_detect(rule, k) for k in INCIDENTS},
                     "false_pages": len(pages(rule, quiet)) * 30 / days})
    return rows


def budget(days: int = 30) -> dict:
    q = month(days)
    bad = int((q > FRESH).sum())
    return {"bad_seconds": bad, "budget_seconds": (1 - TARGET) * len(q),
            "used": O.error_budget_used(bad, len(q), TARGET),
            "pauses_over_5s": int(np.sum((q[1:] > FRESH) & (q[:-1] <= FRESH)))}


# ------------------------------------------------------------ one traced message
STAGES = [("capture", "tickcap", 0.00002), ("store", "tickstore", 0.0002), ("positions", "posservice", 0.0001),
          ("risk: queue", "rtrisk", None), ("risk: compute", "rtrisk", 0.001)]


def traced(ts: float, lag: float, stream=None) -> list:
    """The spans of one market-data message through the chain, the risk queue waiting `lag` s."""
    tr, stream = O.Tracer(prefix=f"m{int(ts)}-"), stream or io.StringIO()
    root = tr.start("market data message", "feed", ts)
    t = ts
    for name, service, d in STAGES:
        d = lag if d is None else d
        s = tr.start(name, service, t, parent=root)
        O.log(stream, t, "INFO", service, name, trace=s.trace_id, span=s.span_id, seconds=d)
        t += d
        tr.finish(s, t)
    tr.finish(root, t)
    return tr.trace(root.trace_id)


def stall_timeline() -> list[tuple]:
    kind = "feed stall"
    start, length = INCIDENTS[kind]
    age = incident(kind)
    alerts = [(p, "alert", f"{name}: page") for name, rule in RULES.items() if rule is not None
              for p in pages(rule, age) if start <= p < start + length + 3600]
    fresh = start + 6 + int(np.argmax(age[start + 6:] <= FRESH))           # first good second after it
    logs = [(start, "log", "tickcap: last message on the quote channels"), (start + length, "log",
            "tickcap: quote channels resume"), (fresh, "log", "rtrisk: data age back under 5 s")]
    return O.timeline(alerts, logs)
