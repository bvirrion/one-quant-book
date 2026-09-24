"""Numbers gate: every numerical answer printed in Book 3, Chapter 11 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/degreeday"))
from firm_degreeday import ffa_settlement, hdd, swap_payoff
from m3_weather import freight_month, stats, tce, utility_put

S = stats()
P = utility_put()
PR = utility_put(detrended=False)


def test_text():
    assert S["min"][0] == 2012 and round(S["min"][1]) == 3932 and round(S["max"][1]) == 5999 and S["max"][0] == 2014
    assert S["n"] == 36 and round(S["mean"], 1) == 4911.8 and round(S["slope_decade"]) == -125
    assert round(tce()) == 28667
    assert freight_month() == 72_000
    assert round(P["fair_strike"]) == 4677 and round(P["strike"]) == 4209 and P["freq"] == 0.2
    assert round(P["mean"] / 1e6, 2) == 0.61 and round(P["p90"] / 1e6, 2) == 1.60 and round(P["max"] / 1e6, 2) == 9.30
    assert round(PR["fair_strike"]) == 4871 and round(PR["mean"] / 1e6, 2) == 0.56


def test_exercises():
    assert hdd((40 + 22) / 2) == 34
    assert round((1_500_000 - 450_000 - 100_000) / 38) == 25_000
    assert round(swap_payoff(4054, 4700, 20_000) / 1e6, 2) == -12.92
    assert ffa_settlement([19_500], 21_000, 30) == -45_000
    assert round(S["sd"]) == 477


def test_problem():
    assert round(P["freq"] * 30) == 6
