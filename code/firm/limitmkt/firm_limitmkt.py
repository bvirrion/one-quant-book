"""firm.limitmkt -- a daily price-limit market layer (build of One Quant Book 8, chapter 18).

Takes fair simple returns (for example firm.synthmkt's, scaled to the volatility of a retail-dominated market) and
produces the prices a market with daily price limits would print. Each stock has a fair log value v and an attention
premium A; its target is v + A. The close moves toward the target but no further than the limit from the previous
close: a target beyond the limit locks the stock at it, and the rest of the move waits for the next day.
Three behaviours are layered on top, each switchable:
* attention: a limit-up close draws buyers the next day, adding a premium to the target that decays geometrically
  (the reversal over the following week that Seasholes and Wu document);
* magnet: a target within `magnet` of the upper limit is pushed to lock with probability `push` (large buyers
  finishing the move, as in Chen, Gao, He, Jiang and Xiong); the close is then above the target;
* queue fills: a buy order joining the queue at a locked limit fills with probability exp(-excess / fill_scale),
  where excess is how far the target is beyond the limit (near one when the lock is pushed).
The open of day t is the previous close moved toward day t-1's fair value plus day t's premium, within the limit:
yesterday's backlog and the attention buying arrive at the open, today's news during the day. NumPy only.

API (stable):
    LimitConfig(...)                         limit width, scale and behaviour parameters
    apply_limits(R, cfg, rng)                R (T, N) fair returns (NaN: not listed) -> dict of (T, N) arrays:
                                             close, open (log prices), fair, premium, up (limit-up close),
                                             down, pushed, fill (queue fill probability on up days, else 0)
    northbound(alpha, skill, rng)            daily foreign net buying, informed by `alpha` with correlation `skill`
    holdings_seen(flow, every, lag)          cumulative holdings as published every `every` days with `lag` days
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LimitConfig:
    limit: float = 0.10               # daily limit, as a simple return
    scale: float = 1.5                # fair returns are multiplied by this (a more volatile market)
    attention: float = 0.03           # log premium added the day after a limit-up close
    decay: float = 0.6                # daily persistence of the premium
    magnet: float = 0.02              # targets within this log distance below the upper limit may be pushed
    push: float = 0.5                 # probability that such a target is pushed to lock
    fill_scale: float = 0.02          # queue fill probability exp(-excess / fill_scale)


def apply_limits(R, cfg: LimitConfig | None = None, rng=None):
    cfg = cfg or LimitConfig()
    rng = rng or np.random.default_rng(18)
    R = np.asarray(R, float)
    T, N = R.shape
    ub, db = np.log1p(cfg.limit), np.log1p(-cfg.limit)
    out = {k: np.zeros((T, N)) for k in ("close", "open", "fair", "premium", "fill")}
    for k in ("up", "down", "pushed"):
        out[k] = np.zeros((T, N), bool)
    v = np.zeros(N)
    p = np.zeros(N)
    A = np.zeros(N)
    up_prev = np.zeros(N, bool)
    for t in range(T):
        live = ~np.isnan(R[t])
        new = live & np.isnan(R[t - 1]) if t > 0 else live
        v[new] = p[new] = A[new] = 0.0
        up_prev[new] = False
        A = cfg.decay * A + cfg.attention * up_prev
        out["open"][t] = p + np.clip(v + A - p, db, ub)
        v = v + np.log1p(np.maximum(cfg.scale * np.nan_to_num(R[t]), -0.95))
        move = v + A - p
        pushed = live & (move < ub) & (move >= ub - cfg.magnet) & (rng.random(N) < cfg.push)
        step = np.where(pushed, ub, np.clip(move, db, ub))
        up = live & (move >= ub) | pushed
        out["fill"][t] = np.where(pushed, 1.0, np.where(up, np.exp(-(move - ub) / cfg.fill_scale), 0.0))
        p = p + np.where(live, step, 0.0)
        out["close"][t], out["fair"][t], out["premium"][t] = p, v, A
        out["up"][t], out["down"][t], out["pushed"][t] = up, live & (move <= db), pushed
        up_prev = up
    return out


def northbound(alpha, skill: float = 0.1, rng=None):
    """Foreign net buying per stock and day: a standardised mix of the expected return and noise."""
    rng = rng or np.random.default_rng(19)
    a = np.nan_to_num(np.asarray(alpha, float))
    z = (a - a.mean(1, keepdims=True)) / (a.std(1, keepdims=True) + 1e-12)
    return skill * z + np.sqrt(1 - skill**2) * rng.standard_normal(a.shape)


def holdings_seen(flow, every: int = 1, lag: int = 0):
    """Cumulative holdings known at each day's close when they are published every `every` days, `lag` days late."""
    H = np.cumsum(flow, axis=0)
    T = len(H)
    seen = np.full_like(H, np.nan)
    for t in range(T):
        s = ((t - lag) // every) * every
        if s >= 0:
            seen[t] = H[min(s, T - 1)]
    return seen
