"""Chapter 14 of One Quant Book 14: radio hops, rain and a storm across the Chicago-New Jersey route (firm.radiolink).

    geometry_rows()        mid-hop earth bulge, Fresnel radius and tower height for 30, 50 and 70 km at 6 and 11 GHz
    budget_rows(d_km)      the link budget of one hop at 6, 11, 18 and 80 GHz and the rain rate that breaks it
    critical_curve()       critical rain rate against hop length, for a rain cell 10 km across the hop
    route()                the Aurora-Carteret chain: 20 hops on the great circle
    storm(f, peak)         a labelled storm crossing the route: minute-by-minute hops down and route latency
    RADIO_US, FIBRE_US     the route's latency by radio (published, chapter 10) and by fibre (assumed path factor 1.2)
"""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "geomap"))
sys.path.insert(0, str(ROOT / "code" / "firm" / "radiolink"))
import firm_geomap as gm  # noqa: E402
import firm_radiolink as rl  # noqa: E402

SITES = {s.id: s for s in gm.load_sites(ROOT / "data" / "networks" / "sites.csv")}
A, B = (SITES["aurora"].lat, SITES["aurora"].lon), (SITES["carteret"].lat, SITES["carteret"].lon)
D_KM = gm.geodesic_m(*A, *B) / 1e3
RADIO_US = 3982.0                                   # Quincy Data 2016, one way (ledger, chapter 10)
FIBRE_US = 1.2 * gm.floor_us(D_KM * 1e3, "fibre")    # a fibre path 20% longer than the geodesic (chapter 13)
WET_KM = 10.0                                       # rain-cell width across a hop in the budget table
STORM = {"at_km": 600.0, "speed_km_min": 0.8, "radius_km": 15.0}


def geometry_rows():
    return [{"d_km": d, "f_ghz": f, "bulge_m": rl.bulge_m(d / 2, d / 2), "fresnel_m": rl.fresnel_m(d / 2, d / 2, f),
             "tower_m": rl.tower_m(d, f)} for d in (30, 50, 70) for f in (6, 11)]


def budget_rows(d_km=60.0):
    out = []
    for f in (6, 11, 18, 80):
        h = rl.Hop(d_km, f)
        out.append({"f_ghz": f, "gain_dbi": rl.dish_gain_dbi(h.dish_m, f), "fspl_db": rl.fspl_db(d_km, f),
                    "rx_dbm": rl.rx_dbm(h), "margin_db": rl.fade_margin_db(h), "rain_full": rl.critical_rain(h),
                    "rain_cell": rl.critical_rain(h, WET_KM)})
    return out


def critical_curve(lengths=range(5, 81, 5), freqs=(6, 11, 18)):
    return [(d, *(rl.critical_rain(rl.Hop(d, f), WET_KM) for f in freqs)) for d in lengths]


def route(hops=20):
    return rl.hop_lengths(rl.chain(A, B, hops), gm.geodesic_m)


def storm(f_ghz=11, peak=100.0):
    hops = [rl.Hop(d, f_ghz) for d in route()]
    return rl.storm_timeline(hops, rl.Storm(peak_mm_h=peak, **STORM), RADIO_US, FIBRE_US)


def minutes_on_fibre(f_ghz=11, peak=100.0):
    return sum(1 for _, down, _ in storm(f_ghz, peak) if down)


def exceed(r, p0=0.05, r0=4.0):
    """A labelled rain-rate exceedance model, P(R > r) = p0 exp(-r / r0): rain 5% of the time, mean 4 mm/h."""
    return p0 * math.exp(-r / r0)
