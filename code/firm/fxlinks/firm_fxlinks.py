"""firm.fxlinks -- FX connectivity: sites, streams, staleness and last look (build of One Quant Book 14, chapter 24).

FX venues match each currency pair at one site and stream or aggregate prices at several (data/fx_venues.csv, dated
rows; site coordinates in data/networks/sites.csv). A liquidity provider (LP) at one site learns of a price move at
its origin over an information path, prices it, and streams the quote to each venue site over a streaming path; a
taker at the venue learns of the same move over its own path. The quote's staleness at the venue is the LP's lag
minus the taker's. A trade request travels back to the LP; the hold before the LP's price check that would let the
LP know what the taker knew is the LP's lag minus the taker's lag and the request's travel. Paths are the fibre floor
times a stated route factor; jitter is exponential with a stated mean (assumptions); results are labelled a model.

API (stable):
    Venue ; load_venues(path) ; sites(path) -> {id: firm_geomap.Site}
    one_way_ms(a, b, factor, table) -> fibre floor times factor between two site ids (0 at the same site)
    Paths(info=1.5, stream=1.5, taker=1.5, request=1.5, proc_ms=0.1)   route factors and the LP's processing
    staleness_ms(origin, lp, venue, paths, table) ; hold_ms(origin, lp, venue, paths, table)
    caught(origin, lp, venue, paths, holds, jitter_ms=0.5, n=20000, seed=0, table=None) -> share of informed
        requests whose price check, after each hold, already reflects the move
    stale_window_ms(lags) -> how long each quote stays stale after a move (lag minus the smallest lag)
    order_path_ms(send, engine, stages_ms, factor, table) -> network one way plus the order path's stages
"""
import csv
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "geomap"))
import firm_geomap as gm  # noqa: E402

SITES = ROOT / "data" / "networks" / "sites.csv"


@dataclass(frozen=True)
class Venue:
    name: str
    site: str
    role: str
    instruments: str
    source: str
    as_of: str


def load_venues(path=HERE / "data" / "fx_venues.csv"):
    with open(path) as f:
        return [Venue(r["venue"], r["site"], r["role"], r["instruments"], r["source"], r["as_of"])
                for r in csv.DictReader(f)]


def sites(path=SITES):
    return {s.id: s for s in gm.load_sites(path)}


def one_way_ms(a, b, factor, table):
    if a == b:
        return 0.0
    s, t = table[a], table[b]
    return gm.floor_us(gm.geodesic_m(s.lat, s.lon, t.lat, t.lon), "fibre") * factor / 1000.0


@dataclass(frozen=True)
class Paths:
    info: float = 1.5       # origin to the LP: how the LP learns of a move
    stream: float = 1.5     # LP to the venue: its quote stream
    taker: float = 1.5      # origin to the venue: how the taker learns of the move
    request: float = 1.5    # venue to the LP: the trade request
    proc_ms: float = 0.1    # the LP's pricing time


def staleness_ms(origin, lp, venue, paths, table):
    lp_lag = one_way_ms(origin, lp, paths.info, table) + paths.proc_ms
    lp_lag += one_way_ms(lp, venue, paths.stream, table)
    return lp_lag - one_way_ms(origin, venue, paths.taker, table)


def hold_ms(origin, lp, venue, paths, table):
    knows = one_way_ms(origin, lp, paths.info, table) + paths.proc_ms
    arrives = one_way_ms(origin, venue, paths.taker, table)
    arrives += one_way_ms(venue, lp, paths.request, table)
    return max(0.0, knows - arrives)


def caught(origin, lp, venue, paths, holds, jitter_ms=0.5, n=20000, seed=0, table=None):
    """Each leg gets exponential jitter; a request is caught if the LP knows of the move when its hold ends."""
    table = table or sites()
    rng = np.random.default_rng(seed)
    j = rng.exponential(jitter_ms, (3, n))
    knows = one_way_ms(origin, lp, paths.info, table) + paths.proc_ms + j[0]
    arrives = one_way_ms(origin, venue, paths.taker, table) + j[1] + one_way_ms(venue, lp, paths.request, table) + j[2]
    return [float(np.mean(knows <= arrives + h)) for h in holds]


def stale_window_ms(lags):
    m = min(lags.values())
    return {k: v - m for k, v in lags.items()}


def order_path_ms(send, engine, stages_ms, factor, table):
    return one_way_ms(send, engine, factor, table) + sum(stages_ms.values())
