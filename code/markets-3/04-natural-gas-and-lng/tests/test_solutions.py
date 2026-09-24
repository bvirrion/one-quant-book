"""Numbers gate: every numerical answer printed in Book 3, Chapter 4 (text and solutions)."""
import pathlib
import sys
from dataclasses import replace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/lngarb"))
from firm_lngarb import breakeven_spread, choose, fob_price, netback, shipping_cost, usd_mmbtu_to_eur_mwh
from m3_lng import ASIA, CARGO, EUROPE, conversion_example, history, summary

F = fob_price(3.0)
S = summary()


def test_text():
    assert round(conversion_example(), 2) == 13.60
    assert round(F, 2) == 3.45
    assert round(shipping_cost(EUROPE, CARGO, F), 2) == 0.54 and round(shipping_cost(ASIA, CARGO, F), 2) == 0.97
    assert round(S["spread"], 2) == 0.33
    assert round(netback(12.0, EUROPE, CARGO, F), 2) == 10.96 and round(netback(12.5, ASIA, CARGO, F), 2) == 11.13
    assert S["n"] == 125 and S["asia"] == 93
    assert S["not_lifted"] == ["2020-02", "2020-03", "2020-04", "2020-05", "2020-06", "2020-07", "2020-08", "2021-02"]
    assert S["peak"]["month"] == "2022-08" and round(S["peak"]["eu"], 2) == 69.98


def test_exercises():
    assert round(usd_mmbtu_to_eur_mwh(10, 1.16), 2) == 29.42 and round(100 / 1.30, 1) == 76.9
    assert round(1.15 * 2.00, 2) == 2.30 and round(2.30 - 2.10, 2) == 0.20
    assert round(11.0 + S["spread"], 2) == 11.33
    assert round(2.0 - 0.30, 2) == 1.70
    b50 = breakeven_spread(EUROPE, replace(ASIA, days=50), CARGO, F)
    assert round(b50, 2) == 1.35 and round(b50 - S["spread"], 2) == 1.02


def test_problem():
    assert round(0.001 * 14 * 100, 1) == 1.4 and round(0.001 * 25 * 100, 1) == 2.5
    nb = netback(12.5, ASIA, CARGO, F)
    assert round((nb * CARGO * (1 - 0.025) - F * CARGO) / 1e6, 1) == 25.9 and round(CARGO * 0.975 / 1e6, 4) == 3.4125
    e2, a2 = replace(EUROPE, charter_per_day=120_000), replace(ASIA, charter_per_day=120_000)
    assert round(breakeven_spread(e2, a2, CARGO, F), 2) == 0.72
    assert choose({"europe": 12.0, "asia": 12.5}, {"europe": e2, "asia": a2}, CARGO, F)[0] == "europe"
    f22 = fob_price(8.81)
    assert round(netback(69.977, EUROPE, CARGO, f22), 2) == 68.85 and round(netback(54.158, ASIA, CARGO, f22), 2) == 52.62
    jun = [c for c in history() if c["month"] == "2020-06"][0]
    assert round(jun["netback"], 2) == 0.72 and round(jun["fob"], 2) == 1.87 and not jun["lift"]
