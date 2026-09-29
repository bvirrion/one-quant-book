import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_venuefind as v  # noqa: E402


def test_prefix_match():
    r = v.load_ranges()
    assert v.match(r, "192.0.2.200") == ("192.0.2.128/25", "ap-northeast-1", "EC2")      # longest prefix wins
    assert v.match(r, "192.0.2.5")[0] == "192.0.2.0/24"
    assert v.match(r, "2001:db8:2abc::9")[1] == "us-east-1" and v.match(r, "8.8.8.8") is None


def test_triangulation_recovers_a_point():
    gm = v.gm
    true = (35.7, 139.8)
    sites = [(22.3, 114.3), (1.4, 103.8), (-33.8, 151.2), (19.1, 72.9)]
    probes = [(la, lo, 2 * 1.3 * gm.floor_us(gm.haversine_m(la, lo, *true), "fibre")) for la, lo in sites]
    lat, lon, rms = v.triangulate(probes, 35.0, 135.0, span_deg=8.0, step_deg=0.1)
    assert gm.haversine_m(lat, lon, *true) < 15_000 and rms < 20
    with pytest.raises(ValueError):
        v.triangulate([(0.0, 0.0, 10.0)], 40.0, 10.0, span_deg=1.0, step_deg=0.5)
    assert v.distance_bound_km(1000) == pytest.approx(500e-6 * v.gm.C0 / 1.462 / 1e3)


def test_lottery_and_cusum():
    lot = v.Lottery(270, 150)
    b = [v.expected_best(lot, n, 5000) for n in (1, 10, 100)]
    assert b[0] > b[1] > b[2] > 0 and b[2] > 100
    n, net = v.best_n(lot, 0.0, 10.0, n_max=5, sims=500)
    assert (n, net) == (1, 0.0)
    rng = np.random.default_rng(1)
    assert v.moved(rng.normal(100, 1, 80)) is None
    assert v.moved(np.r_[rng.normal(100, 1, 40), rng.normal(110, 1, 40)]) >= 39
