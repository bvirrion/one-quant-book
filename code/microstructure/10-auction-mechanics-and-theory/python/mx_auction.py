"""One Quant Book 10, chapter 10: closing auctions and frequent batch auctions on the exchange simulator.

    close_session(seed, random_end_s, extra)   a five-minute closing call with indicatives every second
                                          (firm.auctionsim): standing limit-on-close interest of 500 shares a tick on
                                          each side, random market-on-close orders, a fund's market-on-close buy of
                                          10,000 shares a minute into the call, and responders who sell (buy) at
                                          100.01 (99.99) when the indicative has been pushed away from 100.00;
                                          extra = (seconds before the close, shares) adds one more market-on-close buy
    auction_study(seeds)                  the gap between indicative and final price against the time to the cross, the
                                          arrival of paired volume, and the move of the closing price caused by a
                                          3,000-share buy sent 60, 10 or 1 seconds before a fixed or a random end
    snipe_race(interval_ms, n, ...)       a quoter and a faster sniper see the same public price jumps; the share of
                                          jumps on which the sniper takes the stale quote, continuous (interval 0)
                                          against frequent batch auctions
    race_study()                          snipe_race for intervals 0, 1, 10 and 100 ms and two latency gaps (cached)
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("exchsim", "auctionsim"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_auctionsim import ClosingAuction, final_cross, indicatives  # noqa: E402
from firm_exchsim import (  # noqa: E402
    SEC,
    Agent,
    ExchangeConfig,
    LatencyModel,
    Order,
    Phases,
    SessionSpec,
    Simulator,
)

T0 = 34_200 * SEC
CONT, CALL = 10.0, 300.0
CLOSE = T0 + int((CONT + CALL) * SEC)


class Responder(Agent):
    """Liquidity for the close at the value it believes (ref): when the indicative price has been pushed more than a
    tick away from ref by an imbalance, it offers the other side, at ref plus a one-tick premium, an amount that grows
    with the distance (per_tick shares a tick beyond the premium, capped), with probability prob at each indicative."""
    name = "resp"

    def __init__(self, seed: int, prob: float = 0.5, per_tick: int = 250, cap: int = 3000, ref: int = 1_000_000,
                 premium: int = 100):
        self.rng, self.prob, self.per_tick, self.cap = np.random.default_rng(seed), prob, per_tick, cap
        self.ref, self.premium = ref, premium

    def on_feed(self, ctx, m):
        if type(m).__name__ != "Feed_I" or m.direction not in "BS":
            return
        if self.rng.random() > self.prob:
            return
        side = "S" if m.direction == "B" else "B"
        away = (m.near - self.ref) if side == "S" else (self.ref - m.near)
        dev = away // 100 - self.premium // 100          # ticks beyond the premium
        if dev < 1:
            return
        px = self.ref + (self.premium if side == "S" else -self.premium)
        ctx.send(Order(side=side, qty=min(self.cap, self.per_tick * dev), price=px, tif="C"))


def close_session(seed: int = 1, random_end_s: float = 0.0, extra: tuple | None = None) -> dict:
    """extra = (seconds before the scheduled close, shares): one more market-on-close buy sent then."""
    pol = ClosingAuction(call_s=CALL, indicative_s=1.0, random_end_s=random_end_s)
    cfg = ExchangeConfig(phases=pol.phases(T0, CLOSE, CLOSE + 120 * SEC))
    sim = Simulator(cfg, seed=seed)
    rng = np.random.default_rng(seed + 500)
    t_call = T0 + int(CONT * SEC)
    orders = []
    for k in range(1, 21):                                    # the close's standing interest: 500 shares a tick
        for side, px in (("S", 1_000_000 + 100 * (k - 1)), ("B", 999_900 - 100 * (k - 1))):
            orders.append((t_call + k, "SIMX", Order(side=side, qty=500, price=px, tif="C")))
    t = CONT
    while True:
        t += rng.exponential(1 / 0.2)
        if t >= CONT + CALL - 5:
            break
        side = "B" if rng.random() < 0.5 else "S"
        q = 100 * int(rng.integers(1, 11))
        orders.append((T0 + int(t * SEC), "SIMX", Order(side=side, qty=q, price=0, tif="C")))
    orders.append((T0 + int((CONT + 60) * SEC), "SIMX", Order(side="B", qty=10_000, price=0, tif="C")))
    if extra:
        orders.append((CLOSE - int(extra[0] * SEC), "SIMX", Order(side="B", qty=extra[1], price=0, tif="C")))
    sim.add_events(orders=orders)
    lat = LatencyModel(entry_ns=1_000_000, ack_ns=1_000_000, data_ns=1_000_000)
    sim.add_agent(Responder(seed), SessionSpec(firm="RESP", latency=lat))
    res = sim.run()
    return {"ind": indicatives(res), "final": final_cross(res)}


GRID = (120, 60, 30, 10, 5, 1)
TAUS = (60.0, 10.0, 1.0)
EXTRA = 3000


@functools.cache
def auction_study(seeds=tuple(range(1, 25))) -> dict:
    gaps, arrive = [], []
    for s in seeds:
        r = close_session(s)
        ind, f = r["ind"], r["final"]
        gaps.append([abs(int(ind["price"][max(np.searchsorted(ind["t"], f[0] - int(g * SEC), side="right") - 1, 0)])
                         - f[1]) / 100 for g in GRID])
        arrive.append([ind["paired"][max(np.searchsorted(ind["t"], f[0] - int(g * SEC), side="right") - 1, 0)] / f[2]
                       for g in (300, *GRID)])
    out = {"gap": np.mean(gaps, axis=0), "gap_se": np.std(gaps, axis=0, ddof=1) / np.sqrt(len(seeds)),
           "arrive": np.mean(arrive, axis=0)}
    for end in (0.0, 30.0):
        base = [close_session(s, end)["final"][1] for s in seeds]
        for tau in TAUS:
            moved = np.array([(close_session(s, end, (tau, EXTRA))["final"][1] - b0) / 100
                              for s, b0 in zip(seeds, base, strict=True)])
            se = float(moved.std(ddof=1) / np.sqrt(len(moved)))
            out[(end, tau)] = {"impact": float(moved.mean()), "impact_se": se}
    return out


class Quoter(Agent):
    """Quotes one lot a tick either side of a public reference; on each jump it cancels and requotes."""
    name = "quoter"

    def __init__(self, jumps):
        self.jumps, self.ref, self.live = jumps, 1_000_000, []

    def on_start(self, ctx):
        self._quote(ctx)
        for k, (t, _) in enumerate(self.jumps):
            ctx.set_timer(t - ctx.now_ns, k)

    def _quote(self, ctx):
        self.live = [ctx.send(Order(side="B", qty=100, price=self.ref - 100)),
                     ctx.send(Order(side="S", qty=100, price=self.ref + 100))]

    def on_timer(self, ctx, k):
        for cl in self.live:
            ctx.cancel(cl)
        self.ref += self.jumps[k][1]
        self._quote(ctx)


class Sniper(Agent):
    """On each jump, buys the stale ask (or sells the stale bid) with a day order, cancelled 100 ms later."""
    name = "sniper"

    def __init__(self, jumps):
        self.jumps, self.ref = jumps, 1_000_000

    def on_start(self, ctx):
        for k, (t, _) in enumerate(self.jumps):
            ctx.set_timer(t - ctx.now_ns, ("go", k))

    def on_timer(self, ctx, tag):
        kind, k = tag
        if kind == "go":
            d = self.jumps[k][1]
            side, px = ("B", self.ref + 100) if d > 0 else ("S", self.ref - 100)
            cl = ctx.send(Order(side=side, qty=100, price=px))
            self.ref += d
            ctx.set_timer(SEC // 10, ("cancel", cl))
        else:
            ctx.cancel(k)


def snipe_race(interval_ms: float = 0.0, n: int = 400, quoter_us: float = 200.0, sniper_us: float = 50.0,
               seed: int = 1) -> dict:
    """n public jumps of +-2 ticks, a quarter of a second apart plus a uniform jitter of up to 100 ms; both agents
    react with their entry latency. Returns the share of jumps on which the sniper traded with the stale quote. (Keep
    the interval at 1 ms or more: every batch is a scheduled event.)"""
    rng = np.random.default_rng(seed)
    t0 = T0 + 5 * SEC
    jumps = [(t0 + int((0.25 * k + 0.1 * rng.random()) * SEC), 200 if rng.random() < 0.5 else -200) for k in range(n)]
    end = jumps[-1][0] + 5 * SEC
    ph = Phases(start_ns=T0 - SEC, open_ns=T0, close_ns=end, end_ns=end + 1)
    cfg = ExchangeConfig(phases=ph, batch_interval_ns=int(interval_ms * 1_000_000))
    sim = Simulator(cfg, seed=seed)
    sim.add_agent(Quoter(jumps), SessionSpec(firm="Q", latency=LatencyModel(int(quoter_us * 1000), 1000, 1000)))
    sim.add_agent(Sniper(jumps), SessionSpec(firm="S", latency=LatencyModel(int(sniper_us * 1000), 1000, 1000)))
    res = sim.run()
    return {"sniped": len(res.agents["sniper"].fills) / n, "jumps": n}


@functools.cache
def race_study(intervals=(0.0, 1.0, 10.0, 100.0), gaps=((200.0, 50.0), (1050.0, 50.0))) -> dict:
    return {(iv, q, sn): snipe_race(iv, quoter_us=q, sniper_us=sn)["sniped"] for q, sn in gaps for iv in intervals}
