"""Trade-flow features (One Quant Book 7, chapter 9).

Three hours of firm.tape with a ten-minute toxic episode (the efficient price moves eight times faster and noise
trading does not rise with it, so informed orders go from 15% to 45% of the flow): trade signing by each rule against
the simulator's true signs, with quotes on time and late; the memory of order signs; a Hawkes fit of order arrivals;
VPIN and a mark-out toxicity measure through the episode; Kyle's lambda. NumPy only.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("tape", "tradeflow", "hawkes", "bars"):
    sys.path.insert(0, str(ROOT / c))
from firm_bars import time_bars  # noqa: E402
from firm_hawkes import fit  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402
from firm_tradeflow import (  # noqa: E402
    aggregate_orders,
    bvc,
    hurst_aggvar,
    kyle_lambda,
    lee_ready,
    quote_rule,
    sign_acf,
    tick_rule,
    vpin,
)

EP0, EP_LEN = 5400.0, 600.0
CFG = TapeConfig(seconds=10_800.0, news_at=EP0, news_len=EP_LEN, news_noise=1.0, seed=9)


@functools.lru_cache(maxsize=1)
def tape():
    return simulate(CFG)


def mids(tp):
    return 0.5 * (tp.top["bid"] + tp.top["ask"])


def signing():
    """Share of executions signed correctly by each rule (quotes as-of the trade, or `lag` seconds stale), and the
    share of volume classified correctly by BVC on one-minute bars."""
    tp = tape()
    tr, top = tp.trades, tp.top
    px, s = tr["price"].astype(float), tr["sign"]
    eidx = np.flatnonzero(tp.msgs["kind"] == b"E")
    out = {"quote (on time)": float((quote_rule(px, top["bid"][eidx - 1], top["ask"][eidx - 1]) == s).mean())}
    for lag in (0.2, 1.0):
        j = np.searchsorted(top["t"], tr["t"] - lag, side="right") - 1
        out[f"quote ({lag:g} s late)"] = float((quote_rule(px, top["bid"][j], top["ask"][j]) == s).mean())
        out[f"Lee-Ready ({lag:g} s late)"] = float((lee_ready(px, top["bid"][j], top["ask"][j]) == s).mean())
    out["tick"] = float((tick_rule(px) == s).mean())
    b = time_bars(tr["t"], px, tr["qty"].astype(float), 60.0, 0.0, CFG.seconds)
    dp = np.diff(np.r_[b.close[0], b.close])
    f = bvc(dp, b.volume, float(np.std(dp[b.n > 0])))
    true_buy = np.array([tr["qty"][a:c + 1][s[a:c + 1] > 0].sum() if n else 0.0
                         for a, c, n in zip(b.first, b.last, b.n, strict=True)])
    est = f * b.volume
    right = np.minimum(true_buy, est) + np.minimum(b.volume - true_buy, b.volume - est)
    out["BVC, 1-minute bars (volume)"] = float(right.sum() / b.volume.sum())
    return out


def stale_quotes(lags=(0.05, 0.5, 2.0)):
    """Share of executions the quote rule signs correctly with quotes `lag` seconds stale (exercise 7)."""
    tp = tape()
    tr, top = tp.trades, tp.top
    out = {}
    for lag in lags:
        j = np.searchsorted(top["t"], tr["t"] - lag, side="right") - 1
        out[lag] = float((quote_rule(tr["price"].astype(float), top["bid"][j], top["ask"][j]) == tr["sign"]).mean())
    return out


def orders():
    tp = tape()
    return aggregate_orders(tp.trades["trade"], tp.trades["t"], tp.trades["qty"], tp.trades["sign"])


def memory(lags=(1, 2, 5, 10, 20, 50, 100)):
    _, _, s = orders()
    return dict(zip(lags, sign_acf(s, lags), strict=True)), hurst_aggvar(s)


def signed_flow(n_orders=(5, 20, 100), horizon: float = 10.0):
    """Signed-flow imbalance over the last N aggressive orders: its correlation with the next order's sign, the share
    of next signs it gets right, and its correlation with the mid change over the next and the previous `horizon`
    seconds (what it knows that the price does not, and what the price already shows)."""
    t, q, s = orders()
    tp = tape()
    top, m = tp.top, mids(tp)
    cs, cq = np.cumsum(s * q), np.cumsum(q)
    out = {}
    for n in n_orders:
        f = (cs[n - 1:] - np.r_[0.0, cs[:-n]]) / (cq[n - 1:] - np.r_[0.0, cq[:-n]])
        i = np.arange(n - 1, len(s) - 1)
        f = f[: len(i)]
        j0 = np.searchsorted(top["t"], t[i], side="right") - 1
        ahead = m[np.searchsorted(top["t"], t[i] + horizon, side="right") - 1] - m[j0]
        behind = m[j0] - m[np.searchsorted(top["t"], t[i] - horizon, side="right") - 1]
        out[n] = {"sign_corr": float(np.corrcoef(f, s[i + 1])[0, 1]), "hit": float((np.sign(f) == s[i + 1]).mean()),
                  "ahead": float(np.corrcoef(f, ahead)[0, 1]), "behind": float(np.corrcoef(f, behind)[0, 1])}
    return out


def hawkes_fits():
    """Branching ratio of a Hawkes fit to aggressive-order times: on this tape (activity changes, informed orders,
    the episode), and on a flat tape with no activity process, no news and no informed flow (the planted 0.4)."""
    t, _, _ = orders()
    flat_cfg = TapeConfig(seconds=10_800.0, news_at=None, act_vol=0.0, informed=0.0, seed=9)
    ft = simulate(flat_cfg)
    tf, _, _ = aggregate_orders(ft.trades["trade"], ft.trades["t"], ft.trades["qty"], ft.trades["sign"])
    return fit(t, CFG.seconds), fit(tf, flat_cfg.seconds)


def vpin_series(n_buckets: int = 400, window: int = 20):
    tp = tape()
    tr = tp.trades
    q = tr["qty"].astype(float)
    B = q.sum() / n_buckets
    v = vpin(np.where(tr["sign"] > 0, q, 0.0), q, B, window)
    ends = np.searchsorted(np.cumsum(q), B * np.arange(1, len(v) + 1) - 1e-9)
    return tr["t"][np.minimum(ends, len(tr) - 1)], v, B


def markout_series(horizon: float = 10.0, window: float = 60.0, step: float = 30.0):
    """Rolling mean over `window` seconds of the aggressors' mark-out (ticks) `horizon` seconds after each trade,
    stamped at the end of the window plus the horizon (when it becomes known)."""
    tp = tape()
    tr, top = tp.trades, tp.top
    j = np.searchsorted(top["t"], tr["t"] + horizon, side="right") - 1
    mo = tr["sign"] * (mids(tp)[j] - tr["price"])
    grid = np.arange(window, CFG.seconds - horizon, step)
    vals = np.array([np.mean(mo[(tr["t"] > g - window) & (tr["t"] <= g)]) for g in grid])
    return grid + horizon, vals, mo


def toxicity_race():
    """VPIN and the mark-out measure through the episode: means before and during, the maximum's time, the first
    crossing of each measure's pre-episode 95th percentile after the episode starts, and the share of time outside
    the episode above that threshold (false alarms)."""
    tv, v, B = vpin_series()
    tm, m, mo = markout_series()
    tr = tape().trades
    out = {"bucket": B, "informed_pre": float(tr["informed"][tr["t"] < EP0].mean()),
           "informed_ep": float(tr["informed"][(tr["t"] >= EP0) & (tr["t"] < EP0 + EP_LEN)].mean()),
           "markout_trade_pre": float(mo[tr["t"] < EP0].mean()),
           "markout_trade_ep": float(mo[(tr["t"] >= EP0) & (tr["t"] < EP0 + EP_LEN)].mean())}
    for name, t, x in (("vpin", tv, v), ("markout", tm, m)):
        pre = (t > 600.0) & (t < EP0)
        ep = (t >= EP0) & (t < EP0 + EP_LEN)
        thr = float(np.nanquantile(x[pre], 0.95))
        cross = t[(t >= EP0) & (x > thr)]
        out[name] = {"pre": float(np.nanmean(x[pre])), "ep": float(np.nanmean(x[ep])), "thr": thr,
                     "argmax": float(t[np.nanargmax(x)]), "first": float(cross[0]) if len(cross) else float("nan"),
                     "false": float(np.nanmean(x[~ep & (t > 600.0)] > thr))}
    return out


def kyle(window: float = 10.0):
    tp = tape()
    tr, top = tp.trades, tp.top
    grid = np.arange(window, CFG.seconds, window)
    m = mids(tp)[np.searchsorted(top["t"], grid, side="right") - 1]
    sv = np.cumsum(tr["sign"] * tr["qty"].astype(float))
    k = np.searchsorted(tr["t"], grid, side="right") - 1
    signed = np.diff(np.where(k >= 0, sv[np.maximum(k, 0)], 0.0)) / 100.0
    return kyle_lambda(np.diff(m), signed)
