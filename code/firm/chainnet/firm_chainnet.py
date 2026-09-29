"""firm.chainnet -- how a transaction travels on a blockchain's network, and where to send it (build of One Quant Book
14, chapter 21).

A peer graph places nodes at cities (firm.geomap) and joins each to random peers; a link's one-way delay is the fibre
floor times a route factor plus a per-hop processing time (assumptions of the model). Gossip spreads a transaction by
flooding (every node forwards to every peer on first receipt) or by square-root fan-out (a node pushes it to sqrt(d)
peers and announces it to the others, who pull it one round trip later). A leader-aware chooser sends a transaction
to the published block-engine region nearest the next leader (data/block_engines.csv, dated rows) instead of a fixed
region. All timings are a labelled simulation.

API (stable):
    Graph(cities, peers, factor=1.5, hop_ms=5.0, seed=0)   .n, .edges {(i, j): ms}
    spread(graph, source, mode="flood"|"sqrt") -> arrival ms per node
    reach_time(arrivals, share) -> ms by which `share` of the nodes have it
    load_engines(path) -> [Engine] ; one_way_ms(a, b, factor=1.5)
    choose_engine(engines, leader_city) -> Engine (nearest to the leader)
    timely(send_city, engine, leader_city, deadline_ms, factor=1.5, engine_ms=1.0) -> bool
"""
import csv
import heapq
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "geomap"))
import firm_geomap as gm  # noqa: E402

DATA = HERE / "data" / "block_engines.csv"


def one_way_ms(a, b, factor=1.5):
    """a, b: (lat, lon). The fibre floor times a route factor, in milliseconds."""
    return gm.floor_us(gm.geodesic_m(a[0], a[1], b[0], b[1]), "fibre") * factor / 1000.0


class Graph:
    def __init__(self, cities, peers, factor=1.5, hop_ms=5.0, seed=0):
        """cities: list of (lat, lon), one per node; each node dials `peers` random others (links are both ways)."""
        rng = np.random.default_rng(seed)
        self.n, self.pos, self.hop_ms = len(cities), list(cities), hop_ms
        self.adj = {i: set() for i in range(self.n)}
        for i in range(self.n):
            for j in rng.choice([k for k in range(self.n) if k != i], size=peers, replace=False):
                self.adj[i].add(int(j))
                self.adj[int(j)].add(i)
        self.edges = {(i, j): one_way_ms(self.pos[i], self.pos[j], factor) + hop_ms
                      for i in self.adj for j in self.adj[i]}


def spread(graph, source, mode="flood"):
    """Earliest arrival at every node (Dijkstra). In 'sqrt' mode a node pushes to ceil(sqrt(d))
    peers; the others are announced to and pull, one extra round trip on that link."""
    best = [math.inf] * graph.n
    best[source] = 0.0
    heap = [(0.0, source)]
    while heap:
        t, i = heapq.heappop(heap)
        if t > best[i]:
            continue
        peers = sorted(graph.adj[i])
        push = set(peers[:math.ceil(math.sqrt(len(peers)))]) if mode == "sqrt" else set(peers)
        for j in peers:
            d = graph.edges[(i, j)] + (0.0 if j in push else 2 * graph.edges[(i, j)])
            if t + d < best[j]:
                best[j] = t + d
                heapq.heappush(heap, (t + d, j))
    return best


def reach_time(arrivals, share):
    return float(np.quantile(np.asarray(arrivals), share))


@dataclass(frozen=True)
class Engine:
    region: str
    city: str
    lat: float
    lon: float
    endpoint: str
    source: str
    as_of: str


def load_engines(path=DATA):
    with open(path) as f:
        return [Engine(r["region"], r["city"], float(r["lat"]), float(r["lon"]), r["endpoint"], r["source"],
                       r["as_of"]) for r in csv.DictReader(f)]


def choose_engine(engines, leader_city):
    return min(engines, key=lambda e: gm.geodesic_m(e.lat, e.lon, *leader_city))


def timely(send_city, engine, leader_city, deadline_ms, factor=1.5, engine_ms=1.0):
    """The transaction reaches the leader through the engine before the deadline."""
    e = (engine.lat, engine.lon)
    t = one_way_ms(send_city, e, factor) + engine_ms + one_way_ms(e, leader_city, factor)
    return t <= deadline_ms
