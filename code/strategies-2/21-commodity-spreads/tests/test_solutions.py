"""Numbers gate: every numerical answer printed in Book 9, chapter 21 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "commspread"))
from firm_commspread import board_crush, crack_321, spark  # noqa: E402
from s2_commspread import bands, bottleneck, real, table  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_table():
    t = table()
    got = {k: (r(v["annual"], 1), r(v["sr"]), r(v["corr"])) for k, v in t.items() if k != "spread_corr"}
    assert got == {"crack": (15.4, 1.05, -0.12), "crack_deseason": (6.2, 0.44, -0.07), "seasonal": (7.4, 0.78, -0.15),
                   "location": (3.8, 0.48, 0.01), "quality": (2.6, 0.98, 0.01), "combined": (got["combined"][0], 1.69, -0.13)}
    assert r(t["spread_corr"]) == -0.36


def test_bottleneck():
    b = bottleneck()
    assert (r(b["before"], 1), r(b["first_half"], 1), r(b["through"], 1), r(b["after"], 1)) == (35.3, -14.1, -9.3, 8.4)


def test_bands():
    b = bands()
    assert [(r(v["sr"]), r(100 * v["inmarket"], 0)) for v in b.values()] == [(0.85, 73.0), (1.05, 56.0), (0.65, 31.0)]


def test_spreads_by_hand():
    assert (crack_321(80, 2.5, 3.0), spark(50, 3, 7), spark(50, 3, 7.5), r(board_crush(10, 300, 50))) == (32.0, 29, 27.5, 2.1)


def test_real():
    x = real()
    assert (r(x["crack321_mean"]), r(x["crack321_sd"]), r(x["crack321_max"]), x["crack321_max_date"], r(x["crack321_min"]),
            x["crack321_min_date"], r(x["crack321_halflife"], 0), r(x["crack321_corr_dwti"])) == (
        21.3, 11.67, 75.89, "2022-05-13", -1.62, "2008-09-22", 51.0, -0.38)
    assert (r(x["brentwti_mean"]), r(x["brentwti_sd"]), r(x["brentwti_max"]), x["brentwti_max_date"], r(x["wti_min"]),
            x["wti_min_date"], r(x["brentwti_min"]), r(x["brentwti_halflife"], 0), r(x["brentwti_ac1_changes"])) == (
        4.76, 5.97, 54.34, "2020-04-20", -36.98, "2020-04-20", -22.18, 16.0, -0.36)
    assert (r(x["crack321_rule_sr"]), r(x["crack321_rule_sr_ex_apr2020"]), r(x["crack321_rule_late_sr_ex_apr2020"]),
            r(x["crack321_rule_corr_dwti"])) == (0.48, 0.35, 0.24, -0.02)
    assert (r(x["brentwti_rule_sr"]), r(x["brentwti_rule_sr_ex_apr2020"]), r(x["brentwti_rule_late_sr_ex_apr2020"]),
            r(x["brentwti_rule_corr_dwti"])) == (0.83, 0.85, 0.32, -0.09)
    assert (int(x["season_up"]), int(x["season_years"]), r(x["season_mean"]), r(x["season_t"], 1), r(x["season_worst"])) == (
        14, 20, 6.17, 2.8, -11.97)
    assert (r(x["crack321_rule_annual"], 1), r(x["crack321_rule_annual_ex_apr2020"], 1), r(x["brentwti_rule_annual"], 1),
            r(x["brentwti_rule_annual_ex_apr2020"], 1), r(100 * x["crack321_rule_inmarket"], 0),
            r(100 * x["brentwti_rule_inmarket"], 0)) == (13.5, 7.7, 20.1, 14.0, 54.0, 50.0)
    assert (x["crack321_rule_best_date"], x["brentwti_rule_best_date"]) == ("2020-04-20", "2020-04-21")
