"""firm.halts -- price bands, limit states, trading pauses, market-wide halts and velocity logic, as venue-side
policies that firm.exchsim loads (build of One Quant Book 10, chapter 25).

A policy is passed as ExchangeConfig(halts=...); the simulator calls policy.schedule(sim, venue) once, and the
policy then watches the venue's engine every `check_s` seconds (Simulator.schedule_call) and sends the engine's own
controls: R (a price band: orders priced outside it are rejected, and matching stops at it), P (phase: 'H' halted,
'U' reopening call, 'T' trading; leaving the call uncrosses it, firm.auctionsim's auction). Prices in the engine's
units (1/10,000 of a currency unit); times in seconds from the open.

API (stable):
    LULD(pct, window_s, limit_state_s, pause_s, check_s, locate, shadow, update_pct)   limit up-limit down in the
                                   manner of the US plan: a reference price (the mean trade price over the last
                                   window_s, or the reopening price; it moves only when it has changed by update_pct
                                   or more), bands at +-pct of it on the tick grid; a limit state when the best offer
                                   is at or below the lower band or the best bid at or above the upper band; a pause
                                   (reopening call) of pause_s if the limit state lasts limit_state_s
    MarketWide(levels, halt_s, check_s, reference)   halts every instrument for halt_s when the price falls by a level
                                   (fractions of `reference`), each level once
    Velocity(ticks, window_s, pause_s, check_s, locate)   a pause (reopening call) of pause_s when the trade price
                                   moves by `ticks` or more within window_s
    Combined(*policies)            several policies on one venue
    policy.log                     [(t_s, event, detail)]; for LULD also policy.bands [(t_s, lo, hi)] and policy.dist
                                   [(t_s, best bid and best ask minus the lower band, in ticks)]; LULD(..., shadow=True)
                                   computes the bands and limit states without sending anything (the market without
                                   the mechanism)
"""
from __future__ import annotations

import pathlib
import sys
from collections import deque

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "exchsim"))
from firm_exchsim_codec import NT  # noqa: E402

CTL = NT["ctl"]
SEC = 1_000_000_000


class _Policy:
    check_s = 0.5

    def schedule(self, sim, venue) -> None:
        self.sim, self.v = sim, venue
        self.t0 = venue.cfg.phases.open_ns
        self.end = venue.cfg.phases.close_ns
        self.seen = 0
        self.log: list = []
        self.trades: deque = deque()
        sim.schedule_call(self.t0, self._tick)

    def _send(self, t_ns: int, msg) -> None:
        self.sim._process(t_ns, self.v, 0, msg)

    def _new_trades(self, t_ns: int, locate: int) -> list:
        tr = self.v.engine.trades
        new = [(t_ns / SEC - self.t0 / SEC, x[2], x[3]) for x in tr[self.seen:] if x[1] == locate]
        self.seen = len(tr)
        return new

    def _tick(self, t_ns: int) -> None:
        self.check(t_ns)
        if t_ns + self.check_s * SEC < self.end:
            self.sim.schedule_call(t_ns + int(self.check_s * SEC), self._tick)

    def check(self, t_ns: int) -> None:                       # pragma: no cover - overridden
        raise NotImplementedError


