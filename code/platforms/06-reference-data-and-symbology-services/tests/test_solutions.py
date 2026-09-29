"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 6 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_refdata as P


def r(x, d=1):
    return round(float(x), d)


def test_small_runs():
    u = P.universe()
    assert len(u.isin) == 110 and len(u.ticker_changes) == 12 and len(u.reused) == 5 and len(u.splits) == 20
    assert sum(s[5] is not None for s in u.splits) == 1


def test_golden_copy_and_mapping():
    u = P.universe()
    rd, info = P.build(u)
    assert P.golden_quality(rd, u) == {"instrument_days": 52492, "A": 0, "B": 153, "golden": 0, "conflict": 150}
    assert P.golden_quality(rd, u, "lot") == {"instrument_days": 52492, "A": 6, "B": 0, "golden": 6, "conflict": 6}
    m = P.mapping_differs(rd, u)
    assert (m["ticker_days"], m["differ"], r(100 * m["share"])) == (10493, 384, 3.7)
    j0, day, i0 = info["first_reuse"]
    assert (j0, day, i0) == (100, 176, 56) and u.ticker_changes[0] == (56, 33, "N056")
    assert rd.conflicts("ticker", day, day) == [(57, {"A": "N056", "B": "T056"})]
    assert 178 - 33 + 1 == 146


def test_basket_and_actions():
    u = P.universe()
    rd, _ = P.build(u)
    b = P.basket_backtest(rd, u)
    assert (r(100 * b["truth"]), r(100 * b["pit"]), r(100 * b["naive"])) == (23.5, 23.5, -16.6)
    assert (r(100 * b["right_names_unadjusted"]), r(100 * b["today_mapping_adjusted"])) == (-22.3, 29.2)
    assert r(100 * (b["naive"] - b["truth"])) == -40.1
    assert r(100 * (b["right_names_unadjusted"] - b["truth"])) == -45.8
    assert r(100 * (b["today_mapping_adjusted"] - b["truth"])) == 5.7
    assert (b["n_changed"], b["n_split"], len(b["tickers"])) == (5, 6, 20)
    e = u.splits[0]
    assert e[:5] == ("CA00", 30, 386, 412, 4.0)
    pid = rd.pid(u.isin[30])
    assert [rd.factor(pid, 0, 499, k) for k in (385, 386, 389, 412)] == [1.0, 1.0, 4.0, 4.0]
    c = u.splits[19]
    assert c[5] == 63 and rd.factor(rd.pid(u.isin[c[1]]), 0, 499, 499) == 1.0


def test_exercises():
    u = P.universe()
    rd, _ = P.build(u)
    rd.precedence["ticker"] = ("B", "A")                 # exercise 7: B first for the ticker
    assert P.golden_quality(rd, u)["golden"] == 150
    cm = P.counterparties()
    assert cm.ultimate_parent("LEI-FUND", 255, 255) == "LEI-FUND" and cm.ultimate_parent("LEI-FUND", 255, 262) == "LEI-HOLD"
    assert cm.ultimate_parent("LEI-FUND", 240, 262) == "LEI-FUND"
