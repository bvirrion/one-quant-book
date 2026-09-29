"""Chapter 17 of One Quant Book 14: finding a cloud-hosted venue and getting close to it (firm.venuefind).

    RANGES, lookups()          endpoint addresses (documentation ranges) matched against the IP-range fixture
    TRUE, PROBES, triangulate_example()   a labelled simulation: probes at four Asia-Pacific sites and a hidden server
    LOTTERY, lottery_curve()   expected best round trip among n launches (labelled model)
    VALUE, LAUNCH, best()      the launches that maximise value net of their cost (assumed value and cost)
    drift_example()            a venue moves: daily medians and the day Book 7's CUSUM test flags it
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "venuefind"))
import firm_venuefind as vf  # noqa: E402

gm = vf.gm
SITES = {s.id: s for s in gm.load_sites(ROOT / "data" / "networks" / "sites.csv")}
RANGES = vf.load_ranges()
ENDPOINTS = ["192.0.2.200", "198.51.100.7", "203.0.113.9", "2001:db8:1abc::1"]
TRUE = (SITES["tokyo"].lat, SITES["tokyo"].lon)          # where the simulated server really is
PROBE_SITES = ["tko", "singapore", "alc", "bkc"]
FACTOR = 1.3                                             # assumed route factor of the probes' paths
LOTTERY = vf.Lottery(median_us=270.0, p01_us=150.0)      # assumed spread of launches (see text)
VALUE = 100.0                                            # USD a month per microsecond saved (assumption)
LAUNCH = 24 * 0.714                                      # one c7i.4xlarge for a day of measurement (chapter 16)


def lookups():
    return {a: vf.match(RANGES, a) for a in ENDPOINTS}


def probes(seed=0, noise_us=200.0):
    rng = np.random.default_rng(seed)
    out = []
    for s in PROBE_SITES:
        d = gm.geodesic_m(SITES[s].lat, SITES[s].lon, *TRUE)
        rtt = 2 * FACTOR * gm.floor_us(d, "fibre") + abs(rng.normal(0, noise_us))
        out.append((SITES[s].lat, SITES[s].lon, rtt))
    return out


def triangulate_example(seed=0):
    p = probes(seed)
    lat, lon, rms = vf.triangulate(p, 35.0, 135.0, span_deg=8.0, step_deg=0.1, factor=FACTOR)
    err = gm.geodesic_m(lat, lon, *TRUE) / 1e3
    return {"probes": p, "estimate": (lat, lon), "rms_km": rms, "error_km": err}


def lottery_curve(ns=(1, 2, 5, 10, 20, 40, 80, 160)):
    return [(n, vf.expected_best(LOTTERY, n)) for n in ns]


def best():
    return vf.best_n(LOTTERY, VALUE, LAUNCH, n_max=150)


def drift_example(seed=3):
    rng = np.random.default_rng(seed)
    x = np.r_[rng.normal(160.0, 6.0, 60), rng.normal(185.0, 6.0, 30)]
    return x, vf.moved(x)
