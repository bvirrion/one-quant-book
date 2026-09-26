"""firm.venueprofile -- venue profiles: one page per venue, validated, and the simulator configuration each one produces
(One Quant Book 11, chapter 29).

A profile holds what a quoting strategy must know about a venue before its first order: the matching rule, the tick and
lot, the fees and their unit, the feed, the order types, the delays (speed bump, batch interval), the message budget,
the session and the quirks, plus the quoting parameters the desk has chosen for that venue. `validate` checks a
profile against its own rules; `exchange_config` turns it into a firm.exchsim configuration (Book 10's simulator);
`venue_record` into Book 1's firm.venues registry row and `fee_schedule` into Book 1's firm.feesched schedule.

The chapter's experiment runs one quoting strategy (`Quoter`, written once) on every simulated profile over the same
market: Book 7's firm_tape flow replayed as real orders, plus jumps of the efficient price that a faster market
reveals first, and a fast arbitrageur (`Sniper`) who takes stale quotes on each jump. The quoter hears of the jump
`signal_ns` later and cancels its stale side. The same run with the home venue's parameters and with the profile's
own shows which parameters must change.

API (stable):
    TYPES, MATCHING                                  venue types and matching rules known to the schema
    Quoting(size, min_move, gap_ns, post_only, cool_ns, limit)      the venue-specific quoting parameters
    Profile(...)                                      the schema (see the dataclass); to_dict / from_dict
    validate(p) -> list[str]                          the rules; an empty list is a valid profile
    Registry(profiles)                                .get(name), .by_type(t), .simulated(), .dump(path), .load(path)
    standard() -> Registry                            the chapter's eleven profiles (eight simulated)
    HOME                                              the home venue's quoting (a price-time equity exchange)
    exchange_config(p) -> firm_exchsim.ExchangeConfig
    venue_record(p) -> firm_venues.Venue;  fee_schedule(p) -> firm_feesched.Schedule
    jumps(seconds, rate, seed) -> list[(t_ns, +-1)]   the efficient-price jumps of the experiment
    run(p, quoting=None, seconds=1800, seed=7) -> dict
        fills, volume, edge (ticks per unit at 5 s against the efficient price), picked (units taken by the Sniper),
        takes (units the quoter's own orders took on arrival),
        messages (orders and cancels sent), orders, rejects, fees_ticks (fees in ticks per unit), pnl_ticks (P&L in
        ticks x units, fees included)
"""
from __future__ import annotations

import json
import pathlib
import sys
from dataclasses import asdict, dataclass, field, replace

import numpy as np

_HERE = pathlib.Path(__file__).resolve().parent
for _dep in ("exchsim", "tape", "venues", "feesched"):
    sys.path.insert(0, str(_HERE.parent / _dep))
import firm_exchsim as X  # noqa: E402
import firm_feesched  # noqa: E402
import firm_venues  # noqa: E402
from firm_tape import TapeConfig  # noqa: E402

TYPES = ("equity_lit", "equity_inverted", "equity_bump", "batch", "futures_pro_rata", "futures_fifo", "crypto",
         "event", "options", "fx_ecn", "on_chain")
MATCHING = ("fifo", "pro_rata", "batch", "amm")
FEE_UNITS = ("share", "contract", "bp")
ORDER_TYPES = ("limit", "ioc", "post_only", "mass_quote", "replace", "midpoint_peg")
SIMULATED = ("equity_lit", "equity_inverted", "equity_bump", "batch", "futures_pro_rata", "futures_fifo", "crypto",
             "event")


@dataclass(frozen=True)
class Quoting:
    size: int = 100                  # units per quote
    offset: int = 0                  # ticks behind the others' best bid and offer
    min_move: int = 1                # requote when the target moves by this many ticks
    gap_ns: int = 0                  # at least this long between two requotes (0: none)
    post_only: bool = False
    cool_ns: int = 500_000_000       # after a jump signal, leave the stale side empty this long
    limit: int = 2000                # position limit, units


HOME = Quoting()


