"""Chapter 12 of One Quant Book 14: the Asia-Pacific map and the dissemination model (firm.geomap, firm.dissem).

    PAIRS, pair_rows()       distances and one-way floors between the Asia-Pacific sites
    TOPOLOGY                 a labelled simulation's topology: four primary servers of three ports of ten members,
                             and a lightly loaded secondary server (the shape SEBI's 2019 order describes)
    scenarios()              unicast, unicast with a randomiser, multicast: fairness, rank stability, race odds
    rank_curve(ticks)        mean receive delay by login rank on port 0 of each server, unicast
    first_vs_median(m)       the first member's advantage over the median member for m members per port
    map_points()             projected coordinates for the TikZ map
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "geomap"))
sys.path.insert(0, str(ROOT / "code" / "firm" / "dissem"))
import firm_dissem as fd  # noqa: E402
import firm_geomap as gm  # noqa: E402

SITES_CSV = ROOT / "data" / "networks" / "sites.csv"
ASIA = ["tokyo", "tko", "singapore", "alc", "bkc"]
PAIRS = [("tokyo", "tko"), ("tko", "singapore"), ("tokyo", "singapore"), ("singapore", "alc"), ("tokyo", "alc"),
         ("singapore", "bkc"), ("tko", "bkc"), ("tokyo", "bkc")]
PARAMS = {"c_centre": 5.0, "c_send": 10.0, "jitter": 1.0}      # microseconds; assumptions, not measurements


def topology(m=10, servers=4, ports=3, secondary=2):
    s = [fd.Server(f"server {k + 1}", (m,) * ports) for k in range(servers)]
    return s + [fd.Server("secondary", (secondary,) * ports)]


TOPOLOGY = topology()


def sites():
    return {s.id: s for s in gm.load_sites(SITES_CSV)}


def pair_rows():
    t = sites()
    out = []
    for a, b in PAIRS:
        d = gm.geodesic_m(t[a].lat, t[a].lon, t[b].lat, t[b].lon)
        out.append({"a": a, "b": b, "km": d / 1e3, "vacuum_us": gm.floor_us(d), "fibre_us": gm.floor_us(d, "fibre")})
    return out


def _first_and_median(times):
    order = sorted(times, key=times.get)
    return order[0], order[len(order) // 2]


PRIMARY_ONLY = [s for s in TOPOLOGY if s.name != "secondary"]
DESIGNS = [("unicast", "u", False, TOPOLOGY), ("unicast, randomised", "u", True, TOPOLOGY),
           ("unicast, randomised, no secondary", "u", True, PRIMARY_ONLY), ("multicast", "m", False, TOPOLOGY)]


def _tick(kind, shuffle, rng, topo=TOPOLOGY):
    if kind == "u":
        return fd.unicast_us(topo, rng=rng, shuffle=shuffle, **PARAMS)
    return fd.multicast_us(topo, c_send=PARAMS["c_send"], jitter=PARAMS["jitter"], rng=rng)


def scenarios(seed=1, ticks=200):
    """For each design: one tick's fairness measures, the rank stability over ticks, and how often the member who
    was first on the first tick beats the member who was median on it, over the following ticks (reaction model of
    firm.dissem.race_win)."""
    out = {}
    for name, kind, shuffle, topo in DESIGNS:
        rng = np.random.default_rng(seed)
        t0 = _tick(kind, shuffle, rng, topo)
        a, b = _first_and_median(t0)
        wins = [fd.race_win(_tick(kind, shuffle, rng, topo), a, b, n=200, seed=k) for k in range(ticks)]
        stab = fd.rank_stability(topo, seed=seed, shuffle=shuffle, **PARAMS) if kind == "u" else None
        out[name] = {**fd.fairness(t0), "stability": stab, "win_first": float(np.mean(wins))}
    return out


def rank_curve(ticks=200, seed=2):
    rng = np.random.default_rng(seed)
    acc = {}
    for _ in range(ticks):
        for mem, us in fd.unicast_us(TOPOLOGY, rng=rng, **PARAMS).items():
            if mem.port == 0:
                acc.setdefault((mem.server, mem.rank), []).append(us)
    return {k: float(np.mean(v)) for k, v in acc.items()}


def first_vs_median(m, ticks=200, seed=3):
    topo = topology(m)
    rng = np.random.default_rng(seed)
    return float(np.mean([fd.fairness(fd.unicast_us(topo, rng=rng, **PARAMS))["first_vs_median"]
                          for _ in range(ticks)]))


def map_points():
    t = sites()
    xy = gm.project([t[i] for i in ASIA], 5.0, 120.0)
    return [(i, *xy[i]) for i in ASIA]
