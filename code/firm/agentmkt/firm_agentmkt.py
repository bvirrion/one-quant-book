"""firm.agentmkt -- agent populations on the exchange simulator (build of One Quant Book 10, chapter 27; first used in
chapter 11).

A Population is one firm.exchsim Agent that runs the background traders of a market as independent Poisson clocks,
each seeded from the population's seed, and sends their orders through its own sessions with a latency of zero, so
that everything they do reacts to the book as it is:

  liquidity providers    limit orders on each side: a share `near` one tick from the opposite best quote, the others
                         at k = 1..depth ticks from it with probability proportional to k ** shape (shape 1: a book
                         whose depth grows linearly away from the price), one lot each; every resting order cancels
                         at rate `cancel`
  noise takers           market orders at rate `noise`, sizes geometric in lots; their signs follow runs of Pareto
                         length (tail `run_tail`) when run_tail > 0 (long memory of order flow), else fair coins
  fundamentalists        market orders toward a hidden value V at rate fund * |V - mid| (ticks); V is a random walk
                         with jumps of one tick at rate v_rate
  chartists              market orders in the direction of the mid's change over chart_window seconds, at rate
                         chart * |change| (ticks) (chapter 27; none by default)
An intraday activity curve (`curve`: multipliers over equal segments of the session, empty for none) scales the noise
rate and the providers' rate together, so that volume and depth follow a daily pattern (chapter 16).
The noise orders and the jumps of V are exogenous: drawn in advance from the seed, the same whatever else happens in
the market, so that two runs that differ by one agent's orders can be compared path by path (counterfactual impact);
the providers and fundamentalists react and draw from a second stream.
Other agents (execution algorithms, market makers) are added to the same Simulator as usual; the Result's tape()
is in firm.tape's format.

API (stable):
    PopulationConfig(...)                     the rates above (seconds, ticks, lots of 100 shares)
    Population(cfg, seed, seconds)            the Agent; .v_path (times ns, V in price units) after the run
    Metaorder(plan, name="meta")              an execution agent: plan = [(start_ns, sign, shares, children,
                                              duration_ns)], equal market-order children spread over the duration
    MarketMaker(lots, skew, max_lots, refresh_s)   an inventory-skewing market maker (chapter 27)
    facts(tape, sample_s)                     stylised facts: return kurtosis and autocorrelation, volatility
                                              clustering, trade-sign memory, spread, depth (FACTS)
    distance(sim, target, scale), msm(run, grid, target, scale, seeds)   the method of simulated moments on a grid
    session(cfg, seconds, seed, agents=(), venue=None) -> (Result, Population)   one venue, the population, agents
"""
from __future__ import annotations

import pathlib
import sys
from collections import deque
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "exchsim"))
from firm_exchsim import SEC, Agent, ExchangeConfig, LatencyModel, Order, Phases, SessionSpec, Simulator  # noqa: E402

T0 = 34_200 * SEC
ZERO = LatencyModel(entry_ns=0, ack_ns=0, data_ns=0)


@dataclass(frozen=True)
class PopulationConfig:
    lo_rate: float = 6.0                   # limit orders a second, per side
    near: float = 0.4                      # share of them one tick from the opposite best quote
    depth: int = 20
    shape: float = 1.0
    cancel: float = 0.02                   # per resting order a second
    noise: float = 1.0                     # market orders a second
    mo_lots: float = 2.0
    run_tail: float = 0.0                  # Pareto tail of sign runs (0: independent signs)
    fund: float = 0.05                     # fundamentalist orders a second per tick of |V - mid|
    v_rate: float = 0.05
    start: int = 1_000_000                 # price units (100.00)
    tick: int = 100
    curve: tuple = ()                      # activity multipliers over equal segments of the session
    chart: float = 0.0                     # chartist market orders a second per tick of the mid's recent trend
    chart_window: float = 30.0             # seconds over which chartists measure the trend


