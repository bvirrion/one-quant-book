"""Chapter 18 of One Quant Book 14: private paths to a cloud-hosted venue (firm.privlink on firm.cloudplan).

    PATHS, path_rows()         each documented path's simulated round trip (p50, p99) and its costs
    wrong_zone()               the named result: added round trip and cost per million messages of an endpoint in
                               another zone against the same zone
    monthly_curve(volumes)     monthly cost of the two endpoint paths against message volume (millions)
    ALIGN                      a zone-alignment example on synthetic identifiers
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "privlink"))
import firm_privlink as pl  # noqa: E402

PATHS = pl.load_paths()
ORDER = ["peering_cpg", "peering", "endpoint_same", "endpoint_other", "internet"]
BYTES = 400                         # an order and its acknowledgement, bytes (assumption)
ALIGN = {"instance": "apne1-az4", "endpoint": ["apne1-az1", "apne1-az2"]}


def path_rows():
    out = []
    for k in ORDER:
        p = PATHS[k]
        q = pl.rtt_percentiles(p)
        out.append({"key": k, "kind": p.kind, "p50": q[50], "p99": q[99],
                    "per_million": pl.cost_per_million(p, BYTES), "fixed": pl.monthly_fixed(p)})
    return out


def wrong_zone():
    s, o = PATHS["endpoint_same"], PATHS["endpoint_other"]
    qs, qo = pl.rtt_percentiles(s), pl.rtt_percentiles(o)
    cost = pl.cost_per_million(o, BYTES) - pl.cost_per_million(s, BYTES)
    return {"p50_added": qo[50] - qs[50], "p99_added": qo[99] - qs[99], "cost_added_per_million": cost}


def monthly_curve(volumes=(0, 100, 500, 1000, 2000, 5000, 10000)):
    s, o = PATHS["endpoint_same"], PATHS["endpoint_other"]
    cs, co = pl.cost_per_million(s, BYTES), pl.cost_per_million(o, BYTES)
    return [(v, pl.monthly_fixed(s) + v * cs, pl.monthly_fixed(o) + v * co) for v in volumes]
