"""firm.queuevalue -- what a place in the queue is worth (build of One Quant Book 10, chapter 6).

A limit order joins the best price with n orders (or shares) ahead of it. It fills if the orders ahead are traded or
cancelled before it is cancelled itself; when it fills it earns the distance to the mid (spread capture) and loses what
the mid does next (adverse selection). The value of the slot is the product.

API (stable):
    fill_probability(n, mu, theta, nu)       birth-death: market orders at rate mu take one order from the front, each
                                             order ahead cancels at rate theta, ours at rate nu (Book 10, chapter 1)
    expected_time_to_fill(n, mu, theta)      the same queue with our order never cancelled
    slot_value(n, mu, theta, nu, capture, adverse)   fill probability times (capture - adverse), per share
    ENTRY                                    dtype of one observed order: t, side (+1 bid, -1 ask), price, qty, ahead
                                             (shares ahead at entry), n_ahead (orders ahead), filled,
                                             t_fill (first fill, nan if none),
                                             capture (sum over fills of qty x side (mid before - price)),
                                             adverse (sum of qty x side (mid h later - mid before))
    empirical(entries, edges, by)            per bucket of shares ahead: orders, fill share, median time to first fill,
                                             capture and adverse per filled share, value per posted share
    eta_hat(prices)                          uncertainty-zone parameter from one-tick alternations and continuations of
                                             the traded price (Robert and Rosenbaum): N_cont / (2 N_alt)
    implicit_spread(eta, tick)               2 eta tick (Dayri and Rosenbaum)
"""
from __future__ import annotations

import numpy as np

ENTRY = np.dtype([("t", "f8"), ("side", "i1"), ("price", "f8"), ("qty", "i8"), ("ahead", "i8"), ("n_ahead", "i8"),
                  ("filled", "i8"),
                  ("t_fill", "f8"), ("capture", "f8"), ("adverse", "f8")])


def fill_probability(n: int, mu: float, theta: float, nu: float) -> float:
    p = mu / (mu + nu)
    for k in range(1, n + 1):
        p *= (mu + k * theta) / (mu + k * theta + nu)
    return p


def expected_time_to_fill(n: int, mu: float, theta: float) -> float:
    return 1.0 / mu + sum(1.0 / (mu + k * theta) for k in range(1, n + 1))


def slot_value(n: int, mu: float, theta: float, nu: float, capture: float, adverse: float) -> float:
    return fill_probability(n, mu, theta, nu) * (capture - adverse)


def empirical(entries, edges=(0, 1, 1000, 3000, 6000, 10**12), by: str = "ahead") -> list[dict]:
    """Buckets [edges[i], edges[i+1]) of shares ahead (by='ahead') or orders ahead (by='n_ahead'); the bucket [0, 1)
    is the front of a new level."""
    e = np.asarray(entries)
    out = []
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        b = e[(e[by] >= lo) & (e[by] < hi)]
        if len(b) == 0:
            continue
        got = b[b["filled"] > 0]
        fq = got["filled"].sum()
        cap = float(got["capture"].sum() / fq) if fq else float("nan")
        adv = float(-got["adverse"].sum() / fq) if fq else float("nan")
        out.append({"lo": lo, "hi": hi, "orders": len(b), "fill": float(len(got) / len(b)),
                    "t_fill": float(np.median(got["t_fill"] - got["t"])) if len(got) else float("nan"),
                    "capture": cap, "adverse": adv,
                    "value": float((got["capture"].sum() + got["adverse"].sum()) / b["qty"].sum())})
    return out


def eta_hat(prices) -> dict:
    d = np.diff(np.asarray(prices, float))
    d = d[d != 0]
    one = np.abs(d[1:]) == 1
    same = np.sign(d[1:]) == np.sign(d[:-1])
    n_cont, n_alt = int(np.sum(one & same)), int(np.sum(one & ~same))
    return {"eta": n_cont / (2 * n_alt) if n_alt else float("nan"), "continuations": n_cont, "alternations": n_alt}


def implicit_spread(eta: float, tick: float) -> float:
    return 2.0 * eta * tick
