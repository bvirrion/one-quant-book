"""Sovereign spread monitor (build of Book 2, Chapter 7): spreads to a benchmark issuer, their
decomposition into the two yields' moves, and a rolling z-score alert.

Yields in percent; spreads in basis points. A series is a list of (date, value) sorted by date.
"""
from dataclasses import dataclass
from statistics import mean, pstdev


def spreads(yields: dict[str, list[tuple[str, float]]], benchmark: str) -> dict[str, list[tuple[str, float]]]:
    """Spread of every issuer to the benchmark, in basis points, on dates both have."""
    base = dict(yields[benchmark])
    out = {}
    for name, series in yields.items():
        if name == benchmark:
            continue
        out[name] = [(d, (y - base[d]) * 100.0) for d, y in series if d in base]
    return out


@dataclass(frozen=True)
class Decomposition:
    change_bp: float          # change in the spread
    issuer_bp: float          # contribution of the issuer's own yield
    benchmark_bp: float       # contribution of the benchmark (a fall in the benchmark widens the spread)


def decompose(issuer: dict[str, float], benchmark: dict[str, float], start: str, end: str) -> Decomposition:
    di = (issuer[end] - issuer[start]) * 100.0
    db = (benchmark[end] - benchmark[start]) * 100.0
    return Decomposition(di - db, di, -db)


def zscore(series: list[tuple[str, float]], window: int) -> list[tuple[str, float]]:
    """Latest value against the mean and standard deviation of the previous `window` values."""
    out = []
    values = [v for _, v in series]
    for k in range(window, len(series)):
        past = values[k - window:k]
        sd = pstdev(past)
        out.append((series[k][0], (values[k] - mean(past)) / sd if sd > 0 else 0.0))
    return out


def alerts(series: list[tuple[str, float]], window: int, threshold: float) -> list[str]:
    return [d for d, z in zscore(series, window) if abs(z) >= threshold]
