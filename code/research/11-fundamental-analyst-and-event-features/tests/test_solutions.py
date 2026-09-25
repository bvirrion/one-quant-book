"""Numbers gate: every numerical answer printed in Book 7, chapter 11 (text and solutions)."""
import datetime as dt
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "fundpit"))
from firm_fundpit import sue
from rs_fundamentals import apple_ttm, calendar_summary, ic_inflation, release_to_filing, restatements, store


def r(x, d=3):
    return round(float(x), d)


def test_calendar():
    c = calendar_summary()
    assert (c["periods"], c["matched"]) == (542, 541)
    assert (c["q_release"], c["q_filing"], c["k_release"], c["k_filing"]) == (23, 29, 26, 48)
    assert (c["q_filing_max"], c["k_filing_max"]) == (41, 60)
    assert (round(100 * c["same_day"]), c["gap"]) == (16, 7)
    by = c["by_name"]
    med = {n: (by.loc[n, ("release", "median")], by.loc[n, ("filing", "median")]) for n in by.index}
    assert med["Home Depot"] == (16, 23) and med["Apple"] == (31, 32) and med["Johnson & Johnson"] == (16, 30)
    assert med["Walmart"] == (17, 33) and med["Exxon Mobil"] == (30, 34)
    assert by.loc["Home Depot", ("release", "std")] == 0 and round(by.loc["Exxon Mobil", ("release", "std")]) == 2
    assert round(by.loc["Apple", ("release", "std")]) == 5
    rf = release_to_filing()
    assert (rf["Microsoft"][0], round(100 * rf["Procter & Gamble"][0]), round(100 * rf["Coca-Cola"][0]),
            round(100 * rf["Intel"][0])) == (1.0, 95, 7, 10)
    assert {n: rf[n][1] for n in ("Apple", "Intel", "Coca-Cola", "Procter & Gamble", "Exxon Mobil", "Home Depot",
                                  "Johnson & Johnson", "Nike", "Walmart")} == {
        "Apple": 1, "Intel": 1, "Coca-Cola": 2, "Procter & Gamble": 2, "Exxon Mobil": 5, "Home Depot": 7,
        "Johnson & Johnson": 14, "Nike": 14, "Walmart": 16}


def test_restatements_and_ttm():
    rs = restatements()
    table = {n: (v["changed"], v["splits"], v["ratios"]) for n, v in rs.items()}
    assert table["Apple"] == (13, 13, [4, 7]) and table["Nike"] == (7, 6, [2]) and table["Microsoft"] == (5, 0, [])
    assert table["Walmart"] == (3, 3, [3]) and table["Coca-Cola"] == (2, 2, [2]) and table["Johnson & Johnson"] == (1, 0, [])
    assert sum(v[0] for v in table.values()) == 31 and sum(v[1] for v in table.values()) == 24
    assert sum(1 for v in table.values() if v[0] == 0) == 4
    s = store()
    assert [s.first(320193, "eps_Q", e)[1] for e in ("2013-12-28", "2014-03-29", "2014-06-28", "2014-09-27")] == [
        14.50, 11.62, 1.28, 1.42]
    assert s.first(320193, "eps_FY", "2014-09-27")[1] == 6.45 and s.first(320193, "eps_FY", "2020-09-26")[1] == 3.28
    assert [v for _, v in s.vintages(789019, "eps_FY", "2017-06-30")][:2] == [2.71, 3.25]
    assert s.vintages(789019, "eps_FY", "2017-06-30")[1][0] == "2018-08-03"
    first, _ = apple_ttm()
    assert (r(first["2014-09-27"], 2), r(first["2020-09-26"], 2)) == (28.82, 10.85)


def test_ic_inflation():
    ic = ic_inflation()
    assert (r(ic["head_mean"], 0), r(ic["in_window"])) == (31, 0.330)
    assert (r(ic["sue_known"]), r(ic["sue_known_se"]), r(ic["sue_end"]), r(ic["sue_end_se"])) == (0.020, 0.006, 0.167, 0.006)
    assert round(ic["sue_end"] / ic["sue_known"]) == 8
    assert (r(ic["bp_end"]), r(ic["bp_end_se"]), r(ic["bp_known_stale"]), r(ic["bp_known_stale_se"])) == (
        0.029, 0.038, -0.005, 0.023)
    assert abs(ic["bp_end"] - ic["bp_known_stale"]) < ic["bp_end_se"] and ic["quarters"] == 39


def test_exercises():
    assert r(4.80 - 3.30, 2) == 1.50
    assert dt.date(2026, 6, 30) + dt.timedelta(days=55) == dt.date(2026, 8, 24)
    assert dt.date(2026, 9, 30) + dt.timedelta(days=40) == dt.date(2026, 11, 9)
    assert dt.date(2025, 12, 31) + dt.timedelta(days=60) == dt.date(2026, 3, 1)
    assert 1.42 / 0.355 == 4.0
    x = np.array([1.00, 1.10, 0.90, 1.20, 1.04, 1.12, 0.96, 1.22, 1.06, 1.16, 0.94, 1.40])
    d = np.round(x[4:] - x[:-4], 2)
    assert list(d) == [0.04, 0.02, 0.06, 0.02, 0.02, 0.04, -0.02, 0.18]
    assert (r(np.std(d[1:7], ddof=1), 4), r(sue(x, 6)[-1], 1)) == (0.0266, 6.8)
    assert r(21 / 63) == 0.333
