"""Tests of the Chapter 24 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_business as m


def test_summary():
    s = m.summary()
    assert s["loan_usd"] == 1_000_000 and round(s["calls_usd"]) == 264_619
    assert abs(s["calls_mc_usd"] / s["calls_usd"] - 1) < 0.01
    assert round(s["hedge_tokens"]) == 992_331 and round(s["hedge_share"], 3) == 0.496


def test_curves():
    fees = dict(m.fee_by_vol())
    assert fees[0.4] < fees[1.2] < fees[2.4]
    rows = m.hedge_curves()
    assert rows[0][1] < rows[-1][1] <= 2_000_000
