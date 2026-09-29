"""Numbers gate: every number printed in Book 14, chapter 17 (text and solutions)."""
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_find as f  # noqa: E402

vf, gm = f.vf, f.gm


def test_lookups():
    got = f.lookups()
    assert got["192.0.2.200"] == ("192.0.2.128/25", "ap-northeast-1", "EC2")
    assert got["198.51.100.7"][1] == "ap-southeast-1" and got["203.0.113.9"][1:] == ("GLOBAL", "CLOUDFRONT")
    assert got["2001:db8:1abc::1"] == ("2001:db8:1000::/36", "ap-northeast-1", "EC2")


def test_triangulation():
    t = f.triangulate_example()
    assert [round(p[2] / 1000, 1) for p in t["probes"]] == [36.5, 67.4, 98.8, 85.5]
    assert round(t["error_km"]) == 23
    p = f.probes()
    for fac in (1.2, 1.4):
        la, lo, _ = vf.triangulate(p, 35.0, 135.0, 8.0, 0.1, factor=fac)
        assert gm.geodesic_m(la, lo, *f.TRUE) / 1e3 > 540
    assert round(vf.distance_bound_km(1000), 1) == 102.5


@pytest.mark.reference
def test_lottery():
    c = dict(f.lottery_curve())
    assert [round(c[n]) for n in (1, 10, 40, 160)] == [279, 185, 157, 138]
    assert (round(c[1] - c[10]), round(c[10] - c[160]), round(c[40] - c[160])) == (94, 47, 19)
    n, net = f.best()
    assert n == 77 and round(net, -2) == 11_700
    b = vf.expected_best(f.LOTTERY, 1, 4000, 0)
    assert round(f.VALUE * (b - vf.expected_best(f.LOTTERY, 40, 4000, 0)) - 40 * f.LAUNCH, -2) == 11_400
    n20, net20 = vf.best_n(f.LOTTERY, 20.0, f.LAUNCH, n_max=150)
    assert n20 == 23 and round(net20, -1) == 1_830
    assert round(f.LAUNCH, 2) == 17.14


def test_drift():
    x, d = f.drift_example()
    assert d + 2 == 73 and round((185 - 160) / 6) == 4


def test_small_runs():
    assert vf.expected_best(f.LOTTERY, 3, 500) < vf.expected_best(f.LOTTERY, 1, 500)
