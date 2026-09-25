"""News and events (One Quant Book 8, chapter 17).

Eight years (2,016 days) of a synthetic news stream on 1,000 stocks (firm.newsevent): about 40 items a day,
busier on some days than others, each with a total move of 2% in standard deviation, an attention that falls with
the day's number of items, a share of the move made by machines within a fraction of a second (time constant 0.2
seconds; the share rises from one half with no attention to one with full attention), the rest drifting in over
the next five days, and halts for moves above 5%. Measured: the share of the move still ahead of a trader acting
after 1 millisecond to an hour, and at the next close; the trader's P&L per item at each latency after 10 basis
points a round trip; and a daily trader who reads each item's tone with a text model (error 1.5 times the tone's
spread) and enters at the next close in its direction, holding five days (with 2% daily noise on each stock), by
attention. NumPy only.
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

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "newsevent"))
from firm_newsevent import NewsConfig, immediate_share, remaining, simulate_news  # noqa: E402

DAYS, STOCKS, COST, HOLD, NOISE, READ = 2016, 1000, 0.0010, 5, 0.02, 1.5
LATENCIES = (0.001, 0.01, 0.1, 1.0, 10.0, 60.0, 3600.0)


@functools.lru_cache(maxsize=1)
def items():
    return simulate_news(DAYS, STOCKS, NewsConfig(), np.random.default_rng(17))


def capture(latency):
    """Share of the total absolute move still ahead, weighted by the items' moves, and the mean P&L per item (bp)."""
    it = items()
    w = np.abs(it["tone"])
    rem = remaining(it, latency)
    share = float((w * rem).sum() / w.sum())
    pnl = float((w * rem).mean() - COST)
    return share, 1e4 * pnl


@functools.lru_cache(maxsize=4)
def daily(split: str = "all"):
    """The daily trader's book: items entered at the next close in the tone's direction, held five days with daily
    noise; equal weight across open items. split: 'all', 'quiet' (attention above the median) or 'busy' (below)."""
    it = items()
    rng = np.random.default_rng(18)
    med = np.median(it["attention"])
    keep = {"all": np.ones(len(it), bool), "quiet": it["attention"] > med, "busy": it["attention"] <= med}[split]
    sel = it[keep]
    read = sel["tone"] + READ * 0.02 * np.random.default_rng(19).standard_normal(len(sel))   # a text model's reading
    drift = np.sign(read) * sel["tone"] * (1 - immediate_share(sel["attention"]))
    pnl = np.zeros(DAYS + HOLD + 1)
    cnt = np.zeros(DAYS + HOLD + 1)
    for d, g in zip(sel["day"], drift, strict=True):
        r = g / HOLD + NOISE * rng.standard_normal(HOLD)
        pnl[d + 1:d + 1 + HOLD] += r
        cnt[d + 1:d + 1 + HOLD] += 1
        pnl[d + 1] -= COST
    x = np.where(cnt > 0, pnl / np.maximum(cnt, 1), 0.0)[1:DAYS + 1]
    return {"sr": float(x.mean() / x.std(ddof=1) * math.sqrt(252)), "ret": float(x.mean() * 252),
            "drift_bp": float(1e4 * drift.mean()), "items": int(keep.sum()),
            "right": float((np.sign(read) == np.sign(sel["tone"])).mean())}


def stream():
    it = items()
    return {"items": len(it), "per_day": len(it) / DAYS, "halted": float(it["halted"].mean()),
            "att_median": float(np.median(it["attention"])), "att_min": float(it["attention"].min())}
