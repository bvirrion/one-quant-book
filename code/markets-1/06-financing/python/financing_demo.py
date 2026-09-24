"""Leverage, margin and the cost of financing a book (Chapter 6). Rates illustrative."""
from dataclasses import dataclass


def return_on_equity(asset_return: float, leverage: float, funding_rate: float) -> float:
    """r_E = L r_A - (L - 1) r_f for assets = L x equity, the rest borrowed at r_f."""
    return leverage * asset_return - (leverage - 1.0) * funding_rate


def wipeout_drop(leverage: float) -> float:
    """Fall of the assets that brings the equity to zero."""
    return 1.0 / leverage


def max_leverage(haircut: float) -> float:
    """Repo at haircut h finances 1 - h of each purchase: assets / equity <= 1 / h."""
    return 1.0 / haircut


def margin_call_price(p0: float, initial: float, maintenance: float) -> float:
    """Price at which equity / value of a long bought at p0 falls to the maintenance ratio."""
    loan = p0 * (1.0 - initial)
    return loan / (1.0 - maintenance)


def forced_sale(assets: float, leverage: float, drop: float) -> float:
    """Assets to sell after a fall `drop` to restore the leverage ratio: (L - 1) x drop x A."""
    return (leverage - 1.0) * drop * assets


def spiral(leverage: float, shock: float, impact_per_unit_sold: float, rounds: int = 12):
    """Iterate: price falls -> forced sale -> sale moves the price -> further fall.

    Assets start at 1. `impact_per_unit_sold` is the fractional price fall caused by
    selling one unit of assets. Returns the cumulative price fall after each round.
    """
    assets, equity, price, out = 1.0, 1.0 / leverage, 1.0, []
    drop = shock
    for _ in range(rounds):
        price *= 1.0 - drop
        loss = assets * drop
        assets, equity = assets - loss, equity - loss
        if equity <= 0:
            out.append(1.0 - price)
            break
        sale = max(0.0, assets - leverage * equity)
        assets -= sale
        drop = impact_per_unit_sold * sale
        out.append(1.0 - price)
    return out


@dataclass(frozen=True)
class Book:
    long_value: float
    short_value: float
    equity: float


def annual_cost_cash(b: Book, rate: float, debit_spread: float, borrow_fee: float,
                     short_credit_spread: float) -> float:
    """Cash prime brokerage: pay (r + spread) on the debit, receive (r - credit spread - fee) on shorts."""
    debit = max(0.0, b.long_value - b.equity)
    return debit * (rate + debit_spread) - b.short_value * (rate - short_credit_spread - borrow_fee)


def annual_cost_swap(b: Book, rate: float, long_spread: float, short_spread: float,
                     borrow_fee: float) -> float:
    """Swaps: pay (r + spread) on the long notional, receive (r - spread - fee) on the short
    notional; the fund's equity, posted as margin or not, earns r."""
    return (b.long_value * (rate + long_spread) - b.short_value * (rate - short_spread - borrow_fee)
            - b.equity * rate)
