"""Chapter 1 of One Quant Book 14: what a byte costs on the wire, and why averages hide bursts.

Everything here is arithmetic on published figures or a labelled simulation on firm.netsim:
    frame_table()            serialisation delay by frame size and line rate
    mold_example()           the frame carrying one 36-byte add-order message in a MoldUDP64 packet
    opra_curve()             OPRA's published peaks per window as rates (million messages per second)
    opra_capacity()          SIAC's capacity projection for July 2026, per stream, as rates and averages
    fanin(...)               eight bursty feeds into one 10 Gb/s egress port (simulation): drops by buffer size
    zero_loss_buffer(...)    the buffer that would have lost nothing (the maximum backlog), over seeds
    burst_queue(...)         the fluid bound: backlog = (sum of input rates - output rate) x burst length
"""
import csv
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "netsim"))
import firm_netsim as ns  # noqa: E402

RATES = (1, 10, 25, 100)                       # Gb/s
SIZES = (64, 128, 256, 512, 1024, 1518)        # frame bytes
ADD_ORDER = 36                                 # the simulator's (and ITCH's) add-order message, bytes
FEED_PPS = 400_000                             # simulation: packets a second per feed
SECONDS = 0.05


def frame_table():
    return {(f, r): ns.ser_ns(f, r) for f in SIZES for r in RATES}


def mold_example():
    payload = ns.mold_payload([ADD_ORDER])
    frame = ns.frame_bytes(payload)
    return {"payload": payload, "frame": frame, "wire": ns.wire_bytes(frame),
            "ns_10g": ns.ser_ns(frame, 10), "ns_25g": ns.ser_ns(frame, 25),
            "useful_share": ADD_ORDER / ns.wire_bytes(frame)}


def opra_curve():
    """{month: [(window_s, million messages per second)]} from data/networks/opra_metrics.csv."""
    out = {}
    with open(ROOT / "data" / "networks" / "opra_metrics.csv") as f:
        for row in csv.DictReader(f):
            out[row["month"]] = [(1.0, float(row["peak_1s_m"])), (0.1, float(row["peak_100ms_m"]) / 0.1),
                                 (0.01, float(row["peak_10ms_m"]) / 0.01), (0.001, float(row["peak_1ms_m"]) / 0.001)]
    return out


def opra_capacity():
    """SIAC, Revised OPRA Capacity Projections (15 September 2025), row 7/2026, one stream."""
    msgs_100, gbit_100, kpk_100 = 13.575e6, 4.403, 1564e3
    gbit_10, kpk_10 = 0.501, 169e3                     # 1.562 million messages per 10 ms
    return {"gbps_100ms": gbit_100 / 0.1, "gbps_10ms": gbit_10 / 0.01,
            "gbps_both_streams_10ms": 2 * gbit_10 / 0.01, "with_retx_10ms": 1.1 * gbit_10 / 0.01,
            "bytes_per_packet": gbit_100 * 1e9 / 8 / kpk_100, "msgs_per_packet": msgs_100 / kpk_100,
            "bytes_per_packet_10ms": gbit_10 * 1e9 / 8 / kpk_10,
            "links_10g_both": int(np.ceil(2 * 1.1 * gbit_10 / 0.01 / 10))}


def feed(seed, common, share, seconds=SECONDS, pps=FEED_PPS):
    """One simulated feed: clusters of packets; 1 to 30 add-order messages per packet."""
    t = ns.bursty_arrivals(pps, seconds, 8, 100, seed, common, share)
    k = np.minimum(np.random.default_rng(seed + 1000).geometric(1 / 3, len(t)), 30)
    frames = np.array([ns.frame_bytes(ns.mold_payload([ADD_ORDER] * int(x))) for x in k])
    return t, frames


def fanin_traffic(n_feeds=8, share=0.3, seed=1, seconds=SECONDS, event_hz=400):
    ev = ns.event_times(event_hz, seconds, 99 + seed)
    return ns.merge(*[feed(10 * seed + i, ev, share, seconds) for i in range(n_feeds)])


def fanin(buffers, n_feeds=8, share=0.3, seed=1, seconds=SECONDS, gbps=10.0):
    t, f, _ = fanin_traffic(n_feeds, share, seed, seconds)
    return [100.0 * ns.egress(t, f, gbps, b).n_dropped / len(t) for b in buffers]


def load_gbps(n_feeds=8, share=0.3, seed=1, seconds=SECONDS):
    t, f, _ = fanin_traffic(n_feeds, share, seed, seconds)
    return 8.0 * (f + ns.OVERHEAD).sum() / seconds / 1e9


def peak_by_window(windows_ns, n_feeds=8, share=0.3, seed=1, seconds=SECONDS):
    t, f, _ = fanin_traffic(n_feeds, share, seed, seconds)
    return [ns.peak_rate(t, f + ns.OVERHEAD, w)[1] / 1e9 for w in windows_ns]


def zero_loss_buffer(n_feeds=8, share=0.3, seeds=range(1, 21), seconds=SECONDS, gbps=10.0):
    out = []
    for s in seeds:
        t, f, _ = fanin_traffic(n_feeds, share, s, seconds)
        out.append(ns.egress(t, f, gbps, 1e12).max_backlog)
    return np.array(out)


def burst_queue(n_inputs, gbps_each, out_gbps, burst_s):
    """Fluid bound: bytes queued at the end of a burst in which n inputs each send at gbps_each."""
    return max(0.0, n_inputs * gbps_each - out_gbps) * 1e9 * burst_s / 8
