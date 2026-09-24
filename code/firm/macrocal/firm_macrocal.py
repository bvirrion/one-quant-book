"""Event calendar and rates-screen summary (build of Book 2, Chapter 31).

The calendar merges scheduled releases with central-bank meetings and marks the FOMC blackout: from
the second Saturday before a meeting to the day after it. The screen summarises a curve by its
slopes and fly in basis points, classifies a day's move (bull or bear, steepening or flattening),
compares moves on event days with other days, sizes a DV01-neutral curve trade and measures the
sensitivity of yields to data surprises.
"""
import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    day: dt.date
    time: str                          # local time, e.g. "08:30 ET"
    name: str


def blackout(meeting_start: dt.date, meeting_end: dt.date) -> tuple[dt.date, dt.date]:
    """First and last days of the FOMC blackout for a meeting (ignoring the holiday rule)."""
    back = (meeting_start.weekday() - 5) % 7 or 7          # days back to the Saturday before
    return meeting_start - dt.timedelta(days=back + 7), meeting_end + dt.timedelta(days=1)


def calendar(events: list[Event], meetings: list[tuple[dt.date, dt.date]]) -> list[tuple[Event, bool]]:
    """Events in date order, each flagged if it falls in a blackout."""
    windows = [blackout(a, b) for a, b in meetings]
    return [(e, any(s <= e.day <= t for s, t in windows)) for e in sorted(events, key=lambda e: (e.day, e.time))]


def curve_summary(y2: float, y5: float, y10: float, y30: float) -> dict[str, float]:
    """Slopes and the 2s5s10s fly, in basis points, from yields in percent."""
    return {"2s10s": 100 * (y10 - y2), "5s30s": 100 * (y30 - y5), "2s30s": 100 * (y30 - y2),
            "2s5s10s": 100 * (2 * y5 - y2 - y10)}


def classify(d2: float, d10: float) -> str:
    """Name a move from the changes in the 2- and 10-year yields."""
    level = "bull" if d2 + d10 < 0 else "bear"
    shape = "steepening" if d10 - d2 > 0 else "flattening"
    return f"{level} {shape}"


def event_day_moves(dates: list[str], y: list[float], events: set[str]) -> tuple[float, float, int, int]:
    """Mean absolute daily change (bp) on event days and on other days, and the counts."""
    on, off = [], []
    for k in range(1, len(dates)):
        (on if dates[k] in events else off).append(abs(100 * (y[k] - y[k - 1])))
    return sum(on) / len(on), sum(off) / len(off), len(on), len(off)


def dv01_neutral(dv01_short_leg: float, dv01_long_leg: float, notional_short: float) -> float:
    """Notional of the leg with dv01_long_leg per unit that matches the DV01 of notional_short."""
    return notional_short * dv01_short_leg / dv01_long_leg


def steepener_pnl(dv01: float, d2_bp: float, d10_bp: float) -> float:
    """First-order P&L of a DV01-neutral steepener (long the 2-year, short the 10-year) of the given
    DV01 per leg, for changes in basis points."""
    return dv01 * (d10_bp - d2_bp)


def sensitivity(surprises: list[float], moves: list[float]) -> tuple[float, float]:
    """OLS slope of yield moves on surprises (with intercept) and its standard error."""
    n = len(surprises)
    mx, my = sum(surprises) / n, sum(moves) / n
    sxx = sum((x - mx) ** 2 for x in surprises)
    beta = sum((x - mx) * (y - my) for x, y in zip(surprises, moves, strict=True)) / sxx
    resid = [y - my - beta * (x - mx) for x, y in zip(surprises, moves, strict=True)]
    se = (sum(r * r for r in resid) / (n - 2) / sxx) ** 0.5
    return beta, se
