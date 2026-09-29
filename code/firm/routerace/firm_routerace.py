"""firm.routerace -- racing the same message down several routes (build of One Quant Book 14, chapter 19).

Routes are lognormal one-way latencies (median and 99th percentile) with a price; their draws are correlated through
a Gaussian copula with correlation rho (a common cause: the same congestion, the same cable). The sender sends one
message on k routes with the same idempotency key and the venue keeps the first; the model counts what a venue's
duplicate rule does with the others. A hub matrix on firm.geomap compares published inter-region round trips with
the geodesic floors (path inflation). Everything is a labelled simulation except the geometry and the published rows.

API (stable):
    Route(name, median_us, p99_us, usd_month=0.0)
    first_arrival(routes, rho, n=200000, seed=0) -> (first, all_draws)
    percentile_gain(routes, rho, q=99, n, seed) -> us saved at the q-th percentile against the best single route
    break_even_price(gain_us, value_per_us_month) -> the monthly price of an extra route at which racing stops paying
    duplicates(draws, fill_us, rule="open-only") -> dict(accepted_duplicates, rejected)   per message, averaged
    path_inflation(published_rtt_us, d_m, medium="fibre") -> published / (2 x one-way floor)
"""
import math
from dataclasses import dataclass

import numpy as np

Z = 2.3263478740408408
C0 = 299_792_458.0
N = {"vacuum": 1.0, "air": 1.0003, "fibre": 1.462}


@dataclass(frozen=True)
class Route:
    name: str
    median_us: float
    p99_us: float
    usd_month: float = 0.0


def first_arrival(routes, rho, n=200_000, seed=0):
    """Correlated lognormal draws (one column per route) and the row-wise first arrival."""
    rng = np.random.default_rng(seed)
    k = len(routes)
    common = rng.normal(size=(n, 1))
    own = rng.normal(size=(k, n)).T          # route i keeps its draws whatever k
    z = math.sqrt(rho) * common + math.sqrt(1 - rho) * own
    draws = np.column_stack([r.median_us * np.exp(z[:, i] * math.log(r.p99_us / r.median_us) / Z)
                             for i, r in enumerate(routes)])
    return draws.min(axis=1), draws


def percentile_gain(routes, rho, q=99, n=200_000, seed=0):
    first, draws = first_arrival(routes, rho, n, seed)
    best_single = min(float(np.percentile(draws[:, i], q)) for i in range(draws.shape[1]))
    return best_single - float(np.percentile(first, q))


def break_even_price(gain_us, value_per_us_month):
    return gain_us * value_per_us_month


def duplicates(draws, fill_us, rule="open-only"):
    """For each message sent on every route: the first copy is accepted. Under rule 'open-only' (a venue that rejects
    a duplicate key only while the first order is open) a later copy arriving after the first has filled
    (first + fill_us) is accepted as a new order; under 'ever' every later copy is rejected."""
    s = np.sort(draws, axis=1)
    late = s[:, 1:] > (s[:, :1] + fill_us)
    if rule == "ever":
        return {"accepted_duplicates": 0.0, "rejected": float(s.shape[1] - 1)}
    return {"accepted_duplicates": float(late.sum(axis=1).mean()), "rejected": float((~late).sum(axis=1).mean())}


def path_inflation(published_rtt_us, d_m, medium="fibre"):
    return published_rtt_us / (2 * d_m * N[medium] / C0 * 1e6)
