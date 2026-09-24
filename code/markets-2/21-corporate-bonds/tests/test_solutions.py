"""Numbers gate: every numerical answer printed in Book 2, Chapter 21 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from credit_demo import (
    COUPON,
    GOVT,
    SWAP,
    YEARS,
    ZERO,
    asset_swap_spread,
    callable_oas,
    fallen_angel,
    g_spread,
    i_spread,
    load_hqm,
    measures,
    spread_price_impact,
    yield_from_price,
    z_spread,
)

M = measures()
OPT = callable_oas()
F = fallen_angel()
H = {d: round(h - g, 2) for d, h, g in load_hqm()}


def test_text():
    assert round(M["yield"] * 100, 4) == 5.6751 and (round(M["govt7"] * 100, 2), round(M["swap7"] * 100, 2)) == (4.5, 4.25)
    assert (round(M["g"] * 1e4, 1), round(M["i"] * 1e4, 1), round(M["z"] * 1e4, 1), round(M["asw"] * 1e4, 1)) == (
        117.5, 142.5, 140.7, 142.9)
    assert round(OPT["option"], 2) == 4.80 and round(OPT["cost_bp"], 1) == 79.7 and round(OPT["oas"] * 1e4) == 61
    assert round(M["z"] * 1e4) == 141
    assert (H["2007-01-01"], H["2008-10-01"], H["2020-03-01"], H["2020-04-01"], H["2026-08-01"]) == (
        0.92, 5.04, 2.05, 2.11, 0.90)
    assert round(0.014 / 0.6 * 100, 1) == 2.3


def test_exercises():
    assert (round((0.061 - 0.0468) * 1e4), round((0.061 - 0.044) * 1e4)) == (142, 170)
    assert round(spread_price_impact(6, 0.008), 1) == -4.8
    assert round((M["asw"] - M["z"]) * 1e4, 1) == 2.2
    assert (round(z_spread(COUPON, YEARS, 85, ZERO) * 1e4, 1), round(asset_swap_spread(COUPON, YEARS, 85, ZERO) * 1e4, 1)) == (
        401.6, 375.5)
    assert round(0.014 / 0.6 * 100, 2) == 2.33
    y = yield_from_price(COUPON, YEARS, 105)
    assert round(y * 100, 4) == 4.6548
    assert (round(g_spread(y, YEARS, GOVT) * 1e4, 1), round(i_spread(y, YEARS, SWAP) * 1e4, 1),
            round(z_spread(COUPON, YEARS, 105, ZERO) * 1e4, 1), round(asset_swap_spread(COUPON, YEARS, 105, ZERO) * 1e4, 1)) == (
        15.5, 40.5, 41.2, 43.2)


def test_problem():
    assert (F["pre_to_down"], round(spread_price_impact(6, 0.008), 1), round(F["reaction_at_down"], 1)) == (-9.0, -4.8, -4.2)
    assert round(4.8 / 9 * 100) == 53
    assert (F["overshoot_pts"], F["overshoot_usd"], F["buyer_gain_pts"]) == (-3.0, -1_500_000.0, 3.0)
    assert round(4.00 * 0.25, 1) == 1.0


def test_seniority_figure():
    value, secured, senior, sub = 600, 200, 500, 200
    left = value - secured
    assert (min(secured, value) / secured, min(left, senior) / senior, max(0, left - senior) / sub) == (1.0, 0.8, 0.0)
