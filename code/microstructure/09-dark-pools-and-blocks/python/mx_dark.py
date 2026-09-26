"""One Quant Book 10, chapter 9: a lit venue, a midpoint dark pool and a block venue, and a large order worked in each.

    Market(seed, strategy, ...)      two firm.exchsim engines driven directly: LIT and a midpoint dark pool whose pegs
                                     price off LIT's best bid and offer (control N); an efficient price P* moved by
                                     exogenous jumps and by the permanent impact of uninformed lit market orders
                                     (lambda per share; informed orders reveal P*, they do not move it); liquidity
                                     providers on LIT; noise and informed takers that try the dark pool first with
                                     probability dark_first; patient uninformed traders resting
                                     midpoint pegs in the dark; a pinger that probes the dark pool with small
                                     immediate-or-cancel orders and buys (sells) on LIT when a probe fills; natural
                                     sellers' conditional orders in a block venue (firm.darkpool), some of whom never
                                     firm up and trade ahead instead
    run(seed, strategy) -> dict      a fund buys 20,000 shares from t = 600 s over 30 minutes: 'lit' (a market order of
                                     200 every 18 s), 'dark' (one resting midpoint peg), 'dark_min' (the same with a
                                     minimum quantity of 1,000), 'block' (conditionals in the block venue); whatever
                                     is left at the end is bought on LIT. Shortfall and drift in basis points
    compare(seeds)                   every strategy on the same seeds: means and standard errors of shortfall, drift,
                                     and the accounted own-impact and leakage costs
    zhu(seeds, h)                    no fund and no pinger: dark fill rates of informed and uninformed takers, and for
                                     resting fills in the dark and on the lit book the capture and the h-second move
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("exchsim", "lob", "darkpool"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_darkpool import ConditionalBook, pre_completion_drift_bps, shortfall_bps  # noqa: E402
from firm_exchsim import SEC, ExchangeConfig, midpoint_dark_pool  # noqa: E402
from firm_exchsim_codec import NT  # noqa: E402
from firm_exchsim_engine import Engine  # noqa: E402

C, IN = NT["ctl"], NT["in"]
OPEN = 34_200 * SEC
PX = 100                                   # one tick (one cent) in 1/10,000 units
LP, NOISE, INF, PATIENT, FUND, PINGER, BLOCK = 1, 2, 3, 4, 5, 6, 7
START, WINDOW, TARGET = 600.0, 1800.0, 20_000


class Market:
    def __init__(self, seed: int = 1, strategy: str = "none", seconds: float = 2700.0, lam: float = 0.0005,
                 dark_first: float = 0.5, pinger: bool = True, v_rate: float = 0.01, leaky: float = 0.3,
                 fund_min: int = 1000):
        self.seed, self.strategy, self.seconds, self.lam = seed, strategy, seconds, lam
        self.dark_first, self.pinger, self.leaky, self.v_rate = dark_first, pinger, leaky, v_rate
        self.fund_min = fund_min
        self.lit = Engine(ExchangeConfig(venue="LIT").engine_config())
        self.dark = Engine(midpoint_dark_pool(reference="LIT").engine_config())
        for e, sess in ((self.lit, (LP, NOISE, INF, FUND, PINGER, BLOCK)), (self.dark, (NOISE, INF, PATIENT, FUND,
                                                                                         PINGER))):
            e.process(OPEN - SEC, 0, C["S"]("O"))
            for s in sess:
                e.process(OPEN - SEC, 0, C["L"](s, s, "N"))
            e.process(OPEN - SEC, 0, C["P"](0, "T", "OPEN"))
        self.vstar = 10_000.0
        self.t = 0.0
        self.cl = 0
        self.live: list[int] = []
        self.pos: dict[int, int] = {}
        self.lp_px: dict[int, tuple[int, int]] = {}
        self.ref = (0, 0)
        self.fills: dict[int, list] = {}          # session -> [(t, venue, side, qty, price in ticks, informed)]
        self.taker_kind: dict[int, bool] = {}     # taker cl -> informed
        self.mids: list[tuple[float, float]] = []
        self.pings = 0
        self.leaks = 0
        self.fund_cl = None
        self._side: dict[tuple[str, int], int] = {}
        self._last_ping: dict[int, tuple[float, bool]] = {}
        self.front_runs: list[tuple[float, int, bool]] = []      # (t, lit shares bought ahead, triggered by the fund)
        self.fund_pings = 0
        self.dark_tries: dict[bool, int] = {}
        self.fund_left = TARGET
        self.block = ConditionalBook(firm_up_ns=int(0.2 * SEC))
        rx = np.random.default_rng(seed)                # exogenous streams: the same for every strategy
        self.rng = np.random.default_rng(seed + 10_000)  # endogenous draws
        self.ev = self._exogenous(rx)

    # -- plumbing ---------------------------------------------------------------------------------------------
    def _exogenous(self, rx) -> list:
        ev = []
        for kind, rate in (("jump", self.v_rate), ("noise", 0.6), ("patient", 0.01), ("cond", 1 / 300)):
            t = 0.0
            while True:
                t += rx.exponential(1 / rate)
                if t >= self.seconds:
                    break
                if kind == "jump":
                    ev.append((t, kind, 1 if rx.random() < 0.5 else -1, 0))
                elif kind == "noise":
                    ev.append((t, kind, 1 if rx.random() < 0.5 else -1, 100 * int(rx.geometric(1 / 1.5))))
                elif kind == "patient":
                    ev.append((t, kind, 1 if rx.random() < 0.5 else -1, 100 * int(rx.integers(5, 21))))
                else:
                    ev.append((t, kind, -1, 1000 * int(rx.integers(5, 16))))
        if self.pinger:
            ev += [(2.0 * k, "ping", 1 if k % 2 else -1, 100) for k in range(1, int(self.seconds / 2))]
        if self.strategy == "lit":
            ev += [(START + 18.0 * k, "child", 1, 200) for k in range(100)]
        ev.sort(key=lambda e: e[0])
        return ev

    def _go(self, e: Engine, sess: int, msg):
        venue = "LIT" if e is self.lit else "DARK"
        _, reps = e.process(OPEN + int(round(self.t * SEC)), sess, msg)
        for s, r in reps:
            if type(r).__name__ != "Out_E":
                continue
            side = self._side.get((venue, r.cl_ord_id), 0)
            self.fills.setdefault(s, []).append((self.t, venue, side, r.qty, r.price / PX,
                                                 self.taker_kind.get(r.cl_ord_id, False)))
            if venue == "LIT" and r.liquidity == "R" and s != INF:
                self.vstar += self.lam * side * r.qty           # permanent impact of uninformed lit market orders
            if s == LP and r.leaves == 0:
                self._drop(r.cl_ord_id)
            if s == FUND:
                self.fund_left -= r.qty
            if s == PINGER and venue == "DARK":
                self.pings += 1
                fund = self.dark.trades[-1][4] == FUND       # whose order the probe hit
                self.fund_pings += fund
                last = self._last_ping.get(side, (-1e9, False))
                if last[0] > self.t - 5.0:                   # two fills in a row: a large order
                    self._market(PINGER, -side, 500, False)  # trade ahead of it on LIT
                    self.front_runs.append((self.t, 500, fund or last[1]))
                self._last_ping[side] = (self.t, fund)
        if venue == "LIT":
            self._reference()
        return reps

    def _order(self, e: Engine, sess: int, side: int, qty: int, px: int, tif: str = "D", disp: str = "Y",
               min_qty: int = 0) -> int:
        self.cl += 1
        self._side[("LIT" if e is self.lit else "DARK", self.cl)] = side
        self._go(e, sess, IN["O"](self.cl, 1, "B" if side > 0 else "S", qty, px, tif, disp, "N", 0, min_qty, 0, "N",
                                  0))
        return self.cl

    def _reference(self):
        b, _, a, _ = self.lit.book(1).top()
        ref = (b, a) if b is not None and a is not None else (0, 0)
        if ref != self.ref:
            self.ref = ref
            self._go(self.dark, 0, C["N"](1, *ref))

    def _drop(self, cl: int):
        i = self.pos.pop(cl, None)
        if i is None:
            return
        last = self.live.pop()
        if last != cl:
            self.live[i], self.pos[last] = last, i
        self.lp_px.pop(cl, None)

    def mid(self):
        b, a = self.ref
        return 0.5 * (b + a) / PX if b and a else self.vstar

    def _market(self, sess: int, side: int, qty: int, informed: bool, dark_first: bool = False):
        if dark_first:
            self.dark_tries[informed] = self.dark_tries.get(informed, 0) + qty
            cl = self._order(self.dark, sess, side, qty, 0, "I", "M")
            self.taker_kind[cl] = informed
            got = sum(f[3] for f in self.fills.get(sess, []) if f[0] == self.t and f[1] == "DARK" and f[2] == side)
            qty -= got
            if qty <= 0:
                return
        cl = self._order(self.lit, sess, side, qty, 0, "I")
        self.taker_kind[cl] = informed

    # -- the flow ---------------------------------------------------------------------------------------------
    def _limit(self):
        side = 1 if self.rng.random() < 0.5 else -1
        b, a = self.ref
        b, a = (b // PX or None), (a // PX or None)
        best = b if side == 1 else a
        if best is None:
            best = math.floor(self.vstar) if side == 1 else math.ceil(self.vstar)
        k = 0 if self.rng.random() < 0.5 else int(self.rng.geometric(0.5))
        px = best - side * k
        if b and a and a - b > 1 and self.rng.random() < 0.5 and (self.vstar - 0.5 * (a + b)) * side > 0:
            px = b + 1 if side == 1 else a - 1
        if side == 1 and a:
            px = min(px, a - 1)
        if side == -1 and b:
            px = max(px, b + 1)
        cl = self._order(self.lit, LP, side, 100 * int(self.rng.geometric(0.5)), px * PX)
        self.pos[cl] = len(self.live)
        self.live.append(cl)
        self.lp_px[cl] = (side, px)

    def _stale(self):
        through = [c for c, (s, p) in self.lp_px.items() if (s == 1 and p > self.vstar) or (s == -1 and p < self.vstar)]
        for cl in through:
            if self.rng.random() < 0.5:
                self._go(self.lit, LP, IN["X"](cl, 0))
                self._drop(cl)

    def run(self) -> dict:
        for k in range(1, 6):                          # an opening book
            for side in (1, -1):
                cl = self._order(self.lit, LP, side, 500, (10_000 - side * k) * PX)
                self.pos[cl], self.lp_px[cl] = len(self.live), (side, 10_000 - side * k)
                self.live.append(cl)
        i = 0
        while True:
            m = self.mid()
            gap = self.vstar - m
            rates = np.array([3.0, 0.05 * len(self.live), 0.2 * abs(gap)])
            dt = self.rng.exponential(1 / rates.sum())
            nxt = self.ev[i][0] if i < len(self.ev) else math.inf
            if self.t + dt >= min(nxt, self.seconds):
                if nxt >= self.seconds:
                    break
                self.t = nxt
                self._exo(self.ev[i])
                i += 1
            else:
                self.t += dt
                k = int(self.rng.choice(3, p=rates / rates.sum()))
                if k == 0:
                    self._limit()
                elif k == 1 and self.live:
                    cl = self.live[int(self.rng.integers(len(self.live)))]
                    self._go(self.lit, LP, IN["X"](cl, 0))
                    self._drop(cl)
                elif k == 2:
                    self._market(INF, 1 if gap > 0 else -1, 100 * int(self.rng.geometric(1 / 1.5)), True,
                                 self.rng.random() < self.dark_first)
            self._block_step()
            self.mids.append((self.t, self.mid()))
        return self._result()

    def _exo(self, e):
        t, kind, side, qty = e
        if kind == "jump":
            self.vstar += side
            self._stale()
        elif kind == "noise":
            self._market(NOISE, side, qty, False, self.rng.random() < self.dark_first)
        elif kind == "patient":
            self._order(self.dark, PATIENT, side, qty, 0, "D", "M")
        elif kind == "ping":
            self._order(self.dark, PINGER, side, qty, 0, "I", "M")
        elif kind == "child" and self.fund_left > 0:
            self._market(FUND, 1, min(qty, self.fund_left), False)
        elif kind == "cond" and self.strategy == "block" and START <= t < START + WINDOW:
            self.block.add(f"seller{self.cl}", -1, qty, 1000, int(t * SEC))
        if self.strategy in ("dark", "dark_min") and self.fund_cl is None and t >= START:
            self.fund_cl = self._order(self.dark, FUND, 1, TARGET, 0, "D", "M",
                                       self.fund_min if self.strategy == "dark_min" else 0)
        if self.strategy == "block" and t >= START and not any(o.owner == "fund" for o in self.block.orders.values()):
            if self.fund_left > 0 and t < START + WINDOW:
                self.block.add("fund", 1, self.fund_left, 1000, int(t * SEC))
        if t >= START + WINDOW and self.fund_left > 0 and self.strategy != "none":
            if self.fund_cl is not None:
                self._go(self.dark, FUND, IN["X"](self.fund_cl, 0))
                self.fund_cl = -1
            for o in [o for o in self.block.orders.values() if o.owner == "fund"]:
                self.block.cancel(o.id)
            while self.fund_left > 0 and self.lit.book(1).best(-1) is not None:
                self._market(FUND, 1, self.fund_left, False)

    def _block_step(self):
        if self.strategy != "block":
            return
        now = int(self.t * SEC)
        for iid, _bid, sid, q in self.block.invitations(now):
            seller = self.block.orders[sid].owner
            self.block.firm_up(iid, "fund", now)
            if self.rng.random() < 1 - self.leaky:
                got = self.block.firm_up(iid, seller, now)
                if got:
                    p = self.mid()
                    self.fills.setdefault(FUND, []).append((self.t, "BLOCK", 1, q, p, False))
                    self.fund_left -= q
            else:                                           # learns there is a buyer, buys ahead on LIT
                self.leaks += 1
                self.block.cancel(sid)
                self._market(BLOCK, 1, 2000, False)
                self.front_runs.append((self.t, 2000, True))
        self.block.expire(now)

    def _result(self) -> dict:
        return {"fills": self.fills, "mids": np.array(self.mids), "pings": self.pings, "leaks": self.leaks,
                "vstar": self.vstar, "front_runs": self.front_runs, "fund_pings": self.fund_pings,
                "dark_tries": self.dark_tries}


def run(seed: int = 1, strategy: str = "lit", **kw) -> dict:
    mk = Market(seed, strategy, **kw)
    r = mk.run()
    mids = r["mids"]
    m0 = mids[np.searchsorted(mids[:, 0], START) - 1, 1]
    f = [(p, q) for _t, _v, _s, q, p, _i in r["fills"].get(FUND, [])]
    by: dict[str, int] = {}
    for _t, v, _s, q, _p, _i in r["fills"].get(FUND, []):
        by[v] = by.get(v, 0) + q
    done = max((t for t, *_ in r["fills"].get(FUND, [])), default=START)
    fills = r["fills"].get(FUND, [])
    ft = np.array([x[0] for x in fills])
    fq = np.array([x[3] for x in fills], float)
    lam, price = mk.lam, m0

    def after(t):                                   # fund shares filled strictly after time t
        return fq[ft > t].sum()
    # accounting in basis points of the arrival price (a tick is 0.01 at 100.00): a lit buy of q moves P* by lam q
    own = sum(lam * x[3] * after(x[0]) for x in fills if x[1] == "LIT") / TARGET / price * 1e4
    leak = sum(lam * q * after(t) for t, q, fund in r["front_runs"] if fund) / TARGET / price * 1e4
    return {"shortfall": shortfall_bps(1, f, m0), "filled": sum(q for _, q in f), "by_venue": by,
            "drift": pre_completion_drift_bps(1, mids[:, 0], mids[:, 1], START, START + WINDOW),
            "pings": r["pings"], "fund_pings": r["fund_pings"], "leaks": r["leaks"], "done": done,
            "own_impact": own, "leakage": leak,
            "front_run": sum(q for _, q, fund in r["front_runs"] if fund)}


STRATEGIES = ("lit", "dark", "dark_min", "block")


@functools.cache
def compare(seeds=tuple(range(1, 17))) -> dict:
    """Every strategy on the same seeds: means and standard errors of the shortfall, the drift, and the accounted
    own-impact and leakage costs."""
    out = {}
    for s in STRATEGIES:
        rs = [run(seed, s) for seed in seeds]

        def mse(key, rs=rs):
            x = np.array([r[key] for r in rs], float)
            return float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x)))
        out[s] = {k: mse(k) for k in ("shortfall", "drift", "own_impact", "leakage", "front_run", "fund_pings",
                                      "leaks", "done")}
        share = np.array([(r["by_venue"].get("DARK", 0) + r["by_venue"].get("BLOCK", 0)) / r["filled"] for r in rs])
        out[s]["dark_share"] = (float(share.mean()), float(share.std(ddof=1) / np.sqrt(len(share))))
    return out


@functools.cache
def zhu(seeds=(1, 2, 3, 4), h: float = 30.0) -> dict:
    """No fund, no pinger: the dark fill rate of informed and uninformed takers who try the dark pool first, and the
    h-second mark-out per share of resting fills in the dark (patient traders) and on the lit book (providers)."""
    tried = {True: 0, False: 0}
    got = {True: 0, False: 0}
    mo = {"DARK": [0.0, 0.0, 0], "LIT": [0.0, 0.0, 0]}          # capture, move, shares
    for seed in seeds:
        r = Market(seed, "none", pinger=False).run()
        mids = r["mids"]

        def mid_at(t, mids=mids):
            return mids[max(np.searchsorted(mids[:, 0], t, side="right") - 1, 0), 1]
        for k in (True, False):
            tried[k] += r["dark_tries"].get(k, 0)
        for sess in (NOISE, INF):
            for _t, v, _side, q, _p, _inf in r["fills"].get(sess, []):
                if v == "DARK":
                    got[sess == INF] += q
        for sess, venue in ((PATIENT, "DARK"), (LP, "LIT")):
            for t, v, side, q, p, _inf in r["fills"].get(sess, []):
                if v == venue and t < 2700.0 - h:
                    m0 = mid_at(t - 1e-9)
                    mo[venue][0] += q * side * (m0 - p)
                    mo[venue][1] += q * side * (mid_at(t + h) - m0)
                    mo[venue][2] += q
    return {"fill_informed": got[True] / tried[True], "fill_uninformed": got[False] / tried[False],
            "capture_dark": mo["DARK"][0] / mo["DARK"][2], "move_dark": mo["DARK"][1] / mo["DARK"][2],
            "capture_lit": mo["LIT"][0] / mo["LIT"][2], "move_lit": mo["LIT"][1] / mo["LIT"][2],
            "dark_shares": mo["DARK"][2], "lit_shares": mo["LIT"][2]}
