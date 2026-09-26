"""One Quant Book 10, chapter 1: the limit order book as data and as a queueing system.

    event_mix(tape)                 message shares, rates, order lifetimes and outcomes of a firm.tape session
    best_survival(tape)             how long the best bid and ask prices last
    depth_profile(tape, levels)     mean displayed depth k ticks from the best, sampled once a second
    tree_vs_array(tape)             the two book structures of firm.lob agree message by message
    fill_probability(n, mu, theta, nu)   the chapter's proposition: an order behind n unit orders
    queue_mc(n, mu, theta, nu, paths, seed)   Monte Carlo of the same queue
    zi_market(...)                  a zero-intelligence market on firm.lob (unit orders); returns the empirical fill
                                    probability of orders joining the back of the best bid, by orders ahead,
                                    the time-averaged spread and depth
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("lob", "tape"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_lob import ArrayBook, LimitOrderBook, MessageBook, Order, apply_tape, l2_lines  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402


@functools.lru_cache(maxsize=4)
def session(seconds: float = 3600.0, seed: int = 7):
    return simulate(TapeConfig(seconds=seconds, seed=seed))


def event_mix(tape) -> dict:
    """Shares of adds, cancels and executions; messages and trades per second; what happened to each order."""
    m = tape.msgs
    kinds = m["kind"]
    n = len(m)
    secs = float(tape.cfg.seconds)
    added: dict[int, float] = {}
    left: dict[int, int] = {}
    executed: dict[int, bool] = {}
    life = []
    for row in m:
        oid = int(row["oid"])
        if row["kind"] == b"A":
            added[oid], left[oid], executed[oid] = float(row["t"]), int(row["qty"]), False
            continue
        left[oid] -= int(row["qty"])
        if row["kind"] == b"E":
            executed[oid] = True
        if left[oid] == 0:
            life.append((float(row["t"]) - added[oid], executed[oid]))
    life_t = np.array([x for x, _ in life])
    ex = np.array([e for _, e in life])
    return {"messages": n, "per_second": n / secs, "add": float(np.mean(kinds == b"A")),
            "cancel": float(np.mean(kinds == b"X")), "execute": float(np.mean(kinds == b"E")),
            "trades_per_second": len(tape.trades) / secs, "orders": len(added), "removed": len(life),
            "share_executed": float(ex.mean()), "median_life": float(np.median(life_t)),
            "median_life_executed": float(np.median(life_t[ex])),
            "median_life_cancelled": float(np.median(life_t[~ex])),
            "messages_per_trade": n / len(tape.trades)}


def best_survival(tape) -> dict:
    """Median and mean time (seconds) a best bid or best ask price stays the best."""
    top = tape.top[tape.n_open:]
    out = {}
    for side, col in (("bid", "bid"), ("ask", "ask")):
        px, t = top[col], top["t"]
        change = np.flatnonzero(np.diff(px) != 0) + 1
        starts = np.concatenate([[0], change])
        ends = np.concatenate([change, [len(px) - 1]])
        dur = t[ends] - t[starts]
        dur = dur[dur > 0]
        out[side] = (float(np.median(dur)), float(dur.mean()), len(dur))
    return out


def depth_profile(tape, levels: int = 10, every: float = 1.0) -> np.ndarray:
    """Mean displayed shares at k = 0..levels-1 ticks from the best, per side (rows: bids, asks), sampled on a grid."""
    book = MessageBook()
    acc = np.zeros((2, levels))
    samples = 0
    nxt = every
    for row in tape.msgs:
        t = float(row["t"])
        while t >= nxt:
            b, _, a, _ = book.top()
            if b is not None and a is not None:
                for s, (side, best) in enumerate(((1, b), (-1, a))):
                    for k in range(levels):
                        acc[s, k] += book.book.visible_qty(side, best - k if side == 1 else best + k)
                samples += 1
            nxt += every
        if row["kind"] == b"A":
            book.apply("A", int(row["oid"]), int(row["side"]), int(row["price"]), int(row["qty"]))
        else:
            book.apply("X", int(row["oid"]), qty=int(row["qty"]))
    return acc / samples


def tree_vs_array(tape) -> tuple[int, int]:
    """Replay into both structures; count level-2 snapshots compared and mismatches."""
    tree, arr = MessageBook(), ArrayBook(int(tape.msgs["price"].min()) - 10, int(tape.msgs["price"].max()) + 10)
    checked = bad = 0
    for i, (a, b) in enumerate(zip(apply_tape(tree, tape.msgs), apply_tape(arr, tape.msgs), strict=True)):
        if i % 10 == 0:
            checked += 1
            bad += l2_lines(a, 10) != l2_lines(b, 10)
    return checked, bad


def fill_probability(n: int, mu: float, theta: float, nu: float) -> float:
    """Probability that an order behind n unit orders fills before it is cancelled. Market orders arrive at rate mu
    and take one unit from the front; each order ahead cancels at rate theta; ours cancels at rate nu."""
    p = mu / (mu + nu)
    for k in range(1, n + 1):
        p *= (mu + k * theta) / (mu + k * theta + nu)
    return p


def expected_wait(n: int, mu: float, theta: float) -> float:
    """Expected time to reach the front and fill when our order is never cancelled (nu = 0)."""
    return 1.0 / mu + sum(1.0 / (mu + k * theta) for k in range(1, n + 1))


def queue_mc(n: int, mu: float, theta: float, nu: float, paths: int = 20_000, seed: int = 1) -> float:
    rng = np.random.default_rng(seed)
    filled = 0
    for _ in range(paths):
        k = n
        while True:
            rate = mu + k * theta + nu
            u = rng.random() * rate
            if u < nu:
                break
            if k == 0:
                filled += 1
                break
            k -= 1
    return filled / paths


def zi_market(events: int = 400_000, alpha: float = 0.5, mu: float = 2.0, delta: float = 0.05, width: int = 20,
              improve: bool = True, seed: int = 3, max_ahead: int = 12) -> dict:
    """A zero-intelligence market in the style of Smith, Farmer, Gillemot and Krishnamurthy (2003), unit orders:
    limit orders arrive at rate alpha per price per side over `width` prices; market orders at rate mu per side;
    each resting order cancels at rate delta. With improve=True a buy is placed uniformly in (ask - width, ask - 1]
    (so it may improve the bid, as in the original model); with improve=False uniformly in (bid - width, bid] (it
    joins the best or deeper, never ahead of it). Tracks every bid that joins the back of the best bid queue: the
    orders ahead of it when it arrives, and whether it filled before its own cancellation."""
    rng = np.random.default_rng(seed)
    book = LimitOrderBook()
    ref = 0
    mid0 = 10_000
    for k in range(1, 6):                          # a small opening book
        for side, px in ((1, mid0 - k), (-1, mid0 + k)):
            for _ in range(3):
                ref += 1
                book.add(Order(ref, side, px, 1))
    t, spread_t, depth_t, clock = 0.0, 0.0, 0.0, 0.0
    tracked: dict[int, int] = {}                   # ref -> orders ahead at arrival
    outcome = {k: [0, 0] for k in range(max_ahead + 1)}   # ahead -> [filled, total]
    lam_limit = 2 * alpha * width
    mids: list[float] = []
    for _ in range(events):
        n_orders = len(book.orders)
        total = lam_limit + 2 * mu + delta * n_orders
        dt = rng.exponential(1.0 / total)
        b, a = book.best(1), book.best(-1)
        if b is not None and a is not None:
            spread_t += (a - b) * dt
            depth_t += (sum(o.qty for o in book.level_orders(1, b)) + sum(o.qty for o in book.level_orders(-1, a))) \
                / 2.0 * dt
            clock += dt
        t += dt
        u = rng.random() * total
        if u < lam_limit:                          # a limit order
            side = 1 if u < lam_limit / 2 else -1
            j = int(rng.integers(0, width))
            if improve:
                opp = a if side == 1 else b
                if opp is None and side == 1:
                    opp = b + 1 if b is not None else mid0 + 1
                elif opp is None:
                    opp = a - 1 if a is not None else mid0 - 1
                px = opp - 1 - j if side == 1 else opp + 1 + j
            else:
                own = b if side == 1 else a
                if own is None:
                    own = mid0 - 1 if side == 1 else mid0 + 1
                px = own - j if side == 1 else own + j
            ref += 1
            if side == 1 and b is not None and px == b:
                ahead = len(book.level_orders(1, b))
                if ahead <= max_ahead:
                    tracked[ref] = ahead
            book.add(Order(ref, side, px, 1))
        elif u < lam_limit + 2 * mu:               # a market order takes one unit from the opposite best
            side = -1 if u < lam_limit + mu else 1  # the side it hits
            if b is not None and a is not None:
                mids.append(0.5 * (a + b))
            best = book.best(side)
            if best is None:
                continue
            o = book.level_orders(side, best)[0]
            book.remove(o.ref)
            k = tracked.pop(o.ref, None)
            if k is not None:
                outcome[k][0] += 1
                outcome[k][1] += 1
        else:                                      # a random resting order cancels
            refs = list(book.orders)
            victim = refs[int(rng.integers(len(refs)))]
            book.remove(victim)
            k = tracked.pop(victim, None)
            if k is not None:
                outcome[k][1] += 1
    return {"fill": {k: (f / n if n else math.nan, n) for k, (f, n) in outcome.items()},
            "spread": spread_t / clock, "depth": depth_t / clock, "orders": len(book.orders), "time": t,
            "vol_per_trade": float(np.std(np.diff(mids))) if len(mids) > 2 else math.nan}


def joiners(tape) -> dict:
    """Orders that join the back of the best bid or ask: shares ahead at arrival, and what became of them."""
    book = MessageBook()
    info: dict[int, list] = {}                     # oid -> [ahead, executed shares, qty]
    for i, row in enumerate(tape.msgs):
        oid, kind = int(row["oid"]), row["kind"]
        if kind == b"A":
            side, px = int(row["side"]), int(row["price"])
            b, _, a, _ = book.top()
            if i >= tape.n_open and ((side == 1 and px == b) or (side == -1 and px == a)):
                info[oid] = [book.book.visible_qty(side, px), 0, int(row["qty"])]
            book.apply("A", oid, side, px, int(row["qty"]))
        else:
            if kind == b"E" and oid in info:
                info[oid][1] += int(row["qty"])
            book.apply("X", oid, qty=int(row["qty"]))
    ahead = np.array([v[0] for v in info.values()])
    part = np.array([v[1] > 0 for v in info.values()])
    full = np.array([v[1] == v[2] for v in info.values()])
    return {"orders": len(info), "mean_ahead": float(ahead.mean()), "median_ahead": float(np.median(ahead)),
            "traded": float(part.mean()), "filled": float(full.mean())}
