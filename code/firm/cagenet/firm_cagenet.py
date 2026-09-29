"""firm.cagenet -- a trading cage's network as data (build of One Quant Book 14, chapter 2).

Devices (venue handoffs, layer-1 switches and multiplexers, cut-through and store-and-forward switches, taps, servers)
joined by cables. A path's latency is the time from the first bit leaving its source to the last bit reaching its
destination: one serialisation of the frame, the propagation over every cable, and what each device adds
(firm.netsim.forward_ns: the whole frame for store-and-forward, the header for cut-through, a constant for layer 1).
Taps are passive: they add only their fibre. Redundancy is checked by removing every device and every cable in turn.

API (stable):
    Device(name, kind, fabric_ns=0.0)      kind: handoff | server | l1 | mux | cut-through | store-and-forward | tap
    Cable(a, b, length_m, n_g=1.462)       fibre by default (n_g: group index); undirected
    Cage(devices, cables)
        .path(src, dst) -> [names]         shortest path by hop count (deterministic tie-break by name)
        .latency_ns(path, frame, gbps) -> float
        .breakdown(path, frame, gbps) -> dict(serialisation, propagation, devices)
        .single_points(feeds, orders, servers) -> [element]   elements whose loss cuts a server off from every feed
                                                               handoff, or from every order handoff
        .untapped(handoffs) -> [handoff]   handoffs whose cable carries no tap
"""
import collections
import pathlib
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "netsim"))
import firm_netsim as ns  # noqa: E402

KINDS = ("handoff", "server", "l1", "mux", "cut-through", "store-and-forward", "tap")


@dataclass(frozen=True)
class Device:
    name: str
    kind: str
    fabric_ns: float = 0.0


@dataclass(frozen=True)
class Cable:
    a: str
    b: str
    length_m: float
    n_g: float = 1.462


class Cage:
    def __init__(self, devices, cables):
        self.dev = {d.name: d for d in devices}
        for d in devices:
            if d.kind not in KINDS:
                raise ValueError(f"unknown kind {d.kind}")
        self.cables = list(cables)
        for c in self.cables:
            if c.a not in self.dev or c.b not in self.dev:
                raise ValueError(f"cable to unknown device {c}")

    def _adj(self, skip=None):
        adj = collections.defaultdict(list)
        for c in self.cables:
            if c is skip or skip in (c.a, c.b):
                continue
            adj[c.a].append((c.b, c))
            adj[c.b].append((c.a, c))
        return adj

    def path(self, src, dst, skip=None):
        adj = self._adj(skip)
        prev = {src: None}
        q = collections.deque([src])
        while q:
            u = q.popleft()
            if u == dst:
                break
            for v, _ in sorted(adj[u], key=lambda x: x[0]):
                if v not in prev and (v == dst or self.dev[v].kind not in ("server", "handoff")):
                    prev[v] = u
                    q.append(v)
        if dst not in prev:
            return None
        out = [dst]
        while prev[out[-1]] is not None:
            out.append(prev[out[-1]])
        return out[::-1]

    def _cable(self, a, b):
        for c in self.cables:
            if {c.a, c.b} == {a, b}:
                return c
        raise KeyError((a, b))

    def breakdown(self, path, frame, gbps):
        hops = [self._cable(a, b) for a, b in zip(path, path[1:], strict=False)]
        prop = sum(ns.prop_ns(c.length_m, c.n_g) for c in hops)
        dev = 0.0
        for n in path[1:-1]:
            d = self.dev[n]
            if d.kind in ("l1", "mux"):
                dev += ns.forward_ns(frame, gbps, "layer-1", d.fabric_ns)
            elif d.kind in ("cut-through", "store-and-forward"):
                dev += ns.forward_ns(frame, gbps, d.kind, d.fabric_ns)
        return {"serialisation": 8.0 * frame / gbps, "propagation": prop, "devices": dev}

    def latency_ns(self, path, frame, gbps):
        return sum(self.breakdown(path, frame, gbps).values())

    def single_points(self, feeds, orders, servers):
        elems = [n for n, d in self.dev.items() if d.kind not in ("server", "handoff")] + self.cables
        bad = []
        for e in elems:
            for s in servers:
                fed = any(self.path(f, s, skip=e) for f in feeds)
                out = any(self.path(s, o, skip=e) for o in orders)
                if not (fed and out):
                    bad.append(e)
                    break
        return bad

    def untapped(self, handoffs):
        out = []
        for h in handoffs:
            nbrs = [c.b if c.a == h else c.a for c in self.cables if h in (c.a, c.b)]
            if not any(self.dev[n].kind == "tap" for n in nbrs):
                out.append(h)
        return out