class LULD(_Policy):
    def __init__(self, pct: float, window_s: float = 60.0, limit_state_s: float = 5.0, pause_s: float = 30.0,
                 check_s: float = 0.5, locate: int = 1, shadow: bool = False, update_pct: float = 0.0):
        self.pct, self.window, self.ls, self.pause = pct, window_s, limit_state_s, pause_s
        self.update = update_pct
        self.check_s, self.locate, self.shadow = check_s, locate, shadow
        self.bands: list = []
        self.dist: list = []
        self.ref = None
        self.band = (0, 0)
        self.limit_since = None
        self.paused_until = None

    def _set_band(self, t_ns: int, ref: float) -> None:
        st = self.v.engine.inst[self.locate]
        tick = st.tick
        lo = int(ref * (1 - self.pct)) // tick * tick
        hi = -(-int(ref * (1 + self.pct)) // tick) * tick
        if (lo, hi) != self.band:
            self.band = (lo, hi)
            if not self.shadow:
                self._send(t_ns, CTL["R"](self.locate, int(ref), lo, hi))
            self.bands.append(((t_ns - self.t0) / SEC, lo, hi))

    def check(self, t_ns: int) -> None:
        t = (t_ns - self.t0) / SEC
        st = self.v.engine.inst[self.locate]
        for x in self._new_trades(t_ns, self.locate):
            self.trades.append(x)
        while self.trades and self.trades[0][0] < t - self.window:
            self.trades.popleft()
        if self.paused_until is not None:
            if t >= self.paused_until:
                self._send(t_ns, CTL["P"](self.locate, "T", "RESM"))
                self.paused_until = None
                self.log.append((t, "resume", st.last))
                self.trades.clear()
                self.trades.append((t, st.last, 1))
                self._set_band(t_ns, st.last)
            return
        if self.trades:
            ref = sum(p for _, p, _ in self.trades) / len(self.trades)
        else:
            ref = self.ref if self.ref is not None else st.ref_price
        if self.ref is not None and abs(ref / self.ref - 1) < self.update:
            ref = self.ref                                # the reference moves only by update_pct or more
        self.ref = ref
        self._set_band(t_ns, ref)
        lo, hi = self.band
        bid, ask = st.book.best(1), st.book.best(-1)
        if bid is not None and ask is not None:
            self.dist.append((t, (bid - lo) / st.tick, (ask - lo) / st.tick))
        limit = (ask is not None and ask <= lo) or (bid is not None and bid >= hi)
        if self.shadow:
            if limit and self.limit_since is None:
                self.log.append((t, "limit", lo))
            self.limit_since = t if limit else None
            return
        if limit:
            if self.limit_since is None:
                self.limit_since = t
                self.log.append((t, "limit", lo if ask is not None and ask <= lo else hi))
            elif t - self.limit_since >= self.ls:
                self._send(t_ns, CTL["P"](self.locate, "U", "LULD"))
                self.paused_until = t + self.pause
                self.limit_since = None
                self.log.append((t, "pause", self.pause))
        else:
            self.limit_since = None


class MarketWide(_Policy):
    def __init__(self, levels=(0.07, 0.13, 0.20), halt_s: float = 60.0, check_s: float = 0.5, reference=None,
                 locate: int = 1):
        self.levels, self.halt, self.check_s, self.reference, self.locate = levels, halt_s, check_s, reference, locate
        self.done: set = set()
        self.halted_until = None

    def check(self, t_ns: int) -> None:
        t = (t_ns - self.t0) / SEC
        st = self.v.engine.inst[self.locate]
        ref = self.reference or st.ref_price
        if self.halted_until is not None:
            if t >= self.halted_until:
                self._send(t_ns, CTL["P"](0, "U", "MWCR"))
                self._send(t_ns + 1, CTL["P"](0, "T", "RESM"))
                self.halted_until = None
                self.log.append((t, "resume", st.last))
            return
        if not st.last:
            return
        drop = 1 - st.last / ref
        for i, lv in enumerate(self.levels):
            if drop >= lv and i not in self.done:
                self.done.add(i)
                self._send(t_ns, CTL["P"](0, "H", "MWCB"))
                self.halted_until = t + self.halt
                self.log.append((t, "halt", lv))
                break


class Velocity(_Policy):
    def __init__(self, ticks: int, window_s: float = 1.0, pause_s: float = 5.0, check_s: float = 0.1,
                 locate: int = 1):
        self.ticks, self.window, self.pause, self.check_s, self.locate = ticks, window_s, pause_s, check_s, locate
        self.paused_until = None

    def check(self, t_ns: int) -> None:
        t = (t_ns - self.t0) / SEC
        st = self.v.engine.inst[self.locate]
        for x in self._new_trades(t_ns, self.locate):
            self.trades.append(x)
        while self.trades and self.trades[0][0] < t - self.window:
            self.trades.popleft()
        if self.paused_until is not None:
            if t >= self.paused_until:
                self._send(t_ns, CTL["P"](self.locate, "T", "RESM"))
                self.paused_until = None
                self.trades.clear()
                self.log.append((t, "resume", st.last))
            return
        if self.trades:
            ps = [p for _, p, _ in self.trades]
            if (max(ps) - min(ps)) >= self.ticks * st.tick:
                self._send(t_ns, CTL["P"](self.locate, "U", "VELO"))
                self.paused_until = t + self.pause
                self.log.append((t, "pause", max(ps) - min(ps)))


class Combined:
    def __init__(self, *policies):
        self.policies = policies

    def schedule(self, sim, venue) -> None:
        for p in self.policies:
            p.schedule(sim, venue)
