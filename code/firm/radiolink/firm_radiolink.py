"""firm.radiolink -- line-of-sight radio hops and chains, rain, and failover to fibre (build of One Quant Book 14,
chapter 14).

Geometry: the earth bulge at a point of a hop, h = d1 d2 / (12.74 K) metres (d in km, K the effective-earth-radius
factor), and the first Fresnel zone radius, r = 17.32 sqrt(d1 d2 / (f d)) metres (f in GHz). Link budget: free-space
path loss 92.45 + 20 log10 f + 20 log10 d dB, dish gain 10 log10(eta (pi D f / c)^2). Rain: specific attenuation
gamma = k R^alpha dB/km with the ITU-R P.838-3 coefficients of data/p838_3.csv (each row names its ledger row), applied
over the length of the hop inside the rain cell. Radio and equipment figures are parameters, not product data.

API (stable):
    bulge_m(d1, d2, K=4/3) ; fresnel_m(d1, d2, f_ghz) ; tower_m(d_km, f_ghz, K=4/3, obstacle_m=10, clearance=1.0)
    fspl_db(d_km, f_ghz) ; dish_gain_dbi(diameter_m, f_ghz, eta=0.6)
    Hop(d_km, f_ghz, tx_dbm=30, dish_m=1.8, losses_db=3, threshold_dbm=-70, pol="h")
    rx_dbm(hop) ; fade_margin_db(hop)
    coefficients(f_ghz, pol) ; gamma_db_km(rain_mm_h, f_ghz, pol) ; rain_db(hop, rain_mm_h, wet_km=None)
    critical_rain(hop, wet_km=None) -> mm/h at which the hop loses its fade margin
    chain(a, b, hops) -> [(lat, lon)] points on the great circle ; hop_lengths(points) -> [km]
    Storm(at_km, speed_km_min, radius_km, peak_mm_h) ; storm_timeline(hops, storm, radio_us, fibre_us)
    availability(hop, exceed, wet_km) -> fraction of time up, for an exceedance function P(R > r)
"""
import csv
import math
import pathlib
from dataclasses import dataclass

C0 = 299_792_458.0
DATA = pathlib.Path(__file__).resolve().parent / "data" / "p838_3.csv"
R_EARTH_KM = 6371.0088


def bulge_m(d1, d2, K=4 / 3):
    return d1 * d2 / (12.74 * K)


def fresnel_m(d1, d2, f_ghz):
    return 17.32 * math.sqrt(d1 * d2 / (f_ghz * (d1 + d2)))


def tower_m(d_km, f_ghz, K=4 / 3, obstacle_m=10.0, clearance=1.0):
    """Height of two equal towers so that the mid-hop obstacle clears the first Fresnel zone times `clearance`."""
    h = d_km / 2
    return bulge_m(h, h, K) + clearance * fresnel_m(h, h, f_ghz) + obstacle_m


def fspl_db(d_km, f_ghz):
    return 92.45 + 20 * math.log10(f_ghz) + 20 * math.log10(d_km)


def dish_gain_dbi(diameter_m, f_ghz, eta=0.6):
    return 10 * math.log10(eta * (math.pi * diameter_m * f_ghz * 1e9 / C0) ** 2)


@dataclass(frozen=True)
class Hop:
    d_km: float
    f_ghz: float
    tx_dbm: float = 30.0
    dish_m: float = 1.8
    losses_db: float = 3.0
    threshold_dbm: float = -70.0
    pol: str = "h"


def rx_dbm(hop):
    g = dish_gain_dbi(hop.dish_m, hop.f_ghz)
    return hop.tx_dbm + 2 * g - fspl_db(hop.d_km, hop.f_ghz) - hop.losses_db


def fade_margin_db(hop):
    return rx_dbm(hop) - hop.threshold_dbm


def _table():
    with open(DATA) as f:
        return {float(r["f_ghz"]): r for r in csv.DictReader(f)}


def coefficients(f_ghz, pol="h"):
    row = _table()[float(f_ghz)]
    return float(row[f"k_{pol}"]), float(row[f"alpha_{pol}"])


def gamma_db_km(rain_mm_h, f_ghz, pol="h"):
    k, a = coefficients(f_ghz, pol)
    return k * rain_mm_h ** a


def rain_db(hop, rain_mm_h, wet_km=None):
    wet = hop.d_km if wet_km is None else min(wet_km, hop.d_km)
    return gamma_db_km(rain_mm_h, hop.f_ghz, hop.pol) * wet


def critical_rain(hop, wet_km=None):
    k, a = coefficients(hop.f_ghz, hop.pol)
    wet = hop.d_km if wet_km is None else min(wet_km, hop.d_km)
    fm = fade_margin_db(hop)
    return 0.0 if fm <= 0 else (fm / (k * wet)) ** (1 / a)


def _xyz(lat, lon):
    p, q = math.radians(lat), math.radians(lon)
    return math.cos(p) * math.cos(q), math.cos(p) * math.sin(q), math.sin(p)


def chain(a, b, hops):
    """hops + 1 points evenly spaced on the great circle from a=(lat, lon) to b (spherical interpolation)."""
    va, vb = _xyz(*a), _xyz(*b)
    om = math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(va, vb, strict=True)))))
    pts = []
    for i in range(hops + 1):
        t = i / hops
        s1, s2 = math.sin((1 - t) * om) / math.sin(om), math.sin(t * om) / math.sin(om)
        x, y, z = (s1 * p + s2 * q for p, q in zip(va, vb, strict=True))
        pts.append((math.degrees(math.atan2(z, math.hypot(x, y))), math.degrees(math.atan2(y, x))))
    return pts


def hop_lengths(points, geodesic_m):
    return [geodesic_m(*points[i], *points[i + 1]) / 1e3 for i in range(len(points) - 1)]


@dataclass(frozen=True)
class Storm:
    at_km: float              # where the cell's track crosses the route, km from its first tower
    speed_km_min: float       # the cell's speed across the route
    radius_km: float          # rain-cell radius
    peak_mm_h: float          # rain rate at the cell's centre, falling linearly to zero at its edge


def storm_timeline(hops, storm, radio_us, fibre_us):
    """Minute by minute while the cell crosses the route (from one radius before it to one
    after): hops down, and the latency, radio if every hop holds its margin, else fibre."""
    starts = [sum(h.d_km for h in hops[:i]) for i in range(len(hops))]
    out, m = [], 0
    while True:
        y = -storm.radius_km + storm.speed_km_min * m
        if y > storm.radius_km:
            return out
        down = 0
        half = math.sqrt(max(0.0, storm.radius_km ** 2 - y * y))
        for h, s in zip(hops, starts, strict=True):
            lo, hi = max(s, storm.at_km - half), min(s + h.d_km, storm.at_km + half)
            if hi <= lo:
                continue
            dist = math.hypot(y, (lo + hi) / 2 - storm.at_km)
            rate = storm.peak_mm_h * max(0.0, 1 - dist / storm.radius_km)
            if rain_db(h, rate, hi - lo) > fade_margin_db(h):
                down += 1
        out.append((m, down, radio_us if down == 0 else fibre_us))
        m += 1


def availability(hop, exceed, wet_km=None):
    """1 - P(rain rate > the hop's critical rate), for an exceedance function exceed(r) = P(R > r)."""
    return 1.0 - exceed(critical_rain(hop, wet_km))
