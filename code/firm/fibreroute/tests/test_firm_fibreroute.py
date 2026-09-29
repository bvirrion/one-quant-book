import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_fibreroute as fr  # noqa: E402


def test_components_by_hand():
    r = fr.build("t", 100.0, 1.2, span_km=40, amp_us=0.1, terminal_us=5)
    assert len(r.spans) == 3 and r.km == pytest.approx(120)
    c = fr.components(r)
    per_km = 1.462 / fr.C0 * 1e9                                  # microseconds per kilometre of glass
    assert c["glass"] == pytest.approx(100 * per_km) and c["path"] == pytest.approx(20 * per_km)
    assert c["amps"] == pytest.approx(0.3) and c["terminals"] == 10
    assert c["total"] == pytest.approx(120 * per_km + 10.3)
    with pytest.raises(ValueError):
        fr.build("bad", 100, 0.9)


def test_invert_and_index():
    r = fr.build("t", 500.0, 1.1, terminal_us=10, amp_us=0.0)
    total = fr.components(r)["total"]
    inv = fr.invert(total, 500.0, equipment_us=20)
    assert inv["factor"] == pytest.approx(1.1) and inv["excess_km"] == pytest.approx(50)
    h = fr.components(fr.with_index(r, 1.003))
    assert h["glass"] / fr.components(r)["glass"] == pytest.approx(1.003 / 1.462)
    dcf = fr.components(fr.build("d", 100, 1.0, span_km=100, dcf_frac=0.2))
    assert dcf["dcf"] == pytest.approx(0.2 * dcf["glass"])


def test_costs():
    assert fr.dark(20, 20, 1, 7, 7) == 3 and fr.lit(10) == 120
    assert fr.break_even_years(10, 2, 0, 1) == pytest.approx(1.0)
    assert fr.break_even_years(10, 20, 0, 1) == float("inf")
