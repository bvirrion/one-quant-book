"""firm.portplan -- ports, links and handler cores for an options desk (build of One Quant Book 14, chapter 22).

The feed side reads the consolidated options feed's published capacity projection (data/opra_capacity.csv, dated
rows), turns messages into wire bits with firm.netsim's framing, and spreads a simulated busy minute over the feed's
96 lines: 1-ms bins whose aggregate is a slow log-AR(1) level times rare 1-ms spikes, the level's spread and the spikes'
size fitted to two published peak ratios, and whose line shares vary lognormally around equal (assumptions). Links
are sized on a planning percentile of each link's 1-ms rate; handler cores on the 10-ms peak, a queue absorbing the ms.
The order-entry side turns a quoting load into bulk-quote messages and ports, one message in flight per port on a
synchronous quoting interface (an assumption read from the venue's specification), a risk layer adding its latency to
every round trip. Everything simulated is labelled so in the book.

API (stable):
    Projection ; load_capacity(path) -> [Projection] ; projection(effective) -> Projection
    wire_bytes_per_msg(p) -> float            UDP framing added to the notice's bytes (conservative)
    burst(n_bins, sigma_s, spike, q=0.001, phi=0.999, sigma_w=0.1, seed=0) -> aggregate per 1-ms bin (mean 1)
    window_peak(x, k) -> max sum over k consecutive bins ; ratios(x) -> (1 ms / 10 ms, 10 ms / 100 ms) peak rates
    fit_burst(r1, r2, n_bins=60000, seed=0) -> (sigma_s, spike)
    line_split(agg, n_lines=96, sigma_i=0.5, seed=0) -> array (bins, lines), rows summing to agg
    links_needed(lines_gbps, pct, link_gbps=10.0, retrans=0.10) -> links for one stream (lines kept whole)
    cores_needed(peak_msgs_s, per_core=10e6)
    quotes_per_s(classes, series, updates, sides=2) ; port_msgs_per_s(rtt_us) ; ports_needed(...)
"""
import csv
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np
from scipy.signal import lfilter

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "netsim"))
import firm_netsim as ns  # noqa: E402

DATA = HERE / "data"
LINES = 96                 # OPRA's multicast lines since the 96-line expansion (networks/22:F2)
BULK_MAX = 50              # single-side quotes in one MIAX MEI Simple Bulk Quote message (networks/22:F5)
BULK_HDR, QUOTE_BYTES = 51, 15   # that message's header and per-quote bytes


@dataclass(frozen=True)
class Projection:
    effective: str
    msgs_100ms: float
    gbit_100ms: float
    packets_100ms: float
    msgs_10ms: float
    gbit_10ms: float
    packets_10ms: float
    msgs_day: float
    line_max_100ms: float


def load_capacity(path=DATA / "opra_capacity.csv"):
    with open(path) as f:
        return [Projection(r["effective"], float(r["msgs_100ms_m"]) * 1e6, float(r["gbit_100ms"]),
                           float(r["packets_100ms_k"]) * 1e3, float(r["msgs_10ms_m"]) * 1e6, float(r["gbit_10ms"]),
                           float(r["packets_10ms_k"]) * 1e3, float(r["msgs_day_bn"]) * 1e9,
                           float(r["line_max_100ms_k"]) * 1e3) for r in csv.DictReader(f)]


def projection(effective):
    return next(p for p in load_capacity() if p.effective == effective)


def wire_bytes_per_msg(p):
    """Treat the notice's bits as UDP payload and add Ethernet, IPv4, UDP and line overhead per packet."""
    payload = p.gbit_100ms * 1e9 / 8 / p.packets_100ms
    per_packet = p.msgs_100ms / p.packets_100ms
    return ns.wire_bytes(ns.frame_bytes(payload)) / per_packet


def burst(n_bins, sigma_s, spike, q=0.001, phi=0.999, sigma_w=0.1, seed=0):
    """Messages per 1-ms bin, mean 1: exp(slow + noise) * (1 + J); slow is a log-AR(1),
    s.d. sigma_s, persistence phi; J is spike * Exp(1) in a fraction q of bins, else 0."""
    rng = np.random.default_rng(seed)
    e = rng.standard_normal((2, n_bins))
    slow = lfilter([sigma_s * math.sqrt(1 - phi * phi)], [1, -phi], e[0])
    jump = (rng.random(n_bins) < q) * spike * rng.exponential(1.0, n_bins)
    x = np.exp(slow + sigma_w * e[1]) * (1 + jump)
    return x / x.mean()


def window_peak(x, k):
    c = np.concatenate(([0.0], np.cumsum(x)))
    return float(np.max(c[k:] - c[:-k]))


def ratios(x):
    p1, p10, p100 = window_peak(x, 1), window_peak(x, 10) / 10, window_peak(x, 100) / 100
    return p1 / p10, p10 / p100


def fit_burst(r1, r2, n_bins=60000, seed=0):
    """Grid fit of (sigma_s, spike) to the two peak-rate ratios, in log distance; other parameters as stated."""
    best = None
    for s in np.round(np.arange(0.02, 1.001, 0.02), 2):
        for a in np.arange(0.5, 10.001, 0.25):
            r = ratios(burst(n_bins, s, a, seed=seed))
            err = math.log(r[0] / r1) ** 2 + math.log(r[1] / r2) ** 2
            if best is None or err < best[0]:
                best = (err, float(s), float(a))
    return best[1], best[2]


def line_split(agg, n_lines=LINES, sigma_i=0.5, seed=0):
    rng = np.random.default_rng(seed + 1)
    w = np.exp(sigma_i * rng.standard_normal((len(agg), n_lines)))
    return agg[:, None] * w / w.sum(axis=1, keepdims=True)


def links_needed(lines_gbps, pct, link_gbps=10.0, retrans=0.10):
    """Fewest links, lines kept whole and packed in order, whose pct-th percentile 1-ms rate fits the link."""
    cap = link_gbps / (1 + retrans)
    n = lines_gbps.shape[1]
    for links in range(1, n + 1):
        groups = np.array_split(np.arange(n), links)
        if all(np.percentile(lines_gbps[:, g].sum(axis=1), pct) <= cap for g in groups):
            return links
    return math.inf


def cores_needed(peak_msgs_s, per_core=10e6):
    return math.ceil(peak_msgs_s / per_core)


def quotes_per_s(classes, series, updates, sides=2):
    return classes * series * updates * sides


def port_msgs_per_s(rtt_us):
    """One bulk message in flight per port: a port sends one message per round trip."""
    return 1e6 / rtt_us


def ports_needed(quotes_s, rtt_us, engines=1, per_msg=BULK_MAX, min_per_engine=1):
    msgs = quotes_s / per_msg / engines
    return engines * max(min_per_engine, math.ceil(msgs / port_msgs_per_s(rtt_us)))


def bulk_bytes(per_msg=BULK_MAX):
    return BULK_HDR + QUOTE_BYTES * per_msg
