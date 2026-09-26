"""One Quant Book 10, chapter 21: one risk transfer (USD 50 million) in four markets.

    NOTIONAL, MARKETS                the simulated markets' spreads, daily volatilities and daily volumes (assumptions
                                     of realistic orders of magnitude, not measurements)
    futures()                        an index future: 200 contracts; the roll of the position through legging, the
                                     direct spread book and the implied book (firm.match)
    fx()                             EUR/USD in 20 child requests (firm.acexec's straight-line schedule) to an
                                     aggregator of four last-look streams and one firm stream (firm.lastlook), 2,000
                                     simulated parent orders; against the firm stream alone
    bonds()                          a corporate bond block by request for quote (firm.rfq): the cost against the
                                     number of dealers, split into markup, competition and leakage
    crypto()                         bitcoin across an exchange and a constant-product pool (firm.amm): the best
                                     split; the schedule against a large venue's rate limits (firm.ratelimit)
    table()                          the all-in cost in each market, split into spread, impact and the market's rule
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("xexec", "match", "acexec", "ratelimit"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_acexec import LinearScheduler  # noqa: E402
from firm_match import Quote  # noqa: E402
from firm_ratelimit import binance_like  # noqa: E402
from firm_xexec import (  # noqa: E402
    LP,
    Market,
    cex_amm_split,
    children,
    fx_child,
    orders_allowed,
    rfq,
    roll,
    sqrt_impact_bp,
)

NOTIONAL = 50e6
MARKETS = {"futures": Market("index future", 0.25, 100.0, 200e9),
           "fx": Market("EUR/USD", 0.08, 50.0, 300e9),
           "bond": Market("corporate bond", 5.0, 40.0, 20e6),
           "crypto": Market("bitcoin", 0.5, 300.0, 5e9)}

# futures: prices in hundredths of an index point, tick 25 (0.25 point), 5,000 points x USD 50 = USD 250,000 a lot
PRICE, LOTS, TICK = 500_000, 200, 25
FRONT, BACK, SPREAD = Quote(499_975, 150, 500_000, 120), Quote(501_000, 80, 501_025, 100), Quote(-1025, 60, -1000, 60)


@functools.cache
def futures() -> dict:
    r = roll(FRONT, BACK, SPREAD, LOTS, TICK)
    return {k: v / PRICE * 1e4 for k, v in r.items() if k != "mid"} | {"points": {k: v / 100 for k, v in r.items()}}


LPS = (LP("stream 1", 0.08, 60, 0.06), LP("stream 2", 0.09, 40, 0.06), LP("stream 3", 0.10, 80, 0.08),
       LP("stream 4", 0.11, 20, 0.05), LP("firm", 0.15, 0, 0.0, "none"))
SIGMA_MS = 50.0 / np.sqrt(86_400_000)                    # 50 bp a day, in bp per square-root millisecond
FX_CHILDREN = 20


@functools.cache
def fx(orders: int = 2000, seed: int = 21) -> dict:
    rng = np.random.default_rng(seed)
    q = children(NOTIONAL, LinearScheduler(1.0, 1.0), FX_CHILDREN)
    costs, rej = [], []
    for _ in range(orders):
        c = [fx_child(LPS, SIGMA_MS, rng) for _ in q]
        costs.append(float(np.dot(q, [x[0] for x in c]) / q.sum()))
        rej.append(sum(x[1] for x in c))
    reject_rate = float(np.sum(rej) / (orders * FX_CHILDREN))
    return {"aggregator": float(np.mean(costs)), "firm_only": LPS[-1].half_bp, "best_quote": LPS[0].half_bp,
            "last_look": float(np.mean(costs)) - LPS[0].half_bp, "reject_rate": reject_rate,
            "child": float(q[0])}


BOND = {"markup": MARKETS["bond"].half_spread_bp + sqrt_impact_bp(MARKETS["bond"], NOTIONAL), "sigma": 8.0,
        "leak": 1.5}


@functools.cache
def bonds() -> dict:
    by_n = {n: rfq(n, BOND["markup"], BOND["sigma"], BOND["leak"]) for n in range(1, 11)}
    best = min(by_n, key=lambda n: by_n[n]["total"])
    return {"by_n": by_n, "best_n": best, "best": by_n[best]}


POOL_USD, POOL_FEE, BTC = 1e9, 5, 60_000.0


@functools.cache
def crypto() -> dict:
    s = cex_amm_split(NOTIONAL, MARKETS["crypto"], POOL_USD, POOL_USD / BTC, POOL_FEE)
    return s | {"schedule_ok": orders_allowed(binance_like(), 3_600_000, 12),
                "burst_ok": orders_allowed(binance_like(), 1_000, 120)}


@functools.cache
def table() -> dict:
    out = {}
    f = futures()
    m = MARKETS["futures"]
    out["futures"] = {"spread": m.half_spread_bp, "impact": sqrt_impact_bp(m, NOTIONAL), "rule": f["spread_book"]}
    x = fx()
    m = MARKETS["fx"]
    out["fx"] = {"spread": x["best_quote"], "impact": sqrt_impact_bp(m, NOTIONAL), "rule": x["last_look"]}
    b = bonds()["best"]
    out["bond"] = {"spread": 0.0, "impact": b["markup"], "rule": b["competition"] + b["leakage"]}
    c = crypto()
    m = MARKETS["crypto"]
    out["crypto"] = {"spread": m.half_spread_bp, "impact": sqrt_impact_bp(m, NOTIONAL), "rule": -c["saving"]}
    for v in out.values():
        v["total"] = v["spread"] + v["impact"] + v["rule"]
        v["rule_share"] = v["rule"] / v["total"]
    return out