@dataclass(frozen=True)
class Profile:
    name: str
    venue_type: str
    mic: str                         # a fictitious four-character code in the chapter's registry
    kind: str = "exchange"           # firm.venues kind
    asset_class: str = "equity"
    currency: str = "USD"
    session: str = "09:30-16:00"
    matching: str = "fifo"
    top_pct: int = 0                 # pro rata: share of an incoming order given first to the order that set the price
    tick: int = 100                  # price units of 1/10,000 currency
    lot: int = 100
    fee_unit: str = "share"
    make: float = -0.0020            # per unit (share, contract) or in basis points; negative = rebate
    take: float = 0.0030
    feed: str = "mbo"                # 'mbo' order by order, 'mbp' by price level, 'top' best only
    order_types: tuple = ("limit", "ioc", "post_only", "replace")
    speed_bump_ns: int = 0
    asymmetric: bool = False         # the delay spares cancels (and post-only orders, where they exist)
    batch_ns: int = 0
    budget_orders_per_s: float = 0.0     # new orders a second the account may send for this instrument (0: none)
    budget_burst: int = 0
    cancels_free: bool = True        # cancels do not count against the budget
    last_look_ms: float = 0.0
    quirks: tuple = ()
    quoting: Quoting = field(default_factory=Quoting)
    simulated: bool = True

    def to_dict(self) -> dict:
        d = asdict(self)
        d["order_types"], d["quirks"] = list(self.order_types), list(self.quirks)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Profile:
        d = dict(d)
        d["quoting"] = Quoting(**d["quoting"])
        d["order_types"], d["quirks"] = tuple(d["order_types"]), tuple(d["quirks"])
        return cls(**d)


def validate(p: Profile) -> list[str]:
    e = []
    if p.venue_type not in TYPES:
        e.append(f"unknown venue type {p.venue_type!r}")
    if p.matching not in MATCHING:
        e.append(f"unknown matching rule {p.matching!r}")
    if p.fee_unit not in FEE_UNITS:
        e.append(f"unknown fee unit {p.fee_unit!r}")
    if p.tick <= 0 or p.lot <= 0:
        e.append("tick and lot must be positive")
    if len(p.mic) != 4 or not p.mic.isalnum() or not p.mic.isupper():
        e.append("MIC must be four upper-case characters")
    if p.top_pct and p.matching != "pro_rata":
        e.append("top_pct belongs to pro-rata matching only")
    if (p.matching == "batch") != (p.batch_ns > 0):
        e.append("batch matching needs a batch interval, and only batch matching has one")
    for t in p.order_types:
        if t not in ORDER_TYPES:
            e.append(f"unknown order type {t!r}")
    q = p.quoting
    if q.size <= 0 or q.size % p.lot:
        e.append("quote size must be a positive multiple of the lot")
    if q.post_only and "post_only" not in p.order_types:
        e.append("the quoting uses post-only orders, which the venue does not offer")
    if p.asymmetric and not p.speed_bump_ns:
        e.append("an asymmetric delay needs a delay")
    if p.asymmetric and "post_only" in p.order_types and not q.post_only:
        e.append("the delay spares post-only orders: the quoting should send them")
    if p.budget_orders_per_s > 0:
        if q.gap_ns <= 0:
            e.append(f"requotes are not paced, against a budget of {p.budget_orders_per_s} orders a second")
        elif 2e9 / q.gap_ns > p.budget_orders_per_s * 1.0001:      # a requote sends at most one new order a side
            e.append(f"requotes can need {2e9 / q.gap_ns:.3f} orders a second against a budget of "
                     f"{p.budget_orders_per_s}")
        if not p.cancels_free:
            e.append("cancels must be free: the jump cancel cannot wait for the budget")
    if p.fee_unit == "bp" and p.asset_class in ("equity", "futures"):
        e.append("fees in basis points on an equity or futures venue")
    if p.venue_type in SIMULATED and not p.simulated:
        e.append("a simulated venue type marked as not simulated")
    return e


class Registry:
    def __init__(self, profiles):
        self._p = {}
        for p in profiles:
            if p.name in self._p:
                raise ValueError(f"duplicate profile {p.name}")
            errs = validate(p)
            if errs:
                raise ValueError(f"{p.name}: " + "; ".join(errs))
            self._p[p.name] = p

    def get(self, name: str) -> Profile:
        return self._p[name]

    def by_type(self, t: str) -> list[Profile]:
        return [p for p in self._p.values() if p.venue_type == t]

    def simulated(self) -> list[Profile]:
        return [p for p in self._p.values() if p.simulated]

    def __iter__(self):
        return iter(self._p.values())

    def __len__(self) -> int:
        return len(self._p)

    def dump(self, path) -> None:
        pathlib.Path(path).write_text(json.dumps([p.to_dict() for p in self], indent=1) + "\n")

    @classmethod
    def load(cls, path) -> Registry:
        return cls([Profile.from_dict(d) for d in json.loads(pathlib.Path(path).read_text())])


