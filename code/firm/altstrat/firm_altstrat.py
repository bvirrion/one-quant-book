"""firm.altstrat -- from an alternative dataset to a position (build of One Quant Book 8, chapter 16).

An alternative panel measures each company's coming earnings surprise with noise and is delivered some days before the
announcement. The nowcast is the panel's reading scaled by a slope estimated on past quarters. The data diffuse: a share
of the market buys the same panel, and on the delivery day that share moves the price by its share of the announcement's
expected jump, which is then missing from the announcement itself. The book holds the nowcast from the close of the
delivery day through the announcement. NumPy only.

API (stable):
    measure(surprise, noise, rng)                 the panel's reading: surprise + noise x standard normal
    nowcast_slope(readings, surprises)            least-squares slope of past surprises on past readings
    diffuse(R, events, jump, phi, lead, reading, shrink)
                                                  returns with a share phi of each announcement's expected jump moved to
                                                  the delivery day (events: (day, id); jump: per id, per unit surprise)
    pre_event_book(events, nowcast, lead, T, N)   weights from each delivery's close to the announcement's close,
                                                  proportional to the nowcast, gross one
"""
from __future__ import annotations

import numpy as np


def measure(surprise, noise: float, rng):
    s = np.asarray(surprise, float)
    return s + noise * rng.standard_normal(s.shape)


def nowcast_slope(readings, surprises):
    x, y = np.asarray(readings, float), np.asarray(surprises, float)
    return float((x * y).sum() / (x * x).sum())


def diffuse(R, events, jump, phi: float, lead: int, reading, shrink: float):
    """For each event (t, i) with reading m: add phi x jump[i] x shrink x m to day t - lead's return and subtract it
    from day t's, so the total move is unchanged and a share of it arrives when the panel is delivered."""
    out = np.array(R, float, copy=True)
    for (t, i), m in zip(events, reading, strict=True):
        if t - lead < 0 or not np.isfinite(out[t, i]) or not np.isfinite(out[t - lead, i]):
            continue
        move = phi * jump[i] * shrink * m
        out[t - lead, i] = (1 + out[t - lead, i]) * np.exp(move) - 1
        out[t, i] = (1 + out[t, i]) * np.exp(-move) - 1
    return out


def pre_event_book(events, nowcast, lead: int, T: int, N: int):
    """Hold nowcast-proportional positions from the close of the delivery day (t - lead) to the close before the
    announcement's (weights at close d earn day d + 1), scaled each day to gross one."""
    raw = np.zeros((T, N))
    for (t, i), f in zip(events, nowcast, strict=True):
        a = max(t - lead, 0)
        raw[a:t, i] += f
    g = np.abs(raw).sum(axis=1, keepdims=True)
    return np.where(g > 0, raw / np.maximum(g, 1e-300), 0.0)
