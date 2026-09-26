"""One Quant Book 10, chapter 25: bands, pauses and halts in the simulated market, and the magnet effect.

    MARKET, crash(policy, seed, anticipate)   a five-minute session of firm.agentmkt with a seller who sends
                                   40,000 shares as sixty market orders from the first minute; an optional
                                   anticipating seller who sells faster the closer the best bid is to a published
                                   lower band (it acts only when a band is enforced); the venue runs the policy
    Anticipator                    that seller
    magnet_study(seeds)            first passage: for each session and distance x (ticks from the lower LULD-style
                                   band), the first time the best bid is within x ticks; did it come within one tick
                                   of the band in the next 30 seconds? With the band enforced and anticipating
                                   sellers, with the band alone, and without a band (computed but not enforced)
    mechanisms_study(seeds)        the same crash with no mechanism, LULD-style bands and pauses, velocity logic, and a
                                   market-wide halt: largest fall, seconds halted or paused, the crash seller's fills
    example()                      one session with bands and a pause, for the chapter's figure
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("halts", "agentmkt", "exchsim"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_agentmkt import SEC, T0, Metaorder, PopulationConfig, session  # noqa: E402
from firm_exchsim import Agent, ExchangeConfig, Order, Phases  # noqa: E402
from firm_halts import LULD, MarketWide, Velocity  # noqa: E402

MARKET = PopulationConfig(lo_rate=3.0, near=0.3, cancel=0.05, depth=10, fund=0.05)
SECONDS, CRASH_QTY, CHILDREN = 300.0, 40_000, 60
BAND, WINDOW, LIMIT_S, PAUSE_S = 0.0015, 60.0, 3.0, 20.0
TICK = 100


class Anticipator(Agent):
    """Every half second: if a band is enforced and the best bid is within `within` ticks of its lower edge, sell
    lots x (1 + (within - distance) / within) at the market: the closer, the faster."""

    name = "anticipator"

    def __init__(self, policy, within: int = 8, lots: int = 3):
        self.p, self.within, self.lots = policy, within, lots

    def on_start(self, ctx):
        ctx.set_timer(T0 + SEC - ctx.now_ns, 0)

    def on_timer(self, ctx, tag):
        lo, bid = self.p.band[0], ctx.top(1)[0]
        if lo and bid is not None and not self.p.shadow and self.p.paused_until is None:
            d = (bid - lo) / TICK
            if 0 < d <= self.within:
                ctx.send(Order(side="S", qty=100 * int(self.lots * (1 + (self.within - d) / self.within)), price=0,
                               tif="I"))
        ctx.set_timer(SEC // 2, 0)


def luld(shadow: bool = False) -> LULD:
    return LULD(BAND, window_s=WINDOW, limit_state_s=LIMIT_S, pause_s=PAUSE_S, shadow=shadow)


def crash(policy, seed: int, anticipate: bool = False):
    end = T0 + int(SECONDS * SEC)
    cfg = ExchangeConfig(phases=Phases(start_ns=T0 - SEC, open_ns=T0, close_ns=end, end_ns=end + 1), halts=policy)
    agents = [Metaorder([(T0 + 60 * SEC, -1, CRASH_QTY, CHILDREN, 60 * SEC)])]
    if anticipate:
        agents.append(Anticipator(policy))
    res, _ = session(MARKET, SECONDS, seed, agents=agents, venue=cfg)
    return res


XS = tuple(range(2, 13))
HORIZON = 30.0


def first_passage(dist, xs=XS, horizon: float = HORIZON) -> dict:
    t = np.array([a for a, _, _ in dist])
    d = np.array([b for _, b, _ in dist])
    da = np.array([c for _, _, c in dist])
    near = np.nonzero((d <= 1) | (da <= 1))[0]
    t_hit = t[near[0]] if len(near) else np.inf
    out = {}
    for x in xs:
        first = np.nonzero((d <= x) & (d > 1) & (t < t_hit))[0]
        if len(first):
            out[x] = bool(t_hit <= t[first[0]] + horizon)
    return out


@functools.cache
def magnet_study(seeds=tuple(range(1, 81))) -> dict:
    conds = {"band and anticipators": (False, True), "band alone": (False, False), "no band": (True, False)}
    out = {}
    for name, (shadow, anticipate) in conds.items():
        obs = {x: [] for x in XS}
        for s in seeds:
            pol = luld(shadow)
            crash(pol, 2500 + s, anticipate)
            for x, hit in first_passage(pol.dist).items():
                obs[x].append(hit)
        out[name] = {x: (len(v), float(np.mean(v)), float(math.sqrt(np.mean(v) * (1 - np.mean(v)) / len(v))))
                     for x, v in obs.items() if v}
    mid = range(3, 8)
    for a, b, key in (("band and anticipators", "band alone", "magnet"), ("band alone", "no band", "blocking")):
        diffs = [out[a][x][1] - out[b][x][1] for x in mid]
        out[key] = float(np.mean(diffs))
    return out


def _mid(res):
    top = res.tape().top
    ok = (top["bid"] > 0) & (top["ask"] > 0)
    return top["t"][ok], 0.5 * (top["bid"][ok] + top["ask"][ok])


def _halted(log, end: float) -> float:
    total, start = 0.0, None
    for t, ev, _ in log:
        if ev in ("pause", "halt"):
            start = t
        elif ev == "resume" and start is not None:
            total += t - start
            start = None
    return total + (end - start if start is not None else 0.0)


MECHS = ("none", "LULD", "velocity", "market-wide")


def _policy(name: str):
    if name == "none":
        return None
    if name == "LULD":
        return luld()
    if name == "velocity":
        return Velocity(8, window_s=2.0, pause_s=10.0)
    return MarketWide(levels=(0.001, 0.002, 0.003), halt_s=30.0)


@functools.cache
def mechanisms_study(seeds=tuple(range(1, 21))) -> dict:
    out = {}
    for name in MECHS:
        rows = []
        for s in seeds:
            pol = _policy(name)
            res = crash(pol, 2600 + s)
            t, mid = _mid(res)
            f = res.agents["meta"].fills
            q = sum(x[5] for x in f)
            px = sum(x[4] * x[5] for x in f) / q / TICK if q else float("nan")
            rows.append((float(mid[0] - mid.min()), _halted(pol.log, SECONDS) if pol else 0.0, q, float(mid[0] - px)))
        a = np.array(rows)
        out[name] = {"fall": float(a[:, 0].mean()), "halted": float(a[:, 1].mean()), "filled": float(a[:, 2].mean()),
                     "cost": float(np.nanmean(a[:, 3]))}
    return out


@functools.cache
def example(seed: int = 2541) -> dict:
    pol = luld()
    res = crash(pol, seed, anticipate=True)
    t, mid = _mid(res)
    return {"t": t, "mid": mid, "bands": pol.bands, "log": pol.log}
