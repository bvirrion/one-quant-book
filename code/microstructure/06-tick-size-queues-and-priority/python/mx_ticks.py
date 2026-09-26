"""One Quant Book 10, chapter 6: tick size, queues and priority on the exchange simulator.

    session(mult, seconds, seed, matching, **tape)
                                           firm.tape's order flow sent to firm.exchsim on a grid of `mult` cents: limit
                                           prices rounded away from the market (bids down, asks up); returns the
                                           venue's tape (prices in the venue's ticks)
    grid_stats(tape, mult)                 spread in ticks and cents, share of one-tick time, depth and queue length at
                                           the best, trades, effective half-spread
    queue_study(tape, mult, h)             every limit order that joins the best: shares ahead at entry, fill, time to
                                           fill and the h-second mark-out of its fills, by position bucket
    tick_experiment(mults, seconds, seed)  both of the above for each grid
    priority_compare(mult, seeds)          time priority against pro rata on the same flow
    did_panel(n, ...)                      simulated treated and control stocks before and after a tick change
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import pathlib
import sys
from dataclasses import dataclass, replace

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("exchsim", "lob", "tape", "queuevalue"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_exchsim import SEC, ExchangeConfig, InstrumentSpec, Phases, Simulator, TapeBackground  # noqa: E402
from firm_tape import TapeConfig  # noqa: E402

OPEN = 34_200 * SEC


@dataclass
class CoarseTape(TapeBackground):
    """firm.tape's flow on a coarser grid: the same orders, their limit prices rounded to `mult` cents."""
    mult: int = 1

    def build(self, sim, venue_cfg, jumps=()):
        cents = tuple(replace(i, tick=100) if i.locate == self.locate else i
                      for i in venue_cfg.instruments)
        recs, truth = super().build(sim, replace(venue_cfg, instruments=cents), jumps)
        step = 100 * self.mult
        out = []
        for t, m in recs:
            if type(m).__name__ == "In_O" and m.price > 0:
                p = (m.price // step) * step if m.side == "B" else -((-m.price) // step) * step
                m = m._replace(price=p)
            out.append((t, m))
        return out, truth


def session(mult: int = 1, seconds: float = 3600.0, seed: int = 7, matching: str = "fifo", **tape):
    end = OPEN + int(seconds * SEC) + SEC
    ph = Phases(start_ns=OPEN - SEC, open_ns=OPEN, close_ns=end, end_ns=end + 1)
    alloc = {"top_pct": 0, "fifo_pct": 0, "min_alloc": 1} if matching == "pro_rata" else None
    inst = InstrumentSpec(tick=100 * mult, matching=matching, alloc=alloc)
    sim = Simulator(ExchangeConfig(phases=ph, instruments=(inst,)), seed=seed)
    sim.add_background(CoarseTape(TapeConfig(seconds=seconds, seed=seed, news_at=None, **tape), mult=mult))
    return sim.run().tape()


def _window(tape, lo: float, hi: float):
    top = tape.top
    k = (top["t"] >= lo) & (top["t"] < hi)
    return top[k]


def grid_stats(tape, mult: int, lo: float = 10.0, hi: float | None = None) -> dict:
    """Time-weighted statistics of the venue's book on [lo, hi) seconds; money in cents."""
    hi = hi if hi is not None else float(tape.top["t"].max()) - 1.0
    top = _window(tape, lo, hi)
    s = top["ask"] - top["bid"]
    dt = np.diff(np.concatenate([top["t"], [hi]]))
    w = dt / dt.sum()
    tr = tape.trades[(tape.trades["t"] >= lo) & (tape.trades["t"] < hi)]
    ok = (tape.top["bid"] > 0) & (tape.top["ask"] > 0)
    t, mid = tape.top["t"][ok], 0.5 * (tape.top["bid"][ok] + tape.top["ask"][ok])
    i = np.clip(np.searchsorted(t, tr["t"] - 1e-9, side="right") - 1, 0, len(t) - 1)
    eff = tr["sign"] * (tr["price"] - mid[i])
    return {"spread_ticks": float(w @ s), "spread_cents": float(w @ s) * mult, "one_tick": float(w @ (s == 1)),
            "depth": float(w @ (0.5 * (top["bid_qty"] + top["ask_qty"]))), "trades": len(tr),
            "volume": int(tr["qty"].sum()),
            "eff_half_cents": float(np.average(eff, weights=tr["qty"])) * mult}


def queue_study(tape, mult: int, h: float = 30.0, lo: float = 10.0, hi: float | None = None) -> np.ndarray:
    """Every limit order that joins or improves the best on [lo, hi): shares ahead at entry, fills, time to first fill
    and, per fill, capture side (mid before - price) and adverse side (mid h later - mid before), in cents."""
    from firm_queuevalue import ENTRY
    hi = hi if hi is not None else float(tape.top["t"].max()) - h - 1.0
    levels = {1: {}, -1: {}}
    where: dict[int, tuple[int, int]] = {}
    left: dict[int, int] = {}
    track: dict[int, int] = {}
    rows = []
    fills = []                                       # (row index, t, qty, price, side)
    for m in tape.msgs:
        oid, side, px, q, t = int(m["oid"]), int(m["side"]), int(m["price"]), int(m["qty"]), float(m["t"])
        lv = levels[side]
        if m["kind"] == b"A":
            best = (max(lv) if side == 1 else min(lv)) if lv else None
            joins = best is None or (px >= best if side == 1 else px <= best)
            if joins and lo <= t < hi:
                queue = lv.get(px, ())
                track[oid] = len(rows)
                rows.append((t, side, px * mult, q, sum(left[o] for o in queue), len(queue), 0, np.nan, 0.0, 0.0))
            lv.setdefault(px, []).append(oid)
            where[oid], left[oid] = (side, px), q
            continue
        if oid not in left:
            continue
        if m["kind"] == b"E" and oid in track:
            fills.append((track[oid], t, q, px * mult, side))
        left[oid] -= q
        if left[oid] <= 0:
            lv[px].remove(oid)
            if not lv[px]:
                del lv[px]
            del left[oid]
    e = np.array(rows, dtype=ENTRY)
    ok = (tape.top["bid"] > 0) & (tape.top["ask"] > 0)            # both sides quoted (not the open or the close)
    t_top, mid = tape.top["t"][ok], 0.5 * (tape.top["bid"][ok] + tape.top["ask"][ok]) * mult
    for r, t, q, p, side in fills:
        i0 = max(np.searchsorted(t_top, t - 1e-9, side="right") - 1, 0)
        i1 = max(np.searchsorted(t_top, t + h, side="right") - 1, 0)
        e["filled"][r] += q
        if np.isnan(e["t_fill"][r]):
            e["t_fill"][r] = t
        e["capture"][r] += q * side * (mid[i0] - p)
        e["adverse"][r] += q * side * (mid[i1] - mid[i0])
    return e


def rates(tape, lo: float = 10.0, hi: float | None = None) -> dict:
    """Birth-death rates at the best, per side: mu = market orders per second, theta = cancellations per resting
    order per second (orders at the best), and the mean number of orders at the best."""
    hi = hi if hi is not None else float(tape.top["t"].max()) - 1.0
    levels = {1: {}, -1: {}}
    where: dict[int, tuple[int, int]] = {}
    left: dict[int, int] = {}
    expo = cancels = 0.0
    last = lo
    for m in tape.msgs:
        t = float(m["t"])
        if lo <= t < hi:
            n_best = sum(len(lv[max(lv) if s == 1 else min(lv)]) for s, lv in levels.items() if lv)
            expo += n_best * (t - last)
            last = t
        oid, side, px, q = int(m["oid"]), int(m["side"]), int(m["price"]), int(m["qty"])
        lv = levels[side]
        if m["kind"] == b"A":
            lv.setdefault(px, []).append(oid)
            where[oid], left[oid] = (side, px), q
            continue
        if oid not in left:
            continue
        if m["kind"] == b"X" and lo <= t < hi and lv and px == (max(lv) if side == 1 else min(lv)):
            cancels += 1
        left[oid] -= q
        if left[oid] <= 0:
            lv[px].remove(oid)
            if not lv[px]:
                del lv[px]
            del left[oid]
    n_tr = int(np.sum((tape.trades["t"] >= lo) & (tape.trades["t"] < hi)))
    return {"mu": n_tr / 2.0 / (hi - lo), "theta": cancels / expo, "orders_at_best": expo / 2.0 / (hi - lo)}


MULTS = (1, 2, 5, 10)
SEEDS = (7, 8, 9, 10)
EDGES = (0, 1, 500, 1500, 3000, 6000, 10**12)


@functools.cache
def tick_experiment(mults=MULTS, seeds=SEEDS, seconds: float = 3600.0) -> dict:
    """For each grid: statistics averaged over the seeds' sessions, the pooled queue study by shares ahead and by
    orders ahead, the uncertainty-zone eta and implicit spread, and birth-death rates."""
    from firm_queuevalue import empirical, eta_hat, implicit_spread
    out = {}
    for m in mults:
        stats, entries, rts, nc, na = [], [], [], 0, 0
        for s in seeds:
            tp = session(m, seconds, s)
            stats.append(grid_stats(tp, m))
            entries.append(queue_study(tp, m))
            rts.append(rates(tp))
            z = eta_hat(tp.trades["price"])
            nc, na = nc + z["continuations"], na + z["alternations"]
        e = np.concatenate(entries)
        filled = e[e["filled"] > 0]
        eta = nc / (2 * na)
        out[m] = {k: float(np.mean([x[k] for x in stats])) for k in stats[0]} | {
            "buckets": empirical(e, EDGES), "by_orders": empirical(e, (0, 1, 2, 3, 5, 8, 12, 20, 10**6), "n_ahead"),
            "t_fill_median": float(np.median(filled["t_fill"] - filled["t"])),
            "fill_share": float(len(filled) / len(e)),
            "eta": eta, "continuations": nc, "alternations": na, "implicit_cents": implicit_spread(eta, m),
            "mu": float(np.mean([r["mu"] for r in rts])), "theta": float(np.mean([r["theta"] for r in rts])),
            "orders_at_best": float(np.mean([r["orders_at_best"] for r in rts]))}
    return out


@functools.cache
def did_panel(n: int = 8, seconds: float = 1200.0, window: float = 300.0, treat_mult: int = 5, seed: int = 100) -> dict:
    """n treated and n control stocks (firm.tape flows with random liquidity), each simulated before and after; after,
    every stock sees 50% more efficient-price moves and 20% more noise orders (a common shock) and the treated stocks
    move to a grid of `treat_mult` cents. Observations: quoted spread (cents) and depth at the best per window."""
    import pandas as pd
    import statsmodels.formula.api as smf
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(2 * n):
        treated = i < n
        liq = float(np.exp(0.3 * rng.standard_normal()))
        base = {"lo_rate": 1.4 * liq, "noise_mu": 0.35 * float(np.exp(0.2 * rng.standard_normal()))}
        for post in (0, 1):
            kw = dict(base)
            if post:
                kw |= {"v_rate": 0.12 * 1.5, "noise_mu": base["noise_mu"] * 1.2}
            mult = treat_mult if (treated and post) else 1
            tp = session(mult, seconds, seed + 10 * i + post, **kw)
            for w0 in np.arange(10.0, seconds - window + 10.0, window):
                g = grid_stats(tp, mult, w0, w0 + window)
                rows.append({"stock": i, "treated": int(treated), "post": post, "spread": g["spread_cents"],
                             "depth": g["depth"]})
    df = pd.DataFrame(rows)
    out = {"n_obs": len(df)}
    for y in ("spread", "depth"):
        fit = smf.ols(f"{y} ~ treated * post", df).fit(cov_type="cluster", cov_kwds={"groups": df["stock"]})
        naive = smf.ols(f"{y} ~ treated * post", df).fit()
        cell = df.groupby(["treated", "post"])[y].mean()
        out[y] = {"did": float(fit.params["treated:post"]), "se_cluster": float(fit.bse["treated:post"]),
                  "se_ols": float(naive.bse["treated:post"]), "before_after": float(cell[1, 1] - cell[1, 0]),
                  "control_change": float(cell[0, 1] - cell[0, 0]),
                  "cells": {f"t{k[0]}p{k[1]}": float(v) for k, v in cell.items()}}
    return out


@functools.cache
def priority_compare(mult: int = 5, seeds=(7, 8), seconds: float = 3600.0) -> dict:
    """The same flow on a grid of `mult` cents under time priority and under pure pro rata: the queue study by orders
    ahead."""
    from firm_queuevalue import empirical
    out = {}
    for match in ("fifo", "pro_rata"):
        e = np.concatenate([queue_study(session(mult, seconds, s, matching=match), mult) for s in seeds])
        out[match] = empirical(e, (0, 1, 3, 8, 20, 10**6), "n_ahead")
    return out