BUDGET = 0.125                      # new orders a second: a 200,000-a-day account cap shared by about 18 instruments


def standard() -> Registry:
    """The chapter's registry. Fees and limits are illustrative of each type; chapter 29's dated box gives real ones."""
    ms, s = 1_000_000, 1_000_000_000
    return Registry([
        Profile("lit", "equity_lit", "XLIT", quirks=("round lots of 100 displayed", "access fee cap on takers")),
        Profile("inverted", "equity_inverted", "XINV", make=0.0010, take=-0.0005,
                quirks=("the maker pays; the taker is paid", "queues shorter at the touch")),
        Profile("bump", "equity_bump", "XBMP", speed_bump_ns=350_000, quirks=("the delay applies to every message",)),
        Profile("batch", "batch", "XBAT", matching="batch", batch_ns=100 * ms, make=0.0, take=0.0,
                quirks=("no time priority inside an interval", "one clearing price per batch")),
        Profile("futures_pr", "futures_pro_rata", "XFPR", asset_class="futures", session="17:00-16:00",
                matching="pro_rata", top_pct=40, tick=2500, lot=1, fee_unit="contract", make=0.0, take=0.0,
                order_types=("limit", "ioc", "replace", "mass_quote"), quoting=Quoting(size=500, post_only=False),
                quirks=("the order that sets a new best price gets 40% first", "size shown sets the share")),
        Profile("futures_fifo", "futures_fifo", "XFFI", asset_class="futures", session="17:00-16:00", tick=2500,
                lot=1, fee_unit="contract", make=0.0, take=0.0, order_types=("limit", "ioc", "replace"),
                quirks=("messaging efficiency ratio", "one queue per price")),
        Profile("crypto", "crypto", "XCRY", asset_class="crypto", currency="USDT", session="24h", tick=10_000, lot=1,
                fee_unit="bp", make=-0.5, take=2.5, feed="mbp", budget_orders_per_s=BUDGET, budget_burst=5,
                quoting=Quoting(gap_ns=16 * s), quirks=("order budget per account", "funding every 8 h on perps")),
        Profile("event", "event", "XEVT", asset_class="event", session="match", tick=100, lot=1, fee_unit="share",
                make=0.0, take=0.0, order_types=("limit", "replace"), speed_bump_ns=5 * s, asymmetric=True,
                quoting=Quoting(min_move=3),
                quirks=("placing is delayed in play; cancelling is not", "prices bounded by 0 and 1")),
        Profile("options", "options", "XOPT", asset_class="options", tick=100, lot=1, fee_unit="contract", make=-0.25,
                take=0.50, matching="pro_rata", top_pct=40, order_types=("limit", "ioc", "mass_quote", "replace"),
                quirks=("thousands of series quoted at once", "exchange-side quote risk protection"),
                simulated=False),
        Profile("fx_ecn", "fx_ecn", "XFXE", kind="mtf", asset_class="fx", session="24h-5d", tick=1, lot=1_000_000,
                fee_unit="bp", make=0.0, take=0.05, feed="mbp", last_look_ms=0.0,
                quoting=Quoting(size=1_000_000), quirks=("disclosed or undisclosed last look on other channels",),
                simulated=False),
        Profile("on_chain", "on_chain", "XAMM", kind="otc", asset_class="crypto", currency="USDC", session="24h",
                matching="amm", tick=1, lot=1, fee_unit="bp", make=0.0, take=30.0, order_types=("limit",),
                quirks=("blocks, gas and builders instead of a matching engine",), simulated=False),
    ])


def exchange_config(p: Profile) -> X.ExchangeConfig:
    if not p.simulated:
        raise ValueError(f"{p.name}: a {p.venue_type} venue is not simulated here")
    matching = {"fifo": "fifo", "pro_rata": "configurable", "batch": "fifo"}[p.matching]
    alloc = {"top_pct": p.top_pct, "fifo_pct": 0, "min_alloc": 1} if p.matching == "pro_rata" else None
    inst = X.InstrumentSpec("SIM1", 1, tick=p.tick, lot=p.lot, start_price=10_000 * p.tick, matching=matching,
                            alloc=alloc)
    unit = "bp" if p.fee_unit == "bp" else "share"
    return X.ExchangeConfig(venue=p.mic, instruments=(inst,), fees=X.FeeSchedule(p.make, p.take, unit=unit),
                            speed_bump_ns=p.speed_bump_ns, asymmetric_delay=p.asymmetric, batch_interval_ns=p.batch_ns)


