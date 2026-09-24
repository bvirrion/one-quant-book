"""Initial-margin models (build of One Quant Book 6, chapter 25).

- Historical-simulation IM: the (1 - q) quantile loss of the portfolio over h-day overlapping moves in a
  look-back window; filtered historical simulation rescales past moves to today's EWMA volatility.
- A sensitivity-based bilateral IM with the shape of the industry's standard model: delta sensitivities per
  tenor, risk weights and a tenor correlation matrix (parameters are illustrative inputs, not the
  licensed calibration), IM = sqrt(WS' R WS).
- The BCBS-IOSCO standardised schedule: a share of notional by asset class and duration, netted as
  0.4 x gross + 0.6 x NGR x gross.
- Anti-procyclicality tools: a buffer held in calm markets and released in stress, a weight on a stressed
  period, and a floor from a long look-back.
- Backtest: the days on which the realised h-day loss exceeded the margin held.
"""
import math
from collections.abc import Sequence

import numpy as np

SCHEDULE = {("ir", 0): 0.01, ("ir", 2): 0.02, ("ir", 5): 0.04, ("fx", 0): 0.06, ("equity", 0): 0.15,
            ("commodity", 0): 0.15, ("credit", 0): 0.02, ("credit", 2): 0.05, ("credit", 5): 0.10}


def overlapping(changes: np.ndarray, h: int) -> np.ndarray:
    """h-day overlapping sums of daily factor changes (rows oldest first)."""
    c = np.cumsum(np.vstack([np.zeros((1, changes.shape[1])), changes]), axis=0)
    return c[h:] - c[:-h]


def hs_im(pnl: np.ndarray, q: float = 0.99) -> float:
    losses = np.sort(-np.asarray(pnl))[::-1]
    k = max(1, math.ceil((1 - q) * len(losses) - 1e-9))
    return float(max(losses[k - 1], 0.0))


def ewma_vol(x: np.ndarray, lam: float = 0.97) -> tuple[np.ndarray, np.ndarray]:
    v, s2 = np.empty_like(x), x[:20].var(axis=0) + 1e-18
    for t in range(x.shape[0]):
        v[t] = np.sqrt(s2)
        s2 = lam * s2 + (1 - lam) * x[t] ** 2
    return v, np.sqrt(s2)


def fhs_moves(daily: np.ndarray, h: int, lam: float = 0.97) -> np.ndarray:
    """Filter daily moves to today's volatility, then form h-day overlapping sums."""
    past, now = ewma_vol(daily, lam)
    return overlapping(daily / past * now, h)


def simm_like(sens: np.ndarray, tenors: Sequence[float], rw: Sequence[float], theta: float = 0.03,
              floor: float = 0.40) -> float:
    """sqrt(WS' R WS) with WS = RW x sensitivity and rho = max(exp(-theta |Tk - Tl| / min), floor)."""
    ws = np.asarray(rw) * np.asarray(sens)
    R = np.array([[1.0 if a == b else max(math.exp(-theta * abs(a - b) / min(a, b)), floor) for b in tenors]
                  for a in tenors])
    return math.sqrt(max(float(ws @ R @ ws), 0.0))


def schedule_rate(asset: str, duration: float = 0.0) -> float:
    if asset in ("ir", "credit"):
        b = 5 if duration > 5 else (2 if duration > 2 else 0)
        return SCHEDULE[(asset, b)]
    return SCHEDULE[(asset, 0)]


def schedule_im(trades: Sequence[tuple[str, float, float]], net_replacement: float,
                gross_replacement: float) -> dict:
    """trades: (asset class, notional, duration). Net IM = 0.4 gross + 0.6 NGR gross."""
    gross = sum(abs(n) * schedule_rate(a, d) for a, n, d in trades)
    ngr = net_replacement / gross_replacement if gross_replacement > 0 else 1.0
    return {"gross": gross, "ngr": ngr, "net": gross * (0.4 + 0.6 * ngr)}


def apc_buffer(model: np.ndarray, stress: np.ndarray, buffer: float = 0.25, rebuild_days: int = 20) -> np.ndarray:
    """Charge (1 + buffer) x model in calm periods. In stress the buffer absorbs increases: the charge is the
    larger of the model and the last calm charge. After stress the buffer is rebuilt linearly."""
    out = np.empty_like(model)
    last_calm, w = (1 + buffer) * model[0], 1.0
    for t in range(len(model)):
        if stress[t]:
            out[t] = max(model[t], last_calm)
            w = 0.0
        else:
            w = min(1.0, w + 1.0 / rebuild_days)
            out[t] = model[t] * (1 + buffer * w)
            last_calm = out[t]
    return out


def apc_stressed_weight(model: np.ndarray, stressed_im: float, weight: float = 0.25) -> np.ndarray:
    return np.maximum(model, weight * stressed_im + (1 - weight) * model)


def backtest(im: np.ndarray, realised_loss: np.ndarray) -> int:
    return int(np.sum(realised_loss > im))


def peak_increase(im: np.ndarray, base: float) -> float:
    return float(np.max(im) - base)
