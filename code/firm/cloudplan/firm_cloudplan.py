"""firm.cloudplan -- zones, placements and their cost in a public cloud (build of One Quant Book 14, chapter 16).

Zone names are per account; zone identifiers are physical (ledger networks/16:F1). The resolver reads the response
of a describe-availability-zones call (fixtures in data/ have the documented shape and synthetic values) and maps
names to identifiers, so that two accounts can compare where their machines really are. The round-trip model is a
labelled simulation: lognormal round trips fitted to a published measurement's median and 99th percentile (F5), with
rare noisy-neighbour spikes on shared hosts. The catalogue holds dated list prices (F6); data moved between zones is
charged in each direction (F7).

API (stable):
    load_zones(path) -> {zone_name: zone_id} ; same_physical(a, b, name) ; locate(zones, zone_id) -> name
    p_same_name_same_zone(n) = 1/n ; expected_penalty_us(n, same_us, cross_us)
    RTT_PUBLISHED ; Rtt(median_us, p99_us, spike_p=0.0, spike_lo=5.0, spike_hi=50.0)
    sample_rtt(rtt, n, seed=0) -> numpy array of microseconds
    load_catalogue(path) -> {key: Instance} ; Instance(key, instance, vcpu, network_gbps, usd_hour, bare_metal, ...)
    monthly_cost(plan, catalogue, cross_zone_gb=0.0, hours=730, usd_per_gb_each_way=0.01)
"""
import csv
import json
import math
import pathlib
from dataclasses import dataclass

import numpy as np

DATA = pathlib.Path(__file__).resolve().parent / "data"
Z99 = 2.3263478740408408

# Published round trips between two m5.large VMs in one AWS US East region (networks/16:F5), microseconds.
RTT_PUBLISHED = {"same subnet": {"median": 270.0, "p99": 395.0, "p9999": 760.0},
                 "cross AZ": {"median": 555.0, "p99": 755.0, "p9999": 1905.0}}


def load_zones(path):
    with open(path) as f:
        doc = json.load(f)
    zones = [z for z in doc["AvailabilityZones"] if z.get("ZoneType") == "availability-zone"]
    return {z["ZoneName"]: z["ZoneId"] for z in zones}


def same_physical(zones_a, zones_b, name):
    return zones_a[name] == zones_b[name]


def locate(zones, zone_id):
    """The name under which this account sees a physical zone."""
    return next(n for n, i in zones.items() if i == zone_id)


def p_same_name_same_zone(n):
    """Names shuffled independently per account over n zones: P(same name, same zone)."""
    return 1.0 / n


def expected_penalty_us(n, same_us, cross_us):
    return (1 - p_same_name_same_zone(n)) * (cross_us - same_us)


@dataclass(frozen=True)
class Rtt:
    median_us: float
    p99_us: float
    spike_p: float = 0.0        # probability that a round trip hits a noisy neighbour
    spike_lo: float = 5.0       # spike multiplies the round trip by U(spike_lo, spike_hi)
    spike_hi: float = 50.0


def sample_rtt(rtt, n, seed=0):
    rng = np.random.default_rng(seed)
    sigma = math.log(rtt.p99_us / rtt.median_us) / Z99
    x = rtt.median_us * np.exp(rng.normal(0.0, sigma, n))
    hit = rng.random(n) < rtt.spike_p
    x[hit] *= rng.uniform(rtt.spike_lo, rtt.spike_hi, hit.sum())
    return x


@dataclass(frozen=True)
class Instance:
    key: str
    instance: str
    vcpu: int
    network_gbps: float
    usd_hour: float
    bare_metal: bool
    region: str
    source: str
    as_of: str


def load_catalogue(path=DATA / "instances.csv"):
    with open(path) as f:
        return {r["key"]: Instance(r["key"], r["instance"], int(r["vcpu"]), float(r["network_gbps"]),
                                   float(r["usd_hour"]), r["bare_metal"] == "1", r["region"], r["source"], r["as_of"])
                for r in csv.DictReader(f)}


def monthly_cost(plan, catalogue, cross_zone_gb=0.0, hours=730.0, usd_per_gb_each_way=0.01):
    """plan: [(instance key, count)]. Instances by the hour, plus cross-zone data charged out of one zone and into
    the other."""
    compute = sum(catalogue[k].usd_hour * n * hours for k, n in plan)
    transfer = 2 * usd_per_gb_each_way * cross_zone_gb
    return {"compute": compute, "transfer": transfer, "total": compute + transfer}
