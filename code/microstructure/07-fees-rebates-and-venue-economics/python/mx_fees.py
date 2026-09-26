"""One Quant Book 10, chapter 7: fees, rebates and the choice of venue, on two venues of the exchange simulator.

    two_venues(share_mt, fees, seconds, seed)   a small reactive market (Flow) on a maker-taker venue (MT) and an
                                                inverted venue (INV): each limit order goes to MT with probability
                                                share_mt; every market order is routed by fee-adjusted price
                                                (firm.venuefees). Returns per-venue statistics (cents per share)
    by_awareness(awares, share_mt, seconds, seeds)   two_venues for several shares of fee-aware takers, averaged over
                                                seeds, with standard errors
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("exchsim", "lob", "venuefees"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_exchsim import SEC, ExchangeConfig, FeeSchedule  # noqa: E402
from firm_exchsim_codec import NT  # noqa: E402
from firm_exchsim_engine import Engine  # noqa: E402
from firm_venuefees import route_take  # noqa: E402

C, IN = NT["ctl"], NT["in"]
OPEN = 34_200 * SEC
PX = 100                                   # one tape tick (one cent) in 1/10,000 units
CBOE_2026 = {"MT": (-0.0016, 0.0030), "INV": (0.0020, -0.0002)}   # (make, take) per share, dat box of the chapter


class _Venue:
    def __init__(self, name: str, make: float, take: float):
        self.name, self.make, self.take = name, make, take
        self.e = Engine(ExchangeConfig(venue=name, fees=FeeSchedule(make, take)).engine_config())
        for m in (C["S"]("O"), C["L"](1, 1, "N"), C["L"](2, 2, "N"), C["P"](0, "T", "OPEN")):
            self.e.process(OPEN - SEC, 0, m)
        self.book = self.e.book(1)

    def best(self, side: int):
        p = self.book.best(side)
        return (p, self.book.visible_qty(side, p)) if p is not None else (None, 0)


@dataclass(frozen=True)
class Flow:
    """A small reactive market in ticks: an efficient price P* that jumps one tick at rate v_rate; limit orders at the
    best or a few ticks behind, and inside a spread wider than one tick on the side P* favours; cancellations at a
    constant rate per order, and at once with probability `stale` when P* jumps through an order's price; noise market
    orders; informed market orders at a rate proportional to the distance between P* and the mid."""
    lo_rate: float = 1.5                   # limit orders per second per side
    at_best: float = 0.5                   # share of them joining the best; the rest 1, 2, ... ticks behind
    behind: float = 0.5                    # geometric parameter of the distance behind
    improve: float = 2.0                   # per second into a spread wider than one tick
    lo_lots: float = 2.0
    cancel: float = 0.05                   # per resting order per second
    stale: float = 0.5
    noise: float = 0.6                     # noise market orders per second
    mo_lots: float = 1.5
    informed: float = 0.1                  # informed market orders per second per tick of |P* - mid|
    v_rate: float = 0.12
    aware: float = 1.0                     # share of market orders routed by fee-adjusted price; the others go to
                                           # the venue with the most shares displayed at the best price first
    start: int = 10_000                    # ticks (100.00)


def _lots(rng, mean: float) -> int:
    return 100 * int(rng.geometric(1.0 / mean))


def two_venues(share_mt: float = 0.5, fees=None, seconds: float = 3600.0, seed: int = 7, h: float = 30.0,
               warm: float = 60.0, flow: Flow | None = None) -> dict:
    fees = fees or CBOE_2026
    f = flow or Flow()
    ven = {k: _Venue(k, *v) for k, v in fees.items()}
    rng = np.random.default_rng(seed)
    entry: dict[int, tuple] = {}                    # cl -> (venue, t, side, price, qty, ahead)
    fills: list[tuple] = []                         # (cl, venue, t, qty, price)
    takes: list[tuple] = []                         # (venue, t, qty, price, informed)
    tops: list[tuple] = []
    live: list[int] = []
    pos: dict[int, int] = {}
    info: dict[int, tuple] = {}                     # cl -> (venue, side, price in ticks)
    state = {"cl": 0, "informed": False}

    def run(v: _Venue, t: float, sess: int, msg):
        _, reps = v.e.process(OPEN + int(round(t * SEC)), sess, msg)
        for sid, r in reps:
            if type(r).__name__ != "Out_E":
                continue
            if sid == 1:
                fills.append((r.cl_ord_id, v.name, t, r.qty, r.price))
                if r.leaves == 0:
                    _drop(r.cl_ord_id)
            else:
                takes.append((v.name, t, r.qty, r.price, state["informed"]))

    def _drop(cl: int):
        i = pos.pop(cl, None)
        if i is None:
            return
        last = live.pop()
        if last != cl:
            live[i], pos[last] = last, i
        info.pop(cl, None)

    def nbbo():
        b = [v.book.best(1) for v in ven.values()]
        a = [v.book.best(-1) for v in ven.values()]
        b = max((x for x in b if x is not None), default=None)
        a = min((x for x in a if x is not None), default=None)
        return (None if b is None else b // PX), (None if a is None else a // PX)

    def limit(t: float, side: int, px: int):
        name = "MT" if rng.random() < share_mt else "INV"
        v = ven[name]
        state["cl"] += 1
        cl, q = state["cl"], _lots(rng, f.lo_lots)
        ahead = sum(o.qty for o in v.book.level_orders(side, px * PX))
        entry[cl] = (name, t, side, px, q, ahead)
        info[cl] = (name, side, px)
        pos[cl] = len(live)
        live.append(cl)
        run(v, t, 1, IN["O"](cl, 1, "B" if side == 1 else "S", q, px * PX, "D", "Y", "N", 0, 0, 0, "N", 0))

    def market(t: float, side: int, qty: int, informed: bool):
        state["informed"] = informed
        quotes = [(v.name, p, v.book.visible_qty(-side, p), v.take * 10_000)
                  for v in ven.values() for p in v.book.prices(-side)[:5]]
        if rng.random() >= f.aware:          # fee-blind: the larger displayed size first
            quotes = [(n, p, q, -1e-9 * q) for n, p, q, _ in quotes]
        for name, p, qq in route_take(quotes, side, qty):
            state["cl"] += 1
            o = IN["O"](state["cl"], 1, "BS"[side < 0], qq, p, "I", "Y", "N", 0, 0, 0, "N", 0)
            run(ven[name], t, 2, o)

    vstar = float(f.start)
    for k in range(5):                               # an opening book: five lots a level, split at random
        limit(0.0, 1, f.start - 1 - k)
        limit(0.0, -1, f.start + 1 + k)
    t = 0.0
    while True:
        b, a = nbbo()
        mid = 0.5 * (b + a) if b is not None and a is not None else vstar
        gap = vstar - mid
        rates = np.array([f.lo_rate, f.lo_rate, f.improve if (b and a and a - b > 1) else 0.0,
                          f.cancel * len(live), f.noise, f.informed * abs(gap), f.v_rate])
        t += rng.exponential(1.0 / rates.sum())
        if t >= seconds:
            break
        ev = int(rng.choice(7, p=rates / rates.sum()))
        if ev in (0, 1):
            side = 1 if ev == 0 else -1
            best = b if side == 1 else a
            if best is None:
                best = int(np.floor(vstar)) if side == 1 else int(np.ceil(vstar))
            k = 0 if rng.random() < f.at_best else int(rng.geometric(f.behind))
            px = best - side * k
            if side == 1 and a is not None:
                px = min(px, a - 1)
            if side == -1 and b is not None:
                px = max(px, b + 1)
            limit(t, side, px)
        elif ev == 2:
            side = 1 if gap > 0 else -1
            limit(t, side, b + 1 if side == 1 else a - 1)
        elif ev == 3:
            cl = live[int(rng.integers(len(live)))]
            name = info[cl][0]
            run(ven[name], t, 1, IN["X"](cl, 0))
            _drop(cl)
        elif ev == 4:
            market(t, 1 if rng.random() < 0.5 else -1, _lots(rng, f.mo_lots), False)
        elif ev == 5:
            market(t, 1 if gap > 0 else -1, _lots(rng, f.mo_lots), True)
        else:
            vstar += 1 if rng.random() < 0.5 else -1
            through = [cl for cl in live if (info[cl][1] == 1 and info[cl][2] > vstar)
                       or (info[cl][1] == -1 and info[cl][2] < vstar)]
            for cl in through:
                if rng.random() < f.stale:
                    run(ven[info[cl][0]], t, 1, IN["X"](cl, 0))
                    _drop(cl)
        (bm, bi), (am, ai) = (ven["MT"].book.best(1), ven["INV"].book.best(1)), (ven["MT"].book.best(-1),
                                                                               ven["INV"].book.best(-1))
        bb = max((x for x in (bm, bi) if x is not None), default=0)
        aa = min((x for x in (am, ai) if x is not None), default=10**9)
        qm = ven["MT"].book.visible_qty(1, bb) + ven["MT"].book.visible_qty(-1, aa)
        qi = ven["INV"].book.visible_qty(1, bb) + ven["INV"].book.visible_qty(-1, aa)
        tops.append((t, bb, aa, qm / 2, qi / 2, vstar))
    return _stats(entry, fills, takes, np.array(tops, dtype=float), fees, seconds, h, warm)


def _stats(entry, fills, takes, tops, fees, seconds, h, warm) -> dict:
    ok = (tops[:, 1] > 0) & (tops[:, 2] < 10**9)
    tt, mid = tops[ok, 0], 0.5 * (tops[ok, 1] + tops[ok, 2]) / PX            # mid in cents
    dt = np.diff(np.concatenate([tops[:, 0], [seconds]]))
    win = (tops[:, 0] >= warm) & ok

    def mid_at(t):
        return mid[max(np.searchsorted(tt, t, side="right") - 1, 0)]

    out = {}
    for k, name in ((3, "MT"), (4, "INV")):
        make, take = fees[name]
        ents = {o: e for o, e in entry.items() if e[0] == name and warm <= e[1] < seconds - h - 1}
        got: dict[int, list] = {}
        for oid, _v, t, q, p in fills:
            if oid in ents:
                got.setdefault(oid, []).append((t, q, p / PX))
        posted = sum(e[4] for e in ents.values())
        filled = sum(q for fl in got.values() for _, q, _ in fl)
        cap = adv = 0.0
        for oid, fl in got.items():
            s = ents[oid][2]
            for t, q, p in fl:
                m0 = mid_at(t - 1e-9)
                cap += q * s * (m0 - p)
                adv += q * s * (mid_at(t + h) - m0)
        waits = [fl[0][0] - ents[o][1] for o, fl in got.items()]
        net = (cap + adv) / filled if filled else float("nan")          # adv holds the mark-out: side (m_h - m_0)
        out[name] = {"orders": len(ents), "posted": posted, "fill_share": filled / posted,
                     "orders_filled": len(got) / len(ents), "t_fill": float(np.median(waits)),
                     "capture": cap / filled, "adverse": -adv / filled, "net": net, "make_cents": 100 * make,
                     "value": (filled / posted) * (net - 100 * make),
                     "queue": float((tops[win, k] * dt[win]).sum() / dt[win].sum()),
                     "take_volume": sum(q for v, t, q, _p, _i in takes if v == name and t >= warm)}
    tot = out["MT"]["take_volume"] + out["INV"]["take_volume"]
    for name in out:
        out[name]["volume_share"] = out[name]["take_volume"] / tot
    return out


@functools.cache
def by_awareness(awares=(0.0, 0.5, 1.0), share_mt: float = 0.5, seconds: float = 7200.0, seeds=(7, 8, 9)) -> dict:
    """two_venues for several shares of fee-aware takers: per venue, the mean of each statistic over the seeds and
    the standard error of the fill share and of the value per posted share."""
    out = {}
    for a in awares:
        runs = [two_venues(share_mt, None, seconds, s, flow=Flow(aware=a)) for s in seeds]
        out[a] = {}
        for v in ("MT", "INV"):
            st = {k: float(np.mean([r[v][k] for r in runs])) for k in runs[0][v]}
            for k in ("fill_share", "value", "adverse"):
                st[k + "_se"] = float(np.std([r[v][k] for r in runs], ddof=1) / np.sqrt(len(runs)))
            out[a][v] = st
        out[a]["diff_se"] = float(np.std([r["MT"]["value"] - r["INV"]["value"] for r in runs], ddof=1)
                                  / np.sqrt(len(runs)))
    return out
