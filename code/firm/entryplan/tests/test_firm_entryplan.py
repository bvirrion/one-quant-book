import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_entryplan as ep  # noqa: E402

T = [ep.Task("a", 2, 1.0), ep.Task("b", 3, 2.0, ("a",)), ep.Task("c", 1, 1.0, ("a",)), ep.Task("d", 1, 0.0, ("b", "c"))]


def test_schedule_and_critical_path():
    s = ep.schedule(T)
    assert s["b"] == (2, 5, 0) and s["c"] == (2, 3, 2) and s["d"] == (5, 6, 0)
    assert ep.critical_path(T) == ["a", "b", "d"]


def test_costs_npv_irr():
    c = ep.cost_by_month(T, 6)
    assert list(c) == [1.0, 1.0, 3.0, 2.0, 2.0, 0.0]
    assert ep.npv([1.0] * 12, 0.0) == pytest.approx(12.0)
    cash = [-100.0] + [10.0] * 11 + [110.0]
    assert ep.irr(cash) is not None and ep.npv(cash, ep.irr(cash)) == pytest.approx(0.0, abs=1e-6)


def test_entry_cash_and_staging():
    cash = ep.entry_cash(T, 6, 10.0, 1e-9, 4.0, 10)
    assert cash[5] == pytest.approx(0.0) and cash[6] == pytest.approx(6.0)
    stopped = ep.entry_cash(T, 6, 10.0, 1e-9, 4.0, 10, stop=8)
    assert stopped[8] == 0.0 and stopped[7] == pytest.approx(6.0)
    p, s, k = ep.staged_npv(T, 6, np.array([1.0, 100.0]), 1.0, 5.0, 24, 0.0, 2, 10.0, 0.0)
    assert list(k) == [True, False] and s[0] > p[0] and s[1] == pytest.approx(p[1])
