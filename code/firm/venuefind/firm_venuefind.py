"""firm.venuefind -- where a cloud-hosted venue is, and how close a firm can get (build of One Quant Book 14,
chapter 17).

Three tools. A prefix matcher over a provider's published IP-range file (the fixture in data/ has the documented
shape and addresses from the documentation ranges of RFC 5737 and RFC 3849, so it names no real host). Round-trip
triangulation on firm.geomap: from probes at known sites, the point whose distances best match the distances the
round trips allow, never beyond the light-time bound. And the instance lottery: instances land at random distances
from the venue's servers, the firm launches n, keeps the best, and pays for every launch. A re-measurement check
wraps Book 7's CUSUM test (firm.decay) to flag a venue that has moved.

API (stable):
    load_ranges(path) -> [(network, region, service)] ; match(ranges, address) -> (prefix, region, service) or None
    distance_bound_km(rtt_us, n_g=1.462, overhead_us=0.0) -> km     the farthest a server can be for that round trip
    triangulate(probes, lat0, lon0, span_deg, step_deg, n_g, factor, overhead_us) -> (lat, lon, rms_km)
    Lottery(median_us, p01_us) ; expected_best(lottery, n, sims=20000, seed=0)
    best_n(lottery, value_per_us_month, launch_cost, n_max=200) -> (n*, net value)
    moved(daily_medians) -> first index where the CUSUM path leaves its 5% boundary, or None
"""
import ipaddress
import json
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "geomap"))
sys.path.insert(0, str(HERE.parent / "decay"))
import firm_decay as fdc  # noqa: E402
import firm_geomap as gm  # noqa: E402

DATA = HERE / "data"
Z = 2.3263478740408408


def load_ranges(path=DATA / "ip_ranges_fixture.json"):
    with open(path) as f:
        doc = json.load(f)
    out = [(ipaddress.ip_network(p["ip_prefix"]), p["region"], p["service"]) for p in doc["prefixes"]]
    out += [(ipaddress.ip_network(p["ipv6_prefix"]), p["region"], p["service"]) for p in doc.get("ipv6_prefixes", [])]
    return out


def match(ranges, address):
    """Longest-prefix match of an address against the published ranges."""
    ip = ipaddress.ip_address(address)
    hits = [(n, r, s) for n, r, s in ranges if n.version == ip.version and ip in n]
    if not hits:
        return None
    n, r, s = max(hits, key=lambda h: h[0].prefixlen)
    return str(n), r, s


def distance_bound_km(rtt_us, n_g=1.462, overhead_us=0.0):
    return max(0.0, rtt_us / 2 - overhead_us) * 1e-6 * gm.C0 / n_g / 1e3


def triangulate(probes, lat0, lon0, span_deg=6.0, step_deg=0.1, n_g=1.462, factor=1.3,
                overhead_us=0.0):
    """probes: [(lat, lon, rtt_us)]. A round trip bounds the distance (light in glass) and
    estimates it as bound / factor; least squares on a grid around (lat0, lon0)."""
    best = None
    grid = np.arange(-span_deg, span_deg + 1e-9, step_deg)
    for dlat in grid:
        for dlon in grid:
            lat, lon = lat0 + dlat, lon0 + dlon
            res, ok = 0.0, True
            for plat, plon, rtt in probes:
                d = gm.haversine_m(plat, plon, lat, lon) / 1e3
                bound = distance_bound_km(rtt, n_g, overhead_us)
                if d > bound:
                    ok = False
                    break
                res += (d - bound / factor) ** 2
            if ok and (best is None or res < best[0]):
                best = (res, lat, lon)
    if best is None:
        raise ValueError("no point satisfies every probe's light-time bound")
    return best[1], best[2], math.sqrt(best[0] / len(probes))


@dataclass(frozen=True)
class Lottery:
    median_us: float      # median round trip of a freshly launched instance to the venue
    p01_us: float         # the best 1% of launches


def _draw(lot, size, rng):
    sigma = math.log(lot.median_us / lot.p01_us) / Z
    return lot.median_us * np.exp(rng.normal(0.0, sigma, size))


def expected_best(lot, n, sims=20000, seed=0):
    rng = np.random.default_rng(seed)
    return float(_draw(lot, (sims, n), rng).min(axis=1).mean())


def best_n(lot, value_per_us_month, launch_cost, n_max=200, sims=4000, seed=0):
    """n maximising the monthly value of the round trip saved, net of the launches' cost."""
    base = expected_best(lot, 1, sims, seed)
    best = (1, 0.0)
    for n in range(1, n_max + 1):
        net = value_per_us_month * (base - expected_best(lot, n, sims, seed)) - launch_cost * n
        if net > best[1]:
            best = (n, net)
    return best


def moved(daily_medians):
    """Book 7's CUSUM test on standardised daily median round trips: the first day the path leaves the boundary."""
    x = np.asarray(daily_medians, dtype=float)
    path, bound = fdc.cusum(x)
    out = np.nonzero(np.abs(path) > bound)[0]
    return int(out[0]) if len(out) else None
