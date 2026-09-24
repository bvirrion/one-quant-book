"""Numbers gate: every numerical answer printed in Book 3, Chapter 13 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/nominate"))
from firm_nominate import uncovered_exposure
from m3_access import baseload, first_trade, routes

B = baseload()
F = first_trade()
R = {r["route"]: r for r in routes()}


def test_text():
    assert round(B["notional"] / 1e6, 1) == 37.2
    assert uncovered_exposure(3e6, -1e6, 2e6) == 1e6 and uncovered_exposure(3e6, 0.5e6, 2e6) == 1.5e6


def test_exercises():
    assert B["mwh"] == 438_000 and round(B["notional"] / 1e6, 2) == 37.23
    assert 120 - 30 - 80 == 10
    assert round(R["exchange"]["collateral"] / 1e6, 2) == 4.47 and round(R["exchange"]["annual"] / 1e6, 3) == 0.283
    assert round(R["OTC"]["collateral"] / 1e6, 2) == 6.21 and round(R["OTC"]["annual"] / 1e6, 3) == 0.118
    assert R["physical BRP"]["collateral"] == 5e5 and round(R["physical BRP"]["annual"] / 1e6, 3) == 0.175
    m = (R["OTC"]["annual"] - 60_000) / (B["notional"] * 0.05)
    assert round(m * 100, 1) == 3.1


def test_problem():
    assert round(F["margin"] / 1e6, 2) == 4.47 and round(F["lc"] / 1e6, 2) == 6.21
    assert round(F["posted"] / 1e6, 2) == 4.97 and F["carry"] == 248_380 and round(F["lc_fee"]) == 93_075
