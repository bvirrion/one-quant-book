"""ETF premium monitor (build of Book 1, Chapter 14): indicative value, premium, arbitrage signal.

Prices are integers (ticks or cents). A quote that is too old makes its component stale; when
stale components are worth more than `max_stale_weight` of the basket the monitor refuses to
print a premium.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Basket:
    etf: str
    shares_per_unit: int
    components: tuple[tuple[str, int], ...]      # (symbol, quantity per creation unit)
    cash: int = 0                                # cash component per creation unit, in price units


@dataclass(frozen=True)
class Quote:
    bid: int
    ask: int
    ts: int                                      # time of the last update

    @property
    def mid(self) -> float:
        return 0.5 * (self.bid + self.ask)


@dataclass(frozen=True)
class Costs:
    basket_bp: float
    etf_bp: float
    fee_bp: float
    financing_bp: float

    @property
    def band_bp(self) -> float:
        return self.basket_bp + self.etf_bp + self.fee_bp + self.financing_bp


@dataclass(frozen=True)
class Reading:
    inav: float | None
    premium_bp: float | None
    signal: str                                  # 'create', 'redeem', 'none' or 'unreliable'
    stale: tuple[str, ...]


def indicative_nav(basket: Basket, quotes: dict[str, Quote]) -> float:
    value = basket.cash + sum(q * quotes[sym].mid for sym, q in basket.components)
    return value / basket.shares_per_unit


def premium_bp(price: float, inav: float) -> float:
    return (price / inav - 1.0) * 1e4


def signal(price: float, inav: float, costs: Costs) -> str:
    p = premium_bp(price, inav)
    if p > costs.band_bp:
        return "create"                          # sell the ETF, buy the basket, create
    if p < -costs.band_bp:
        return "redeem"                          # buy the ETF, sell the basket, redeem
    return "none"


def read(basket: Basket, quotes: dict[str, Quote], etf_price: float, costs: Costs, now: int,
         max_age: int = 5, max_stale_weight: float = 0.10) -> Reading:
    stale = tuple(sym for sym, _ in basket.components if now - quotes[sym].ts > max_age)
    inav = indicative_nav(basket, quotes)
    total = inav * basket.shares_per_unit
    stale_value = sum(q * quotes[sym].mid for sym, q in basket.components if sym in stale)
    if stale_value > max_stale_weight * total:
        return Reading(None, None, "unreliable", stale)
    return Reading(inav, premium_bp(etf_price, inav), signal(etf_price, inav, costs), stale)
