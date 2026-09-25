"""Simulation versus live (One Quant Book 7, chapter 19).

The stand-in for live: the touch quoter of chapter 18 trading inside firm.tape as an agent (its orders are real
orders, matched in time priority and seen by the other traders), with latencies it draws itself: market data
0.02 s + an exponential of mean 0.02 s, order entry 0.03 s + an exponential of mean 0.02 s; it pays 0.1 tick a share.
The research estimate made before trading: the same quoter replayed by firm.lobreplay (fifo) on the same hour
without it (same seed, same efficient-price path), with no latency and no fees. The estimate is walked to live one
assumption at a time: live mean latencies; the market the quoter actually met (the live tape without its own
messages); the live fills themselves; fees. A second realisation of the same hour (same efficient price, another
order-flow seed) measures how much of the market step is chance. Six one-hour sessions. NumPy only.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("simlive", "lobreplay", "tape"):
    sys.path.insert(0, str(ROOT / c))
from firm_lobreplay import Replay, Strategy  # noqa: E402
from firm_simlive import as_fills, calibrate, parity, waterfall  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402

SEEDS = (41, 42, 43, 44, 45, 46)
LOT, MAX_LOTS, FEE = 100, 5, 0.1                        # fee in ticks a share
DATA_MEAN, ENTRY_MEAN = 0.04, 0.05


def cfg(seed: int) -> TapeConfig:
    return TapeConfig(seconds=3600.0, news_at=None, seed=seed)


class LiveQuoter:
    """The agent: one lot on the best bid and one on the best ask, within five lots of inventory."""

    def __init__(self, seed: int):
        self.rng = np.random.default_rng(seed + 500)
        self.cid, self.pos = 0, 0
        self.quote = {1: None, -1: None}

    def delay_data(self) -> float:
        return 0.02 + self.rng.exponential(0.02)

    def delay_entry(self) -> float:
        return 0.03 + self.rng.exponential(0.02)

    def on_market(self, t, top):
        _, bid, _, ask, _ = top
        acts = []
        for side, px in ((1, int(bid)), (-1, int(ask))):
            cur = self.quote[side]
            allowed = self.pos < MAX_LOTS * LOT if side > 0 else self.pos > -MAX_LOTS * LOT
            if cur is not None and (cur[1] != px or not allowed):
                acts.append(("cancel", cur[0]))
                self.quote[side] = cur = None
            if cur is None and allowed:
                self.cid += 1
                acts.append(("limit", self.cid, side, px, LOT))
                self.quote[side] = (self.cid, px)
        return acts

    def on_fill(self, t, cid, side, px, qty, passive):
        self.pos += side * qty
        for s in (1, -1):
            if self.quote[s] is not None and self.quote[s][0] == cid:
                self.quote[s] = None
        return []


class ReplayQuoter(Strategy):
    """The same quoter in firm.lobreplay."""

    def __init__(self):
        self.quote = {1: None, -1: None}

    def on_market(self, ctx, t, snap):
        for side, px in ((1, snap["bid"]), (-1, snap["ask"])):
            if px is None:
                continue
            vid = self.quote[side]
            sh = ctx.shadows[vid] if vid is not None else None
            live = sh is not None and sh.status in ("sent", "working") and sh.cancel_sent == float("inf")
            allowed = ctx.position < MAX_LOTS * LOT if side > 0 else ctx.position > -MAX_LOTS * LOT
            if live and (sh.price != px or not allowed):
                ctx.cancel(vid)
                live = False
            if not live and allowed:
                self.quote[side] = ctx.send(side, px, LOT)
            elif not live:
                self.quote[side] = None


@functools.lru_cache(maxsize=16)
def session(seed: int):
    """(tape without the agent, live tape with it, live tape without the agent's messages, a second realisation)."""
    base = simulate(cfg(seed))
    live = simulate(cfg(seed), agent=LiveQuoter(seed))
    ex = live.msgs[~np.isin(live.msgs["oid"], live.own)]
    other = simulate(TapeConfig(seconds=3600.0, news_at=None, seed=seed + 1000), v_path=(base.v_t, base.v, base.act))
    return base, live, ex, other


def replay_pnl(msgs, entry: float, data: float):
    res = Replay(msgs, ReplayQuoter(), "fifo", entry_latency=entry, data_latency=data).run()
    return res.pnl() / 100.0, res


def live_pnl(live):
    f = live.agent_fills
    mid = 0.5 * (live.top["bid"][-1] + live.top["ask"][-1])
    gross = float(np.sum(f["side"] * f["qty"] * (mid - f["price"]))) / 100.0
    return gross, float(FEE * f["qty"].sum()) / 100.0


def decomposition():
    """Per session and on average: the research estimate, each step toward live, and the chance benchmark."""
    rows = []
    for seed in SEEDS:
        base, live, ex, other = session(seed)
        sim0, _ = replay_pnl(base.msgs, 0.0, 0.0)
        sim1, _ = replay_pnl(base.msgs, ENTRY_MEAN, DATA_MEAN)
        sim2, r2 = replay_pnl(ex, ENTRY_MEAN, DATA_MEAN)
        chance, _ = replay_pnl(other.msgs, ENTRY_MEAN, DATA_MEAN)
        gross, fees = live_pnl(live)
        lf = live.agent_fills
        sim_f = as_fills([(t, sd, px, q) for t, _, sd, q, px in r2.fills])
        live_f = as_fills([(r["t"], r["side"], r["price"], r["qty"]) for r in lf])
        rows.append({"sim": sim0, "latency": sim1, "market": sim2, "live_gross": gross, "live": gross - fees,
                     "fees": fees, "chance": chance, "live_lots": float(lf["qty"].sum()) / LOT,
                     "sim_lots": float(sum(q for *_, q, _ in r2.fills)) / LOT, "parity": parity(live_f, sim_f, 1.0)})
    mean = {k: float(np.mean([r[k] for r in rows])) for k in rows[0] if k != "parity"}
    mean["parity_live"] = float(np.mean([r["parity"][0] for r in rows]))
    mean["parity_sim"] = float(np.mean([r["parity"][1] for r in rows]))
    mean["chance_gap"] = float(np.mean([abs(r["chance"] - r["latency"]) for r in rows]))
    return rows, mean


def steps(mean: dict):
    return waterfall([("research simulation", mean["sim"]), ("+ live latency", mean["latency"]),
                      ("+ the market met", mean["market"]), ("+ live fills", mean["live_gross"]),
                      ("+ fees: live", mean["live"])])


def effective_latency(grid=(0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0)):
    """Calibration: the order-entry latency (market-data latency = 0.8 of it) at which the replay on the live tape
    without the agent fills as many lots as live did, summed over the sessions."""
    target = sum(float(session(s)[1].agent_fills["qty"].sum()) for s in SEEDS) / LOT

    def lots(lat):
        return sum(sum(q for *_, q, _ in replay_pnl(session(s)[2], lat, 0.8 * lat)[1].fills) for s in SEEDS) / LOT
    return calibrate(grid, lots, target), target


def alone_at_price():
    """Locating the divergence: for each live fill, the quantity of other traders' orders resting at the fill's price
    just before it. Fills with none (the quoter was the last order left at a price everyone else had abandoned)
    cannot happen in a replay of the market without the quoter. Their share of live lots and the mean 10-second
    mark-out (ticks) of each group, over the sessions."""
    alone_q, other_q, mo_alone, mo_other = 0.0, 0.0, [], []
    for seed in SEEDS:
        _, live, _, _ = session(seed)
        m, own = live.msgs, set(live.own.tolist())
        mids = 0.5 * (live.top["bid"] + live.top["ask"])
        levels = {1: {}, -1: {}}
        where = {}
        for r in m:
            oid, side, px, q, kind = int(r["oid"]), int(r["side"]), int(r["price"]), int(r["qty"]), r["kind"]
            if kind == b"E" and oid in own:
                others = sum(n for o, n in levels[side].get(px, {}).items() if o not in own)
                j = np.searchsorted(m["t"], r["t"] + 10.0, side="right") - 1
                mo = side * (mids[j] - px)
                if others == 0:
                    alone_q += q
                    mo_alone.append(mo)
                else:
                    other_q += q
                    mo_other.append(mo)
            if kind == b"A":
                levels[side].setdefault(px, {})[oid] = q
                where[oid] = (side, px)
            else:
                sd, p = where[oid]
                levels[sd][p][oid] -= q
                if levels[sd][p][oid] <= 0:
                    del levels[sd][p][oid]
    return {"share_alone": alone_q / (alone_q + other_q), "markout_alone": float(np.mean(mo_alone)),
            "markout_other": float(np.mean(mo_other))}


def vanished_volume():
    """Live lots filled by aggressive orders whose whole execution was against the quoter: in the live tape without
    the quoter's messages those trades do not exist, so no replay of it can fill them."""
    only, total = 0.0, 0.0
    for seed in SEEDS:
        _, live, _, _ = session(seed)
        m, own = live.msgs, set(live.own.tolist())
        e = m[m["kind"] == b"E"]
        mine = np.isin(e["oid"], list(own))
        others_by_trade = {}
        for r, mn in zip(e, mine, strict=True):
            if not mn:
                others_by_trade[int(r["trade"])] = others_by_trade.get(int(r["trade"]), 0) + int(r["qty"])
        for r in e[mine]:
            total += int(r["qty"])
            if others_by_trade.get(int(r["trade"]), 0) == 0:
                only += int(r["qty"])
    return only / total


def model_calibration(models=("fifo", "prob", "front")):
    """Summed over the sessions: lots and P&L of the replay on the live tape without the quoter, with the live mean
    latencies, under each queue model, against live."""
    out = {}
    for model in models:
        lots, pnl = 0.0, 0.0
        for seed in SEEDS:
            res = Replay(session(seed)[2], ReplayQuoter(), model, entry_latency=ENTRY_MEAN,
                         data_latency=DATA_MEAN).run()
            lots += sum(q for *_, q, _ in res.fills) / LOT
            pnl += res.pnl() / 100.0
        out[model] = (lots, pnl)
    live = [live_pnl(session(s)[1])[0] for s in SEEDS]
    out["live"] = (sum(float(session(s)[1].agent_fills["qty"].sum()) for s in SEEDS) / LOT, float(sum(live)))
    return out
