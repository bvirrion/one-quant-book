"""Numbers gate: every numerical answer printed in Book 2, Chapter 24 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/tranche"))
from firm_tranche import expected_tranche_loss, intrinsic_upfront, tranche_loss
from index_demo import SPREADS, TRANCHES, annuity, skew_trade, spread_from_upfront, tutorial, upfront

T = tutorial()
S = skew_trade()


def test_text():
    assert round(1e4 * T["median"]) == 55 and round(1e4 * T["min"], 1) == 6.6 and round(1e4 * T["max"]) == 459
    assert sorted(round(1e4 * s) for s in SPREADS if s > 0.03) == [335, 459]
    assert round(1e4 * T["average"], 1) == 75.3 and round(100 * T["upfront"], 3) == -1.157
    assert round(1e4 * T["intrinsic"], 1) == round(1e4 * T["weighted"], 1) == 73.6
    assert round(1e4 * S["entry"], 1) == 65.6
    assert round(S["pnl_close"] / 1e6, 2) == 3.55 and round(S["pnl_widen"] / 1e6, 2) == -5.37
    assert round(S["round_trip_cost"] / 1e6, 2) == 1.53
    assert round(0.03 / 0.0048, 2) == 6.25 and round(0.15 / 0.0048, 2) == 31.25
    assert round(100 * T["p"], 2) == 5.95 and round(100 * T["pool_el"], 2) == 3.57
    el = [expected_tranche_loss(a, d, T["p"], 0.3) for a, d in TRANCHES]
    assert [round(100 * el[0], 1), round(100 * el[1], 1), round(100 * el[2], 2), round(100 * el[3], 2)] == \
        [59.6, 24.1, 7.83, 0.22]
    assert round(100 * T["eq_25"], 1) == 64.0 and round(T["base_corr"], 4) == 0.25
    assert [round(100 * T[k], 1) for k in ("mezz_10", "mezz_20", "mezz_45")] == [24.3, 25.0, 21.9]


def test_exercises():
    assert 1e9 / 125 * 0.6 == 4.8e6 and 1e9 - 1e9 / 125 == 992e6
    assert [tranche_loss(x, 0.03, 0.07) for x in (0.02, 0.05, 0.09)] == [0.0, 0.5, 1.0]
    u = intrinsic_upfront([upfront(0.005), upfront(0.025)])
    assert round(1e4 * spread_from_upfront(u), 1) == 146.0
    assert (round(annuity(0.025), 3), round(annuity(0.005), 3)) == (4.085, 4.420)
    el = [expected_tranche_loss(a, d, T["p"], 0.3) for a, d in TRANCHES]
    assert [round(100 * x, 3) for x in el[:3]] == [59.57, 24.09, 7.828] and round(100 * el[3], 3) == 0.224
    assert round(100 * sum((d - a) * x for (a, d), x in zip(TRANCHES, el, strict=True)), 3) == 3.568
    lo, hi, target = 0.2, 0.9, expected_tranche_loss(0.03, 0.07, T["p"], 0.1)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if expected_tranche_loss(0.03, 0.07, T["p"], mid) > target else (lo, mid)
    assert round(lo, 2) == 0.28
    assert round(1e4 * (T["average"] - T["intrinsic"]), 1) == 1.7


def test_problem():
    assert (round(100 * -S["u_index"], 3), round(100 * -S["u_intrinsic"], 3)) == (1.513, 1.157)
    assert round(-S["u_index"] * 1e9 / 1e6, 2) == 15.13 and round(-S["u_intrinsic"] * 1e9 / 1e6, 2) == 11.57
    assert S["default_payout"] == 4.8e6 and S["per_name"] == 8e6
    assert (round(S["single_cost"] / 1e6, 3), round(S["index_cost"] / 1e6, 3)) == (0.657, 0.109)
    assert round((S["single_cost"] + S["index_cost"]) / 1e6, 2) == 0.77
    assert round(S["net_close"] / 1e6, 2) == 2.02 and S["breakeven_bp"] == 3.5
