"""Tests of the Chapter 13 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from m3_access import routes


def test_three_routes():
    r = routes()
    assert [x["route"] for x in r] == ["exchange", "OTC", "physical BRP"] and all(x["annual"] > 0 for x in r)
