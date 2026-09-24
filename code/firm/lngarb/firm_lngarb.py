"""LNG cargo arbitrage and netbacks (build of Book 3, Chapter 4).

Prices in dollars per MMBtu unless the function says otherwise. A US Gulf cargo is bought free on
board at a Henry Hub-linked price (a slope times Henry Hub plus a fixed liquefaction fee); it is
shipped to a regasification terminal, where it sells at the destination's hub price.
"""
from dataclasses import dataclass

MWH_PER_MMBTU = 0.293071
MMBTU_PER_THERM = 0.1


def eur_mwh_to_usd_mmbtu(p_eur_mwh: float, eurusd: float) -> float:
    """A European hub price in EUR/MWh converted to USD/MMBtu at an EURUSD rate (USD per EUR)."""
    return p_eur_mwh * MWH_PER_MMBTU * eurusd


def usd_mmbtu_to_eur_mwh(p: float, eurusd: float) -> float:
    return p / MWH_PER_MMBTU / eurusd


def fob_price(henry_hub: float, slope: float = 1.15, fee: float = 0.0) -> float:
    """Henry Hub-linked FOB price: slope * HH + fixed fee."""
    return slope * henry_hub + fee


@dataclass(frozen=True)
class Route:
    """A voyage: one-way days, charter rate in dollars a day, boil-off share of cargo per laden day,
    and regasification fee at the destination, $/MMBtu."""
    name: str
    days: float
    charter_per_day: float
    boiloff_per_day: float
    regas: float


def shipping_cost(route: Route, cargo_mmbtu: float, cargo_value: float) -> float:
    """Cost per delivered MMBtu of the round trip: charter for twice the one-way days, plus the value
    of the gas boiled off on the laden leg."""
    delivered = cargo_mmbtu * (1.0 - route.boiloff_per_day * route.days)
    charter = 2.0 * route.days * route.charter_per_day
    boiloff = cargo_mmbtu * route.boiloff_per_day * route.days * cargo_value
    return (charter + boiloff) / delivered


def netback(dest_price: float, route: Route, cargo_mmbtu: float, fob_value: float) -> float:
    """Value per MMBtu at the loading terminal of a cargo sold at the destination price."""
    return dest_price - route.regas - shipping_cost(route, cargo_mmbtu, fob_value)


def choose(dest_prices: dict[str, float], routes: dict[str, Route], cargo_mmbtu: float,
           fob_value: float) -> tuple[str, float]:
    """The destination with the highest netback, and that netback."""
    nb = {k: netback(dest_prices[k], routes[k], cargo_mmbtu, fob_value) for k in dest_prices}
    best = max(nb, key=lambda k: (nb[k], k))
    return best, nb[best]


def breakeven_spread(a: Route, b: Route, cargo_mmbtu: float, fob_value: float) -> float:
    """Price of destination b minus price of destination a at which the netbacks are equal."""
    return (shipping_cost(b, cargo_mmbtu, fob_value) + b.regas) - (shipping_cost(a, cargo_mmbtu, fob_value) + a.regas)


def lift(best_netback: float, henry_hub: float, slope: float = 1.15) -> bool:
    """Lift the cargo only if the netback covers the variable (Henry Hub-linked) part of the price;
    the fixed fee is owed whether or not the cargo is lifted."""
    return best_netback >= slope * henry_hub
