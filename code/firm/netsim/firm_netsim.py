"""firm.netsim -- a packet network model (build of One Quant Book 14, chapter 1).

Frames, links, egress queues with finite buffers, store-and-forward and cut-through forwarding, multicast
replication with or without IGMP snooping, and bursty synthetic traffic. Times are integer nanoseconds, sizes
bytes, rates Gb/s (1 Gb/s = one bit per nanosecond). Deterministic: every random draw comes from a seeded
numpy Generator. The egress queue has a C++20 twin (cpp/firm_netsim.hpp) that reproduces data/fixture_*.csv.

Wire accounting (IEEE 802.3): a frame of F bytes (destination address to frame check sequence, 64 to 1518
without a VLAN tag) occupies F + 20 bytes of line time: 8 of preamble and start delimiter, 12 of inter-frame gap.

API (stable):
    OVERHEAD, ETH, FCS, IPV4, UDP, TCP, VLAN, MIN_FRAME, MAX_FRAME, MOLD_HDR     byte counts
    frame_bytes(payload, l4="udp", vlan=False) -> int     Ethernet frame carrying an L4 payload (padded to 64)
    mold_payload(msg_lengths) -> int                      MoldUDP64 packet: 20-byte header + (2 + len) per message
    wire_bytes(frame) -> int ; ser_ns(frame, gbps) -> float    line time of a frame
    prop_ns(length_m, n_g=1.462) -> float                 propagation delay in a medium of group index n_g
    mcast_mac(ip) -> str                                  RFC 1112 group address to Ethernet address mapping
    peak_rate(t_ns, nbytes, window_ns) -> (packets/s, bits/s)   busiest window (sliding, exact)
    bursty_arrivals(rate_pps, seconds, cluster_mean, gap_ns, seed, common=None, common_share=0.0) -> int64 ns
    event_times(rate_hz, seconds, seed) -> int64 ns       common market events (Poisson)
    egress(t_ns, frames, gbps, buffer_bytes) -> Egress    tail-drop FIFO at an output port
    Egress: depart_ns (last bit on the wire; -1 if dropped), dropped (bool), backlog (bytes found at arrival),
            max_backlog, n_dropped, dropped_bytes
    forward_ns(frame, gbps_in, mode, fabric_ns, header=64) -> float   first bit in to first bit leaving the fabric
    replicate(groups, members, n_ports, snooping=True) -> list[np.ndarray]   packet indices each port must send
    merge(*streams) -> (t_ns, frames, source)             time-ordered merge of (t_ns, frames) streams
"""
import ipaddress

import numpy as np

C0 = 299_792_458.0
OVERHEAD = 20          # preamble + start delimiter (8) + inter-frame gap (12)
ETH, FCS, VLAN = 14, 4, 4
IPV4, UDP, TCP = 20, 8, 20
MIN_FRAME, MAX_FRAME = 64, 1518
MOLD_HDR = 20          # session 10 + sequence number 8 + message count 2


def frame_bytes(payload, l4="udp", vlan=False):
    l4h = UDP if l4 == "udp" else TCP
    return max(MIN_FRAME, ETH + (VLAN if vlan else 0) + IPV4 + l4h + int(payload) + FCS)


def mold_payload(msg_lengths):
    return MOLD_HDR + sum(2 + int(n) for n in msg_lengths)


def wire_bytes(frame):
    return int(frame) + OVERHEAD


def ser_ns(frame, gbps):
    return 8.0 * wire_bytes(frame) / gbps


def prop_ns(length_m, n_g=1.462):
    return length_m * n_g / C0 * 1e9


def mcast_mac(ip):
    a = int(ipaddress.IPv4Address(ip))
    if a >> 28 != 0xE:
        raise ValueError("not an IPv4 multicast address")
    low = a & 0x7FFFFF
    return f"01:00:5e:{low >> 16:02x}:{(low >> 8) & 0xFF:02x}:{low & 0xFF:02x}"


def peak_rate(t_ns, nbytes, window_ns):
    """Busiest window of length window_ns starting at any packet: (packets per second, bits per second)."""
    t = np.asarray(t_ns, dtype=np.int64)
    b = np.cumsum(np.concatenate(([0], np.asarray(nbytes, dtype=np.int64))))
    j = np.searchsorted(t, t + window_ns, side="left")      # packets in [t_i, t_i + w)
    n = j - np.arange(len(t))
    k = int(np.argmax(n))
    by = int(np.max(b[j] - b[:-1]))
    return n[k] * 1e9 / window_ns, 8 * by * 1e9 / window_ns


