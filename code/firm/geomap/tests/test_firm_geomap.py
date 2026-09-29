import math
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_geomap as g  # noqa: E402


def test_vincenty_against_karney_test_set():
    worst, n = 0.0, 0
    for line in (HERE / "data" / "geodtest_subset.txt").read_text().splitlines():
        lat1, lon1, lat2, lon2, s = map(float, line.split())
        worst = max(worst, abs(g.geodesic_m(lat1, lon1, lat2, lon2) - s))
        n += 1
    assert n > 200 and worst < 1e-4                       # a tenth of a millimetre on WGS-84


def test_simple_cases_and_floors():
    assert g.geodesic_m(10, 20, 10, 20) == 0
    meridian_deg = g.geodesic_m(0, 0, 1, 0)
    assert 110_500 < meridian_deg < 110_600                    # one degree of latitude at the equator
    assert abs(g.haversine_m(40, -74, 41, -88) / g.geodesic_m(40, -74, 41, -88) - 1) < 0.005
    assert g.floor_us(299_792.458) == pytest.approx(1000.0)
    assert g.floor_us(1000, "fibre") == pytest.approx(1000 * 1.462 / g.C0 * 1e6)
    assert g.route_factor(g.floor_us(5000, "fibre") * 1.2, 5000) == pytest.approx(1.2)
    with pytest.raises(ArithmeticError):
        g.geodesic_m(0, 0, 0.5, 179.7)                          # nearly antipodal: Vincenty fails


def test_sites_io_matrix_projection(tmp_path):
    s = [g.Site("a", "A", "op", 40.0, -74.0, "F1", ("V1", "V2")), g.Site("b", "B", "op", 41.0, -74.0, "F2")]
    g.write_sites(tmp_path / "s.csv", s)
    back = g.load_sites(tmp_path / "s.csv")
    assert back == s
    m = g.matrix(s)
    assert list(m) == [("a", "b")] and m[("a", "b")] == pytest.approx(g.geodesic_m(40, -74, 41, -74))
    p = g.project(s, 40.0, -74.0)
    assert p["a"] == (0.0, 0.0) and math.isclose(p["b"][1], 110.574)
