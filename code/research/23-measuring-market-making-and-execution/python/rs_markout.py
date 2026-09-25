"""Measuring market making and execution (One Quant Book 7, chapter 23).

A market maker trading inside firm.tape (the live stand-in of chapter 19): one lot on the best bid and one on the
best ask within five lots of inventory, with latencies it draws itself and a fee of 0.05 tick a share. Two versions:
the plain touch quoter, and one that withdraws the quote on the side the queue imbalance points against (the bid
when the bid queue holds less than 30% of the touch size, the ask when the ask queue does). Each fill's counterparty
is known from the tape (an informed or an uninformed market order). Mark-out curves against the mid and the
microprice, by counterparty; the P&L decomposed into spread capture, adverse selection, inventory and fees; fill
rates. And a parent order (buy 300 lots between minute 11 and minute 30, decided at minute 10) worked by a simple
schedule, with its transaction cost analysis. Twelve one-hour sessions. NumPy only.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("markout", "tape"):
    sys.path.insert(0, str(ROOT / c))
from firm_markout import curve, markouts, microprice, mm_decompose, shortfall, vwap_slippage  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402

SEEDS = tuple(range(61, 73))
LOT, MAX_LOTS, FEE, PULL = 100, 5, 0.05, 0.3
HORIZONS = (0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0, 300.0)
HOURS_A_YEAR = 6.5 * 252


def cfg(seed: int) -> TapeConfig:
    return TapeConfig(seconds=3600.0, news_at=None, seed=seed)


class MarketMaker:
    """One lot a side at the touch, inventory within MAX_LOTS lots; `pull` withdraws a side the imbalance is against."""

    def __init__(self, seed: int, pull: bool):
        self.rng = np.random.default_rng(seed + 700)
        self.pull = pull
        self.cid, self.pos, self.posted = 0, 0, 0
        self.quote = {1: None, -1: None}

    def delay_data(self) -> float:
        return 0.02 + self.rng.exponential(0.02)

    def delay_entry(self) -> float:
        return 0.03 + self.rng.exponential(0.02)

    def on_market(self, t, top):
        _, bid, bq, ask, aq = top
        share = bq / max(bq + aq, 1)
        acts = []
        for side, px in ((1, int(bid)), (-1, int(ask))):
            cur = self.quote[side]
            allowed = self.pos < MAX_LOTS * LOT if side > 0 else self.pos > -MAX_LOTS * LOT
            if self.pull and (share < PULL if side > 0 else 1 - share < PULL):
                allowed = False
            if cur is not None and (cur[1] != px or not allowed):
                acts.append(("cancel", cur[0]))
                self.quote[side] = cur = None
            if cur is None and allowed:
                self.cid += 1
                self.posted += LOT
                acts.append(("limit", self.cid, side, px, LOT))
                self.quote[side] = (self.cid, px)
        return acts

    def on_fill(self, t, cid, side, px, qty, passive):
        self.pos += side * qty
        for s in (1, -1):
            if self.quote[s] is not None and self.quote[s][0] == cid:
                self.quote[s] = None
        return []


@functools.lru_cache(maxsize=32)
def session(seed: int, pull: bool):
    """The live tape with the market maker, and what we measure from it."""
    mm = MarketMaker(seed, pull)
    tape = simulate(cfg(seed), agent=mm)
    f = tape.agent_fills
    top = tape.top
    ok = (top["bid"] > 0) & (top["ask"] > 0) & (top["ask"] > top["bid"])
    rt = top["t"][ok]
    mid = 0.5 * (top["bid"][ok] + top["ask"][ok])
    micro = microprice(top["bid"][ok], top["bid_qty"][ok], top["ask"][ok], top["ask_qty"][ok])
    tr = tape.trades
    informed = tr["informed"][np.searchsorted(tr["t"], f["t"])]      # the market order our quote met
    before = np.searchsorted(rt, f["t"], side="left") - 1                # the reference just before the fill
    return {"t": f["t"], "side": f["side"].astype(float), "px": f["price"].astype(float), "qty": f["qty"].astype(float),
            "informed": informed.astype(bool), "rt": rt, "mid": mid, "micro": micro, "posted": mm.posted,
            "mid_before": mid[np.clip(before, 0, len(mid) - 1)]}


def pooled(pull: bool):
    """Mark-outs (ticks a share, against the mid just before each fill at h = 0) pooled over sessions."""
    rows = []
    for s in SEEDS:
        d = session(s, pull)
        M = markouts(d["t"], d["side"], d["px"], d["rt"], d["mid"], HORIZONS)
        M[:, 0] = d["side"] * (d["mid_before"] - d["px"])
        Mm = markouts(d["t"], d["side"], d["px"], d["rt"], d["micro"], HORIZONS)
        rows.append((M, Mm, d["qty"], d["informed"]))
    M = np.vstack([r[0] for r in rows])
    Mm = np.vstack([r[1] for r in rows])
    q = np.concatenate([r[2] for r in rows])
    inf = np.concatenate([r[3] for r in rows])
    return M, Mm, q, inf


def curves(pull: bool = False):
    M, Mm, q, inf = pooled(pull)
    by = curve(M, q, np.where(inf, "informed", "uninformed"))
    return {"all": curve(M, q)[0], "all_micro": curve(Mm, q)[0], "informed": by["informed"],
            "uninformed": by["uninformed"], "share_informed": float(q[inf].sum() / q.sum()),
            "lots": float(q.sum() / LOT)}


def decomposition(pull: bool, H: float):
    """Summed over the sessions (ticks x shares -> dollars at 0.01 a tick): spread, adverse, inventory, fees, total,
    and the lots filled and posted."""
    tot = {"spread": 0.0, "adverse": 0.0, "inventory": 0.0, "fees": 0.0, "total": 0.0}
    lots = posted = 0.0
    for s in SEEDS:
        d = session(s, pull)
        dec = mm_decompose(d["t"] - 1e-9, d["side"], d["px"], d["qty"], d["rt"], d["mid"], H, FEE, t_end=3600.0)
        for k in tot:
            tot[k] += dec[k] / 100.0
        lots += d["qty"].sum() / LOT
        posted += d["posted"] / LOT
    return tot, lots, posted


def annual(tot: dict) -> dict:
    return {k: v * HOURS_A_YEAR / len(SEEDS) for k, v in tot.items()}


class Executor:
    """Buy TARGET lots between START and END against a straight-line schedule: every STEP seconds, cancel the resting
    bid, send a market order for whatever is more than CATCH lots behind schedule, and rest the next step's lots at
    the best bid; stop at END (the rest is unfilled)."""

    TARGET, START, END, STEP, CATCH = 300, 660.0, 1800.0, 20.0, 8

    def __init__(self, seed: int):
        self.rng = np.random.default_rng(seed + 900)
        self.cid, self.filled, self.next, self.resting = 0, 0, self.START, None

    def delay_data(self) -> float:
        return 0.02 + self.rng.exponential(0.02)

    def delay_entry(self) -> float:
        return 0.03 + self.rng.exponential(0.02)

    def on_market(self, t, top):
        if t < self.next or t > self.END + self.STEP:
            return []
        self.next = t + self.STEP
        acts = []
        if self.resting is not None:
            acts.append(("cancel", self.resting))
            self.resting = None
        if t > self.END:
            return acts
        due = self.TARGET * LOT * min(1.0, (t - self.START) / (self.END - self.START))
        behind = int((due - self.filled) // LOT)
        if behind > self.CATCH:
            self.cid += 1
            acts.append(("market", self.cid, 1, (behind - self.CATCH) * LOT))
        step = self.TARGET * LOT * self.STEP / (self.END - self.START)
        size = int(min(self.TARGET * LOT - self.filled, max(step, LOT)) // LOT) * LOT
        if size > 0:
            self.cid += 1
            self.resting = self.cid
            acts.append(("limit", self.cid, 1, int(top[1]), size))
        return acts

    def on_fill(self, t, cid, side, px, qty, passive):
        self.filled += qty
        return []


def _mid(tape):
    top = tape.top
    ok = (top["bid"] > 0) & (top["ask"] > top["bid"])
    return top["t"][ok], 0.5 * (top["bid"][ok] + top["ask"][ok])


@functools.lru_cache(maxsize=16)
def execution(seed: int, decision: float = 600.0):
    """One parent order (ticks): decision at minute 10, released at minute 11, deadline minute 30. The shortfall and
    its parts, the VWAP slippage, the passive share, the execution cost split into the mid's drift from arrival to
    each fill and the price paid against that mid, and the mid's move from release to deadline with and without the
    order (the same session, same seed, run without the executor)."""
    ex = Executor(seed)
    tape = simulate(cfg(seed), agent=ex)
    rt, mid = _mid(tape)
    at = lambda x: float(mid[np.searchsorted(rt, x, side="right") - 1])  # noqa: E731
    f = tape.agent_fills
    fills = [(float(p), float(q)) for p, q in zip(f["price"], f["qty"], strict=True)]
    sf = shortfall(1, ex.TARGET * LOT, at(decision), at(ex.START), fills, at(ex.END), fee=FEE)
    tr = tape.trades
    win = (tr["t"] >= ex.START) & (tr["t"] <= ex.END) & ~np.isin(tr["t"], f["t"])
    q = f["qty"].astype(float)
    before = mid[np.clip(np.searchsorted(rt, f["t"], side="left") - 1, 0, len(mid) - 1)]
    bt, bmid = _mid(simulate(cfg(seed)))
    at0 = lambda x: float(bmid[np.searchsorted(bt, x, side="right") - 1])  # noqa: E731
    return {"sf": sf, "vwap": vwap_slippage(1, fills, tr["price"][win], tr["qty"][win]),
            "passive": float(q[f["passive"]].sum() / q.sum()), "drift": float(q @ (before - at(ex.START))),
            "paid": float(q @ (f["price"] - before)), "move": at(ex.END) - at(ex.START),
            "move_without": at0(ex.END) - at0(ex.START), "delay_without": at0(ex.START) - at0(decision)}


def settle(pull: bool = False) -> float:
    """The horizon from which the pooled mark-out curve stays within two standard errors of its 5-minute value."""
    from firm_markout import settle_horizon
    mean, se = curves(pull)["all"]
    return settle_horizon(mean, HORIZONS, 2 * se[-1])


def tca_all():
    """Per session: the shortfall's parts per share (ticks), the VWAP slippage, the passive share, the execution cost's
    drift and paid parts per share, and the order's impact (the mid's move with the order minus without it)."""
    rows = []
    for s in SEEDS:
        e = execution(s)
        q = e["sf"]["filled"]
        row = {k: e["sf"][k] / q for k in ("delay", "execution", "opportunity", "fees", "total")}
        row.update({"vwap": e["vwap"], "passive": e["passive"], "lots": q / LOT, "drift": e["drift"] / q,
                    "paid": e["paid"] / q, "move": e["move"], "move_without": e["move_without"],
                    "impact": e["move"] - e["move_without"], "delay_without": e["delay_without"]})
        rows.append(row)
    mean = {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}
    se = {k: float(np.std([r[k] for r in rows], ddof=1) / np.sqrt(len(rows))) for k in rows[0]}
    return rows, mean, se
