"""One Quant Book 10, chapter 24: did the rule make the market better? Market quality on a simulated stock-day panel.

    STOCKS, DAYS, EVENT     20 stocks of different activity, 16 days of ten-minute sessions of firm.agentmkt; the rule
                            starts on day 8 for every other stock (treated(i))
    session_day(i, d, rule) one stock-day: activity from the stock; from the event day on, a market-wide change hits
                            every stock (the hidden value moves three times as often and liquidity providers send a
                            quarter fewer orders: the confounder); for treated stocks after the event an order-to-trade
                            cap that makes the liquidity providers send 30% fewer orders and cancel less
    panel()                 the measures of every stock-day (firm.mktquality), and for the treated stock-days after the
                            event the same day without the rule (common random numbers): the rule's true effect
    study()                 difference-in-differences with stock and day effects and errors clustered by stock, against
                            the treated stocks' before-after change and the truth; the event study by day
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("mktquality", "agentmkt", "exchsim"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_agentmkt import PopulationConfig, session  # noqa: E402
from firm_mktquality import before_after, day_measures, did, event_study  # noqa: E402

STOCKS, DAYS, EVENT = 20, 16, 8
SECONDS = 600.0
MEASURES = ("quoted", "effective", "realised", "impact", "depth", "amihud", "variance_ratio", "otr")


def treated(i: int) -> bool:
    return i % 2 == 0                                          # every other stock by activity: comparable groups


def treated_low(i: int) -> bool:
    return i < STOCKS // 2                                     # the ten least active stocks (exercise)


def activity(i: int) -> float:
    return 0.6 + 0.8 * i / (STOCKS - 1)                      # from 0.6 to 1.4 times the base flow


def config(i: int, d: int, rule: bool) -> PopulationConfig:
    a = activity(i)
    v_rate, lo, cancel = (0.05, 3.0 * a, 0.05) if d < EVENT else (0.15, 2.25 * a, 0.05)   # the market-wide confounder
    if rule:
        lo, cancel = 0.7 * lo, 0.02                            # an order-to-trade cap: fewer quotes, fewer cancels
    return PopulationConfig(lo_rate=lo, near=0.3, cancel=cancel, depth=10, noise=1.0 * a, fund=0.05, v_rate=v_rate)


def session_day(i: int, d: int, rule: bool) -> dict:
    res, _ = session(config(i, d, rule), SECONDS, 24_000 + 100 * i + d)
    tp = res.tape()
    msgs = sum(1 for _, _, m in res.feed_messages() if type(m).__name__[-1] in "AXDU")
    return day_measures(tp.top, tp.trades, msgs, px_per_ccy=100.0)          # tape prices in cents


@functools.cache
def panel(assign: str = "alternate") -> dict:
    """assign: 'alternate' (every other stock by activity) or 'low' (the ten least active)."""
    rule = treated if assign == "alternate" else treated_low
    rows, truth = [], []
    for i in range(STOCKS):
        for d in range(DAYS):
            tr, post = rule(i), d >= EVENT
            m = session_day(i, d, tr and post)
            rows.append((i, d, tr, post, m))
            if tr and post:
                truth.append({k: m[k] - v for k, v in session_day(i, d, False).items()})
    return {"rows": rows, "truth": {k: float(np.mean([t[k] for t in truth])) for k in MEASURES},
            "truth_se": {k: float(np.std([t[k] for t in truth], ddof=1) / np.sqrt(len(truth))) for k in MEASURES}}


@functools.cache
def study(assign: str = "alternate") -> dict:
    p = panel(assign)
    unit = np.array([r[0] for r in p["rows"]])
    day = np.array([r[1] for r in p["rows"]])
    tr = np.array([r[2] for r in p["rows"]])
    po = np.array([r[3] for r in p["rows"]])
    out = {}
    for k in MEASURES:
        y = np.array([r[4][k] for r in p["rows"]])
        out[k] = {"did": did(y, tr, po, unit, day), "ba": before_after(y, tr, po, unit), "truth": p["truth"][k],
                  "truth_se": p["truth_se"][k],
                  "means": {(g, t): float(y[(tr == g) & (po == t)].mean())
                            for g in (True, False) for t in (False, True)}}
    y = np.array([r[4]["quoted"] for r in p["rows"]])
    out["event"] = event_study(y, tr, day, unit, base=EVENT - 1)
    out["daily"] = {g: [float(y[(tr == g) & (day == d)].mean()) for d in range(DAYS)] for g in (True, False)}
    return out
