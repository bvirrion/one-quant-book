"""firm.indexevent -- index membership rules, their prediction, and the event they create (build of One Quant Book 8,
chapter 10).

A rank-based index: on each rank day, stocks are ranked by market capitalisation; a non-member joins if its rank is at
most size - band, a member leaves if its rank is beyond size + band (the band keeps stocks near the cut-off from
flipping in and out). Index funds track a share of each member's shares and trade the changes at the effective date's
close. The demand's price effect follows the square-root law, eta sigma sqrt(Q / V); a share `early` of it is taken
before the announcement by traders who predict the change, the rest accrues from the announcement to the effective date,
and a share `revert` of the whole reverses over the following weeks. Membership is predicted before the rank day by
simulating each stock's capitalisation forward. NumPy only.

API (stable):
    reconstitute(cap, members, size, band)        (new members bool (N,), additions, deletions)
    predict(cap, vol, members, size, band, days, sims, rng)
                                                  probability of being a member after the rank day `days` ahead
    event_push(q, adv, sigma, eta)                square-root price effect of buying q shares (a fraction)
    event_path(push, early, revert, pre, run, post)
                                                  the planted cumulative abnormal log return of one event, day by day
                                                  from `pre` days before the announcement to `post` days after the
                                                  effective date
"""
from __future__ import annotations

import numpy as np


def reconstitute(cap, members, size: int, band: int):
    cap, members = np.asarray(cap, float), np.asarray(members, bool)
    ok = np.isfinite(cap)
    order = np.argsort(-np.where(ok, cap, -np.inf), kind="stable")
    rank = np.empty(len(cap), int)
    rank[order] = np.arange(1, len(cap) + 1)
    rank[~ok] = len(cap) + 1
    add = ~members & (rank <= size - band) & ok
    drop = members & ((rank > size + band) | ~ok)
    return (members | add) & ~drop, add, drop


def predict(cap, vol, members, size: int, band: int, days: int, sims: int = 200, rng=None):
    """cap and vol (daily) as known today; each simulation moves every cap by an independent lognormal step."""
    rng = rng or np.random.default_rng(0)
    cap, vol = np.asarray(cap, float), np.asarray(vol, float)
    hits = np.zeros(len(cap))
    for _ in range(sims):
        c = cap * np.exp(vol * np.sqrt(days) * rng.standard_normal(len(cap)) - 0.5 * vol**2 * days)
        new, _, _ = reconstitute(c, members, size, band)
        hits += new
    return hits / sims


def event_push(q, adv, sigma, eta: float = 0.7):
    return eta * np.asarray(sigma, float) * np.sqrt(np.asarray(q, float) / np.asarray(adv, float))


def event_path(push: float, early: float, revert: float, pre: int = 20, run: int = 24, post: int = 20):
    """Days -pre..-1 before the announcement: early x push accrues evenly (traders who predict the change); day 0: the
    announcement; days 1..run: the rest accrues evenly to the effective close; then revert x push over post days."""
    path = np.zeros(pre + 1 + run + post)
    path[:pre] = early * push * np.arange(1, pre + 1) / pre
    path[pre] = early * push
    path[pre + 1:pre + 1 + run] = early * push + (1 - early) * push * np.arange(1, run + 1) / run
    path[pre + 1 + run:] = push - revert * push * np.arange(1, post + 1) / post
    return path