class Population(Agent):
    name = "pop"

    def __init__(self, cfg: PopulationConfig = PopulationConfig(), seed: int = 1, seconds: float = 3600.0):  # noqa: B008
        self.cfg, self.seed = cfg, seed
        self.rng = np.random.default_rng(seed + 7919)                # endogenous stream
        w = np.arange(1, cfg.depth + 1, dtype=float) ** cfg.shape
        self.w = w / w.sum()
        self.v = float(cfg.start)
        self.v_path = [(0, self.v)]
        self.seconds = seconds
        self.live: list[int] = []
        self.pos: dict[int, int] = {}
        self.exo = self._exogenous(np.random.default_rng(seed), seconds)

    def _exogenous(self, rx, seconds: float) -> list:
        """(t_s, kind, value): noise orders (signed shares) and jumps of V (signed ticks), drawn in advance."""
        c, ev = self.cfg, []
        run_left, run_sign = 0, 1
        t = 0.0
        top = max(c.curve) if c.curve else 1.0
        while c.noise > 0:
            t += rx.exponential(1 / (c.noise * top))
            if t >= seconds:
                break
            if c.curve and rx.random() * top > self._level(t):
                continue
            if c.run_tail > 0:
                if run_left <= 0:
                    run_left, run_sign = int(rx.pareto(c.run_tail)) + 1, 1 if rx.random() < 0.5 else -1
                run_left -= 1
                sign = run_sign
            else:
                sign = 1 if rx.random() < 0.5 else -1
            ev.append((t, "noise", sign * 100 * int(rx.geometric(1 / c.mo_lots))))
        t = 0.0
        while c.v_rate > 0:
            t += rx.exponential(1 / c.v_rate)
            if t >= seconds:
                break
            ev.append((t, "jump", 1 if rx.random() < 0.5 else -1))
        return sorted(ev)

    def _level(self, t_s: float) -> float:
        c = self.cfg
        if not c.curve:
            return 1.0
        return float(c.curve[min(int(t_s / self.seconds * len(c.curve)), len(c.curve) - 1)])

    # -- clocks ---------------------------------------------------------------------------------------------------
    def on_start(self, ctx):
        c = self.cfg
        for k in range(1, c.depth + 1):                              # an opening book, one lot a level
            for side, px in (("B", c.start - k * c.tick), ("S", c.start + k * c.tick)):
                self._add(ctx, side, px)
        self.v_path = [(ctx.now_ns, self.v)]
        self.t0 = ctx.now_ns
        self.hist = deque()
        self.trend = 0.0
        for i, (t, _, _) in enumerate(self.exo):
            ctx.set_timer(int(t * SEC), ("exo", i))
        self._next(ctx)

    def _trend(self, ctx) -> float:
        """The mid's change over the last chart_window seconds, in ticks (chartists' signal)."""
        t, m = (ctx.now_ns - self.t0) / SEC, self._mid(ctx)
        self.hist.append((t, m))
        while len(self.hist) > 1 and self.hist[1][0] <= t - self.cfg.chart_window:
            self.hist.popleft()
        return (m - self.hist[0][1]) / self.cfg.tick

    def _rates(self, ctx):
        c = self.cfg
        gap = abs(self.v - self._mid(ctx)) / c.tick
        lo = 2 * c.lo_rate
        if c.curve:
            lo *= self._level((ctx.now_ns - self.t0) / SEC)
        if c.chart > 0:
            self.trend = self._trend(ctx)
            return np.array([lo, c.cancel * len(self.live), c.fund * gap, c.chart * abs(self.trend)])
        return np.array([lo, c.cancel * len(self.live), c.fund * gap])

    def _next(self, ctx):
        r = self._rates(ctx)
        self._r = r
        ctx.set_timer(max(1, int(self.rng.exponential(1 / r.sum()) * SEC)), "tick")

    def on_timer(self, ctx, tag):
        c = self.cfg
        if tag != "tick":
            _, kind, x = self.exo[tag[1]]
            if kind == "noise":
                ctx.send(Order(side="B" if x > 0 else "S", qty=abs(x), price=0, tif="I"))
            else:
                self.v += x * c.tick
                self.v_path.append((ctx.now_ns, self.v))
            return
        r = self._r
        k = int(self.rng.choice(len(r), p=r / r.sum()))
        if k == 0:
            side = "B" if self.rng.random() < 0.5 else "S"
            b, _, a, _ = ctx.top(1)
            ref = a if side == "B" else b
            if ref is None:
                ref = int(round(self._mid(ctx) / c.tick)) * c.tick + (c.tick if side == "B" else -c.tick)
            d = 1 if self.rng.random() < c.near else 1 + int(self.rng.choice(c.depth, p=self.w))
            self._add(ctx, side, ref - d * c.tick if side == "B" else ref + d * c.tick)
        elif k == 1 and self.live:
            cl = self.live[int(self.rng.integers(len(self.live)))]
            ctx.cancel(cl)
            self._drop(cl)
        elif k == 2:
            ctx.send(Order(side="B" if self.v > self._mid(ctx) else "S", qty=100, price=0, tif="I"))
        elif k == 3:                                                  # a chartist follows the trend
            ctx.send(Order(side="B" if self.trend > 0 else "S", qty=100, price=0, tif="I"))
        self._next(ctx)

    # -- helpers --------------------------------------------------------------------------------------------------
    def _mid(self, ctx) -> float:
        b, _, a, _ = ctx.top(1)
        if b is None or a is None:
            return self.v
        return 0.5 * (b + a)

    def _add(self, ctx, side, px):
        if px <= 0:
            return
        cl = ctx.send(Order(side=side, qty=100, price=int(px)))
        self.pos[cl] = len(self.live)
        self.live.append(cl)

    def _drop(self, cl):
        i = self.pos.pop(cl, None)
        if i is None:
            return
        last = self.live.pop()
        if last != cl:
            self.live[i], self.pos[last] = last, i

    def on_report(self, ctx, rep):
        if type(rep).__name__ in ("Out_E", "Out_C") and getattr(rep, "leaves", 0) == 0:
            self._drop(rep.cl_ord_id)


