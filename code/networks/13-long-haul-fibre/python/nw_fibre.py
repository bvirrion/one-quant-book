"""Chapter 13 of One Quant Book 14: long-haul fibre routes taken apart (firm.fibreroute on firm.geomap).

    EQUIP                      the model's equipment assumptions (terminals, amplifiers, spans): not measurements
    PUBLISHED, published()     published one-way latencies inverted into path length and route factor
    variants()                 the 2010 Chicago-New Jersey route rebuilt four ways: as inverted, with dispersion-
                               compensating fibre, in hollow-core fibre, and along the geodesic
    sensitivity(eq_us)         implied path factor of the 2010 route against the equipment time assumed
    costs(years)               illustrative dark-fibre against lit-service cumulative costs (assumed prices)
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "geomap"))
sys.path.insert(0, str(ROOT / "code" / "firm" / "fibreroute"))
import firm_fibreroute as fr  # noqa: E402
import firm_geomap as gm  # noqa: E402

SITES = {s.id: s for s in gm.load_sites(ROOT / "data" / "networks" / "sites.csv")}
EQUIP = {"terminal_us": 10.0, "amp_us": 0.1, "span_km": 80.0, "n_g": 1.462, "hollow_n_g": 1.003, "dcf_frac": 0.2}
# label, from, to, published one-way latency (us), how derived
PUBLISHED = [("Chicago-New Jersey fibre, 2010", "cermak", "carteret", 6650.0, "quoted one way"),
             ("Chicago-New Jersey fibre, later", "cermak", "carteret", 6550.0, "quoted one way"),
             ("New York-London subsea, 2015", "ny4", "ld4", 58950.0 / 2, "half of a 58.95 ms round trip")]
# illustrative prices for the cost comparison: assumptions, not quotes
PRICES = {"iru": 6e6, "iru_years": 20, "om_year": 0.3e6, "capex": 1.5e6, "capex_years": 20, "lit_monthly": 90e3}


def geodesic_km(a, b):
    s, t = SITES[a], SITES[b]
    return gm.geodesic_m(s.lat, s.lon, t.lat, t.lon) / 1e3


def _equipment_us(path_km):
    spans = max(1, int(-(-path_km // EQUIP["span_km"])))
    return 2 * EQUIP["terminal_us"] + spans * EQUIP["amp_us"]


def published():
    out = []
    for label, a, b, us, how in PUBLISHED:
        g = geodesic_km(a, b)
        first = fr.invert(us, g, EQUIP["n_g"], 2 * EQUIP["terminal_us"])
        eq = _equipment_us(first["path_km"])
        inv = fr.invert(us, g, EQUIP["n_g"], eq)
        out.append({"label": label, "geodesic_km": g, "published_us": us, "how": how, "equipment_us": eq,
                    "floor_us": gm.floor_us(g * 1e3, "fibre"), **inv})
    return out


def variants():
    p = published()[0]
    g, f = p["geodesic_km"], p["factor"]
    kw = {"span_km": EQUIP["span_km"], "amp_us": EQUIP["amp_us"], "terminal_us": EQUIP["terminal_us"]}
    base = fr.build("as inverted", g, f, n_g=EQUIP["n_g"], **kw)
    rows = {"as inverted": base,
            "with a DCF spool": fr.build("with DCF", g, f, n_g=EQUIP["n_g"], dcf_frac=EQUIP["dcf_frac"], **kw),
            "hollow-core on the same path": fr.with_index(base, EQUIP["hollow_n_g"]),
            "standard fibre on the geodesic": fr.build("geodesic", g, 1.0, n_g=EQUIP["n_g"], **kw)}
    return {k: fr.components(r) for k, r in rows.items()}


def sensitivity(eq_us=(0, 25, 50, 100, 150, 200)):
    p = published()[0]
    return [(e, fr.invert(p["published_us"], p["geodesic_km"], EQUIP["n_g"], e)["factor"]) for e in eq_us]


def costs(years=20):
    """Cumulative cost after y years: dark fibre pays the IRU and its equipment up front and O&M each year; the lit
    service pays its monthly fee. Illustrative prices (PRICES), not quotes."""
    q = PRICES
    return [(y, q["iru"] + q["capex"] + q["om_year"] * y, fr.lit(q["lit_monthly"]) * y) for y in range(years + 1)]
