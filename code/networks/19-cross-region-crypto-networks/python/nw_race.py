"""Chapter 19 of One Quant Book 14: the hubs, their path inflation, and racing a message down several routes
(firm.routerace on firm.geomap).

    HUBS, hub_rows()           Tokyo to four hubs: geodesic, floors, published round trips (backbone, specialist) and
                               path inflation against the round-trip fibre floor
    ROUTES                     three routes Tokyo -> Singapore, one way (medians from published round trips; tails
                               and the third route are assumptions)
    race_rows(rhos)            p99 gain of racing two and three routes against the best single one
    VALUE, break_even(rho)     the monthly price of the third route at which racing it stops paying
    duplicate_rows(fills)      duplicates a venue accepts under the open-only rule, against the first copy's fill time
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "geomap"))
sys.path.insert(0, str(ROOT / "code" / "firm" / "routerace"))
import firm_geomap as gm  # noqa: E402
import firm_routerace as rr  # noqa: E402

SITES = {s.id: s for s in gm.load_sites(ROOT / "data" / "networks" / "sites.csv")}
# published median round trips from Tokyo, ms: (VPC peering, Direct Connect with a specialist network)
PUBLISHED = {"aws-sin": (68.0, 65.4), "aws-iad": (150.2, 135.4), "aws-fra": (224.3, 136.5), "aws-lon": (210.0, 139.6),
             "aws-sto": (245.3, 124.3)}
NAMES = {"aws-sin": "Singapore", "aws-iad": "N. Virginia", "aws-fra": "Frankfurt", "aws-lon": "London",
         "aws-sto": "Stockholm", "aws-hkg": "Hong Kong"}
TAIL = 1.15                                           # assumed p99 / median of a long-haul route
ROUTES = [rr.Route("specialist", 65.4e3 / 2, 65.4e3 / 2 * TAIL), rr.Route("backbone", 68.0e3 / 2, 68.0e3 / 2 * TAIL),
          rr.Route("internet", 35.0e3, 35.0e3 * 1.3)]
VALUE = 10.0                                          # USD a month per microsecond of p99 saved (assumption)
RHOS = (0.0, 0.25, 0.5, 0.75, 0.9)


def distance(a, b):
    return gm.geodesic_m(SITES[a].lat, SITES[a].lon, SITES[b].lat, SITES[b].lon)


def hub_rows():
    out = []
    for h in ["aws-hkg", "aws-sin", "aws-iad", "aws-fra", "aws-lon", "aws-sto"]:
        d = distance("aws-nrt", h)
        row = {"hub": h, "km": d / 1e3, "vac_rtt": 2 * gm.floor_us(d) / 1e3,
               "fib_rtt": 2 * gm.floor_us(d, "fibre") / 1e3}
        if h in PUBLISHED:
            bb, sp = PUBLISHED[h]
            row |= {"backbone": bb, "specialist": sp, "infl_bb": rr.path_inflation(bb * 1e3, d),
                    "infl_sp": rr.path_inflation(sp * 1e3, d)}
        out.append(row)
    return out


def race_rows(rhos=RHOS):
    return [(rho, rr.percentile_gain(ROUTES[:2], rho), rr.percentile_gain(ROUTES, rho)) for rho in rhos]


def break_even(rho):
    g2, g3 = rr.percentile_gain(ROUTES[:2], rho), rr.percentile_gain(ROUTES, rho)
    return rr.break_even_price(g3 - g2, VALUE)


def duplicate_rows(fills=(0, 250, 500, 1000, 2000, 4000, 8000), rho=0.5):
    _, draws = rr.first_arrival(ROUTES, rho)
    return [(f, rr.duplicates(draws, f)["accepted_duplicates"]) for f in fills]
