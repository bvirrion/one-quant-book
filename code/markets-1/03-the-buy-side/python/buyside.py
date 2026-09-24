"""Benchmarks, tracking error and fund fees (Chapter 3)."""
import math
from dataclasses import dataclass

import numpy as np


def tracking_error(fund: np.ndarray, bench: np.ndarray, periods_per_year: int = 12) -> float:
    """Annualised standard deviation of the active return."""
    active = np.asarray(fund) - np.asarray(bench)
    return float(active.std(ddof=1) * math.sqrt(periods_per_year))


def information_ratio(fund: np.ndarray, bench: np.ndarray, periods_per_year: int = 12) -> float:
    active = np.asarray(fund) - np.asarray(bench)
    return float(active.mean() * periods_per_year / tracking_error(fund, bench, periods_per_year))


def years_to_significance(ir: float, t_stat: float = 2.0) -> float:
    """Years of data for an information ratio `ir` to reach a given t-statistic."""
    return (t_stat / ir) ** 2


@dataclass
class FeeResult:
    nav: list[float]            # investor's net asset value, start of year 0 = 1.0
    mgmt_fees: list[float]
    perf_fees: list[float]
    high_water: list[float]


def run_fees(gross: list[float], mgmt: float = 0.02, perf: float = 0.20) -> FeeResult:
    """Annual fees with a high-water mark.

    Each year: the management fee is charged on opening NAV; the performance
    fee is `perf` times the amount by which NAV after the management fee
    exceeds the high-water mark; the mark then rises to the closing NAV.
    """
    nav, hwm = 1.0, 1.0
    out = FeeResult([1.0], [], [], [1.0])
    for g in gross:
        m = mgmt * nav
        before_perf = nav * (1.0 + g) - m
        p = perf * max(0.0, before_perf - hwm)
        nav = before_perf - p
        hwm = max(hwm, nav)
        out.nav.append(nav)
        out.mgmt_fees.append(m)
        out.perf_fees.append(p)
        out.high_water.append(hwm)
    return out


def gross_nav(gross: list[float]) -> list[float]:
    out = [1.0]
    for g in gross:
        out.append(out[-1] * (1.0 + g))
    return out
