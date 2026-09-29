import math
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_radiolink as r  # noqa: E402


def test_geometry_matches_midpoint_rules():
    # at mid-hop: bulge ~ D^2 / (51 K) m and Fresnel ~ 8.66 sqrt(D / f) m (D km, f GHz)
    for d, f in ((30, 6), (60, 11)):
        assert r.bulge_m(d / 2, d / 2, 1.0) == pytest.approx(d * d / 50.96, rel=1e-3)
        assert r.fresnel_m(d / 2, d / 2, f) == pytest.approx(8.66 * math.sqrt(d / f), rel=1e-3)
    assert r.tower_m(70, 6) == pytest.approx(r.bulge_m(35, 35) + r.fresnel_m(35, 35, 6) + 10)


def test_budget_and_rain():
    assert r.fspl_db(1, 1) == pytest.approx(92.45)
    assert r.fspl_db(60, 11) - r.fspl_db(30, 11) == pytest.approx(20 * math.log10(2))
    h = r.Hop(60, 11)
    assert r.fade_margin_db(h) == pytest.approx(r.rx_dbm(h) + 70)
    k, a = r.coefficients(11)
    assert (k, a) == (0.01772, 1.2140) and r.coefficients(6, "v") == (0.0004878, 1.5728)
    R = r.critical_rain(h)
    assert r.rain_db(h, R) == pytest.approx(r.fade_margin_db(h))
    assert r.critical_rain(h, 10) > R
    assert r.critical_rain(r.Hop(60, 11, tx_dbm=-100)) == 0.0


def test_chain_storm_availability():
    pts = r.chain((41.8, -88.2), (40.6, -74.2), 4)
    assert len(pts) == 5 and pts[0] == pytest.approx((41.8, -88.2)) and pts[-1] == pytest.approx((40.6, -74.2))
    hops = [r.Hop(50, 18) for _ in range(4)]
    dry = r.storm_timeline(hops, r.Storm(100, 1.0, 10, 0.0), 1.0, 2.0)
    assert len(dry) == 21 and all(x[1] == 0 and x[2] == 1.0 for x in dry)
    wet = r.storm_timeline(hops, r.Storm(100, 1.0, 10, 500.0), 1.0, 2.0)
    assert any(x[2] == 2.0 for x in wet) and max(x[1] for x in wet) >= 1
    assert r.availability(hops[0], lambda x: 0.0) == 1.0 and r.availability(hops[0], lambda x: 0.01) == 0.99
