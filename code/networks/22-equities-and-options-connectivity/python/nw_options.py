"""Chapter 22 of One Quant Book 14: taking the consolidated options feed and quoting every series (firm.portplan).

    P, R1, R2                 the feed's July 2026 projection; the published peak ratios the burst model is fitted to
    AGG, LINES_GBPS           a simulated busy minute: messages per 1-ms bin, scaled to the projection's 10-ms peak,
                              and each of the 96 lines' rate in Gb/s on the wire
    links_table()             10 Gb/s links for both streams against the planning percentile
    feed_plan()               stream rate, links, handler cores and the backlog of the busiest millisecond
    backlog(cores)            the largest queue in front of the handler cores, in messages and milliseconds
    quote_plan(rtt_us)        quoting load to bulk messages, ports and refresh time after a market-wide move
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "portplan"))
import firm_portplan as pp  # noqa: E402

P = pp.projection("2026-07")
with open(ROOT / "data" / "networks" / "opra_metrics.csv") as f:
    JUL26 = next(r for r in csv.DictReader(f) if r["month"] == "2026-07")
R1 = float(JUL26["peak_1ms_m"]) / (float(JUL26["peak_10ms_m"]) / 10)     # busiest 1 ms against busiest 10 ms
R2 = (P.msgs_10ms * 10) / P.msgs_100ms                                    # busiest 10 ms against busiest 100 ms
FIT = (0.58, 3.5)          # pp.fit_burst(R1, R2) with seed 0 (checked by the tests)
X = pp.burst(60000, *FIT)
AGG = X * P.msgs_10ms / pp.window_peak(X, 10)
BITS = pp.wire_bytes_per_msg(P) * 8
LINES_GBPS = pp.line_split(AGG) * BITS * 1000 / 1e9
PCTS = (50, 90, 99, 99.9, 99.99, 100)
PER_CORE = 10e6            # messages a second one handler core decodes and books (assumption)


def links_table(pcts=PCTS, streams=2, link_gbps=10.0):
    return [(p, streams * pp.links_needed(LINES_GBPS, p, link_gbps)) for p in pcts]


def backlog(cores):
    """Fluid queue over the 1-ms bins: the largest backlog and the time the cores need to clear it."""
    rate = cores * PER_CORE / 1000
    q = worst = 0.0
    for a in AGG:
        q = max(0.0, q + a - rate)
        worst = max(worst, q)
    return worst, worst / rate


def feed_plan(pct=99.99):
    peak10 = P.msgs_10ms * 100
    cores = pp.cores_needed(peak10, PER_CORE)
    peak1 = pp.window_peak(AGG, 1)
    return {"gbps_100ms": P.gbit_100ms * 10, "gbps_10ms": P.gbit_10ms * 100, "wire_bytes": BITS / 8,
            "peak_1ms_gbps": float(LINES_GBPS.sum(axis=1).max()), "links": 2 * pp.links_needed(LINES_GBPS, pct),
            "cores": cores, "peak_1ms_msgs": peak1,
            "line_peak_100ms": max(pp.window_peak(AGG_LINES[:, i], 100) for i in range(pp.LINES))}


AGG_LINES = pp.line_split(AGG)
CLASSES, SERIES, UPDATES, ENGINES = 1200, 250, 4, 12   # the firm's quoting load and the venue's engines (assumptions)
PORT_RTT_US = 20.0         # port to matching engine and back, colocated, no risk layer (assumption)
RISK_US = {"none": 0.0, "FPGA gateway": 0.2, "software layer": 5.0}   # one way; FPGA figure published, software assumed


def quote_plan(risk="none", ports_per_engine=2):
    rtt = PORT_RTT_US + 2 * RISK_US[risk]
    q = pp.quotes_per_s(CLASSES, SERIES, UPDATES)
    per_port = pp.port_msgs_per_s(rtt) * pp.BULK_MAX
    all_quotes = CLASSES * SERIES * 2
    return {"quotes_s": q, "msgs_s": q / pp.BULK_MAX, "rtt_us": rtt,
            "ports": pp.ports_needed(q, rtt, engines=ENGINES), "ports_held": ENGINES * ports_per_engine,
            "refresh_ms": 1000 * all_quotes / ENGINES / (ports_per_engine * per_port),
            "gbps": q / pp.BULK_MAX * pp.bulk_bytes() * 8 / 1e9}


def refresh_curve(ports_per_engine, risks_us=tuple(x / 2 for x in range(0, 21))):
    out = []
    for r in risks_us:
        per_port = pp.port_msgs_per_s(PORT_RTT_US + 2 * r) * pp.BULK_MAX
        out.append((r, 1000 * CLASSES * SERIES * 2 / ENGINES / (ports_per_engine * per_port)))
    return out


def port_cost(exchange, n):
    """Monthly quoting-port cost of n ports from the dated fee rows (volume discounts ignored)."""
    if exchange == "Phlx":
        return 1185 * n
    if exchange == "BOX":
        return 1000
    if exchange == "MIAX":
        return 20500
    if exchange in ("Arca", "Amex"):
        return 510 * min(n, 40) + 170 * max(0, n - 40)
    if exchange == "EDGX":
        return 750 * n
    raise KeyError(exchange)
