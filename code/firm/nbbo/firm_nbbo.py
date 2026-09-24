"""firm.nbbo -- consolidated best bid and offer (build of Chapter 9, One Quant Book 1).

Prices are integers (ledger units or ticks). A venue's quote is protected, and enters the
NBBO, only if its size is at least one round lot.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Quote:
    venue: str
    bid: int
    bid_size: int
    ask: int
    ask_size: int


@dataclass(frozen=True)
class Nbbo:
    bid: int
    bid_size: int
    bid_venues: tuple[str, ...]
    ask: int
    ask_size: int
    ask_venues: tuple[str, ...]

    @property
    def locked(self) -> bool:
        return self.bid == self.ask

    @property
    def crossed(self) -> bool:
        return self.bid > self.ask


class NbboBuilder:
    def __init__(self, round_lot: int = 100) -> None:
        self.round_lot = round_lot
        self._quotes: dict[str, Quote] = {}

    def update(self, q: Quote) -> Nbbo | None:
        """Store the venue's latest quote; return the new NBBO if it changed, else None."""
        if q.bid <= 0 or q.ask <= 0 or q.bid_size < 0 or q.ask_size < 0:
            raise ValueError("bad quote")
        before = self.nbbo()
        self._quotes[q.venue] = q
        after = self.nbbo()
        return after if after != before else None

    def nbbo(self) -> Nbbo | None:
        bids = [q for q in self._quotes.values() if q.bid_size >= self.round_lot]
        asks = [q for q in self._quotes.values() if q.ask_size >= self.round_lot]
        if not bids or not asks:
            return None
        bb, ba = max(q.bid for q in bids), min(q.ask for q in asks)
        at_bid = sorted(q.venue for q in bids if q.bid == bb)
        at_ask = sorted(q.venue for q in asks if q.ask == ba)
        return Nbbo(bb, sum(q.bid_size for q in bids if q.bid == bb), tuple(at_bid),
                    ba, sum(q.ask_size for q in asks if q.ask == ba), tuple(at_ask))

    def trades_through(self, side: int, price: int) -> bool:
        """Would a trade at `price` (side +1 = buy) trade through a protected quotation?"""
        n = self.nbbo()
        if n is None:
            return False
        return price > n.ask if side > 0 else price < n.bid