def venue_record(p: Profile) -> firm_venues.Venue:
    return firm_venues.Venue(p.mic, p.mic, p.name, p.kind, "XX", p.currency,
                             {"share": "per_share", "contract": "per_contract", "bp": "bps"}[p.fee_unit])


def fee_schedule(p: Profile) -> firm_feesched.Schedule:
    return firm_feesched.Schedule(p.mic, p.make, p.take)


def jumps(seconds: float, rate: float = 1 / 20, seed: int = 7) -> list:
    rng = np.random.default_rng(seed + 1000)
    t, out = rng.exponential(1 / rate), []
    while t < seconds - 5:
        out.append((X.OPEN_NS + int(t * 1e9), int(rng.choice((-1, 1)))))
        t += rng.exponential(1 / rate)
    return out


# ------------------------------------------------------------------ the strategy and the arbitrageur
class Quoter(X.Agent):
    """Join the best bid and offer of the others; requote when the target moves by min_move ticks, no more often than
    gap_ns; on a jump signal cancel the stale side and leave it empty for cool_ns."""

    name = "quoter"

    def __init__(self, q: Quoting, tick: int, signals=(), signal_ns: int = 20_000):
        self.q, self.tick, self.signals, self.signal_ns = q, tick, list(signals), signal_ns
        self.last, self.pending = -(10**18), False
        self.cool = {"B": -1, "S": -1}
        self.messages = self.orders = self.rejects = 0

    def on_start(self, ctx):
        for t, s in self.signals:
            ctx.set_timer(t + self.signal_ns - ctx.now_ns, ("jump", s))

    def _ext_best(self, ctx, side: int):
        """The best price with someone else's order on it: our orders are known by the reference in their
        acknowledgement, which arrives before the feed shows them (ack_ns < data_ns)."""
        bk = ctx.book(1).book
        mine = {o["ref"] for o in ctx.orders.values() if o["ref"] is not None}
        for px in bk.prices(side):
            if any(o.ref not in mine for o in bk.level_orders(side, px) if o.visible):
                return px
        return None

    def _cancel(self, ctx, o):
        ctx.cancel(o["cl"])
        o["status"] = "cancelling"
        self.messages += 1

    def on_book(self, ctx, locate, top):
        wait = self.last + self.q.gap_ns - ctx.now_ns
        if wait > 0:
            if not self.pending:
                self.pending = True
                ctx.set_timer(wait, ("requote", 0))
            return
        self._requote(ctx)

    def on_timer(self, ctx, tag):
        kind, s = tag
        if kind == "requote":
            self.pending = False
            self._requote(ctx)
            return
        side = "S" if s > 0 else "B"                      # a jump up makes our offer stale
        self.cool[side] = ctx.now_ns + self.q.cool_ns
        for o in list(ctx.orders.values()):
            if o["side"] == side and o["status"] in ("live", "pending"):
                self._cancel(ctx, o)

    def on_report(self, ctx, rep):
        if type(rep).__name__[-1] == "J" and getattr(rep, "reason", "") == "T":
            self.rejects += 1

    def _requote(self, ctx):
        b, a = self._ext_best(ctx, 1), self._ext_best(ctx, -1)
        if b is None or a is None or b >= a:
            return
        pos, q = ctx.position(1), self.q
        b, a = b - q.offset * self.tick, a + q.offset * self.tick
        want = {"B": (b, q.size if pos + q.size <= q.limit and ctx.now_ns >= self.cool["B"] else 0),
                "S": (a, q.size if pos - q.size >= -q.limit and ctx.now_ns >= self.cool["S"] else 0)}
        changed = False
        for side, (px, qty) in want.items():
            mine = [o for o in ctx.orders.values() if o["side"] == side and o["status"] in ("live", "pending")]
            keep = [o for o in mine if qty and abs(o["price"] - px) < q.min_move * self.tick]
            for o in mine:
                if not keep or o is not keep[0]:
                    self._cancel(ctx, o)
                    changed = True
            if not keep and qty:
                ctx.send(X.Order(1, side, qty, px, post_only=q.post_only))
                self.messages += 1
                self.orders += 1
                changed = True
        if changed:
            self.last = ctx.now_ns


