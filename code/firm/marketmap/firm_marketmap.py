"""Registry of markets and shift planning (build of Book 3, Chapter 29).

Each market carries its size (daily turnover in USD, with the source's measure), its structure, whether it
is centrally cleared, and its hours as intervals in UTC minutes for each weekday (0 = Monday). Queries say
what is open at a moment; the shift planner finds the fewest shifts of a given length, overlapping by a
given margin, that cover the hours the firm must staff, and how many traders each shift needs.
"""
import math
from dataclasses import dataclass, field

DAY = 24 * 60


@dataclass(frozen=True)
class Market:
    name: str
    daily_usd_bn: float | None
    structure: str
    cleared: bool
    hours: dict = field(default_factory=dict)        # weekday -> list of (start_min, end_min) in UTC


def every_day(start_min: int, end_min: int, days=range(7)) -> dict:
    return {d: [(start_min, end_min)] for d in days}


def is_open(m: Market, weekday: int, minute: int) -> bool:
    return any(a <= minute < b for a, b in m.hours.get(weekday, []))


def open_markets(markets: list[Market], weekday: int, minute: int) -> list[str]:
    return [m.name for m in markets if is_open(m, weekday, minute)]


def staffed_minutes(markets: list[Market], weekday: int) -> list[int]:
    """Number of markets open in each minute of the day."""
    return [sum(is_open(m, weekday, t) for m in markets) for t in range(DAY)]


def plan_shifts(markets: list[Market], weekday: int, length_h: float, overlap_h: float,
                start_min: int = 0) -> list[tuple]:
    """Fewest shifts of `length_h` hours, each starting `length_h - overlap_h` after the previous, that cover every
    minute at which some market is open; returns (start, end, traders) with traders = the most markets open at once
    during the shift (one trader per open market)."""
    need = staffed_minutes(markets, weekday)
    covered = [t for t in range(DAY) if need[t] > 0]
    if not covered:
        return []
    step, length = int((length_h - overlap_h) * 60), int(length_h * 60)
    if len(covered) == DAY:                                   # round the clock: cover the cycle
        first, n = start_min, math.ceil(DAY / step)
    else:
        first, span = covered[0], covered[-1] - covered[0] + 1
        n = 1 if span <= length else 1 + math.ceil((span - length) / step)
    out = []
    for k in range(n):
        s = first + k * step
        e = s + length
        traders = max(need[t % DAY] for t in range(s, e))
        out.append((s % DAY, e % DAY, traders))
    return out
