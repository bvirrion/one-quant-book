import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from pnl_day import CLOSING_MID, U, explain, fifo, fx_split, replay, three_numbers, units


def test_the_three_numbers_of_the_hook():
    assert three_numbers() == {"trader": 40_000.0, "risk": 31_000.0, "finance": 27_000.0}


def test_accounting_method_does_not_change_the_total():
    p = replay()
    avg_total = (p.realised + p.unrealised(units(CLOSING_MID))) / U
    r, u = fifo()
    assert avg_total == pytest.approx(31_000) and r + u == pytest.approx(31_000)
    assert r != pytest.approx(p.realised / U)          # but the split differs


def test_explain_adds_up():
    e = explain(30_000, 50.00, 50.40, [("t", -1, 10_000, 50.35, 0), ("t", 1, 5_000, 50.10, 0)], 900, 650)
    assert e["total"] == pytest.approx(sum(v for k, v in e.items() if k != "total"))


def test_fx_split_adds_up():
    s = fx_split(10_000, 40.0, 41.0, 1.10, 1.08)
    assert s["price"] + s["currency"] + s["cross"] == pytest.approx(s["total"])
