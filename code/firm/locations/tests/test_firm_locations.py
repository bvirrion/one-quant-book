"""Acceptance tests for firm.locations."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_locations as fl  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[4]
P = fl.at.load(ROOT / "data/industry/tax_2026.csv", ROOT / "data/industry/ch_federal_tax_2026.csv")
DUBAI = fl.City("Dubai", "dubai", 5000.0, "usd", "illustrative", "2026", "test")
CHI = fl.City("Chicago", "chicago", 2000.0, "usd", "illustrative", "2026", "test")


def test_disposable_no_tax():
    d = fl.disposable(P, DUBAI, 100_000.0)
    assert d["net"] == 100_000.0 and d["rent"] == 60_000.0 and d["disposable"] == 40_000.0


def test_equivalent_is_inverse():
    g = fl.equivalent(P, DUBAI, 200_000.0, CHI)
    assert fl.disposable(P, CHI, g)["disposable"] == pytest.approx(fl.disposable(P, DUBAI, 200_000.0)["disposable"],
                                                                   abs=2.0)
    assert g > 200_000.0


def test_crossing_none_when_one_dominates():
    assert fl.crossing(P, DUBAI, fl.City("D2", "dubai", 6000.0, "usd", "x", "x", "x")) is None
