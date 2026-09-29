"""firm.slamodel -- circuits, availability, service credits and the cost of downtime (build of One Quant Book 14,
chapter 15).

A circuit is a catalogue row: what it is, its monthly price and its source, and the failure behaviour the firm
assumes for it (mean time between failures, mean time to repair). A design is one or more circuits, with a rate of
common-mode events (a cut duct, a flooded building) that take all of them down at once. The simulation draws a
year of failures (Poisson arrivals, lognormal repairs whose mean is the MTTR) and reports the minutes during
which the design carried no traffic; the credit calculator applies a published credit schedule to a month's uptime.

API (stable):
    Tier(below_pct, credit_pct) ; CATALOGUE ; SCHEDULES
    Circuit(name, kind, monthly, one_time, mtbf_h, mttr_h, source, as_of)
    Design(name, circuits, common_rate_y=0.0, common_mttr_h=8.0)
    availability(mtbf_h, mttr_h) ; design_availability(design)             steady state, independent + common mode
    simulate_year(design, seed=0, sigma=1.0) -> dict(down_min, outages, per_circuit_down_min, intervals)
    monthly_down_min(intervals, months=12)
    credit(tiers, uptime_pct, monthly) -> currency ; uptime_pct(down_min, days=30)
    downtime_cost(down_min, per_min)
"""
import math
from dataclasses import dataclass

import numpy as np

HOURS_Y = 8766.0


@dataclass(frozen=True)
class Tier:
    below_pct: float          # the credit applies when uptime is below this percentage
    credit_pct: float         # of the month's charge


@dataclass(frozen=True)
class Circuit:
    name: str
    kind: str
    monthly: float
    one_time: float
    mtbf_h: float
    mttr_h: float
    source: str
    as_of: str


@dataclass(frozen=True)
class Design:
    name: str
    circuits: tuple
    common_rate_y: float = 0.0     # common-mode events a year (shared duct, building)
    common_mttr_h: float = 8.0


# A published credit schedule (AWS Direct Connect, ledger networks/15:F1): uptime thresholds and credits.
SCHEDULES = {
    "single connection": (Tier(95.0, 10), Tier(92.5, 25), Tier(90.0, 100)),
    "multi-site non-redundant": (Tier(99.9, 10), Tier(99.0, 25), Tier(95.0, 100)),
    "multi-site redundant": (Tier(99.99, 10), Tier(99.0, 25), Tier(95.0, 100)),
}

# Published monthly prices (ledger networks/15:F4, NYSE connectivity fee schedule; networks/9:F5, MIAX Pearl).
CATALOGUE = {
    "nyse_ip_1g": ("NYSE IP network, 1 Gb circuit", 2_500.0, 2_500.0, "networks/15:F4"),
    "nyse_ip_10g": ("NYSE IP and NMS networks, 10 Gb", 11_000.0, 10_000.0, "networks/15:F4"),
    "nyse_ip_40g": ("NYSE IP and NMS networks, 40 Gb", 18_000.0, 10_000.0, "networks/15:F4"),
    "nyse_xc": ("NYSE data-centre fibre cross connect", 600.0, 500.0, "networks/15:F4"),
    "nyse_wl_mah_sec_10m": ("NYSE wireless Mahwah-Secaucus, 10 Mb", 9_000.0, 10_000.0, "networks/15:F4"),
    "nyse_wl_mah_sec_200m": ("NYSE wireless Mahwah-Secaucus, 200 Mb", 44_000.0, 10_000.0, "networks/15:F4"),
    "nyse_wl_cme": ("NYSE wireless connection of CME data", 6_000.0, 5_000.0, "networks/15:F4"),
    "miax_ull_10g": ("MIAX Pearl 10 Gb ultra-low-latency", 15_000.0, 0.0, "networks/9:F5"),
}


def availability(mtbf_h, mttr_h):
    return mtbf_h / (mtbf_h + mttr_h)


def design_availability(design):
    """Down when every circuit is down (independently) or a common-mode event is under way."""
    p_all = 1.0
    for c in design.circuits:
        p_all *= 1 - availability(c.mtbf_h, c.mttr_h)
    p_common = design.common_rate_y * design.common_mttr_h / HOURS_Y
    return 1 - (p_all + p_common - p_all * p_common)


def _outages(rng, rate_h, mttr_h, sigma):
    n = rng.poisson(rate_h * HOURS_Y)
    starts = np.sort(rng.uniform(0, HOURS_Y, n))
    lengths = mttr_h * np.exp(rng.normal(-sigma * sigma / 2, sigma, n))   # lognormal with mean mttr_h
    return [(s, min(HOURS_Y, s + d)) for s, d in zip(starts, lengths, strict=True)]


def _merge(intervals):
    out = []
    for a, b in sorted(intervals):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def _intersect(x, y):
    i = j = 0
    out = []
    while i < len(x) and j < len(y):
        a, b = max(x[i][0], y[j][0]), min(x[i][1], y[j][1])
        if a < b:
            out.append((a, b))
        if x[i][1] < y[j][1]:
            i += 1
        else:
            j += 1
    return out


def simulate_year(design, seed=0, sigma=1.0):
    rng = np.random.default_rng(seed)
    per = [_merge(_outages(rng, 1 / c.mtbf_h, c.mttr_h, sigma)) for c in design.circuits]
    common = _merge(_outages(rng, design.common_rate_y / HOURS_Y, design.common_mttr_h, sigma))
    all_down = per[0]
    for p in per[1:]:
        all_down = _intersect(all_down, p)
    down = _merge(all_down + common)
    per_min = [60 * sum(b - a for a, b in _merge(p + common)) for p in per]
    return {"down_min": 60 * sum(b - a for a, b in down), "outages": len(down),
            "per_circuit_down_min": per_min, "intervals": down}


def monthly_down_min(intervals, months=12):
    """Minutes down in each of `months` equal months of the simulated year."""
    edge = HOURS_Y / months
    out = [0.0] * months
    for a, b in intervals:
        m = int(a // edge)
        while a < b and m < months:
            end = min(b, (m + 1) * edge)
            out[m] += 60 * (end - a)
            a, m = end, m + 1
    return out


def uptime_pct(down_min, days=30):
    return 100 * (1 - down_min / (days * 1440))


def credit(tiers, up_pct, monthly):
    pct = 0.0
    for t in tiers:
        if up_pct < t.below_pct:
            pct = max(pct, t.credit_pct)
    return monthly * pct / 100


def downtime_cost(down_min, per_min):
    return down_min * per_min


def expected_down_min(design):
    return (1 - design_availability(design)) * HOURS_Y * 60


def nines(a):
    return -math.log10(1 - a) if a < 1 else float("inf")
