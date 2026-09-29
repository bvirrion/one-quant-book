"""Chapter 10 of One Quant Book 14: the North American map from computed coordinates (firm.geomap).

    sites()                     the site table of data/networks/sites.csv (each row names its ledger rows)
    distance(a, b)              WGS-84 geodesic between two sites, metres
    PAIRS, pair_rows()          the chapter's site pairs: distance and one-way floors in vacuum, air and fibre
    ROUTES, route_rows()        published one-way route latencies, their floor in the route's medium,
                                route factor, excess time and the excess path it is worth
    map_points(region)          projected coordinates (km) of a region's sites for the TikZ maps
    chord_saving_m(a, b)        how much shorter the straight chord through the Earth is than the geodesic
    spherical_error(a, b)       relative error of the spherical (haversine) distance against the geodesic
"""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "geomap"))
import firm_geomap as gm  # noqa: E402

SITES_CSV = ROOT / "data" / "networks" / "sites.csv"
R_MEAN = 6_371_008.8

PAIRS = [("mahwah", "carteret"), ("mahwah", "ny4"), ("ny4", "carteret"), ("ny4", "ny5"),
         ("aurora", "carteret"), ("aurora", "mahwah"), ("aurora", "ny5"), ("aurora", "cermak"),
         ("cermak", "carteret"), ("markham", "mahwah"), ("markham", "ny4"), ("markham", "carteret")]

# label, from, to, medium, published one-way latency (us), ledger row
ROUTES = [
    ("Quincy 2016 to Carteret", "aurora", "carteret", "air", 3982.0, "F13"),
    ("Quincy 2016 to Mahwah", "aurora", "mahwah", "air", 3986.0, "F13"),
    ("ICE Toronto to Mahwah", "markham", "mahwah", "air", 1890.0, "F7"),
    ("ICE Toronto to NY4", "markham", "ny4", "air", 1990.0, "F7"),
    ("ICE Toronto to Carteret", "markham", "carteret", "air", 2050.0, "F7"),
    ("Spread 2010 (6.65 ms)", "cermak", "carteret", "fibre", 6650.0, "F12"),
    ("Spread later (6.55 ms)", "cermak", "carteret", "fibre", 6550.0, "F12"),
]

REGIONS = {
    "na": (["aurora", "cermak", "markham", "mahwah", "carteret"], 41.8, -81.0),
    "nj": (["mahwah", "ny4", "carteret"], 40.8, -74.15),
}


def sites():
    return {s.id: s for s in gm.load_sites(SITES_CSV)}


def distance(a, b, table=None):
    t = table or sites()
    return gm.geodesic_m(t[a].lat, t[a].lon, t[b].lat, t[b].lon)


def pair_rows():
    t = sites()
    rows = []
    for a, b in PAIRS:
        d = distance(a, b, t)
        rows.append({"a": a, "b": b, "km": d / 1e3, "vacuum_us": gm.floor_us(d, "vacuum"),
                     "air_us": gm.floor_us(d, "air"), "fibre_us": gm.floor_us(d, "fibre")})
    return rows


def route_rows():
    t = sites()
    rows = []
    for label, a, b, medium, pub, row in ROUTES:
        d = distance(a, b, t)
        floor = gm.floor_us(d, medium)
        n = {"air": gm.N_AIR, "fibre": gm.N_FIBRE}[medium]
        excess = pub - floor
        rows.append({"label": label, "a": a, "b": b, "medium": medium, "km": d / 1e3,
                     "published_us": pub, "floor_us": floor, "vacuum_us": gm.floor_us(d, "vacuum"),
                     "factor": gm.route_factor(pub, d, medium), "excess_us": excess,
                     "excess_km": excess * 1e-6 * gm.C0 / n / 1e3, "row": row})
    return rows


def map_points(region):
    ids, lat0, lon0 = REGIONS[region]
    t = sites()
    xy = gm.project([t[i] for i in ids], lat0, lon0)
    return [(i, *xy[i]) for i in ids]


def chord_saving_m(a, b):
    """Geodesic minus straight chord, on the mean sphere (the ellipsoid changes it by well under 1%)."""
    t = sites()
    s = gm.haversine_m(t[a].lat, t[a].lon, t[b].lat, t[b].lon, R_MEAN)
    chord = 2 * R_MEAN * math.sin(s / (2 * R_MEAN))
    return s - chord


def spherical_error(a, b):
    t = sites()
    return gm.haversine_m(t[a].lat, t[a].lon, t[b].lat, t[b].lon) / distance(a, b, t) - 1
