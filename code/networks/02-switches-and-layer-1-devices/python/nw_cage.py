"""Chapter 2 of One Quant Book 14: switches, layer-1 devices and the network inside one cage.

    DEVICES                 per-device latency parameters: datasheet figures and one labelled model assumption
    forwarding_curve()      latency added by each device type against frame size, at 10 Gb/s
    design(name)            three cages (firm.cagenet): two commodity switches, one cut-through switch, layer 1
    design_table()          feed-in and order-out latency of each design
    mux_contention(...)     simulation: k servers answer the same market event through one N:1 multiplexer
    mirror_load(...)        a mirror port carrying both directions of a link
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("netsim", "cagenet"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
import firm_cagenet as cg  # noqa: E402
import firm_netsim as ns  # noqa: E402

# Datasheet figures (ledger rows): cut-through switch port-to-port 250 ns (Nexus 3548-X, normal mode); layer-1
# switch 4 ns; layer-1 multiplexer 39 ns on average. Store-and-forward fabric: a model assumption, stated as such.
DEVICES = {"cut-through": 250.0, "l1": 4.0, "mux": 39.0, "store-and-forward": 500.0}
FEED_FRAME, ORDER_FRAME = 104, 100
CAGE_M, XC_M = 3.0, 30.0            # cable in the cage; cross-connect to the venue handoff


def forwarding_curve(sizes=(64, 128, 256, 512, 1024, 1518), gbps=10.0):
    rows = []
    for f in sizes:
        rows.append((f, ns.forward_ns(f, gbps, "store-and-forward", DEVICES["store-and-forward"]),
                     ns.forward_ns(f, gbps, "cut-through", 0.0) + DEVICES["cut-through"] - 8 * 64 / gbps,
                     DEVICES["mux"], DEVICES["l1"]))
    return rows


def design(name):
    D, C = cg.Device, cg.Cable
    base = [D("A", "handoff"), D("B", "handoff"), D("O", "handoff"), D("P", "handoff"), D("tapA", "tap"),
            D("tapB", "tap"), D("tapO", "tap"), D("tapP", "tap"), D("s1", "server"), D("s2", "server")]
    cab = [C("A", "tapA", XC_M), C("B", "tapB", XC_M), C("O", "tapO", XC_M), C("P", "tapP", XC_M)]
    if name == "commodity":
        dev = [D("sw1", "store-and-forward", DEVICES["store-and-forward"]),
               D("sw2", "store-and-forward", DEVICES["store-and-forward"])]
        cab += [C("tapA", "sw1", CAGE_M), C("tapB", "sw1", CAGE_M), C("tapO", "sw1", CAGE_M), C("tapP", "sw1", CAGE_M),
                C("sw1", "sw2", CAGE_M),
                C("sw2", "s1", CAGE_M), C("sw2", "s2", CAGE_M)]
    elif name == "cut-through":
        dev = [D("swa", "cut-through", DEVICES["cut-through"]), D("swb", "cut-through", DEVICES["cut-through"])]
        cab += [C("tapA", "swa", CAGE_M), C("tapB", "swb", CAGE_M), C("tapO", "swa", CAGE_M), C("tapP", "swb", CAGE_M)]
        cab += [C(sw, s, CAGE_M) for sw in ("swa", "swb") for s in ("s1", "s2")]
    elif name == "layer-1":
        dev = [D("l1a", "l1", DEVICES["l1"]), D("l1b", "l1", DEVICES["l1"]), D("mux", "mux", DEVICES["mux"]),
               D("muxb", "mux", DEVICES["mux"])]
        cab += [C("tapA", "l1a", CAGE_M), C("tapB", "l1b", CAGE_M), C("tapO", "mux", CAGE_M), C("tapP", "muxb", CAGE_M)]
        cab += [C(x, s, CAGE_M) for x in ("l1a", "l1b", "mux", "muxb") for s in ("s1", "s2")]
    else:
        raise ValueError(name)
    return cg.Cage(base + dev, cab)


def design_table(gbps=10.0):
    out = {}
    for name in ("commodity", "cut-through", "layer-1"):
        c = design(name)
        feed = c.latency_ns(c.path("A", "s1"), FEED_FRAME, gbps)
        order = c.latency_ns(c.path("s1", "O"), ORDER_FRAME, gbps)
        spof = c.single_points(["A", "B"], ["O", "P"], ["s1", "s2"])
        out[name] = {"feed": feed, "order": order, "spof": [e if isinstance(e, str) else f"{e.a}-{e.b}" for e in spof]}
    return out


def mux_contention(k, jitter_ns, n_events=20_000, frame=ORDER_FRAME, gbps=10.0, seed=1):
    """k servers each send one order in response to the same event, after the event plus a delay with standard
    deviation jitter_ns (normal, folded at zero); the multiplexer sends one frame at a time. Returns the mean
    queueing delay of an order, of the last order to arrive, and the probability that an order waits."""
    rng = np.random.default_rng(seed)
    t = np.abs(rng.normal(1000.0, jitter_ns, (n_events, k)))
    t.sort(axis=1)
    ser = ns.ser_ns(frame, gbps)
    free = np.zeros(n_events)
    waits = np.zeros((n_events, k))
    for j in range(k):
        start = np.maximum(t[:, j], free)
        waits[:, j] = start - t[:, j]
        free = start + ser
    return {"mean": float(waits.mean()), "p_wait": float((waits > 0).mean()),
            "last": float(waits[:, -1].mean()), "ser": ser}


def mirror_load(link_gbps_each_way, mirror_gbps):
    """Both directions of a full-duplex link copied to one mirror port: offered load and the share that cannot fit
    when both directions are busy."""
    offered = 2 * link_gbps_each_way
    return offered, max(0.0, 1 - mirror_gbps / offered)