class Metaorder(Agent):
    def __init__(self, plan, name: str = "meta"):
        self.plan, self.name = plan, name

    def on_start(self, ctx):
        for k, (start, _, _, n, dur) in enumerate(self.plan):
            for j in range(n):
                ctx.set_timer(start + j * dur // n - ctx.now_ns, (k, j))

    def on_timer(self, ctx, tag):
        k, _ = tag
        _, sign, qty, n, _ = self.plan[k]
        ctx.send(Order(side="B" if sign > 0 else "S", qty=qty // n, price=0, tif="I"))


class MarketMaker(Agent):
    """Every refresh_s seconds, quotes `lots` on each side at the others' best bid and ask (one tick inside each when
    their spread is wider than two ticks), both shifted against its inventory by skew ticks per lot held: a long
    maker lowers both quotes, to sell more and buy less. It stops bidding (offering) beyond max_lots long (short)
    and keeps a quote that is already at its price, so as not to lose its place in the queue."""

    def __init__(self, lots: int = 2, skew: float = 0.5, max_lots: int = 20, refresh_s: float = 0.5,
                 name: str = "mm", tick: int = 100):
        self.lots, self.skew, self.max, self.refresh, self.name, self.tick = lots, skew, max_lots, refresh_s, name, tick

    def on_start(self, ctx):
        ctx.set_timer(T0 + SEC - ctx.now_ns, 0)

    @staticmethod
    def _best(book, side, mine):
        for p in book.prices(side):
            if any(o.visible and o.ref not in mine for o in book.level_orders(side, p)):
                return p
        return None

    def on_timer(self, ctx, tag):
        live = ctx.working()
        mine = {o["ref"] for o in live}
        bk = ctx.book(1).book
        b, a = self._best(bk, 1, mine), self._best(bk, -1, mine)
        want = {}
        if b is not None and a is not None:
            inside = self.tick if a - b > 2 * self.tick else 0
            inv = ctx.position(1) / 100
            shift = int(round(self.skew * inv)) * self.tick
            if inv < self.max:
                want["B"] = min(b + inside - shift, a - self.tick)
            if inv > -self.max:
                want["S"] = max(a - inside - shift, b + self.tick)
        for o in live:
            if want.get(o["side"]) == o["price"]:
                del want[o["side"]]
            else:
                ctx.cancel(o["cl"])
        for side, px in want.items():
            ctx.send(Order(side=side, qty=100 * self.lots, price=int(px)))
        ctx.set_timer(int(self.refresh * SEC), 0)


FACTS = ("kurtosis", "ret_acf1", "absret_acf", "sign_acf1", "sign_acf10", "spread", "depth")


def facts(tape, sample_s: float = 10.0) -> dict:
    """Stylised facts of a firm.tape-format tape: excess kurtosis and lag-1 autocorrelation of sample_s mid returns,
    mean autocorrelation of their absolute values over lags 1-5 (volatility clustering), autocorrelation of the signs
    of aggressive orders (the prints of one order, same time and sign, counted once) at lags 1 and 10 (long memory of
    order flow), time-weighted mean spread (ticks) and depth at the best (lots, mean of the two sides)."""
    top = tape.top
    ok = (top["bid"] > 0) & (top["ask"] > 0)
    t, bid, ask = top["t"][ok], top["bid"][ok].astype(float), top["ask"][ok].astype(float)
    mid = 0.5 * (bid + ask)
    grid = np.arange(t[0], t[-1], sample_s)
    m = mid[np.maximum(np.searchsorted(t, grid, side="right") - 1, 0)]
    r = np.diff(m)
    r = r - r.mean()

    def acf(x, k):
        x = np.asarray(x, float) - np.mean(x)
        return float(x[k:] @ x[:-k] / (x @ x)) if len(x) > k and x @ x > 0 else 0.0
    w = np.diff(np.r_[t, t[-1]])
    q = (top["bid_qty"][ok] + top["ask_qty"][ok]) / 200.0
    tr = tape.trades
    new = np.r_[True, (np.diff(tr["t"]) > 0) | (np.diff(tr["sign"]) != 0)]   # one aggressive order, one sign
    sgn = tr["sign"][new].astype(float)
    kurt = float(np.mean(r**4) / np.mean(r**2) ** 2 - 3) if np.mean(r**2) > 0 else 0.0
    clus = float(np.mean([acf(np.abs(r), k) for k in range(1, 6)]))
    return {"kurtosis": kurt, "ret_acf1": acf(r, 1), "absret_acf": clus,
            "sign_acf1": acf(sgn, 1), "sign_acf10": acf(sgn, 10), "spread": float(w @ (ask - bid) / w.sum()),
            "depth": float(w @ q / w.sum())}


def distance(sim: dict, target: dict, scale: dict) -> float:
    """Sum over facts of ((simulated - target) / scale)^2."""
    return float(sum(((sim[k] - target[k]) / scale[k]) ** 2 for k in target))


def msm(run, grid, target: dict, scale: dict, seeds) -> dict:
    """The method of simulated moments on a grid: run(params, seed) -> facts; the average over seeds (the same seeds
    at every point: common random numbers) is compared with the target; returns the best point, its facts and every
    point's distance."""
    rows = []
    for params in grid:
        sims = [run(params, s) for s in seeds]
        mean = {k: float(np.mean([x[k] for x in sims])) for k in target}
        rows.append((distance(mean, target, scale), params, mean))
    rows.sort(key=lambda x: x[0])
    return {"best": rows[0][1], "distance": rows[0][0], "facts": rows[0][2], "all": rows}


def session(cfg: PopulationConfig = PopulationConfig(), seconds: float = 3600.0, seed: int = 1,  # noqa: B008
            agents=(), venue: ExchangeConfig | None = None):
    end = T0 + int(seconds * SEC)
    ph = Phases(start_ns=T0 - SEC, open_ns=T0, close_ns=end, end_ns=end + 1)
    venue = venue or ExchangeConfig(phases=ph)
    sim = Simulator(venue, seed=seed)
    pop = Population(cfg, seed, seconds)
    sim.add_agent(pop, SessionSpec(firm="POP", latency=ZERO, cod=False))
    for a in agents:
        sim.add_agent(a, SessionSpec(firm=a.name.upper(), latency=LatencyModel(20_000, 20_000, 20_000)))
    return sim.run(), pop
