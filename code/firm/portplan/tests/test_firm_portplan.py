import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_portplan as pp  # noqa: E402


def test_capacity_rows():
    rows = pp.load_capacity()
    assert [p.effective for p in rows] == ["2025-10", "2026-01", "2026-07", "2027-01", "2027-07"]
    p = pp.projection("2026-07")
    assert p.msgs_10ms == 1.562e6 and p.line_max_100ms == 625e3
    assert 40 < pp.wire_bytes_per_msg(p) < 60


def test_burst_and_windows():
    x = pp.burst(5000, 0.3, 2.0, seed=3)
    assert abs(x.mean() - 1) < 1e-12 and pp.window_peak(np.ones(10), 3) == 3.0
    flat = pp.burst(5000, 1e-9, 0.0, sigma_w=1e-9)
    r1, r2 = pp.ratios(flat)
    assert abs(r1 - 1) < 1e-6 and abs(r2 - 1) < 1e-6


def test_lines_and_links():
    agg = np.full(100, 96.0)
    lines = pp.line_split(agg, sigma_i=0.0)
    assert np.allclose(lines, 1.0) and np.allclose(lines.sum(axis=1), agg)
    assert pp.links_needed(lines * 0.5, 100, link_gbps=11.0, retrans=0.1) == 5   # 48 Gb/s over 10 Gb/s links
    assert pp.cores_needed(25e6) == 3


def test_ports():
    assert pp.quotes_per_s(10, 100, 5) == 10000 and pp.port_msgs_per_s(20) == 50000
    assert pp.ports_needed(5e6, 20, engines=1) == 2 and pp.ports_needed(1e3, 20, engines=4) == 4
    assert pp.bulk_bytes() == 801
