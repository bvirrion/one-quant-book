"""firm.rfqlink -- request-for-quote connectivity: pipelines, quote timers and client rules (build of One Quant Book
14, chapter 25).

A client sends a request for quote to n dealers and starts a quote timer. Each dealer's answer takes the sum of its
pipeline's stages (lognormal, stated medians and spreads), and a share of requests fall outside the auto-responder's
limits and go to a person (a slower lognormal). Prices follow Book 11's firm.rfqmm model: each dealer bids its own
noisy estimate of value less a markup, and the client sells only at or above a reservation price; the bids are drawn
exactly as firm.rfqmm.simulate draws them, so that with every answer in time the auction is firm.rfqmm's. The client
then applies one of three execution rules: the best answer when the timer expires, the best of the first k answers,
or the first acceptable answer. All parameters are assumptions; results are a labelled simulation.

API (stable):
    Stage(name, median_ms, sigma) ; Pipeline(stages, manual_share=0.0, manual_median_ms=6000.0, manual_sigma=0.5)
    response_ms(pipeline, n, rng) -> answer times ; miss_prob(pipeline, timer_ms, n=200000, seed=0)
    auction(n_dealers, ours, theirs, rule="expiry"|"first_k"|"first_ok", timer_ms=2000.0, k=3,
            our_markup=15.0, comp_markup=15.0, n=40000, seed=0, sigma_est=25.0, urgency=30.0) -> dict
        win (share of requests we win), traded, lost_to_speed (requests where ours was the best acceptable answer
        in time but the rule chose another), missed (our answer after the timer)
    value_of(n_dealers, ours, theirs, rule, faster, cheaper_cents=1.0, **kw) ; scaled(p, factor) ; log_grid(lo, hi)
"""
import math
import pathlib
import sys
from dataclasses import dataclass, field

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "rfqmm"))
import firm_rfqmm as mm  # noqa: E402,F401  (the price model this module reproduces; checked by the tests)


@dataclass(frozen=True)
class Stage:
    name: str
    median_ms: float
    sigma: float


@dataclass(frozen=True)
class Pipeline:
    stages: tuple = field(default=())
    manual_share: float = 0.0
    manual_median_ms: float = 6000.0
    manual_sigma: float = 0.5


def response_ms(p, n, rng):
    t = np.zeros(n)
    for s in p.stages:
        t += s.median_ms * np.exp(s.sigma * rng.standard_normal(n))
    manual = rng.random(n) < p.manual_share
    t[manual] += p.manual_median_ms * np.exp(p.manual_sigma * rng.standard_normal(int(manual.sum())))
    return t


def miss_prob(p, timer_ms, n=200000, seed=0):
    return float(np.mean(response_ms(p, n, np.random.default_rng(seed)) > timer_ms))


def auction(n_dealers, ours, theirs, rule="expiry", timer_ms=2000.0, k=3, our_markup=15.0, comp_markup=15.0,
            n=40000, seed=0, sigma_est=25.0, urgency=30.0):
    rng = np.random.default_rng(seed)
    bids = rng.standard_normal((n, n_dealers)) * sigma_est          # as firm.rfqmm.simulate
    bids[:, 0] -= our_markup
    bids[:, 1:] -= comp_markup
    reservation = -rng.exponential(urgency, n)
    t = np.column_stack([response_ms(ours, n, rng)] + [response_ms(theirs, n, rng) for _ in range(n_dealers - 1)])
    in_time = t <= timer_ms
    ok = in_time & (bids >= reservation[:, None])
    if rule == "expiry":
        chosen = np.where(ok, bids, -np.inf).argmax(axis=1)
    elif rule == "first_k":
        order = np.argsort(np.where(in_time, t, np.inf), axis=1)
        first = np.zeros_like(ok)
        np.put_along_axis(first, order[:, :k], True, axis=1)
        chosen = np.where(ok & first, bids, -np.inf).argmax(axis=1)
        ok = ok & first
    elif rule == "first_ok":
        chosen = np.where(ok, t, np.inf).argmin(axis=1)
    else:
        raise ValueError(rule)
    traded = ok.any(axis=1)
    win = traded & (chosen == 0)
    best_ok = np.where(in_time & (bids >= reservation[:, None]), bids, -np.inf).argmax(axis=1)
    lost = traded & ~win & (best_ok == 0)
    return {"win": float(win.mean()), "traded": float(traded.mean()), "lost_to_speed": float(lost.mean()),
            "missed": float(np.mean(~in_time[:, 0]))}


def value_of(n_dealers, ours, theirs, rule, faster, cheaper_cents=1.0, **kw):
    """Win-rate change from a faster pipeline, and from bidding cheaper_cents better, under one rule."""
    base = auction(n_dealers, ours, theirs, rule, **kw)["win"]
    fast = auction(n_dealers, faster, theirs, rule, **kw)["win"]
    kw2 = dict(kw)
    kw2["our_markup"] = kw.get("our_markup", 15.0) - cheaper_cents
    price = auction(n_dealers, ours, theirs, rule, **kw2)["win"]
    return {"base": base, "faster": fast - base, "cheaper": price - base}


def scaled(p, factor):
    """The same pipeline with every automatic stage's median multiplied by factor."""
    return Pipeline(tuple(Stage(s.name, s.median_ms * factor, s.sigma) for s in p.stages), p.manual_share,
                    p.manual_median_ms, p.manual_sigma)


def log_grid(lo, hi, per_decade=4):
    k = round(math.log10(hi / lo) * per_decade)
    return [lo * 10 ** (i / per_decade) for i in range(k + 1)]
