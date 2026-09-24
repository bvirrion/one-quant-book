"""Chapter 11 of Book 3: weather and freight. Winter heating degree days at Chicago O'Hare
(NOAA GHCN-Daily station USW00094846, public domain), November to March, winters 1990/91 to
2025/26; burn analysis of a degree-day swap and put; a freight agreement's monthly settlement
(illustrative index path)."""
import csv
import datetime as dt
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/degreeday"))
from firm_degreeday import burn, c10_to_f, daily_average, detrend, ffa_settlement, hdd, put_payoff

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-3"
TICK = 20_000.0          # dollars per HDD (illustrative)


def load() -> list[tuple[dt.date, float]]:
    """(date, daily average temperature in F)."""
    with open(DATA / "ohare_tmax_tmin_daily.csv") as fh:
        return [(dt.date.fromisoformat(r["date"]),
                 daily_average(c10_to_f(int(r["tmax_c10"])), c10_to_f(int(r["tmin_c10"]))))
                for r in csv.DictReader(fh)]


def winters() -> list[tuple[int, float, int]]:
    """(year of the January, Nov-Mar HDD total, days observed) for complete winters."""
    tot: dict[int, list[float]] = {}
    for d, t in load():
        if d.month in (11, 12, 1, 2, 3):
            w = d.year + 1 if d.month >= 11 else d.year
            tot.setdefault(w, []).append(hdd(t))
    out = []
    for w, v in sorted(tot.items()):
        expected = (dt.date(w, 4, 1) - dt.date(w - 1, 11, 1)).days
        if len(v) == expected:
            out.append((w, float(sum(v)), len(v)))
    return out


def stats() -> dict[str, float]:
    ws = winters()
    x = [h for _, h, _ in ws]
    yrs = [float(w) for w, _, _ in ws]
    slope = np.polyfit(yrs, x, 1)[0]
    return {"n": len(ws), "first": ws[0][0], "last": ws[-1][0], "mean": float(np.mean(x)),
            "sd": float(np.std(x, ddof=1)),
            "min": min(ws, key=lambda r: r[1])[:2], "max": max(ws, key=lambda r: r[1])[:2], "slope_decade": 10 * slope}


def utility_put(strike_below_mean: float = 0.10, cap: float = 20e6, detrended: bool = True) -> dict[str, float]:
    """A gas utility buys a winter HDD put struck `strike_below_mean` below the burn estimate of the
    mean, $20,000 per HDD, capped. Burn analysis on the last 30 winters, optionally detrended to 2027."""
    ws = winters()[-30:]
    hist = [h for _, h, _ in ws]
    if detrended:
        hist = detrend(hist, [float(w) for w, _, _ in ws], 2027.0)
    fair = float(np.mean(hist))
    k = fair * (1 - strike_below_mean)
    b = burn(hist, lambda x: put_payoff(x, k, TICK, cap))
    return {"fair_strike": fair, "strike": k} | b


def freight_month() -> float:
    """A time-charter FFA bought at $21,000 a day for 30 days, settled on an illustrative month of 25
    index days rising from $21,000 to $25,800 (average $23,400)."""
    path = [21_000 + 200 * i for i in range(25)]         # 25 index days, rising from 21,000 to 25,800
    return ffa_settlement(path, 21_000, 30, 1)


def tce(cargo_t: float = 170_000, rate_per_t: float = 12.0, bunkers: float = 600_000, port: float = 150_000,
        days: float = 45) -> float:
    """Time-charter equivalent of a voyage charter: (freight - voyage costs) / voyage days."""
    return (cargo_t * rate_per_t - bunkers - port) / days
