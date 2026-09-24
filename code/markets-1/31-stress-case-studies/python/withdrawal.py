"""A sell programme that follows volume, in a book whose depth withdraws (Chapter 31). Illustrative:
a toy with two feedbacks, calibrated to nothing. Time runs in seconds; the programme re-reads volume each minute."""
import math
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Params:
    depth0: float = 100_000.0       # contracts of resting buy interest in calm conditions
    base_volume: float = 20_000.0   # contracts a minute traded in calm conditions
    participation: float = 0.09     # the programme sells this fraction of the previous minute's volume
    impact: float = 0.03            # fall caused by selling a quantity equal to the current depth
    withdrawal: float = 150.0       # depth = depth0 * (floor + (1 - floor) * exp(-withdrawal * recent fall))
    floor: float = 0.1              # the fraction of depth that never leaves
    churn: float = 100.0            # volume = base * (1 + churn * recent fall): contracts passed from hand to hand
    memory: float = 5.0             # minutes: "recent fall" is measured from an average price with this memory
    pause_at: float | None = None   # one pause, when the fall since the start exceeds this fraction


def run(p: Params, total: float, minutes: int = 60, sub: int = 60):
    """Per-minute (price, depth, programme sales, volume). Price starts at 1."""
    price, anchor, left, volume, paused = 1.0, 1.0, total, p.base_volume, False
    out = []
    for _ in range(minutes):
        rate, traded = min(left, p.participation * volume) / sub, 0.0
        for _ in range(sub):
            fall = max(0.0, 1.0 - price / anchor)               # how far below the recent average
            depth = p.depth0 * (p.floor + (1.0 - p.floor) * math.exp(-p.withdrawal * fall))
            price *= 1.0 - p.impact * rate / depth
            anchor += (price - anchor) / (p.memory * sub)
            traded += p.base_volume * (1.0 + p.churn * fall) / sub + rate
        left, volume = left - rate * sub, traded
        if p.pause_at is not None and not paused and 1.0 - price >= p.pause_at:
            paused, anchor, volume = True, price, p.base_volume     # buyers re-anchor at the reopening price
        out.append((price, depth, rate * sub, volume))
    return out


def trough(path) -> float:
    return 1.0 - min(x[0] for x in path)


def depth_needed(p: Params, total: float, max_fall: float) -> float:
    """Smallest initial depth (bisection on a log scale) that keeps the trough within max_fall."""
    lo, hi = p.depth0 * 0.1, p.depth0 * 100.0
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        if trough(run(replace(p, depth0=mid), total)) > max_fall:
            lo = mid
        else:
            hi = mid
    return hi
