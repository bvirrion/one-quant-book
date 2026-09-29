"""Trade capture and booking (One Quant Book 15, chapter 21).

A block of 9,900 shares is bought on Book 10's simulator in child orders that take liquidity; every execution is
captured as a trade in the canonical model, and the block is allocated to three funds (50%, 30%, 20%) at its average
price under three rounding rules. Two hundred OTC swaps booked on Monday go through a week of lifecycle events
(amendments, novations, partial terminations) at seeded times. Three downstream systems -- risk, confirmation and
settlement -- keep their own copies of the trades under realistic copy policies, or follow the event stream; on
Friday at 15:00 their views are compared with the event-sourced trade.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/tradecap", "code/firm/exchsim", "code/firm/tape", "code/firm/feed"):
    sys.path.insert(0, str(ROOT / p))
import firm_exchsim as X  # noqa: E402
import firm_tradecap as T  # noqa: E402
from firm_tape import TapeConfig  # noqa: E402

FIRM_LEI, CCP_LEI = "5493001KJTIIGC8Y1R12", "549300ZCCP000CLEAR07"
DEALERS = [f"5493000DEALER{i:05d}{i % 100:02d}" for i in range(1, 7)]
BLOCK, CHILD = 9_900, 1_000
FUNDS = {"fund A": 0.5, "fund B": 0.3, "fund C": 0.2}
HOUR, DAY = 3600.0, 24 * 3600.0


class BlockBuyer(X.Agent):
    """Buys BLOCK shares in child orders that take the offer, one every 20 seconds."""

    name = "block"

    def on_start(self, ctx):
        ctx.set_timer(20 * X.SEC, "child")

    def on_timer(self, ctx, tag):
        left = BLOCK - ctx.position(1)
        top = ctx.top(1)
        if left > 0 and top[2] is not None:
            ctx.send(X.Order(1, "B", min(CHILD, left), top[2] + 200, tif="I"))
        if left > 0:
            ctx.set_timer(20 * X.SEC, "child")


def block_fills(seed: int = 21, seconds: float = 1800.0) -> list[tuple]:
    o = X.OPEN_NS
    ph = X.Phases(start_ns=o - X.SEC, open_ns=o, close_ns=o + int(seconds) * X.SEC, end_ns=o + int(seconds + 1) * X.SEC)
    sim = X.Simulator(X.ExchangeConfig(phases=ph), seed=1)
    sim.add_background(X.TapeBackground(TapeConfig(seconds=seconds, seed=seed, news_at=None)))
    sim.add_agent(BlockBuyer(), X.SessionSpec("AM1"))
    ctx = sim.run().agents["block"]
    return [(int(f[5]), int(f[4]), int(f[0])) for f in ctx.fills]          # (qty, price 1e-4, ts)


def capture_block(fills) -> tuple[list, T.TradeStore]:
    store = T.TradeStore()
    inst = {"type": "Equity", "id": "SIM1"}
    events = []
    for n, (q, p, ts) in enumerate(fills):
        rep = {"side": 1, "qty": q, "price": p, "ts": ts / 1e9, "date": 0}
        e = T.from_execution(rep, FIRM_LEI, CCP_LEI, "EQ/cash/block", n + 1, inst)
        store.apply(e)
        events.append(e)
    return events, store


def allocations(fills) -> dict:
    out = {}
    for rule in ("largest-remainder", "floor-then-largest", "round-each"):
        alloc, residual = T.allocate([(q, p) for q, p, _ in fills], FUNDS, rule, lot=100)
        total = sum(q for q, _ in alloc.values())
        exact = {f: sum(q for q, _, _ in fills) * w for f, w in FUNDS.items()}
        out[rule] = {"alloc": {f: q for f, (q, _) in alloc.items()}, "residual": residual, "allocated": total,
                     "max_dev": max(abs(alloc[f][0] - exact[f]) for f in FUNDS),
                     "avg": next(iter(alloc.values()))[1]}
    return out


# ------------------------------------------------------------ a week of OTC lifecycle events
def swap_ticket(i: int, rng) -> dict:
    years = int(rng.choice([2, 5, 7, 10]))
    return {"uti": T.uti(FIRM_LEI, 10_000 + i), "trade_id": f"S{i:03d}", "buyer": FIRM_LEI,
            "seller": DEALERS[i % len(DEALERS)], "book": "Rates/swaps", "trade_date": 0, "settle_date": 2,
            "instrument": {"type": "IRSwap", "years": years, "fixed": round(float(0.03 + 0.01 * rng.random()), 4)},
            "quantity": float(rng.choice([10, 25, 50, 100])) * 1e6, "price": 0.0, "ts": 9 * HOUR}


def week(n: int = 200, seed: int = 21) -> tuple[T.TradeStore, list]:
    rng = np.random.default_rng(seed)
    store, events = T.TradeStore(), []
    for i in range(n):
        e = T.from_ticket(swap_ticket(i, rng))
        store.apply(e)
        events.append(e)
    for i in range(n):
        tid = f"S{i:03d}"
        kinds = [k for k, p in (("amend", 0.35), ("novate", 0.15), ("terminate", 0.2)) if rng.random() < p]
        times = np.sort(rng.uniform(10 * HOUR, 4 * DAY + 14 * HOUR, len(kinds)))     # Monday 10:00 to Friday 14:00
        if i == 0:                         # the hook's swap: amended Monday, novated Wednesday, cut Friday
            kinds, times = ["amend", "novate", "terminate"], [11 * HOUR, 2 * DAY + 14 * HOUR, 4 * DAY + 10 * HOUR]
        for kind, t in zip(kinds, times, strict=True):
            state = store.as_of(tid, float(t))
            if kind == "amend":
                data = {"quantity": state["quantity"] * float(rng.choice([0.5, 1.5, 2.0]))}
            elif kind == "novate":
                data = {"side": "seller", "new": DEALERS[(i + 3) % len(DEALERS)]}
            else:
                data = {"quantity": state["quantity"] * 0.4}
            e = T.Event(float(t), kind, tid, data)
            store.apply(e)
            events.append(e)
    return store, sorted(events, key=lambda e: e.ts)


POLICIES = {                  # what each copy-based system copies, and when
    "risk": ("nightly", None),                          # every trade at 18:00, every day
    "confirmation": ("on", {"new", "amend"}),           # a copy on the events it confirms
    "settlement": ("on", {"new", "terminate"}),         # a copy on the events that move cash
}


def downstream(store: T.TradeStore, events: list, at: float = 4 * DAY + 15 * HOUR,
               hours=(18,)) -> dict:
    ids = sorted({e.trade_id for e in events})
    nights = [d * DAY + h * HOUR for d in range(5) for h in hours if d * DAY + h * HOUR <= at]
    views = {}
    for name, (how, kinds) in POLICIES.items():
        v = {}
        for tid in ids:
            if how == "nightly":
                v[tid] = store.as_of(tid, max(nights))
            else:
                copies = [e.ts for e in events
                          if e.trade_id == tid and e.kind in kinds and e.ts <= at]
                v[tid] = store.as_of(tid, max(copies)) if copies else None
        views[name] = v
    golden = {tid: store.as_of(tid, at) for tid in ids}
    wrong = {name: sum(views[name][t] != golden[t] for t in ids) for name in views}
    disagree = sum(len({repr(views[n][t]) for n in views}) > 1 for t in ids)
    return {"wrong": wrong, "disagree": disagree, "golden": golden, "views": views,
            "n": len(ids)}


def hook_trade(store: T.TradeStore, events: list) -> str:
    """A trade with an amendment, a novation and a partial termination in the week, if one exists."""
    kinds = {}
    for e in events:
        kinds.setdefault(e.trade_id, set()).add(e.kind)
    return next(t for t in sorted(kinds) if {"amend", "novate", "terminate"} <= kinds[t])
