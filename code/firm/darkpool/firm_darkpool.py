"""firm.darkpool -- dark venues: midpoint crossing, conditional orders and leakage (build of One Quant Book 10, ch. 9).

The midpoint crossing itself runs on firm.exchsim's engine (midpoint pegs with a minimum execution quantity: the
`midpoint_dark_pool` preset); this module adds the block venue's conditional layer and the measures of leakage.

A conditional order is a non-binding indication: when two opposite conditionals are both at least the other's
minimum quantity, the venue invites both to firm up within `firm_up_ns`; a participant who firms up sends a firm
order for up to its conditional size; if both firm up the block crosses at the midpoint, otherwise nothing trades
but both sides have learnt that the other exists. The venue scores each participant's firm-up rate.

API (stable):
    ConditionalBook(firm_up_ns=100_000_000)
        .add(owner, side, qty, min_qty, t_ns) -> id      a conditional (side +1 buy, -1 sell)
        .cancel(id)
        .invitations(t_ns) -> [(inv, id_buy, id_sell, qty)]   new matches (an order in one invitation at a time)
        .firm_up(inv, owner, t_ns)                        a response; when both have firmed up, returns
                                                          (buy owner, sell owner, qty) and the block crosses
        .expire(t_ns) -> [inv]                            invitations past the timer; whoever did not respond failed
        .firm_up_rate(owner) -> float
    shortfall_bps(side, fills, arrival_mid)               implementation shortfall of fills (price, qty) in basis points
    pre_completion_drift_bps(side, mid_times, mids, start, end)   the mid's move in the order's direction while it is
                                                          being worked, in basis points of the arrival mid
    counterparty_markout(side, fills, mid_at, h)          mean mark-out per share of the counterparties at horizon h
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class _Cond:
    id: int
    owner: str
    side: int
    qty: int
    min_qty: int
    t_ns: int
    busy: bool = False


@dataclass
class _Inv:
    buy: _Cond
    sell: _Cond
    qty: int
    t_ns: int
    firmed: set = field(default_factory=set)


class ConditionalBook:
    def __init__(self, firm_up_ns: int = 100_000_000):
        self.firm_up_ns = firm_up_ns
        self.orders: dict[int, _Cond] = {}
        self.open: dict[int, _Inv] = {}
        self._next = 1
        self._next_inv = 1
        self.stats: dict[str, list[int]] = {}              # owner -> [invited, firmed]

    def add(self, owner: str, side: int, qty: int, min_qty: int, t_ns: int) -> int:
        oid = self._next
        self._next += 1
        self.orders[oid] = _Cond(oid, owner, side, qty, min_qty, t_ns)
        return oid

    def cancel(self, oid: int) -> None:
        self.orders.pop(oid, None)

    def invitations(self, t_ns: int) -> list[tuple[int, int, int, int]]:
        """Match free conditionals in time priority: (invitation id, buy id, sell id, qty)."""
        out = []
        free = sorted((o for o in self.orders.values() if not o.busy), key=lambda o: o.t_ns)
        buys, sells = [o for o in free if o.side > 0], [o for o in free if o.side < 0]
        for b in buys:
            for s in sells:
                if s.busy or b.busy:
                    continue
                q = min(b.qty, s.qty)
                if q >= b.min_qty and q >= s.min_qty:
                    b.busy = s.busy = True
                    iid = self._next_inv
                    self._next_inv += 1
                    self.open[iid] = _Inv(b, s, q, t_ns)
                    for o in (b, s):
                        self.stats.setdefault(o.owner, [0, 0])[0] += 1
                    out.append((iid, b.id, s.id, q))
                    break
        return out

    def firm_up(self, iid: int, owner: str, t_ns: int):
        inv = self.open.get(iid)
        if inv is None or t_ns > inv.t_ns + self.firm_up_ns:
            return None
        if owner in (inv.buy.owner, inv.sell.owner) and owner not in inv.firmed:
            inv.firmed.add(owner)
            self.stats[owner][1] += 1
        if inv.firmed == {inv.buy.owner, inv.sell.owner}:
            del self.open[iid]
            for o in (inv.buy, inv.sell):
                o.qty -= inv.qty
                o.busy = False
                if o.qty <= 0 or o.qty < o.min_qty:
                    self.orders.pop(o.id, None)
            return inv.buy.owner, inv.sell.owner, inv.qty
        return None

    def expire(self, t_ns: int) -> list[int]:
        gone = [i for i, inv in self.open.items() if t_ns > inv.t_ns + self.firm_up_ns]
        for i in gone:
            inv = self.open.pop(i)
            inv.buy.busy = inv.sell.busy = False
        return gone

    def firm_up_rate(self, owner: str) -> float:
        inv, firmed = self.stats.get(owner, [0, 0])
        return firmed / inv if inv else float("nan")


def shortfall_bps(side: int, fills, arrival_mid: float) -> float:
    f = np.asarray(fills, float).reshape(-1, 2)
    avg = (f[:, 0] * f[:, 1]).sum() / f[:, 1].sum()
    return float(side * (avg - arrival_mid) / arrival_mid * 1e4)


def pre_completion_drift_bps(side: int, mid_times, mids, start: float, end: float) -> float:
    t, m = np.asarray(mid_times, float), np.asarray(mids, float)
    m0 = m[max(np.searchsorted(t, start, side="right") - 1, 0)]
    m1 = m[max(np.searchsorted(t, end, side="right") - 1, 0)]
    return float(side * (m1 - m0) / m0 * 1e4)


def counterparty_markout(side: int, fills, mid_at, h: float) -> float:
    """fills: (t, price, qty) of our side; the counterparty traded -side at price. Per share, in price units."""
    f = np.asarray(fills, float).reshape(-1, 3)
    mo = -side * (np.array([mid_at(t + h) for t in f[:, 0]]) - f[:, 1])
    return float((mo * f[:, 2]).sum() / f[:, 2].sum())