class Sniper(X.Agent):
    """Hears of each jump first and takes everything displayed at the stale best price with an immediate-or-cancel
    order."""

    name = "sniper"

    def __init__(self, signals=()):
        self.signals = list(signals)

    def on_start(self, ctx):
        for t, s in self.signals:
            ctx.set_timer(t - ctx.now_ns, s)

    def on_timer(self, ctx, s):
        b, bq, a, aq = ctx.top(1)
        if s > 0 and a is not None:
            ctx.send(X.Order(1, "B", aq, a, tif="I"))
        elif s < 0 and b is not None:
            ctx.send(X.Order(1, "S", bq, b, tif="I"))


def _limit_session(sim, firm: str, rate: float, burst: int):
    """Apply the budget to one firm's session only (the background stands for many participants, each under its own
    budget): new orders cost 1/rate seconds of a token bucket of `burst` orders; cancels are free."""
    eng = sim.venues[0].engine
    fid = sim._firm_id(firm)
    state = {"tokens": float(burst), "t": None}

    def throttled(s, t, weight=1):
        if s.firm != fid or weight == 0:
            return False
        if state["t"] is not None:
            state["tokens"] = min(float(burst), state["tokens"] + (t - state["t"]) / 1e9 * rate)
        state["t"] = t
        if state["tokens"] >= weight:
            state["tokens"] -= weight
            return False
        return True

    eng._throttled = throttled
    eng.rate = 1                                          # switch the engine's check on (weights in orders)
    eng.weights = {"O": 1, "U": 1, "Q": 2, "X": 0, "M": 0}


def run(p: Profile, quoting: Quoting | None = None, seconds: int = 1800, seed: int = 7, jump_rate: float = 1 / 20,
        signal_ns: int = 20_000, sniper_ns: int = 5_000) -> dict:
    q = quoting or p.quoting
    cfg = exchange_config(p)
    end = X.OPEN_NS + seconds * X.SEC
    cfg = replace(cfg, phases=replace(cfg.phases, close_ns=end, end_ns=end + X.SEC))
    sig = jumps(seconds, jump_rate, seed)
    sim = X.Simulator(cfg, seed=1)
    sim.add_background(X.TapeBackground(TapeConfig(seconds=seconds, seed=seed, news_at=None)))
    sim.add_events(jumps=sig)
    quoter = Quoter(q, p.tick, sig, signal_ns)
    sim.add_agent(quoter, X.SessionSpec(firm="HF1", latency=X.LatencyModel(20_000, 15_000, 20_000)))
    fast = X.LatencyModel(sniper_ns, sniper_ns - 1_000, sniper_ns)
    sim.add_agent(Sniper(sig), X.SessionSpec(firm="ARB", latency=fast))
    if p.budget_orders_per_s:
        _limit_session(sim, "HF1", p.budget_orders_per_s, p.budget_burst)
    res = sim.run(until_ns=end)
    ctx = res.agents["quoter"]
    arb = res.agents["sniper"]
    f = np.array([(x[0], x[3], x[4], x[5]) for x in ctx.fills], float).reshape(-1, 4)
    vt, v = np.asarray(res.truth["v_t"]), np.asarray(res.truth["v"], float)
    vol = float(f[:, 3].sum()) if len(f) else 0.0
    if len(f):
        i = np.searchsorted(vt, f[:, 0] + 5 * X.SEC, side="right") - 1
        edge = float((f[:, 1] * (v[i] - f[:, 2]) * f[:, 3]).sum() / vol / p.tick)
    else:
        edge = 0.0
    pos = int((f[:, 1] * f[:, 3]).sum()) if len(f) else 0
    gross = float(-(f[:, 1] * f[:, 3] * f[:, 2]).sum() + pos * v[-1]) / p.tick if len(f) else 0.0
    fees_ticks = ctx.fees * 10_000 / p.tick
    arb_px = {(round(x[0]), x[4]) for x in arb.fills}
    picked = float(sum(r[3] for r in f if (round(r[0]), r[2]) in arb_px))
    takes = float(sum(x[5] for x in ctx.fills if x[6] == "R"))
    return {"fills": len(f), "volume": vol, "edge": edge, "picked": picked, "takes": takes, "messages": quoter.messages,
            "orders": quoter.orders, "rejects": quoter.rejects, "fees_ticks": fees_ticks,
            "pnl_ticks": gross - fees_ticks, "position": pos}
