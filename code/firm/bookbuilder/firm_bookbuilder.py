"""firm.bookbuilder -- the order-by-order book builder, Python reference (build of One Quant Book 13, chapter 19).

Consumes the normalised events of firm.feedhandler (kind, side, locate, seq, ts, ref, ref2, price, qty) and answers
level 1 and level 2 queries. This reference keeps orders in a dict and levels in a dict per side; the C++20 and Rust
builders keep a dense ladder of price levels around the touch and an open-addressing order map, and must give the same
level 2 after every event (compared by a 64-bit hash of the top five levels on each side).

API (stable):
    Book()                     .apply(event) -> None; .best() -> (bid, bid_qty, ask, ask_qty) or None for an empty side
    .depth(side, n) -> [(price, qty)]      side ord('B') or ord('S'); best first
    .stale                     True from a snapshot's begin (G) until its end (W), and after reset()
    .check() -> list[str]      invariants: level sums equal order sums, no empty level, book not crossed
    l2_hash(book, n=5, h)      FNV-1a of the top n levels of both sides (price u32, qty u64, little-endian)
    recentrings(path_ticks, width) / expected_recentrings(sigma_ticks, width)   the weekend problem's model
"""
import math
import struct

B, S = ord("B"), ord("S")
FNV_OFFSET, FNV_PRIME, MASK = 0xCBF29CE484222325, 0x100000001B3, (1 << 64) - 1


class Book:
    def __init__(self):
        self.orders = {}                      # ref -> [side, price, qty]
        self.levels = {B: {}, S: {}}          # side -> price -> qty
        self.stale = False

    def reset(self):
        self.orders.clear()
        self.levels = {B: {}, S: {}}

    def _add(self, ref, side, price, qty):
        self.orders[ref] = [side, price, qty]
        lv = self.levels[side]
        lv[price] = lv.get(price, 0) + qty

    def _reduce(self, ref, qty):
        o = self.orders.get(ref)
        if o is None:
            return None
        qty = min(qty, o[2])
        lv = self.levels[o[0]]
        lv[o[1]] -= qty
        if lv[o[1]] == 0:
            del lv[o[1]]
        o[2] -= qty
        if o[2] == 0:
            del self.orders[ref]
        return o

    def apply(self, ev):
        kind, side, _loc, _seq, _ts, ref, ref2, price, qty = ev
        k = chr(kind)
        if k == "A":
            self._add(ref, side, price, qty)
        elif k in "EXC":
            self._reduce(ref, qty)
        elif k == "D":
            o = self.orders.get(ref)
            if o:
                self._reduce(ref, o[2])
        elif k == "U":                         # replace: priority lost, new reference, same side
            o = self.orders.get(ref)
            if o:
                s = o[0]
                self._reduce(ref, o[2])
                self._add(ref2, s, price, qty)
        elif k == "G":                         # a snapshot begins: the book is rebuilt from what follows
            self.reset()
            self.stale = True
        elif k == "W":
            self.stale = False

    def best(self):
        bids, asks = self.levels[B], self.levels[S]
        bb = max(bids) if bids else None
        ba = min(asks) if asks else None
        return bb, bids.get(bb, 0), ba, asks.get(ba, 0)

    def depth(self, side, n):
        lv = self.levels[side]
        return [(p, lv[p]) for p in sorted(lv, reverse=(side == B))[:n]]

    def check(self):
        errs = []
        sums = {B: {}, S: {}}
        for side, price, qty in self.orders.values():
            sums[side][price] = sums[side].get(price, 0) + qty
        for side in (B, S):
            if sums[side] != self.levels[side]:
                errs.append(f"side {chr(side)}: levels differ from the orders")
            if any(q <= 0 for q in self.levels[side].values()):
                errs.append(f"side {chr(side)}: empty level")
        bb, _, ba, _ = self.best()
        if bb is not None and ba is not None and bb >= ba:
            errs.append(f"crossed: {bb} >= {ba}")
        return errs


def l2_hash(book, n=5, h=FNV_OFFSET):
    data = b""
    for side in (B, S):
        d = book.depth(side, n)
        d += [(0, 0)] * (n - len(d))
        data += b"".join(struct.pack("<IQ", p, q) for p, q in d)
    for b in data:
        h = ((h ^ b) * FNV_PRIME) & MASK
    return h


def recentrings(path_ticks, width):
    """How often a ladder of `width` ticks, centred on the price, must be recentred when the price follows the path:
    whenever the price leaves the middle half of the ladder, the ladder is moved to centre it again."""
    lo = path_ticks[0] - width // 4
    n = 0
    for p in path_ticks:
        if p < lo or p >= lo + width // 2:
            lo = p - width // 4
            n += 1
    return n


def expected_recentrings(sigma_ticks, width):
    """A Brownian price with daily standard deviation sigma_ticks, recentred when it moves width/4 from the centre:
    the exit time of an interval of half-width a = width/4 has mean a^2 / sigma^2 (in days), hence (sigma/a)^2
    recentrings a day."""
    a = width / 4
    return (sigma_ticks / a) ** 2


def daily_sigma_ticks(price, daily_vol, tick):
    return price * daily_vol / tick


def best_width(sigma_ticks, rebuild_cost, per_tick_cost, widths):
    """The width minimising the day's cost: recentrings times their cost plus a cost per tick of ladder carried
    (memory touched, cache lines)."""
    return min(widths, key=lambda w: expected_recentrings(sigma_ticks, w) * rebuild_cost + w * per_tick_cost)


def quantile_width(sigma_ticks, move_sigmas=5.0):
    """A width that keeps a move of `move_sigmas` daily standard deviations inside the middle half."""
    return math.ceil(4 * move_sigmas * sigma_ticks)
