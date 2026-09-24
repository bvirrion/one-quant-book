"""Physical deal model (build of Book 3, Chapter 1).

A physical cargo is priced by a formula: the average of a published benchmark assessment over a
pricing period (a set of business days, usually counted around the bill-of-lading date) plus a
fixed differential. Days are business-day indices (integers). Prices are in dollars per barrel,
volumes in barrels. Futures lots are 1,000 barrels.
"""
from dataclasses import dataclass

LOT = 1_000


def pricing_days(event_day: int, before: int, after: int, include_event: bool = True) -> list[int]:
    """Business days of a pricing period around an event (the bill-of-lading date): `before` days
    before it, the event day itself if `include_event`, and `after` days after it (e.g. 2-1-2)."""
    days = list(range(event_day - before, event_day)) + ([event_day] if include_event else [])
    return days + list(range(event_day + 1, event_day + after + 1))


def formula_price(assessments: dict[int, float], days: list[int], differential: float) -> float:
    """Average of the assessments over the pricing days, plus the differential."""
    missing = [d for d in days if d not in assessments]
    if missing:
        raise ValueError(f"no assessment on days {missing}")
    return sum(assessments[d] for d in days) / len(days) + differential


@dataclass(frozen=True)
class Leg:
    """One side of a physical deal: +1 bought, -1 sold; priced over `days`."""
    side: int
    volume: float
    days: tuple[int, ...]
    differential: float


def fixed_fraction(leg: Leg, day: int) -> float:
    """Share of the leg's volume whose price is fixed at the close of `day`."""
    return sum(1 for d in leg.days if d <= day) / len(leg.days)


def exposure(legs: list[Leg], day: int) -> float:
    """Flat-price exposure in barrels at the close of `day`: the priced (fixed) part of every leg.
    A floating leg carries no flat-price risk: its price will move with the market."""
    return sum(leg.side * leg.volume * fixed_fraction(leg, day) for leg in legs)


def hedge_trades(legs: list[Leg], lot: int = LOT) -> dict[int, int]:
    """Futures lots to trade at each pricing day's close so that the hedge offsets the exposure:
    as a bought leg prices in, sell; as a sold leg prices in, buy (positive = buy)."""
    trades: dict[int, int] = {}
    for leg in legs:
        per_day = leg.volume / len(leg.days) / lot
        if abs(per_day - round(per_day)) > 1e-9:
            raise ValueError("volume per pricing day is not a whole number of lots")
        for d in leg.days:
            trades[d] = trades.get(d, 0) - leg.side * round(per_day)
    return {d: q for d, q in sorted(trades.items()) if q}


def cost_split(incoterm: str, freight: float, insurance: float) -> dict[str, float]:
    """Who pays freight and insurance to the destination, per barrel, under an Incoterm.
    FOB: the buyer; CIF: the seller (risk passes on board in both)."""
    if incoterm == "FOB":
        return {"seller": 0.0, "buyer": freight + insurance}
    if incoterm == "CIF":
        return {"seller": freight + insurance, "buyer": 0.0}
    raise ValueError(f"unsupported Incoterm {incoterm}")


def netback(delivered_price: float, freight: float, insurance: float = 0.0, loss_rate: float = 0.0,
            other_costs: float = 0.0) -> float:
    """Value at the loading port of a barrel sold delivered: the delivered price times the share that
    arrives, less freight, insurance and other costs per loaded barrel."""
    return delivered_price * (1.0 - loss_rate) - freight - insurance - other_costs


def locked_margin(buy: Leg, sell: Leg, freight: float, insurance: float) -> float:
    """Margin per barrel of a back-to-back cargo hedged at every pricing day, when the benchmark is
    the same on both legs and basis is ignored: sale differential less purchase differential less
    the costs the trader carries."""
    return sell.differential - buy.differential - freight - insurance
