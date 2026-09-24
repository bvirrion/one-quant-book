"""Margin and liquidation engine (build of Book 3, Chapter 18); P&L conventions from firm.perp.

Tiered maintenance margin; liquidation and bankruptcy prices of isolated linear and inverse positions;
cross-margin health; liquidation of a position into an order book with the surplus or deficit against
the bankruptcy price going to the insurance fund; auto-deleveraging of the most profitable, most
leveraged opposite positions when the fund cannot absorb a deficit.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Tier:
    max_notional: float
    mmr: float                 # maintenance margin rate
    maint_amount: float        # makes the requirement continuous across tiers


def maintenance_margin(notional: float, tiers: list[Tier]) -> float:
    """Notional x rate - amount, with the tier chosen by the position's notional."""
    for t in tiers:
        if notional <= t.max_notional:
            return notional * t.mmr - t.maint_amount
    raise ValueError("position above the largest tier")


def liq_price_linear(size: float, entry: float, margin: float, mmr: float, amount: float = 0.0) -> float:
    """Isolated linear position of `size` units (negative = short): the price at which margin plus P&L
    equals maintenance margin mmr x |size| x price - amount."""
    if size > 0:
        return (size * entry - margin - amount) / (size * (1 - mmr))
    n = -size
    return (margin + n * entry + amount) / (n * (1 + mmr))


def bankruptcy_price_linear(size: float, entry: float, margin: float) -> float:
    """Price at which the isolated position's margin is exactly used up."""
    return entry - margin / size


def liq_price_inverse(contracts: float, entry: float, margin_coin: float, mmr: float) -> float:
    """Isolated inverse position of `contracts` one-dollar contracts (negative = short), margin in coin:
    equity M + N(1/E - 1/P) meets maintenance mmr x |N| / P."""
    if contracts > 0:
        return contracts * (1 + mmr) / (margin_coin + contracts / entry)
    n = -contracts
    if n / entry <= margin_coin:
        return float("inf")                          # fully collateralised short: never liquidated
    return n * (1 - mmr) / (n / entry - margin_coin)


def cross_health(wallet: float, positions: list[tuple[float, float, float]], tiers: list[Tier]) -> float:
    """Equity over maintenance for a cross-margined account; positions are (size, entry, mark)."""
    equity = wallet + sum(q * (m - e) for q, e, m in positions)
    req = sum(maintenance_margin(abs(q) * m, tiers) for q, e, m in positions)
    return equity / req if req > 0 else float("inf")


def sell_into_book(qty: float, bids: list[tuple[float, float]]) -> tuple[float, list[tuple[float, float]]]:
    """Average price of selling qty into bids [(price, size)], and the book left."""
    left, value, book = qty, 0.0, []
    for p, s in bids:
        take = min(left, s)
        value += take * p
        left -= take
        if s > take:
            book.append((p, s - take))
    if left > 1e-12:
        raise ValueError("book exhausted")
    return value / qty, book


@dataclass
class Account:
    name: str
    size: float
    entry: float
    margin: float

    def pnl(self, price: float) -> float:
        return self.size * (price - self.entry)


def adl_rank(accounts: list[Account], price: float) -> list[Account]:
    """Profitable accounts ordered by P&L percentage x effective leverage, highest first."""
    def key(a: Account) -> float:
        equity = a.margin + a.pnl(price)
        return (a.pnl(price) / a.margin) * (abs(a.size) * price / equity)
    return sorted((a for a in accounts if a.pnl(price) > 0), key=key, reverse=True)


def liquidate(acct: Account, bids: list[tuple[float, float]], fund: float, opposite: list[Account], price: float):
    """Close a long `acct`. Returns (fund after, book after, ADL fills [(name, qty)]).
    Sold into the bids, a surplus over the bankruptcy price goes to the fund and a deficit is paid by it.
    If the fund cannot pay the deficit, the position is instead closed against the opposite accounts in
    ADL order at the bankruptcy price, leaving the book and the fund unchanged."""
    bpx = bankruptcy_price_linear(acct.size, acct.entry, acct.margin)
    avg, book = sell_into_book(acct.size, bids)
    result = fund + acct.size * (avg - bpx)
    if result >= 0:
        return result, book, []
    fills, need = [], acct.size
    for a in adl_rank(opposite, price):
        take = min(need, -a.size)
        fills.append((a.name, take))
        need -= take
        if need <= 1e-12:
            break
    if need > 1e-12:
        raise ValueError("not enough opposite positions to deleverage")
    return fund, bids, fills
