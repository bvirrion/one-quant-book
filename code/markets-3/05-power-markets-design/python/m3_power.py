"""Chapter 5 of Book 3: power market design. An illustrative merit order, the clearing of one hour
and of two coupled zones, and German day-ahead prices 2024-2025 (Bundesnetzagentur | SMARD.de,
CC BY 4.0): negative hours by year and by local hour, and the day of 11 May 2025."""
import csv
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/dayahead"))
from firm_dayahead import BUY, SELL, Order, clear, couple, dark_spread, marginal_cost, spark_spread

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-3"
FUEL = {"gas": 35.0, "coal": 12.0, "lignite": 5.0}          # EUR/MWh of fuel (illustrative)
EMIS = {"gas": 0.202, "coal": 0.341, "lignite": 0.364}      # t CO2 per MWh of fuel (illustrative)
CARBON = 70.0                                               # EUR/t (illustrative)
# (name, capacity GW, fuel or None, efficiency or fixed marginal cost)
PLANTS = [("biomass and hydro", 8, None, 10.0), ("lignite", 15, "lignite", 0.37), ("coal", 12, "coal", 0.40),
          ("gas CCGT", 20, "gas", 0.55), ("gas OCGT", 8, "gas", 0.38), ("oil", 3, None, 250.0)]


def stack(renewables_gw: float) -> list[tuple[str, float, float]]:
    """(name, GW, marginal cost EUR/MWh) in merit order, renewables first at zero cost."""
    out = [("wind and solar", renewables_gw, 0.0)]
    for name, cap, fuel, x in PLANTS:
        mc = x if fuel is None else marginal_cost(FUEL[fuel], x, EMIS[fuel], CARBON)
        out.append((name, cap, mc))
    return sorted(out, key=lambda s: s[2])


def hour(demand_gw: float, renewables_gw: float) -> dict[str, object]:
    """Clear one hour: the stack as offers (GWh), price-inelastic demand bid at the price cap."""
    offers = [Order(SELL, mc, gw) for _, gw, mc in stack(renewables_gw)]
    r = clear(offers + [Order(BUY, 4000.0, demand_gw)])
    marginal = [n for n, gw, mc in stack(renewables_gw) if mc == r.price][0]
    return {"price": r.price, "marginal": marginal}


def two_zones(capacity: float) -> dict[str, float]:
    """A windy zone A (40 GW of renewables, 50 GW of demand) and a still zone B (5 GW, 55 GW)."""
    def zone(ren: float, dem: float) -> list[Order]:
        return [Order(SELL, mc, gw) for _, gw, mc in stack(ren)] + [Order(BUY, 4000.0, dem)]
    return couple(zone(40, 50), zone(5, 55), capacity)


def load_de() -> list[tuple[dt.datetime, float, float, float, float, float]]:
    """(UTC hour start, price EUR/MWh, solar, wind onshore, wind offshore, load MWh)."""
    with open(DATA / "de_power_hourly_2024_2025.csv") as fh:
        return [(dt.datetime.fromisoformat(r["utc"]), float(r["price"]), float(r["solar"]), float(r["wind_on"]),
                 float(r["wind_off"]), float(r["load"])) for r in csv.DictReader(fh)]


def to_berlin(t: dt.datetime) -> dt.datetime:
    """UTC to German local time: CEST from 01:00 UTC on the last Sunday of March to 01:00 UTC on
    the last Sunday of October, CET otherwise."""
    def last_sunday(y: int, m: int) -> dt.datetime:
        d = dt.datetime(y, m + 1, 1) - dt.timedelta(days=1)
        return d - dt.timedelta(days=(d.weekday() + 1) % 7) + dt.timedelta(hours=1)
    summer = last_sunday(t.year, 3) <= t < last_sunday(t.year, 10)
    return t + dt.timedelta(hours=2 if summer else 1)


def negative_stats() -> dict[str, object]:
    rows = load_de()
    by_year: dict[int, int] = {}
    by_hour = [0] * 24
    for t, p, *_ in rows:
        if p < 0:
            loc = to_berlin(t)
            by_year[loc.year] = by_year.get(loc.year, 0) + 1
            by_hour[loc.hour] += 1
    low = min(rows, key=lambda r: r[1])
    return {"n": len(rows), "by_year": by_year, "by_hour": by_hour, "low": (to_berlin(low[0]), low[1]),
            "max": max(r[1] for r in rows)}


def day(date: dt.date) -> list[tuple[int, float, float, float]]:
    """(local hour, price, solar GW, load GW) for one German day."""
    out = []
    for t, p, s, _w1, _w2, ld in load_de():
        loc = to_berlin(t)
        if loc.date() == date:
            out.append((loc.hour, p, s / 1000, ld / 1000))
    return out


def spreads_example() -> dict[str, float]:
    """Spark and dark spreads at a power price of EUR 100/MWh, fuels of the stack."""
    return {"spark": spark_spread(100.0, FUEL["gas"], 0.55), "dark": dark_spread(100.0, FUEL["coal"], 0.40)}
