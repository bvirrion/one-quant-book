import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_colobill as cb  # noqa: E402


def test_bill_arithmetic():
    s = cb.SCHEDULES["nasdaq-ny11-4"]
    b = cb.bill(s, [("uhd_cabinet", 2), ("cabinet_install", 2), ("power_install_p3", 2)], term_months=36)
    assert b["monthly"] == 14_460 and b["one_time"] == 21_000 and b["amortised"] == pytest.approx(583.333, rel=1e-5)
    assert b["annual"] == pytest.approx(12 * (14_460 + 21_000 / 36)) and len(b["lines"]) == 3
    m = cb.bill(cb.SCHEDULES["miax-pearl"], [("ull_10g", 2), ("dr_10g", 1)])
    assert m["monthly"] == 33_500 and m["one_time"] == 0


def test_staleness_and_break_even_and_equalisation():
    s = cb.SCHEDULES["miax-pearl"]
    assert cb.stale(s, "2026-10-15") == [] and len(cb.stale(s, "2026-12-15")) == 3
    assert cb.break_even(45_000, 1_000_000) == pytest.approx(0.045)
    assert cb.equalisation_ns(5, 100) == pytest.approx(95 * 4.8767, rel=1e-4) and cb.equalisation_ns(120, 100) == 0
    with pytest.raises(KeyError):
        cb.bill(s, [("no_such_item", 1)])
