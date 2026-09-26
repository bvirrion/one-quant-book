"""One Quant Book 10, chapter 8: one stock on three venues of the exchange simulator.

    market(seconds, seed, arb, sip_ns, lags)   three venues (A, B, C) whose background flows share one efficient
                                           price, seen at once on A, 2 s late on B and 10 s late on C (or `lags`), with
                                           less activity on the later venues; an optional cross-venue arbitrageur
                                           with 20-microsecond direct feeds; a consolidated feed with sip_ns from
                                           each venue.
                                           Returns the Result
    views(res)                             per-venue tops, the direct NBBO and the published consolidated feed
    study(seconds, seed)                   everything the chapter prints (cached)
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import pathlib
import sys
from dataclasses import replace

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("exchsim", "lob", "tape", "consolidated"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_consolidated import disagreement, information_shares, locked_crossed, nbbo_events, sample  # noqa: E402
from firm_exchsim import (  # noqa: E402
    SEC,
    Agent,
    ExchangeConfig,
    LatencyModel,
    Order,
    Phases,
    SessionSpec,
    Simulator,
    SipConfig,
    TapeBackground,
)
from firm_tape import TapeConfig, activity, efficient_path  # noqa: E402

OPEN = 34_200 * SEC
VENUES = (("A", 0.0, 1.0), ("B", 2.0, 0.7), ("C", 10.0, 0.45))     # name, delay of P* for its traders (s), activity
CLOSE_LAGS = (0.0, 0.2, 1.0)


class Arbitrageur(Agent):
    """Takes both sides of a crossed consolidated book (from its own direct feeds) with immediate-or-cancel orders."""
    name = "arb"

    def __init__(self, max_qty: int = 500):
        self.max_qty, self.wait_until = max_qty, 0

    def on_start(self, ctx):
        self.names = {s.venue: s.name.split("@")[-1] for s in ctx.sessions}     # venue index -> venue name

    def on_book(self, ctx, locate, top):
        if ctx.now_ns < self.wait_until:
            return
        best_b, best_a = None, None
        for (vi, _loc), bk in ctx.books.items():
            b, bq, a, aq = bk.top()
            if b is not None and (best_b is None or b > best_b[0]):
                best_b = (b, bq, vi)
            if a is not None and (best_a is None or a < best_a[0]):
                best_a = (a, aq, vi)
        if best_b and best_a and best_b[0] > best_a[0]:
            q = min(best_b[1], best_a[1], self.max_qty)
            ctx.send(Order(side="B", qty=q, price=best_a[0], tif="I", venue=self.names[best_a[2]]))
            ctx.send(Order(side="S", qty=q, price=best_b[0], tif="I", venue=self.names[best_b[2]]))
            self.wait_until = ctx.now_ns + 1_000_000


def market(seconds: float = 3600.0, seed: int = 7, arb: bool = True, sip_ns: int = 500_000, lags=None):
    lags = lags or [lag for _, lag, _ in VENUES]
    base = TapeConfig(seconds=seconds, seed=seed, news_at=None)
    rng = np.random.default_rng(seed + 1000)
    act = activity(base, rng)
    vt, v = efficient_path(base, rng, act)
    end = OPEN + int(seconds * SEC) + SEC
    ph = Phases(start_ns=OPEN - SEC, open_ns=OPEN, close_ns=end, end_ns=end + 1)
    sim = Simulator([ExchangeConfig(venue=n, phases=ph) for n, _, _ in VENUES], sip=SipConfig(default_ns=sip_ns),
                    seed=seed)
    for i, ((name, _, scale), lag) in enumerate(zip(VENUES, lags, strict=True)):
        cfg = replace(base, seed=seed + 10 * i + 1, lo_rate=base.lo_rate * scale, noise_mu=base.noise_mu * scale,
                      informed=base.informed * scale, in_spread=base.in_spread * scale)
        shifted = np.concatenate([[0.0], np.minimum(vt[1:] + lag, seconds)])
        sim.add_background(TapeBackground(cfg, venue=name, v_path=(shifted, v, act), name=f"BG{name}"))
    if arb:
        lat = LatencyModel(entry_ns=20_000, ack_ns=20_000, data_ns=20_000)
        sim.add_agent(Arbitrageur(), [SessionSpec(venue=n, latency=lat, firm="ARB") for n, _, _ in VENUES])
    return sim.run()


def views(res) -> dict:
    tops = {n: res.tape(n).top for n, _, _ in VENUES}
    s = res.sip(1)
    sip = np.zeros(len(s), dtype=[("t", "f8"), ("bid", "i8"), ("bid_size", "i8"), ("ask", "i8"), ("ask_size", "i8")])
    sip["t"] = (s["t"] - OPEN) / SEC
    for k in ("bid", "ask"):
        sip[k] = np.where(s[k] > 0, s[k] // 100, -1)
    sip["bid_size"], sip["ask_size"] = s["bid_size"], s["ask_size"]
    return {"tops": tops, "direct": nbbo_events(tops), "sip": sip}


def mids(tops: dict, grid) -> np.ndarray:
    cols = []
    for n, _, _ in VENUES:
        t = tops[n]
        ok = (t["bid"] > 0) & (t["ask"] > 0)
        tt, m = t["t"][ok], 0.5 * (t["bid"][ok] + t["ask"][ok])
        cols.append(m[np.clip(np.searchsorted(tt, grid, side="right") - 1, 0, len(m) - 1)])
    return np.column_stack(cols)


@functools.cache
def study(seconds: float = 3600.0, seed: int = 7) -> dict:
    lo, hi = 10.0, seconds - 1.0
    out = {}
    for arb in (False, True):
        res = market(seconds, seed, arb)
        vw = views(res)
        key = "arb" if arb else "no_arb"
        out[key] = {"lc": locked_crossed(vw["direct"], lo, hi),
                    "volume": {n: int(res.tape(n).trades["qty"].sum()) for n, _, _ in VENUES}}
        if arb:
            out["sip_live"] = disagreement(vw["direct"], vw["sip"], lo, hi)
            out["delays"] = {d: disagreement(vw["direct"], nbbo_events(vw["tops"], {n: d / 1000 for n, _, _ in VENUES}),
                                             lo, hi) for d in (0.05, 0.5, 1.0, 5.0, 20.0, 100.0)}
            out["sip_offline"] = disagreement(vw["direct"], nbbo_events(vw["tops"], {n: 0.00052 for n, _, _ in VENUES}),
                                              lo, hi)
            grid = np.arange(lo, hi, 1.0)
            out["is"] = information_shares(mids(vw["tops"], grid), lags=5)
            out["is_20"] = information_shares(mids(vw["tops"], grid), lags=20)
            tr = np.sort(np.concatenate([res.tape(n).trades["t"] for n, _, _ in VENUES]))
            tr = tr[(tr >= lo) & (tr < hi)]
            d, s = sample(vw["direct"], tr - 1e-9), sample(vw["sip"], tr - 1e-9)
            stale = (d["bid"] != s["bid"]) | (d["ask"] != s["ask"])
            arb_t = np.array([(f[0] - OPEN) / SEC for f in res.agents["arb"].fills])
            mine = np.isin(np.round(tr, 6), np.round(arb_t, 6))
            out["trades_stale"] = float(np.mean(stale))
            out["trades_stale_bg"] = float(np.mean(stale[~mine]))
            dn = vw["direct"][(vw["direct"]["t"] >= lo) & (vw["direct"]["t"] < hi)]
            moves = (np.diff(dn["bid"]) != 0) | (np.diff(dn["ask"]) != 0)
            out["nbbo_changes_per_s"] = float(len(dn) / (hi - lo))
            out["price_changes_per_s"] = float(moves.sum() / (hi - lo))
            out["arb_fills"] = len(res.agents["arb"].fills)
            out["at_best"] = _at_best(vw["tops"], vw["direct"], lo, hi)
    close = views(market(seconds, seed, True, lags=CLOSE_LAGS))
    out["is_close"] = information_shares(mids(close["tops"], np.arange(lo, hi, 1.0)), lags=5)
    return out


def _at_best(tops, direct, lo, hi) -> dict:
    """Time-weighted share of the NBBO's displayed size on each venue (ask side)."""
    t = direct["t"][(direct["t"] >= lo) & (direct["t"] < hi)]
    dt = np.diff(np.concatenate([t, [hi]]))
    nb = sample(direct, t)
    share = {}
    for n in tops:
        tp = tops[n]
        i = np.clip(np.searchsorted(tp["t"], t, side="right") - 1, 0, len(tp) - 1)
        q = np.where(tp["ask"][i] == nb["ask"], tp["ask_qty"][i], 0)
        share[n] = float((dt * q / np.maximum(nb["ask_size"], 1)).sum() / dt.sum())
    return share
