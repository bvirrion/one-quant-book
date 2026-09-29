"""Numbers gate: every number printed in Book 14, chapter 22 (text and solutions)."""
import math
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_options as n  # noqa: E402

pp = n.pp


def test_notice_and_framing():
    p = n.P
    assert (round(p.gbit_100ms * 10, 1), round(p.gbit_10ms * 100, 1)) == (44.0, 50.1)
    assert (round(p.gbit_100ms * 1e9 / 8 / p.packets_100ms), round(p.msgs_100ms / p.packets_100ms, 2)) == (352, 8.68)
    assert round(pp.wire_bytes_per_msg(p), 1) == 48.0 and pp.ns.wire_bytes(pp.ns.frame_bytes(352)) == 418
    w = pp.wire_bytes_per_msg(p) / (p.gbit_100ms * 1e9 / 8 / p.msgs_100ms)
    assert (round(50.1 * w, 1), round(44.03 * w, 1)) == (59.4, 52.2)
    assert (round(50.1 * w * 2.2, 1), round(44.03 * w * 2.2, 1)) == (130.6, 114.8)
    assert round(0.35e6 * n.BITS / 1e6) == 135 and round(p.msgs_10ms * 100 / 1e6, 1) == 156.2
    assert (round(n.R1, 2), round(n.R2, 3)) == (3.93, 1.151)


@pytest.mark.reference
def test_burst_fit():
    assert pp.fit_burst(n.R1, n.R2) == n.FIT
    r1, r2 = pp.ratios(n.X)
    assert (round(r1, 2), round(r2, 3)) == (3.90, 1.152)
    assert round(pp.window_peak(n.AGG, 100) / 1e6, 2) == 13.56


@pytest.mark.reference
def test_links_and_cores():
    assert n.links_table() == [(50, 4), (90, 6), (99, 12), (99.9, 16), (99.99, 44), (100, 178)]
    assert [x for _, x in n.links_table(link_gbps=25.0)] == [2, 4, 6, 6, 16, 32]
    f = n.feed_plan()
    assert (round(f["peak_1ms_gbps"]), f["cores"], round(f["peak_1ms_msgs"], -2)) == (234, 16, 609500)
    assert round(n.LINES_GBPS.max(), 1) == 6.8 and round(f["line_peak_100ms"], -2) == 171500
    assert math.ceil(f["peak_1ms_gbps"] / (10 / 1.1)) == 26 and round(10 / 1.1, 2) == 9.09
    assert sum(n.AGG >= n.AGG.max()) == 1 and round(60000 * (1 - 0.9999)) == 6
    q, t = n.backlog(16)
    assert (round(q, -2), round(t, 1)) == (449500, 2.8)
    assert round(n.backlog(32)[1], 1) == 0.9 and round(n.backlog(48)[1], 2) == 0.27 and n.backlog(64)[0] == 0
    q, t = n.backlog(41)
    assert (round(q, -2), round(t, 2), round(n.backlog(40)[1], 2)) == (199500, 0.49, 0.52)


def test_quotes_and_ports():
    a, b, c = (n.quote_plan(r) for r in ("none", "FPGA gateway", "software layer"))
    assert (a["quotes_s"], a["msgs_s"], round(a["gbps"], 2)) == (2400000, 48000, 0.31)
    assert (a["ports"], a["ports_held"], pp.port_msgs_per_s(20)) == (12, 24, 50000)
    assert [round(x["refresh_ms"], 1) for x in (a, b, c)] == [10.0, 10.2, 15.0]
    assert round(n.quote_plan("none", ports_per_engine=1)["refresh_ms"], 1) == 20.0
    assert round(600000 * 20.4 / (12 * 3 * 50) / 1000, 1) == 6.8 and n.CLASSES * n.SERIES * 2 == 600000
    assert pp.bulk_bytes() == 801 and pp.BULK_HDR == 2 + 4 + 4 + 8 + 1 + 32 and pp.QUOTE_BYTES == 4 + 4 + 4 + 1 + 2
    costs = {e: n.port_cost(e, 24) for e in ("Phlx", "EDGX", "Arca", "Amex", "BOX", "MIAX")}
    assert costs == {"Phlx": 28440, "EDGX": 18000, "Arca": 12240, "Amex": 12240, "BOX": 1000, "MIAX": 20500}
    assert round(28440 / 1000) == 28


def test_small_runs():
    x = pp.burst(2000, 0.3, 2.0, seed=5)
    lines = pp.line_split(x * 100, n_lines=8)
    assert abs(lines.sum() - 100 * x.sum()) < 1e-6
    assert pp.links_needed(lines * 0.01, 50, link_gbps=100.0) == 1
