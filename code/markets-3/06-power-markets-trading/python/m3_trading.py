"""Chapter 6 of Book 3: trading power. Capture prices of German solar and wind, a battery's
day-ahead arbitrage with perfect foresight, and a wind farm's day through intraday and imbalance.
Data: Bundesnetzagentur | SMARD.de, CC BY 4.0 (hourly, 2024-2025); battery and wind-farm
parameters are illustrative."""
import csv
import datetime as dt
import math
import pathlib
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/balancing"))
from firm_balancing import capture_price, day_settlement

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-3"
POWER_MW, ENERGY_MWH, RTE = 100.0, 200.0, 0.88       # battery (illustrative)


def berlin(t: dt.datetime) -> dt.datetime:
    def last_sunday(y: int, m: int) -> dt.datetime:
        d = dt.datetime(y, m + 1, 1) - dt.timedelta(days=1)
        return d - dt.timedelta(days=(d.weekday() + 1) % 7) + dt.timedelta(hours=1)
    return t + dt.timedelta(hours=2 if last_sunday(t.year, 3) <= t < last_sunday(t.year, 10) else 1)


def load() -> list[tuple[dt.datetime, float, float, float]]:
    """(local hour start, price, solar MWh, onshore wind MWh)."""
    with open(DATA / "de_power_hourly_2024_2025.csv") as fh:
        return [(berlin(dt.datetime.fromisoformat(r["utc"])), float(r["price"]), float(r["solar"]),
                 float(r["wind_on"])) for r in csv.DictReader(fh)]


def capture(year: int) -> dict[str, float]:
    rows = [r for r in load() if r[0].year == year]
    base = sum(r[1] for r in rows) / len(rows)
    sol = capture_price([r[1] for r in rows], [r[2] for r in rows])
    wind = capture_price([r[1] for r in rows], [r[3] for r in rows])
    return {"base": base, "solar": sol, "wind": wind, "solar_rate": sol / base, "wind_rate": wind / base}


def battery_plan(prices: list[float], max_cycles: int = 1) -> tuple[float, list[int]]:
    """Best day-ahead arbitrage of the battery over one day with perfect foresight, and its actions
    (+1 charge, -1 discharge, 0 idle, one per hour). States of charge 0, 100, 200 MWh; one hour at
    full power moves 100 MWh; start and end empty; at most `max_cycles` full cycles (two charging
    hours each). Charging draws 100/sqrt(RTE) MWh; discharging delivers 100*sqrt(RTE) MWh."""
    eta, step = math.sqrt(RTE), POWER_MW
    levels = int(ENERGY_MWH // step)
    best: dict[tuple[int, int], tuple[float, list[int]]] = {(0, 0): (0.0, [])}
    for p in prices:
        nxt: dict[tuple[int, int], tuple[float, list[int]]] = {}
        for (s, c), (v, path) in best.items():
            for a in (-1, 0, 1):
                s2, c2 = s + a, c + (a == 1)
                if not 0 <= s2 <= levels or c2 > 2 * max_cycles:
                    continue
                cash = -p * step / eta if a == 1 else p * step * eta if a == -1 else 0.0
                if (s2, c2) not in nxt or v + cash > nxt[(s2, c2)][0]:
                    nxt[(s2, c2)] = (v + cash, path + [a])
        best = nxt
    return max((vp for (s, _), vp in best.items() if s == 0), key=lambda vp: vp[0])


def battery_day(prices: list[float], max_cycles: int = 1) -> float:
    return battery_plan(prices, max_cycles)[0]


def battery_year(year: int, max_cycles: int = 1) -> dict[str, float]:
    days: dict[dt.date, list[float]] = defaultdict(list)
    for t, p, _, _ in load():
        if t.year == year:
            days[t.date()].append(p)
    total = sum(battery_day(v, max_cycles) for v in days.values())
    return {"days": len(days), "eur": total, "eur_per_mw": total / POWER_MW}


def wind_day() -> dict[str, float]:
    """The tutorial's wind farm over four hours: sold day-ahead, one intraday correction, metered
    output below the corrected schedule in the last hour (illustrative)."""
    sales = {1: (80.0, 62.0), 2: (90.0, 58.0), 3: (100.0, 55.0), 4: (100.0, 57.0)}
    intraday = {4: (-30.0, 170.0)}                        # bought back 30 MWh at 170 after a forecast drop
    for m, (q, p) in intraday.items():
        q0, p0 = sales[m]
        sales[m] = (q0 + q, (q0 * p0 + q * p) / (q0 + q))
    metered = {1: 82.0, 2: 88.0, 3: 101.0, 4: 55.0}
    imb_price = {1: 60.0, 2: 75.0, 3: 50.0, 4: 240.0}
    return day_settlement(sales, metered, imb_price)
