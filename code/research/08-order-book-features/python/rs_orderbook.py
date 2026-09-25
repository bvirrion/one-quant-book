"""Order-book features (One Quant Book 7, chapter 8).

Three hours of firm.tape (239,528 messages) through firm.lobfeat: the probability that the next mid-price change is
up, by queue-imbalance bucket, against the race of two birth-death queues (Book 4, chapter 8) with rates estimated
from the same messages; the regression of mid-price changes on order-flow imbalance at three sampling intervals;
the weighted mid and a microprice as forecasts of the mid a few seconds later; and a cancellation feature that reads
the stale-quote mechanism of the simulator. NumPy only.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("tape", "lobfeat", "queues"):
    sys.path.insert(0, str(ROOT / c))
from firm_lobfeat import bucket, run  # noqa: E402
from firm_queues import depletion_cdf, race  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402

CFG = TapeConfig(seconds=10_800.0, news_at=None, seed=8)
LOT = 100
NB = 10


@functools.lru_cache(maxsize=1)
def data():
    tp = simulate(CFG)
    f = run(tp.msgs)
    mid = 0.5 * (f["bid"] + f["ask"])
    return tp, f, mid


def next_move(mid: np.ndarray) -> np.ndarray:
    """Sign of the next change of the mid after each message (NaN if none follows)."""
    ch = np.flatnonzero(np.diff(mid) != 0)
    pos = np.searchsorted(ch, np.arange(len(mid)))
    out = np.full(len(mid), np.nan)
    ok = pos < len(ch)
    out[ok] = np.sign(np.diff(mid))[ch[pos[ok]]]
    return out


def buckets(f) -> np.ndarray:
    return np.array([bucket(x, NB) if not np.isnan(x) else -1 for x in f["imbalance"]])


def up_probability():
    """Per imbalance bucket (one-tick spread only): observations, empirical P(next move up), mean queue sizes (lots)."""
    tp, f, mid = data()
    nxt = next_move(mid)
    b = buckets(f)
    sel = (f["ask"] - f["bid"] == 1) & ~np.isnan(nxt)
    out = []
    for k in range(NB):
        s = sel & (b == k)
        out.append({"n": int(s.sum()), "p_up": float((nxt[s] > 0).mean()),
                    "qb": float(np.mean(f["bid_qty"][s]) / LOT), "qa": float(np.mean(f["ask_qty"][s]) / LOT)})
    return out


def best_level_rates():
    """Lots per second joining and leaving the best bid and ask (additions at the best price; cancellations and
    executions there), averaged over both sides."""
    tp, f, mid = data()
    m = tp.msgs
    prev_bid = np.r_[np.nan, f["bid"][:-1]]
    prev_ask = np.r_[np.nan, f["ask"][:-1]]
    at_best = ((m["side"] == 1) & (m["price"] == prev_bid)) | ((m["side"] == -1) & (m["price"] == prev_ask))
    add = (m["kind"] == b"A") & at_best
    rem = (m["kind"] != b"A") & at_best
    T = CFG.seconds
    return float(m["qty"][add].sum() / LOT / T / 2), float(m["qty"][rem].sum() / LOT / T / 2)


def model_up_probability(qb: float, qa: float, birth: float, death: float, horizon: float = 600.0) -> float:
    """P(the ask queue empties before the bid queue) for independent birth-death queues in lots."""
    t = np.linspace(0.0, horizon, 1201)
    cdf_b = depletion_cdf(birth, death, max(1, round(qb)), t)
    cdf_a = depletion_cdf(birth, death, max(1, round(qa)), t)
    p = race(cdf_a, cdf_b, t)
    q = race(cdf_b, cdf_a, t)
    return p / (p + q)                                   # condition on a depletion within the horizon


def ofi_regression(window: float):
    """Regress mid-price changes (ticks) over `window` seconds on OFI scaled by the average best-queue size."""
    tp, f, mid = data()
    g = np.searchsorted(tp.msgs["t"], np.arange(window, CFG.seconds, window))
    dm, do = np.diff(mid[g]), np.diff(f["ofi_cum"][g])
    depth = np.nanmean(f["bid_qty"] + f["ask_qty"]) / 2.0
    X = np.column_stack([np.ones(len(do)), do / depth])
    coef = np.linalg.lstsq(X, dm, rcond=None)[0]
    res = dm - X @ coef
    return {"r2": float(1 - res.var() / dm.var()), "slope": float(coef[1]), "n": len(dm), "depth": float(depth)}


def micro_table(first_half: bool = True) -> np.ndarray:
    """The microprice adjustment g per imbalance bucket: the mean next mid change (ticks) given the bucket, on a
    one-tick spread, estimated on the first half of the session."""
    tp, f, mid = data()
    nxt_change = np.full(len(mid), np.nan)
    ch = np.flatnonzero(np.diff(mid) != 0)
    pos = np.searchsorted(ch, np.arange(len(mid)))
    ok = pos < len(ch)
    nxt_change[ok] = np.diff(mid)[ch[pos[ok]]]
    b = buckets(f)
    half = tp.msgs["t"] < CFG.seconds / 2 if first_half else np.ones(len(mid), bool)
    sel = (f["ask"] - f["bid"] == 1) & ok & half
    return np.array([np.nanmean(nxt_change[sel & (b == k)]) for k in range(NB)])


def forecast_errors(horizons=(1.0, 5.0, 30.0)):
    """Mean squared error (ticks squared) of mid, weighted mid and microprice as forecasts of the mid h seconds
    later, on the second half of the session (the microprice table is fitted on the first)."""
    tp, f, mid = data()
    g = micro_table(True)
    micro = run(tp.msgs, 5, g)["micro"]
    t = tp.msgs["t"]
    test = np.flatnonzero((t >= CFG.seconds / 2) & (t < CFG.seconds - max(horizons)) & ~np.isnan(mid))[::50]
    out = {}
    for h in horizons:
        j = np.searchsorted(t, t[test] + h, side="right") - 1
        target = mid[j]
        out[h] = {k: float(np.mean((x[test] - target) ** 2)) for k, x in (("mid", mid), ("wmid", f["wmid"]),
                                                                           ("micro", micro))}
    return out, g


def cancel_feature(window: float = 1.0):
    """Cancellations at the best ask minus those at the best bid (lots) over the last `window` seconds, and its
    correlation with the next mid-price change: stale quotes are pulled on the side the efficient price has left."""
    tp, f, mid = data()
    m = tp.msgs
    prev_bid, prev_ask = np.r_[np.nan, f["bid"][:-1]], np.r_[np.nan, f["ask"][:-1]]
    cx = m["kind"] == b"X"
    at_a = cx & (m["side"] == -1) & (m["price"] == prev_ask)
    at_b = cx & (m["side"] == 1) & (m["price"] == prev_bid)
    x = np.cumsum(np.where(at_a, m["qty"], 0) - np.where(at_b, m["qty"], 0)) / LOT
    t = m["t"]
    lag = np.searchsorted(t, t - window, side="left")
    feat = x - np.r_[0.0, x][lag]
    nxt = next_move(mid)
    ok = ~np.isnan(nxt) & ~np.isnan(feat)
    return float(np.corrcoef(feat[ok], nxt[ok])[0, 1]), float(np.corrcoef(f["imbalance"][ok], nxt[ok])[0, 1])
