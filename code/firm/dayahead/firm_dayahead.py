"""Day-ahead auction clearing (build of Book 3, Chapter 5).

One market time unit (MTU) of one bidding zone is cleared from stepwise orders: bids to buy and
offers to sell, each a price limit in EUR/MWh and a quantity in MWh. The clearing maximises
welfare (the value of accepted bids minus the cost of accepted offers) at a uniform price.
Two zones are coupled through an interconnector with a capacity limit; a small set of block
offers (all-or-nothing over several MTUs) is handled by enumeration.
"""
import itertools
from dataclasses import dataclass

BUY, SELL = "buy", "sell"


@dataclass(frozen=True)
class Order:
    side: str
    price: float
    qty: float


@dataclass(frozen=True)
class Result:
    price: float
    volume: float
    welfare: float
    fills: tuple[float, ...] = ()


def clear(orders: list[Order]) -> Result:
    """Uniform-price clearing of one MTU. Bids are served in decreasing price order, offers in
    increasing price order, while the next bid is worth at least the next offer. The price is that
    of the marginal order: the one left partly unfilled (an offer if both are exhausted together).
    `fills` gives the accepted quantity of each order, in input order."""
    idx_b = sorted((k for k, o in enumerate(orders) if o.side == BUY), key=lambda k: -orders[k].price)
    idx_o = sorted((k for k, o in enumerate(orders) if o.side == SELL), key=lambda k: orders[k].price)
    fills = [0.0] * len(orders)
    i = j = 0
    volume = welfare = 0.0
    price = None
    while i < len(idx_b) and j < len(idx_o):
        b, o = orders[idx_b[i]], orders[idx_o[j]]
        if b.price < o.price:
            break
        rb, ro = b.qty - fills[idx_b[i]], o.qty - fills[idx_o[j]]
        q = min(rb, ro)
        fills[idx_b[i]] += q
        fills[idx_o[j]] += q
        volume += q
        welfare += q * (b.price - o.price)
        price = b.price if rb > ro else o.price
        if rb <= ro + 1e-12:
            i += 1
        if ro <= rb + 1e-12:
            j += 1
    if price is None:
        raise ValueError("curves do not cross")
    return Result(price, volume, welfare, tuple(fills))


def couple(zone_a: list[Order], zone_b: list[Order], capacity: float) -> dict[str, float]:
    """Two zones and one interconnector of `capacity` MWh in each direction. Clear both zones as one
    market; if the implied flow fits the line, both zones get the common price. Otherwise the line
    is full: each zone clears alone with the flow as a price-taking export or import, prices split,
    and the congestion rent is the price difference times the flow."""
    joint = clear(zone_a + zone_b)
    fa = joint.fills[:len(zone_a)]
    flow = sum(f for f, o in zip(fa, zone_a, strict=True) if o.side == SELL) - \
        sum(f for f, o in zip(fa, zone_a, strict=True) if o.side == BUY)
    if abs(flow) <= capacity + 1e-9:
        return {"flow": flow, "price_a": joint.price, "price_b": joint.price, "rent": 0.0}
    f = capacity if flow > 0 else -capacity
    pa = clear(zone_a + [Order(BUY, 1e6, f)] if f > 0 else zone_a + [Order(SELL, -1e6, -f)]).price
    pb = clear(zone_b + [Order(SELL, -1e6, f)] if f > 0 else zone_b + [Order(BUY, 1e6, -f)]).price
    return {"flow": f, "price_a": pa, "price_b": pb, "rent": (pb - pa) * f}


@dataclass(frozen=True)
class Block:
    """An all-or-nothing sell offer of `qty` MWh in every MTU of `mtus`, at a limit `price` on the
    average over those MTUs."""
    name: str
    price: float
    qty: float
    mtus: tuple[int, ...]


def clear_with_blocks(hourly: dict[int, list[Order]], blocks: list[Block], floor: float = -1e4) -> dict[str, object]:
    """Enumerate accepted block sets; clear every MTU with the accepted blocks as price-taking supply
    (limit `floor`); keep sets in which every accepted block is fully matched and none is
    paradoxically accepted (average price below its limit); return the set of highest welfare, with
    each accepted block's cost counted at its own limit price."""
    best = None
    for k in range(len(blocks) + 1):
        for acc in itertools.combinations(blocks, k):
            res = {h: clear(orders + [Order(SELL, floor, b.qty) for b in acc if h in b.mtus])
                   for h, orders in hourly.items()}
            full = all(res[h].volume >= sum(b.qty for b in acc if h in b.mtus) - 1e-9 for h in hourly)
            ok = all(sum(res[h].price for h in b.mtus) / len(b.mtus) >= b.price for b in acc)
            if not (full and ok):
                continue
            w = sum(r.welfare for r in res.values()) - sum(b.qty * (b.price - floor) * len(b.mtus) for b in acc)
            if best is None or w > best["welfare"] + 1e-9:
                best = {"accepted": [b.name for b in acc], "prices": {h: r.price for h, r in res.items()}, "welfare": w}
    return best


def marginal_cost(fuel_price: float, efficiency: float, emission_factor: float = 0.0, carbon: float = 0.0,
                  other: float = 0.0) -> float:
    """Short-run marginal cost of a thermal plant in EUR/MWh of electricity: fuel (EUR per MWh of
    fuel) divided by efficiency, plus carbon (t CO2 per MWh of fuel / efficiency, times the
    allowance price), plus other variable costs."""
    return (fuel_price + emission_factor * carbon) / efficiency + other


def spark_spread(power: float, gas: float, efficiency: float) -> float:
    """Power price minus the gas cost of one MWh of electricity."""
    return power - gas / efficiency


def dark_spread(power: float, coal: float, efficiency: float) -> float:
    return power - coal / efficiency
