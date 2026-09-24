"""Positioning reports and daily limits (build of Book 3, Chapter 9).

COT rows are dicts of weekly positions (contracts) by trader category. Limits follow the CBOT
variable-limit rule for grains: 7% of an average settlement price, rounded to the nearest 5 cents
(minimum 20 cents), with an expanded limit of 1.5 times the limit, rounded up to 5 cents. Prices in
dollars per bushel.
"""
import math
from dataclasses import dataclass


def net(row: dict[str, int], category: str) -> int:
    return row[f"{category}_long"] - row[f"{category}_short"]


def net_share(row: dict[str, int], category: str) -> float:
    """Net position of a category as a share of total open interest."""
    return net(row, category) / row["open_interest"]


def zscore(values: list[float], window: int) -> list[float | None]:
    """Trailing z-score of each value against the previous `window` values (None until enough)."""
    out: list[float | None] = []
    for i, v in enumerate(values):
        past = values[max(0, i - window):i]
        if len(past) < window:
            out.append(None)
            continue
        m = sum(past) / window
        sd = math.sqrt(sum((x - m) ** 2 for x in past) / (window - 1))
        out.append((v - m) / sd if sd > 0 else 0.0)
    return out


def variable_limit(average_price: float) -> tuple[float, float]:
    """(initial, expanded) daily limits in dollars per bushel from an average settlement price."""
    initial = max(round(0.07 * average_price / 0.05) * 0.05, 0.20)
    expanded = math.ceil(round(1.5 * initial / 0.05, 9)) * 0.05
    return round(initial, 2), round(expanded, 2)


@dataclass(frozen=True)
class Day:
    settle: float
    locked: bool


def limit_path(start: float, fair: float, limit: float, expanded: float, days: int = 5) -> list[Day]:
    """Settlements when news moves the fair price to `fair`: each day the price moves toward it by at
    most the day's limit; a day that closes at the limit is locked, and the next day uses the
    expanded limit (the normal limit returns after a day that does not close at the limit)."""
    out, p, lim = [], start, limit
    for _ in range(days):
        gap = fair - p
        if abs(gap) > lim + 1e-12:
            p += math.copysign(lim, gap)
            out.append(Day(round(p, 4), True))
            lim = expanded
        else:
            p = fair
            out.append(Day(round(p, 4), False))
            lim = limit
    return out


def crush_margin(beans: float, meal: float, oil_cents: float) -> float:
    """Board crush in dollars per bushel: meal ($/short ton) x 0.022 + oil (cents/lb) x 0.11 - beans."""
    return meal * 0.022 + oil_cents * 0.11 - beans
