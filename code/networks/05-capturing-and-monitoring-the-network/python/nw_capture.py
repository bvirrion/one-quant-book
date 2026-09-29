"""Chapter 5 of One Quant Book 14: measuring the firm's own traffic from captures.

A simulated trading session in chapter 2's layer-1 cage: the venue's feed on lines A and B (with independent loss),
a strategy that answers some packets with an order, and taps on the feed handoffs and the order handoff that
timestamp every frame. The orders' timing is drawn from firm.wirepath: the cage's network (firm.cagenet), the card's
receive and transmit paths (model values), and Book 13's measured software stages. The capture is written as a
nanosecond pcap with timestamp trailers and analysed as a capture appliance would analyse it.

    stages()                   the wire-to-wire budget's stages
    budget_rows()              per-stage and wire-to-wire medians and 99th percentiles (firm.wirepath.report)
    stages(speed, card)        the stages, card and software divided by `speed` (and the card's by `card`)
    session(seconds, seed, speed) -> (records, truth): capture records (t_ns, frame) and the orders' true triggers
    analyse(records)           -> dict(w2w, nearest_wrong, gaps_a, gaps_b, both, n_orders, n_packets,
                                       peak_100us_gbps, mean_gbps)
"""
import pathlib
import struct
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("netsim", "cagenet", "wirepath", "wirecap"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
sys.path.insert(0, str(ROOT / "code" / "networks" / "02-switches-and-layer-1-devices" / "python"))
import firm_netsim as ns  # noqa: E402
import firm_wirecap as wc  # noqa: E402
import firm_wirepath as wp  # noqa: E402
import nw_cage  # noqa: E402

CARD = dict(rx_p50=800.0, rx_p99=2000.0, tx_p50=800.0, tx_p99=2000.0)      # model values, ns
OPEN = 34_200 * 1_000_000_000
PPS, P_TRIGGER, P_ORDER, LOSS, B_LAG = 100_000, 0.15, 0.3, 0.002, 3_000


def stages(speed=1.0, card=1.0):
    """The path's stages; `speed` divides every card and software stage, `card` divides the card's only."""
    cage = nw_cage.design("layer-1")
    wire = wp.wire_stages(cage, cage.path("A", "s1"), cage.path("s1", "O"))
    cards = [wp.Stage(x.name, x.p50_ns / speed / card, x.p99_ns / speed / card, x.kind) for x in wp.card_stages(**CARD)]
    soft = [wp.Stage(x.name, x.p50_ns / speed, x.p99_ns / speed, x.kind) for x in wp.book13_software()]
    return wire[:1] + cards[:1] + soft + cards[1:] + wire[1:]


def budget_rows(n=100_000, seed=1, **kw):
    return wp.report(stages(**kw), n, seed)


def session(seconds=1.0, seed=1, speed=1.0):
    rng = np.random.default_rng(seed)
    t = OPEN + ns.bursty_arrivals(PPS, seconds, 6, 2_000, seed)
    rec, truth, seq = [], [], 1
    w2w = wp.compose(stages(speed), n=len(t), seed=seed + 1)["total"]
    for i, ti in enumerate(t.tolist()):
        k = int(rng.integers(1, 5))
        kinds = [b"E" if rng.random() < P_TRIGGER else b"A" for _ in range(k)]
        body = b"".join(struct.pack(">H", 36) + kd + bytes(35) for kd in kinds)
        payload = struct.pack(">10sQH", b"SESSION001", seq, k) + body
        first = None                                        # the strategy acts on the first copy to arrive
        for line, lag, port in ((b"A", 0, 1), (b"B", B_LAG, 2)):
            if rng.random() >= LOSS:
                dst = "239.1.1.1" if line == b"A" else "239.1.1.2"
                fr = wc.udp_frame("10.0.0.1", dst, 30000, 30001, payload)
                rec.append((ti + lag, wc.add_trailer(fr, ti + lag, 1, port)))
                first = ti + lag if first is None else first
        if first is not None and b"E" in kinds and rng.random() < P_ORDER:
            t_out = first + int(w2w[i])
            order = wc.ORDER.pack(b"O", len(truth) + 1, seq)
            rec.append((t_out, wc.add_trailer(wc.tcp_frame("10.0.1.5", "10.0.2.9", 40000, 50000, len(truth), order),
                                              t_out, 1, 3)))
            truth.append((t_out, seq, first))
        seq += k
    rec.sort(key=lambda r: r[0])
    return rec, truth


def analyse(records):
    feed, seqs, trig_t, orders, stamps, sizes = {}, {b"A": [], b"B": []}, [], [], [], []
    for _, fr in records:                                   # time from the trailer, not the pcap header
        frame, t, _, port = wc.strip_trailer(fr)
        p = wc.parse(frame)
        if p["proto"] == "udp":
            _, s, k, msgs = wc.mold(p["payload"])
            line = b"A" if port == 1 else b"B"
            seqs[line].extend(range(s, s + k))
            if line == b"A":
                stamps.append(t)
                sizes.append(len(frame) + 24)               # frame check sequence, preamble and gap
            if s not in feed:                               # first copy seen, either line
                feed[s] = t
                if any(m[:1] == b"E" for m in msgs):
                    trig_t.append(t)
        else:
            _, _, trig = wc.ORDER.unpack(p["payload"])
            orders.append((t, trig))
    pairs = wc.match_orders(feed, orders)
    w2w = np.array([a - b for a, b in pairs], dtype=float)
    trig_t.sort()
    near = wc.match_nearest(trig_t, [t for t, _ in orders])
    true = [feed.get(s) for _, s in orders]
    wrong = sum(1 for a, b in zip(near, true, strict=True) if a != b)
    naive = np.array([t - n for (t, _), n in zip(orders, near, strict=True) if n is not None], dtype=float)
    ga, gb = wc.gaps(seqs[b"A"]), wc.gaps(seqs[b"B"])
    lost_a = {s for f, n in ga for s in range(f, f + n)}
    lost_b = {s for f, n in gb for s in range(f, f + n)}
    return {"w2w": w2w, "w2w_naive": naive, "nearest_wrong": wrong / max(1, len(orders)),
            "gaps_a": len(ga), "gaps_b": len(gb),
            "both": len(lost_a & lost_b), "n_orders": len(orders), "n_packets": len(feed),
            "peak_100us_gbps": ns.peak_rate(np.array(stamps), np.array(sizes), 100_000)[1] / 1e9,
            "mean_gbps": 8.0 * sum(sizes) / (stamps[-1] - stamps[0])}