def event_times(rate_hz, seconds, seed):
    rng = np.random.default_rng(seed)
    n = rng.poisson(rate_hz * seconds)
    return np.sort(rng.integers(0, int(seconds * 1e9), n)).astype(np.int64)


def bursty_arrivals(rate_pps, seconds, cluster_mean, gap_ns, seed, common=None, common_share=0.0):
    """Packets in clusters. Own clusters start at Poisson times, hold a geometric number of packets of mean
    `cluster_mean`, spaced by exponential gaps of mean `gap_ns`. If `common` event times are given, a share
    `common_share` of the packets instead comes in one cluster per common event (the same events drive every
    feed built on them: a market event that moves every instrument at once), of mean size
    common_share * rate_pps * seconds / len(common). The long-run rate is rate_pps."""
    rng = np.random.default_rng(seed)
    total = rate_pps * seconds
    n_own = rng.poisson(total * (1 - common_share) / cluster_mean)
    starts = rng.integers(0, int(seconds * 1e9), n_own).astype(np.int64)
    sizes = rng.geometric(1.0 / cluster_mean, n_own)
    if common is not None and common_share > 0 and len(common):
        m = max(1.0, common_share * total / len(common))
        starts = np.concatenate((starts, np.asarray(common, dtype=np.int64)))
        sizes = np.concatenate((sizes, rng.geometric(1.0 / m, len(common))))
    offs = rng.exponential(gap_ns, int(sizes.sum()))
    idx = np.repeat(np.arange(len(starts)), sizes)
    first = np.concatenate(([0], np.cumsum(sizes)[:-1]))
    offs[first] = 0.0
    cum = np.cumsum(offs)
    cum -= np.repeat(cum[first], sizes)                       # restart the cumulative gap in each cluster
    t = starts[idx] + cum.astype(np.int64)
    t = t[t < int(seconds * 1e9)]
    return np.sort(t)


class Egress:
    __slots__ = ("depart_ns", "dropped", "backlog", "max_backlog", "n_dropped", "dropped_bytes")


def egress(t_ns, frames, gbps, buffer_bytes):
    """Tail-drop FIFO: an arriving frame is dropped if the bytes waiting (wire bytes, including the frame in
    service) plus its own exceed the buffer. The backlog drains at the line rate between arrivals."""
    t = np.asarray(t_ns, dtype=np.int64)
    w = np.asarray(frames, dtype=np.int64) + OVERHEAD
    n = len(t)
    dep = np.full(n, -1.0)
    drop = np.zeros(n, dtype=bool)
    back = np.zeros(n)
    rate = gbps / 8.0                                         # bytes per ns
    q, prev, mx, nd, db = 0.0, 0, 0.0, 0, 0
    tl, wl = t.tolist(), w.tolist()
    for i in range(n):
        ti, wi = tl[i], wl[i]
        q = max(0.0, q - (ti - prev) * rate)
        prev = ti
        back[i] = q
        if q + wi > buffer_bytes:
            drop[i] = True
            nd += 1
            db += wi
            continue
        q += wi
        mx = max(mx, q)
        dep[i] = ti + q / rate
    r = Egress()
    r.depart_ns, r.dropped, r.backlog, r.max_backlog, r.n_dropped, r.dropped_bytes = dep, drop, back, mx, nd, db
    return r


def forward_ns(frame, gbps_in, mode, fabric_ns, header=64):
    """Latency from the first bit entering the switch to the first bit leaving it, egress idle.
    store-and-forward waits for the whole frame; cut-through only for `header` bytes (the lookup fields)."""
    if mode == "store-and-forward":
        return 8.0 * frame / gbps_in + fabric_ns
    if mode == "cut-through":
        return 8.0 * min(header, frame) / gbps_in + fabric_ns
    if mode == "layer-1":
        return float(fabric_ns)
    raise ValueError(mode)


def replicate(groups, members, n_ports, snooping=True):
    """groups: group id of each packet; members: {port: set(groups)}. With snooping a port gets only the
    groups it joined; without, every multicast packet is flooded to every port."""
    g = np.asarray(groups)
    out = []
    for p in range(n_ports):
        if snooping:
            out.append(np.flatnonzero(np.isin(g, sorted(members.get(p, ())))))
        else:
            out.append(np.arange(len(g)))
    return out


def merge(*streams):
    t = np.concatenate([np.asarray(s[0], dtype=np.int64) for s in streams])
    f = np.concatenate([np.asarray(s[1], dtype=np.int64) for s in streams])
    src = np.concatenate([np.full(len(s[0]), i) for i, s in enumerate(streams)])
    o = np.argsort(t, kind="stable")
    return t[o], f[o], src[o]
