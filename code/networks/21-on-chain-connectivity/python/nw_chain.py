"""Chapter 21 of One Quant Book 14: gossip, block engines and the leader schedule (firm.chainnet, labelled simulation).

    ENGINES, NODES               published block-engine regions; 600 nodes spread evenly over those eight cities
    propagation()                time for a transaction from Tokyo to reach half and nine-tenths of the nodes, flooding
                                 against square-root fan-out
    to_leader(leader_city)       arrival at a leader in a city: through the gossip graph from a public node in Tokyo,
                                 against directly through the block engine nearest the leader
    timely_rates(deadlines)      the share of leaders reached in time, over all cities and deadlines
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "chainnet"))
import firm_chainnet as cn  # noqa: E402

ENGINES = cn.load_engines()
CITIES = {e.region: (e.lat, e.lon) for e in ENGINES}
N_NODES, PEERS, SEED = 600, 8, 1
NODE_CITY = [ENGINES[i % len(ENGINES)].region for i in range(N_NODES)]
GRAPH = cn.Graph([CITIES[c] for c in NODE_CITY], PEERS, seed=SEED)
SOURCE = NODE_CITY.index("tokyo")
ENGINE_MS = 1.0


def propagation():
    out = {}
    for mode in ("flood", "sqrt"):
        a = cn.spread(GRAPH, SOURCE, mode)
        out[mode] = (cn.reach_time(a, 0.5), cn.reach_time(a, 0.9))
    return out


def to_leader(leader_city, mode="flood"):
    """Median over the leader city's nodes of the gossip arrival, and the direct path through the nearest engine."""
    a = cn.spread(GRAPH, SOURCE, mode)
    gossip = float(np.median([a[i] for i, c in enumerate(NODE_CITY) if c == leader_city]))
    e = cn.choose_engine(ENGINES, CITIES[leader_city])
    at = (e.lat, e.lon)
    leg = cn.one_way_ms
    direct = leg(CITIES["tokyo"], at) + ENGINE_MS + leg(at, CITIES[leader_city])
    return {"gossip": gossip, "direct": direct, "engine": e.region}


DEADLINES = tuple(range(0, 151, 5))


def timely_rates(deadlines=DEADLINES):
    rows = []
    legs = {c: to_leader(c) for c in CITIES}
    for d in deadlines:
        g = np.mean([legs[c]["gossip"] <= d for c in CITIES])
        x = np.mean([legs[c]["direct"] <= d for c in CITIES])
        rows.append((int(d), float(g), float(x)))
    return rows


def mean_timely(horizon_ms=300.0):
    """Share of (leader city, deadline) pairs reached in time, deadlines uniform on [0, horizon_ms]."""
    legs = [to_leader(c) for c in CITIES]
    g = np.mean([max(0.0, 1 - x["gossip"] / horizon_ms) for x in legs])
    d = np.mean([max(0.0, 1 - x["direct"] / horizon_ms) for x in legs])
    return float(g), float(d)
