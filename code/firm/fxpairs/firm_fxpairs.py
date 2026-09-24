"""Currency-pair conventions, spot dates and cross rates (build of Book 2, Chapter 14).

A pair BASEQUOTE is quoted as units of the quote currency per unit of the base. Spot settles on
the second business day after the trade (the first for USDCAD), counting days that are business
days in both currencies; a US holiday on the intermediate day does not delay a dollar pair. Which
currency is the base is a convention the firm keeps as data.
"""
import datetime as dt
from dataclasses import dataclass

PRIORITY = ["EUR", "GBP", "AUD", "NZD", "USD", "CAD", "CHF", "NOK", "SEK", "DKK", "JPY"]   # base first
T_PLUS_1 = {"USDCAD"}


@dataclass(frozen=True)
class Quote:
    bid: float
    ask: float

    @property
    def mid(self) -> float:
        return 0.5 * (self.bid + self.ask)


def pair_name(a: str, b: str, priority: list[str] = PRIORITY) -> str:
    """Market name of the pair of currencies a and b: the higher-priority currency is the base."""
    base, quote = sorted((a, b), key=priority.index)
    return base + quote


def pip(pair: str) -> float:
    return 0.01 if pair.endswith("JPY") else 0.0001


def spot_date(trade: dt.date, pair: str, holidays: dict[str, set[dt.date]]) -> dt.date:
    """Value date of a spot trade: T+2 (T+1 for USDCAD) in business days of both currencies."""
    ccys = (pair[:3], pair[3:])

    def open_in(d: dt.date, skip_usd: bool) -> bool:
        return d.weekday() < 5 and all(d not in holidays.get(c, set()) for c in ccys if not (skip_usd and c == "USD"))

    d, lag = trade, 1 if pair in T_PLUS_1 else 2
    for _ in range(lag - 1):                                   # intermediate days
        d += dt.timedelta(days=1)
        while not open_in(d, skip_usd=True):
            d += dt.timedelta(days=1)
    d += dt.timedelta(days=1)
    while not open_in(d, skip_usd=False):                      # the value date itself
        d += dt.timedelta(days=1)
    return d


def cross_via_usd(leg1: tuple[str, Quote], leg2: tuple[str, Quote], target: str) -> Quote:
    """Bid and ask of `target` implied by two dollar pairs, trading each leg on the side that the
    trade forces: the cross's bid sells base and buys quote through the dollar."""
    base, quote = target[:3], target[3:]
    legs = dict((p, q) for p, q in (leg1, leg2))

    def usd_per(ccy: str, side: str) -> float:              # dollars received (bid) or paid (ask) per unit
        if ccy + "USD" in legs:
            q = legs[ccy + "USD"]
            return q.bid if side == "sell" else q.ask
        q = legs["USD" + ccy]
        return 1.0 / (q.ask if side == "sell" else q.bid)

    bid = usd_per(base, "sell") / usd_per(quote, "buy")    # sell base for USD, buy quote with USD
    ask = usd_per(base, "buy") / usd_per(quote, "sell")
    return Quote(bid, ask)


def spread_pips(q: Quote, pair: str) -> float:
    return (q.ask - q.bid) / pip(pair)


def arbitrage(direct: Quote, synthetic: Quote) -> str | None:
    """A direct cross quote that crosses the synthetic one can be arbitraged."""
    if direct.bid > synthetic.ask:
        return "sell direct, buy synthetic"
    if direct.ask < synthetic.bid:
        return "buy direct, sell synthetic"
    return None
