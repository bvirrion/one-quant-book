import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_netsim as ns  # noqa: E402


def test_frame_arithmetic():
    assert ns.frame_bytes(0) == 64 and ns.frame_bytes(18) == 64 and ns.frame_bytes(19) == 65
    assert ns.frame_bytes(1472) == 1518                        # the largest untagged UDP payload
    assert ns.wire_bytes(64) == 84 and ns.ser_ns(64, 10) == pytest.approx(67.2)
    assert ns.ser_ns(1518, 10) == pytest.approx(1230.4)
    assert ns.mold_payload([36]) == 58 and ns.frame_bytes(ns.mold_payload([36])) == 104
    assert ns.prop_ns(1.0) == pytest.approx(4.8767, abs=1e-4)


def test_mcast_mac_rfc1112():
    assert ns.mcast_mac("224.0.0.1") == "01:00:5e:00:00:01"
    assert ns.mcast_mac("239.255.1.2") == "01:00:5e:7f:01:02"
    assert ns.mcast_mac("224.127.1.2") == ns.mcast_mac("239.255.1.2")    # 32 groups share one address
    with pytest.raises(ValueError):
        ns.mcast_mac("10.0.0.1")


def test_peak_rate_windows():
    t = np.array([0, 10, 20, 1000, 5000])
    b = np.array([100, 100, 100, 100, 100])
    p, bits = ns.peak_rate(t, b, 100)
    assert p == pytest.approx(3e7) and bits == pytest.approx(3 * 800 * 1e7)
    p, _ = ns.peak_rate(t, b, 10_000)
    assert p == pytest.approx(5e5)


def test_bursty_rate_and_determinism():
    a = ns.bursty_arrivals(1_000_000, 0.2, 10, 100, seed=5)
    b = ns.bursty_arrivals(1_000_000, 0.2, 10, 100, seed=5)
    assert np.array_equal(a, b) and np.all(np.diff(a) >= 0)
    assert abs(len(a) / 0.2 / 1e6 - 1) < 0.05
    ev = ns.event_times(200, 0.2, seed=1)
    c = ns.bursty_arrivals(1_000_000, 0.2, 10, 100, seed=6, common=ev, common_share=0.5)
    assert abs(len(c) / 0.2 / 1e6 - 1) < 0.1


def test_egress_conservation_and_fifo():
    t = ns.bursty_arrivals(2_000_000, 0.01, 20, 50, seed=2)
    f = np.full(len(t), 200)
    r = ns.egress(t, f, 10.0, 30_000)
    kept = ~r.dropped
    assert r.n_dropped == int(r.dropped.sum()) and r.n_dropped > 0
    d = r.depart_ns[kept]
    assert np.all(np.diff(d) > 0)                               # FIFO, one frame at a time
    assert np.all(d - t[kept] >= ns.ser_ns(200, 10) - 1e-9)     # at least the frame's own line time
    assert r.max_backlog <= 30_000
    big = ns.egress(t, f, 10.0, 1e12)
    assert big.n_dropped == 0 and big.max_backlog >= r.max_backlog


def test_egress_matches_fixture_and_queue_formula():
    here = pathlib.Path(__file__).resolve().parents[1] / "data" / "fixture_egress.csv"
    lines = here.read_text().splitlines()
    gbps, buf, mx, nd = lines[1].split(",")
    rows = [x.split(",") for x in lines[3:]]
    t = np.array([int(x[0]) for x in rows])
    f = np.array([int(x[1]) for x in rows])
    r = ns.egress(t, f, float(gbps), float(buf))
    assert r.n_dropped == int(nd) and abs(r.max_backlog - float(mx)) < 1e-6
    # a burst of n equal frames arriving at once: backlog n * wire bytes, last departure n * line time
    r = ns.egress(np.zeros(10, dtype=np.int64), np.full(10, 64), 10.0, 1e9)
    assert r.max_backlog == 840 and r.depart_ns[-1] == pytest.approx(10 * 67.2)


def test_forwarding_modes_and_replication():
    assert ns.forward_ns(1518, 10, "store-and-forward", 200) == pytest.approx(1214.4 + 200)
    assert ns.forward_ns(1518, 10, "cut-through", 200) == pytest.approx(51.2 + 200)
    assert ns.forward_ns(64, 10, "layer-1", 5) == 5
    groups = np.array([0, 1, 2, 1, 0])
    out = ns.replicate(groups, {0: {0}, 1: {1, 2}}, 3)
    assert out[0].tolist() == [0, 4] and out[1].tolist() == [1, 2, 3] and out[2].tolist() == []
    assert all(len(x) == 5 for x in ns.replicate(groups, {}, 3, snooping=False))
    t, f, s = ns.merge(([5, 1], [64, 65]), ([3], [66]))
    assert t.tolist() == [1, 3, 5] and f.tolist() == [65, 66, 64] and s.tolist() == [0, 1, 0]
