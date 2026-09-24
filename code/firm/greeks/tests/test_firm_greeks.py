"""Acceptance tests of the Book 5, Chapter 4 build (Greeks in desk units)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "bs"))
from firm_bs import bs, greeks
from firm_greeks import breakeven_vol, bump_greeks, desk_units, hedging_pnl, predict_pnl

P = {"spot": 100.0, "strike": 105.0, "t": 0.5, "r": 0.03, "q": 0.0, "vol": 0.25}


def pricer(spot, strike, t, r, q, vol):
    return bs(spot, strike, t, r, q, vol, "C")


def test_bump_matches_analytic_in_desk_units():
    b = bump_greeks(pricer, P, h_spot=1e-4, h_vol=1e-4, h_rate=1e-5)
    a = desk_units(greeks(100, 105, 0.5, 0.03, 0.0, 0.25, "C"), 100.0)
    assert abs(b["delta"] - a["delta"]) < 1e-7 and abs(b["gamma_1pct"] - a["gamma_1pct"]) < 1e-5
    assert abs(b["vega_pt"] - a["vega_pt"]) < 1e-7 and abs(b["rho_bp"] - a["rho_bp"]) < 1e-8
    assert abs(b["theta_day"] - a["theta_day"]) < 2e-4           # a one-day roll against the derivative


def test_desk_units_definitions():
    a = desk_units({"delta": 0.5, "gamma": 0.02}, 100.0)
    assert a["cash_delta"] == 50.0 and abs(a["gamma_1pct"] - 2.0) < 1e-12 and abs(a["cash_gamma"] - 100.0) < 1e-12


def test_prediction_close_for_small_move():
    g = bump_greeks(pricer, P)
    actual = pricer(**{**P, "spot": 101.0, "t": 0.5 - 1 / 365}) - pricer(**P)
    assert abs(predict_pnl(g, 1.0) - actual) < 0.01


def test_gamma_theta_breakeven_equals_implied_at_zero_rate():
    g = desk_units(greeks(100, 100, 0.25, 0.0, 0.0, 0.2, "C"), 100.0)
    assert abs(breakeven_vol(g["theta_day"], g["cash_gamma"]) - 0.2) < 1e-12
    assert abs(hedging_pnl(g["cash_gamma"], 0.2 * math.sqrt(1 / 365), 0.2, 1 / 365)) < 1e-12
