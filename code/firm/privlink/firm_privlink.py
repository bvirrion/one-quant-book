"""firm.privlink -- private paths from a firm's cloud machines to a venue (build of One Quant Book 14, chapter 18).

A venue's documented connectivity options are data (data/paths.csv, each row with its ledger rows and date): VPC
peering (optionally inside a shared cluster placement group), a private endpoint in the firm's zone or served from
another zone, and the public endpoint through an edge network. Each path's round trip is firm.cloudplan's model for
its body (cluster, same zone, cross zone) plus the extra hops the documentation names, whose times are assumptions;
its cost is endpoint-hours, data processed and cross-zone transfer. A zone-alignment check compares the endpoint's
zone identifiers with the instance's.

API (stable):
    Path(key, kind, rtt_body, extra_hop_us, edge_ms, usd_hour, usd_per_gb, cross_zone_gb_each_way, source, as_of)
    load_paths(path) -> {key: Path} ; BODIES
    rtt_percentiles(path, qs=(50, 99), n=200000, seed=0) -> {q: us}
    aligned(instance_zone_id, endpoint_zone_ids) -> bool
    cost_per_million(path, bytes_per_message=400) -> usd ; monthly_fixed(path, zones=1, hours=730) -> usd
"""
import csv
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "cloudplan"))
import firm_cloudplan as cp  # noqa: E402

DATA = HERE / "data" / "paths.csv"
PUB = cp.RTT_PUBLISHED
BODIES = {
    # the AWS blog's "sub-150 us intra-Region" taken as the median in a shared cluster group (an assumption)
    "cluster": cp.Rtt(150.0, 150.0 * PUB["same subnet"]["p99"] / PUB["same subnet"]["median"], 0.0005, 1.5, 3.0),
    "same zone": cp.Rtt(PUB["same subnet"]["median"], PUB["same subnet"]["p99"], 0.0005, 1.5, 3.0),
    "cross zone": cp.Rtt(PUB["cross AZ"]["median"], PUB["cross AZ"]["p99"], 0.0003, 2.0, 4.0),
}


@dataclass(frozen=True)
class Path:
    key: str
    kind: str
    rtt_body: str
    extra_hop_us: float
    edge_ms: float
    usd_hour: float
    usd_per_gb: float
    cross_zone_gb_each_way: float
    source: str
    as_of: str


def load_paths(path=DATA):
    with open(path) as f:
        return {r["key"]: Path(r["key"], r["kind"], r["rtt_body"], float(r["extra_hop_us"]), float(r["edge_ms"]),
                               float(r["usd_hour"]), float(r["usd_per_gb"]), float(r["cross_zone_gb_each_way"]),
                               r["source"], r["as_of"]) for r in csv.DictReader(f)}


def rtt_percentiles(path, qs=(50, 99), n=200_000, seed=0):
    x = cp.sample_rtt(BODIES[path.rtt_body], n, seed) + path.extra_hop_us + 1000.0 * path.edge_ms
    return {q: float(np.percentile(x, q)) for q in qs}


def aligned(instance_zone_id, endpoint_zone_ids):
    """True when the endpoint has a network interface in the instance's physical zone."""
    return instance_zone_id in set(endpoint_zone_ids)


def cost_per_million(path, bytes_per_message=400):
    """Data processed by the endpoint plus cross-zone transfer (out of one zone, into the other), per million
    messages of `bytes_per_message` (request and response together)."""
    gb = 1e6 * bytes_per_message / 1e9
    return gb * path.usd_per_gb + gb * 2 * path.cross_zone_gb_each_way


def monthly_fixed(path, zones=1, hours=730.0):
    return path.usd_hour * zones * hours
