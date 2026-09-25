"""Short-term futures strategies (One Quant Book 8, chapter 25).

firm.futintraday's ten years of one-minute sessions of an index future (16% volatility, a quarter of it overnight,
U-shaped intraday volatility, a daily trend drift with a standard deviation of 0.4%, one-minute bounce of -0.1,
announcements every 32 trading days with a planted drift of 0.5% from the previous midday to the announcement minute,
cut to 30% of that from the sixth year). The cost of a trade is half the quoted spread measured on a session of Book
7's message-level firm.tape (a price of 100.00 and a tick of 0.01, so one tick is one basis point). Measured: the
opening-range breakout by window, the fade of large five-minute moves by threshold, gross and net, and the
pre-announcement hold before and after the crowding, per event and as a strategy. NumPy only.
"""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
for p in ("futintraday", "tape"):
    sys.path.insert(0, str(ROOT / "firm" / p))
from firm_futintraday import SessionConfig, fade, orb, pre_announcement, simulate_sessions  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402


@functools.lru_cache(maxsize=1)
def tape_cost():
    """Half the time-weighted quoted spread of one tape session, in basis points of a 100.00 price."""
    top = simulate(TapeConfig()).top
    w = np.diff(np.r_[top["t"], top["t"][-1]])
    spread = float(((top["ask"] - top["bid"]) * w).sum() / w.sum())
    return spread / 2, spread


@functools.lru_cache(maxsize=1)
def sessions():
    return simulate_sessions(SessionConfig(), np.random.default_rng(25))


def sr(x):
    return float(np.mean(x) / np.std(x, ddof=1) * math.sqrt(252))


def cost():
    return tape_cost()[0] * 1e-4


def orb_table(windows=(15, 30, 60)):
    S = sessions()
    return {w: (sr(orb(S, w, 0.0)), sr(orb(S, w, cost())), float(1e4 * orb(S, w, cost()).mean())) for w in windows}


def fade_table(thresholds=(1.5, 2.0, 2.5, 3.0)):
    S = sessions()
    return {z: (sr(fade(S, 5, z, 5, 0.0)), sr(fade(S, 5, z, 5, cost()))) for z in thresholds}


def announcements():
    S, cfg = sessions(), SessionConfig()
    x = pre_announcement(S, cost())
    days = np.flatnonzero(S["ann"])
    out = {}
    for name, m in (("before", (days > 0) & (days < cfg.crowd_day)), ("after", days >= cfg.crowd_day)):
        e = x[days[m]]
        out[name] = {"n": int(m.sum()), "bp": float(1e4 * e.mean()),
                     "t": float(e.mean() / e.std(ddof=1) * math.sqrt(len(e))),
                     "sr": float(e.mean() / e.std(ddof=1) * math.sqrt(252 / cfg.every))}
    return out


def announcement_path():
    """Average cumulative return (bp) from the previous day's midday to the announcement day's close, by minute."""
    S, cfg = sessions(), SessionConfig()
    half = cfg.minutes // 2
    days = np.flatnonzero(S["ann"])
    paths = {}
    for name, m in (("before", (days > 0) & (days < cfg.crowd_day)), ("after", days >= cfg.crowd_day)):
        seg = [np.concatenate([S["r"][d - 1, half:], [S["gap"][d]], S["r"][d]]) for d in days[m]]
        paths[name] = 1e4 * np.cumsum(np.mean(seg, axis=0))
    return paths, cfg.minutes - half + 1 + cfg.ann_minute


def fade_stats(z: float = 2.0):
    """Gross mean P&L a day (bp), trades a day, and the cost per side (bp) at which the fade breaks even."""
    S = sessions()
    g = fade(S, 5, z, 5, 0.0)
    n = (g - fade(S, 5, z, 5, 1e-4)) / 2e-4                  # trades a day, from the cost difference
    return float(1e4 * g.mean()), float(n.mean()), float(1e4 * g.mean() / (2 * n.mean()))
