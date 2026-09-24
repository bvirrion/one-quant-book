"""Chapter 10 of Book 3: forward curves, storage and convenience yield, on NYMEX WTI futures
(contracts 1 to 4, EIA, 1985 to April 2024) and the 3-month Treasury bill (FRED DTB3). Contract
identities follow the WTI expiry rule of Chapter 2 (weekend calendar, no exchange holidays)."""
import csv
import datetime as dt
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/crude"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/commcurve"))
from firm_commcurve import decompose, net_convenience_yield, roll_weights
from firm_crude import cl_last_trading_day

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-3"


def load() -> list[tuple[dt.date, tuple[float, float, float, float]]]:
    with open(DATA / "wti_futures_c1_c4_daily.csv") as fh:
        return [(dt.date.fromisoformat(r["date"]), (float(r["c1"]), float(r["c2"]), float(r["c3"]), float(r["c4"])))
                for r in csv.DictReader(fh)]


def tbill() -> dict[dt.date, float]:
    with open(DATA / "tbill3m_daily.csv") as fh:
        return {dt.date.fromisoformat(r["date"]): float(r["rate"]) / 100 for r in csv.DictReader(fh)}


def month_index(y: int, m: int) -> int:
    return 12 * y + m - 1


def front(d: dt.date, _cache: dict[int, dt.date] = {}) -> int:  # noqa: B006
    """Delivery month (as an index) of contract 1 on day d: the first whose last trading day is on or after d."""
    k = month_index(d.year, d.month)
    while True:
        if k not in _cache:
            _cache[k] = cl_last_trading_day(k // 12, k % 12 + 1)
        if _cache[k] >= d:
            return k
        k += 1


def samuelson() -> list[float]:
    """Annualised volatility of daily log changes of contracts 1 to 4, on days with no change of
    contract identity and positive prices."""
    rows = load()
    rets: list[list[float]] = [[], [], [], []]
    for (d0, p0), (d1, p1) in zip(rows, rows[1:], strict=False):
        if front(d0) != front(d1):
            continue
        for i in range(4):
            if p0[i] > 0 and p1[i] > 0:
                rets[i].append(math.log(p1[i] / p0[i]))
    return [float(np.std(r, ddof=1) * math.sqrt(252)) for r in rets]


def convenience_monthly() -> list[tuple[str, float, float]]:
    """(month, share of days in backwardation, mean net convenience yield y_c - u) from contracts 1-2."""
    rows, tb = load(), tbill()
    by: dict[str, list[tuple[float, float]]] = {}
    for d, p in rows:
        if d in tb and p[0] > 0:
            y = net_convenience_yield(p[0], p[1], 1 / 12, tb[d])
            by.setdefault(d.isoformat()[:7], []).append((1.0 if p[0] > p[1] else 0.0, y))
    return [(m, float(np.mean([a for a, _ in v])), float(np.mean([b for _, b in v]))) for m, v in sorted(by.items())]


def index_series() -> list[tuple[dt.date, float, float]]:
    """(date, excess-return index, nearby price): a long position in WTI futures that rolls from the
    contract of month M+1 to that of M+2 over the 5th-9th trading days of each month M."""
    rows = load()
    trading_day = {}
    count: dict[tuple[int, int], int] = {}
    for d, _ in rows:
        count[(d.year, d.month)] = count.get((d.year, d.month), 0) + 1
        trading_day[d] = count[(d.year, d.month)]
    level, out = 1.0, [(rows[0][0], 1.0, rows[0][1][0])]
    for (d0, p0), (d1, p1) in zip(rows, rows[1:], strict=False):
        k0, f0, f1 = month_index(d0.year, d0.month), front(d0), front(d1)
        w = roll_weights(trading_day[d0])
        r = 0.0
        for k, wk in ((k0 + 1, 1 - w), (k0 + 2, w)):
            if wk:
                r += wk * (p1[k - f1] / p0[k - f0] - 1)
        level *= 1 + r
        out.append((d1, level, p1[0]))
    return out


def decomposition() -> dict[str, float]:
    s = index_series()
    tb = tbill()
    days = [d for d, _, _ in s]
    coll = sum(math.log(1 + tb.get(a, 0.0) * (b - a).days / 360) for a, b in zip(days, days[1:], strict=False))
    years = (days[-1] - days[0]).days / 365.25
    parts = decompose(math.log(s[-1][1]), math.log(s[-1][2] / s[0][2]), coll)
    return {k: v / years for k, v in parts.items()} | {"years": years, "start": s[0][2], "end": s[-1][2]}


def roll_cost(index_barrels: float = 50e6, impact_per_mbbl: float = 0.004, days: int = 5) -> dict[str, float]:
    """Front-running the roll (illustrative model). The index sells `index_barrels` of the near contract
    and buys the far one in equal parts over `days` days; each day's trade raises the far-minus-near
    spread by `impact_per_mbbl` dollars per million barrels, and the rise persists until the window
    ends. Trading after its own impact each day, the index pays on average (days + 1) / 2 days of
    impact above the spread before the window: that is the cost of a published, predictable roll."""
    per_day = index_barrels / days / 1e6
    step = impact_per_mbbl * per_day
    cost = step * (days + 1) / 2
    return {"per_day_mbbl": per_day, "step": step, "cost_per_bbl": cost, "cost_usd": cost * index_barrels,
            "cost_year": cost * index_barrels * 12}
