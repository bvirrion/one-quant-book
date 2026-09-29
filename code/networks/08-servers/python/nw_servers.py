"""Chapter 8 of One Quant Book 14: choosing the servers of the hot path, with firm.serverspec.

The reference is One Quant Book 13's in-process stages (decode to gateway), measured on a laptop core whose maximum
turbo is 4.8 GHz: medians summing to 1,528 ns. What share of that time scales with the clock is a property of the code
(phi, stated per case); the candidates are the ledger's rows.
    REF_NS, REF_GHZ           the reference path and clock
    table(phi, cabinet_kw)    per candidate: predicted path at its hot clock and at its base clock, servers and cores
    curve(phis, freqs)        the model's latency against the clock
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("serverspec", "wirepath"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
import firm_serverspec as ss  # noqa: E402
import firm_wirepath as wp  # noqa: E402

REF_GHZ = 4.8


def ref_ns():
    return sum(s.p50_ns for s in wp.book13_software())


def table(phi=0.6, cabinet_kw=10.0):
    out = []
    for c in ss.CANDIDATES:
        n = ss.per_cabinet(c, cabinet_kw)
        out.append({"name": c.name, "hot_ghz": c.hot_ghz, "base_ghz": c.base_ghz,
                    "hot_ns": ss.path_ns(ref_ns(), phi, c.hot_ghz, REF_GHZ),
                    "base_ns": ss.path_ns(ref_ns(), phi, c.base_ghz, REF_GHZ),
                    "servers": n, "cores": n * c.cores * c.sockets, "server_w": c.server_w})
    return out


def curve(phis=(1.0, 0.6, 0.3), freqs=(2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0)):
    return [(f, *[ss.path_ns(ref_ns(), p, f, REF_GHZ) for p in phis]) for f in freqs]
