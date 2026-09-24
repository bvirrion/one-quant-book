"""Tests of the chapter 28 teaching module (Book 6)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_tradecontrol as m


def test_blotter_shape():
    b = m.blotter()
    assert len(b) == 2060 and sum(t.fraud for t in b) == 60


def test_two_rules_stricter():
    s = m.surveillance()
    assert s["two"]["combined"]["hit"] <= s["one"]["combined"]["hit"]
    assert s["two"]["combined"]["false"] <= s["one"]["combined"]["false"]


def test_bic_monotone():
    assert m.bic(1.0) == 0.12 and m.bic(40) > m.bic(35) > m.bic(10)
