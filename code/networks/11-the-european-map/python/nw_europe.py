"""Chapter 11 of One Quant Book 14: the European map (firm.geomap, firm.venuesites).

    PAIRS, pair_rows()         distances and one-way floors between the European sites
    migration(from_sites)      Euronext's primary site before and after 6 June 2022 and the floors to it
    ROUTES, route_rows()       published European route latencies against their floors
    triangle(on)               the London-Frankfurt-Euronext triangle on a date: sides in km and vacuum microseconds
    map_points(region)         projected coordinates for the TikZ maps
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "venuesites"))
import firm_venuesites as vs  # noqa: E402

gm = vs.gm
BEFORE, AFTER = "2022-06-05", "2022-06-06"

PAIRS = [("ld4", "fr2"), ("ld4", "bergamo"), ("fr2", "bergamo"), ("ld4", "basildon"), ("docklands", "basildon"),
         ("ld4", "docklands"), ("basildon", "fr2"), ("basildon", "bergamo"), ("fr2", "zh4"), ("zh4", "bergamo"),
         ("fr2", "vasby"), ("ld4", "vasby")]

# label, from, to, medium, published one-way latency (us), ledger row, note
ROUTES = [
    ("McKay 2015 LD4-FR2", "ld4", "fr2", "air", 2320.0, "F13", "half of a 4.64 ms round trip"),
    ("EWIN 2024 LD4-IT3", "ld4", "bergamo", "air", 4000.0, "F12", "published as less than 4 ms"),
]

REGIONS = {
    "eu": (["ld4", "fr2", "zh4", "bergamo"], 49.0, 4.5),
}


def registry():
    return vs.Registry.load()


def distance(a, b, reg=None):
    s = (reg or registry()).sites
    return gm.geodesic_m(s[a].lat, s[a].lon, s[b].lat, s[b].lon)


def pair_rows():
    reg = registry()
    rows = []
    for a, b in PAIRS:
        d = distance(a, b, reg)
        rows.append({"a": a, "b": b, "km": d / 1e3, "vacuum_us": gm.floor_us(d, "vacuum"),
                     "fibre_us": gm.floor_us(d, "fibre")})
    return rows


def migration(from_sites=("ld4", "docklands", "fr2", "zh4")):
    reg = registry()
    old, new = reg.primary("XPAR", on=BEFORE), reg.primary("XPAR", on=AFTER)
    rows = []
    for f in from_sites:
        d0, d1 = distance(f, old, reg), distance(f, new, reg)
        rows.append({"from": f, "old": old, "new": new, "km_before": d0 / 1e3, "km_after": d1 / 1e3,
                     "vac_before": gm.floor_us(d0), "vac_after": gm.floor_us(d1),
                     "fib_before": gm.floor_us(d0, "fibre"), "fib_after": gm.floor_us(d1, "fibre")})
    return rows


def route_rows():
    reg = registry()
    out = []
    for label, a, b, medium, pub, row, note in ROUTES:
        d = distance(a, b, reg)
        out.append({"label": label, "km": d / 1e3, "published_us": pub, "floor_us": gm.floor_us(d, medium),
                    "fibre_us": gm.floor_us(d, "fibre"), "factor": gm.route_factor(pub, d, medium),
                    "row": row, "note": note})
    return out


def triangle(on):
    reg = registry()
    eng = reg.primary("XPAR", on=on)
    sides = [("ld4", "fr2"), ("fr2", eng), (eng, "ld4")]
    return [(a, b, distance(a, b, reg) / 1e3, gm.floor_us(distance(a, b, reg))) for a, b in sides]


def nearest_from(site="ld4"):
    """European venues' current primary sites (west of 30 W excluded) by distance from `site`, one row per site."""
    reg = registry()
    seen, out = {}, []
    for mic, s, _km, _vac in reg.nearest(site):
        if reg.sites[s].lon < -30:
            continue
        seen.setdefault(s, []).append(mic)
    for s, mics in seen.items():
        d = distance(site, s, reg)
        out.append({"site": s, "mics": mics, "km": d / 1e3, "vacuum_us": gm.floor_us(d),
                    "fibre_us": gm.floor_us(d, "fibre")})
    return sorted(out, key=lambda r: r["km"])


def map_points(region):
    ids, lat0, lon0 = REGIONS[region]
    reg = registry()
    xy = gm.project([reg.sites[i] for i in ids], lat0, lon0)
    return [(i, *xy[i]) for i in ids]
