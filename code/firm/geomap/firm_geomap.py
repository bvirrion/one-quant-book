"""firm.geomap -- sites, geodesics and latency floors (build of One Quant Book 14, chapter 10).

Sites are data: each has an id, an operator, the venues it hosts, latitude and longitude, and the ledger row that
sources its location. Distances are geodesics on the WGS-84 ellipsoid by Vincenty's inverse method (1975), tested
against Karney's published test set of geodesics (data/geodtest_subset.txt, a CC0 subset). Latency floors follow:
    vacuum  d / c0 ;  air  d * 1.0003 / c0 ;  fibre along the geodesic  d * n_g / c0.
A C++20 twin of the geodesic (cpp/firm_geomap.hpp) reproduces the same test set.

API (stable):
    A_WGS84, F_WGS84, C0 ; N_AIR, N_FIBRE
    Site(id, name, operator, lat, lon, source, venues=())
    geodesic_m(lat1, lon1, lat2, lon2) -> float             Vincenty inverse, metres (raises for non-convergence)
    haversine_m(lat1, lon1, lat2, lon2, r=6371008.8) -> float    spherical comparison
    floor_us(d_m, medium="vacuum"|"air"|"fibre", n_g=None) -> float   one-way microseconds
    route_factor(published_us, d_m, medium) -> float        a published one-way latency over the medium's floor
    matrix(sites) -> {(a, b): metres}
    project(sites, lat0, lon0) -> {id: (x_km, y_km)}         local equirectangular projection for TikZ maps
    load_sites(path) / write_sites(path, sites)              CSV with a source column
"""
import csv
import math
from dataclasses import dataclass, field

A_WGS84 = 6_378_137.0
F_WGS84 = 1 / 298.257223563
B_WGS84 = A_WGS84 * (1 - F_WGS84)
C0 = 299_792_458.0
N_AIR = 1.0003
N_FIBRE = 1.4620


@dataclass(frozen=True)
class Site:
    id: str
    name: str
    operator: str
    lat: float
    lon: float
    source: str
    venues: tuple = field(default=())


def geodesic_m(lat1, lon1, lat2, lon2, tol=1e-12, max_iter=200):
    if lat1 == lat2 and lon1 == lon2:
        return 0.0
    a, b, f = A_WGS84, B_WGS84, F_WGS84
    L = math.radians(lon2 - lon1)
    U1 = math.atan((1 - f) * math.tan(math.radians(lat1)))
    U2 = math.atan((1 - f) * math.tan(math.radians(lat2)))
    sinU1, cosU1, sinU2, cosU2 = math.sin(U1), math.cos(U1), math.sin(U2), math.cos(U2)
    lam = L
    for _ in range(max_iter):
        sl, cl = math.sin(lam), math.cos(lam)
        sin_s = math.hypot(cosU2 * sl, cosU1 * sinU2 - sinU1 * cosU2 * cl)
        cos_s = sinU1 * sinU2 + cosU1 * cosU2 * cl
        sigma = math.atan2(sin_s, cos_s)
        sin_a = cosU1 * cosU2 * sl / sin_s
        cos2a = 1 - sin_a * sin_a
        cos2sm = cos_s - 2 * sinU1 * sinU2 / cos2a if cos2a else 0.0
        C = f / 16 * cos2a * (4 + f * (4 - 3 * cos2a))
        prev = lam
        inner = cos2sm + C * cos_s * (-1 + 2 * cos2sm ** 2)
        lam = L + (1 - C) * f * sin_a * (sigma + C * sin_s * inner)
        if abs(lam - prev) < tol:
            break
    else:
        raise ArithmeticError("Vincenty inverse did not converge (nearly antipodal points)")
    u2 = cos2a * (a * a - b * b) / (b * b)
    A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    t4 = B / 6 * cos2sm * (-3 + 4 * sin_s ** 2) * (-3 + 4 * cos2sm ** 2)
    ds = B * sin_s * (cos2sm + B / 4 * (cos_s * (-1 + 2 * cos2sm ** 2) - t4))
    return b * A * (sigma - ds)


def haversine_m(lat1, lon1, lat2, lon2, r=6_371_008.8):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def floor_us(d_m, medium="vacuum", n_g=None):
    n = {"vacuum": 1.0, "air": N_AIR, "fibre": N_FIBRE}[medium] if n_g is None else n_g
    return d_m * n / C0 * 1e6


def route_factor(published_us, d_m, medium="fibre"):
    return published_us / floor_us(d_m, medium)


def matrix(sites):
    return {(a.id, b.id): geodesic_m(a.lat, a.lon, b.lat, b.lon) for a in sites for b in sites if a.id < b.id}


def project(sites, lat0, lon0):
    k = math.cos(math.radians(lat0))
    return {s.id: ((s.lon - lon0) * 111.320 * k, (s.lat - lat0) * 110.574) for s in sites}


def load_sites(path):
    with open(path) as f:
        return [Site(r["id"], r["name"], r["operator"], float(r["lat"]), float(r["lon"]), r["source"],
                     tuple(v for v in r["venues"].split(";") if v)) for r in csv.DictReader(f)]


def write_sites(path, sites):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "operator", "lat", "lon", "source", "venues"])
        for s in sites:
            w.writerow([s.id, s.name, s.operator, s.lat, s.lon, s.source, ";".join(s.venues)])
