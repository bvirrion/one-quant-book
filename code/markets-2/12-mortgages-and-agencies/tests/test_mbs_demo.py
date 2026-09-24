"""Chapter 12 of Book 2: the illustrative pass-through behaves as the text says."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mbs_demo import Y0, load_fed_mbs, mbs_price, price_yield, risk_table, speed_at, static_price


def test_at_the_money_is_par_for_both():
    assert abs(mbs_price(Y0) - 100.0) < 1e-9 and abs(static_price(Y0) - 100.0) < 1e-9


def test_price_flattens_below_the_money():
    rows = price_yield()
    gains = [b - a for (_, a, _), (_, b, _) in zip(rows[1:], rows[:-1], strict=True)]   # price rise per 25 bp fall
    assert gains[-1] > gains[0]                     # gains shrink as rates fall
    assert all(m < s for y, m, s in rows if y < 5.99)


def test_speeds_and_durations_move_together():
    r = risk_table()
    assert speed_at(0.055) > speed_at(0.060) > speed_at(0.065)
    assert r[0.055]["duration"] < r[0.060]["duration"] < r[0.065]["duration"]
    assert all(v["convexity"] < 0 for v in r.values())


def test_fed_data():
    rows = load_fed_mbs()
    assert rows[0][0] == "2002-12-25" and rows[-1][0] == "2026-08-26" and len(rows) == 285
    assert max(v for _, v in rows) > 2700
