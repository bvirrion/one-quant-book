"""firm.bars -- sampling clocks and continuous series (build of One Quant Book 7, chapter 2).

Bars from a trade stream (times, prices, sizes, optional signs): by time, by number of trades, by
volume, by traded value, and by signed-flow imbalance; the VWAP; as-of sampling of a quote stream;
and continuous futures series from nearby contracts with back- and ratio-adjustment. A bar that
closes on a threshold closes on the trade that crosses it (trades are never split). NumPy only.

API (stable):
    Bars                                   dataclass of arrays: start, end (times), open, high, low, close,
                                           volume, value, vwap, n (trades), first, last (trade indices)
    time_bars(t, px, qty, width, t0, t1)   empty intervals repeat the last close with n = 0
    tick_bars(t, px, qty, n)               every n trades
    volume_bars(t, px, qty, threshold)     close when cumulative volume reaches the threshold
    dollar_bars(t, px, qty, threshold)     close when cumulative traded value reaches the threshold
    imbalance_bars(t, px, qty, sign, expected_n, alpha=0.1)   tick-imbalance bars (Lopez de Prado)
    vwap(px, qty)
    asof(times, values, at)                last value at or before each time (NaN before the first)
    continuous(c1, c2, expiry, days_before)  held, back-adjusted and ratio-adjusted series from the nearby
                                           and next contracts, rolling `days_before` trading days before expiry
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Bars:
    start: np.ndarray
    end: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray
    value: np.ndarray
    vwap: np.ndarray
    n: np.ndarray
    first: np.ndarray
    last: np.ndarray

    def __len__(self) -> int:
        return len(self.close)

    def returns(self) -> np.ndarray:
        return np.diff(np.log(self.close))


def vwap(px, qty) -> float:
    px, qty = np.asarray(px, float), np.asarray(qty, float)
    return float((px * qty).sum() / qty.sum())


def _from_cuts(t, px, qty, first, last) -> Bars:
    """Bars over trade index ranges [first[i], last[i]] (inclusive, non-empty)."""
    t, px, qty = np.asarray(t, float), np.asarray(px, float), np.asarray(qty, float)
    cv, cq = np.concatenate([[0.0], np.cumsum(px * qty)]), np.concatenate([[0.0], np.cumsum(qty)])
    hi = np.array([px[a:b + 1].max() for a, b in zip(first, last, strict=True)])
    lo = np.array([px[a:b + 1].min() for a, b in zip(first, last, strict=True)])
    vol, val = cq[last + 1] - cq[first], cv[last + 1] - cv[first]
    return Bars(t[first], t[last], px[first], hi, lo, px[last], vol, val, val / vol, last - first + 1, first, last)


def _threshold_cuts(x, threshold: float):
    """Close a bar on the element at which the running sum of x reaches the threshold."""
    last, run = [], 0.0
    for i, v in enumerate(x):
        run += v
        if run >= threshold:
            last.append(i)
            run = 0.0
    last = np.array(last, dtype=int)
    first = np.concatenate([[0], last[:-1] + 1]) if len(last) else last
    return first, last


def tick_bars(t, px, qty, n: int) -> Bars:
    last = np.arange(n - 1, len(px), n)
    return _from_cuts(t, px, qty, last - n + 1, last)


def volume_bars(t, px, qty, threshold: float) -> Bars:
    first, last = _threshold_cuts(np.asarray(qty, float), threshold)
    return _from_cuts(t, px, qty, first, last)


def dollar_bars(t, px, qty, threshold: float) -> Bars:
    first, last = _threshold_cuts(np.asarray(px, float) * np.asarray(qty, float), threshold)
    return _from_cuts(t, px, qty, first, last)


def time_bars(t, px, qty, width: float, t0: float, t1: float) -> Bars:
    """Bars on [t0 + k width, t0 + (k + 1) width); an empty bar repeats the previous close."""
    t, px, qty = np.asarray(t, float), np.asarray(px, float), np.asarray(qty, float)
    edges = t0 + width * np.arange(int(round((t1 - t0) / width)) + 1)
    k = len(edges) - 1
    lo_i = np.searchsorted(t, edges[:-1], side="left")
    hi_i = np.searchsorted(t, edges[1:], side="left") - 1
    out = {f: np.zeros(k) for f in ("open", "high", "low", "close", "volume", "value", "vwap")}
    n = np.maximum(0, hi_i - lo_i + 1)
    prev = px[0]
    for j in range(k):
        if n[j] == 0:
            for f in ("open", "high", "low", "close", "vwap"):
                out[f][j] = prev
            continue
        a, b = lo_i[j], hi_i[j]
        seg, q = px[a:b + 1], qty[a:b + 1]
        out["open"][j], out["high"][j], out["low"][j], out["close"][j] = seg[0], seg.max(), seg.min(), seg[-1]
        out["volume"][j], out["value"][j] = q.sum(), (seg * q).sum()
        out["vwap"][j] = out["value"][j] / out["volume"][j]
        prev = seg[-1]
    return Bars(edges[:-1], edges[1:], out["open"], out["high"], out["low"], out["close"], out["volume"],
                out["value"], out["vwap"], n, lo_i, hi_i)


def imbalance_bars(t, px, qty, sign, expected_n: float, alpha: float = 0.1) -> Bars:
    """Tick-imbalance bars: a bar closes when |sum of signs| since its start reaches E[T] |2 P(b = 1) - 1|,
    both expectations updated by an exponentially weighted average of the bars already closed (the
    first bar uses expected_n and the sample's own buy share up to that point as a starting value).
    With balanced flow E[T] |2 P(b = 1) - 1| collapses towards zero and every trade would close a bar,
    so the threshold is floored at sqrt(E[T]), the level a random walk of signs first reaches after
    E[T] steps on average."""
    sign = np.asarray(sign, float)
    e_t, e_b = float(expected_n), float(np.clip(np.mean(sign[: max(1, int(expected_n))]), -0.9, 0.9))
    last, theta, start = [], 0.0, 0
    for i, b in enumerate(sign):
        theta += b
        if abs(theta) >= max(1.0, e_t * abs(e_b), np.sqrt(e_t)):
            last.append(i)
            n_bar = i - start + 1
            e_t = (1 - alpha) * e_t + alpha * n_bar
            e_b = (1 - alpha) * e_b + alpha * np.mean(sign[start:i + 1])
            theta, start = 0.0, i + 1
    last = np.array(last, dtype=int)
    first = np.concatenate([[0], last[:-1] + 1]) if len(last) else last
    return _from_cuts(t, px, qty, first, last)


def asof(times, values, at) -> np.ndarray:
    times, values = np.asarray(times, float), np.asarray(values, float)
    i = np.searchsorted(times, np.asarray(at, float), side="right") - 1
    out = np.where(i >= 0, values[np.maximum(i, 0)], np.nan)
    return out


def continuous(c1, c2, expiry, days_before: int = 5) -> dict[str, np.ndarray]:
    """Continuous series from the nearby (c1) and next (c2) settlement series, as published: c1 is the
    contract expiring first and becomes the old c2 on the day after its last trading day, marked True
    in `expiry`. The position rolls at the close of the day `days_before` trading days before each
    expiry: from the next day the series follows the next contract (c2 until the expiry, then c1).
    The roll gap is measured on the roll day's settlements. Back-adjustment adds each gap to every
    earlier price, ratio adjustment multiplies every earlier price by c2 / c1; the latest prices are
    unchanged. Returns dict(held, back, ratio, rolls) with rolls the indices of the roll days."""
    c1, c2, expiry = np.asarray(c1, float), np.asarray(c2, float), np.asarray(expiry, bool)
    n = len(c1)
    rolls = np.array([e - days_before for e in np.flatnonzero(expiry) if e - days_before >= 0], dtype=int)
    held = c1.copy()
    for r, e in zip(rolls, np.flatnonzero(expiry)[-len(rolls):] if len(rolls) else [], strict=True):
        held[r + 1:e + 1] = c2[r + 1:e + 1]
    add, mul = np.zeros(n), np.ones(n)
    a, m = 0.0, 1.0
    roll_at = set(rolls.tolist())
    for i in range(n - 1, -1, -1):
        if i in roll_at:
            a += c2[i] - c1[i]
            m *= c2[i] / c1[i]
        add[i], mul[i] = a, m
    return {"held": held, "back": held + add, "ratio": held * mul, "rolls": rolls}
