"""Numbers gate: every numerical answer printed in Book 16, chapter 10 (text and solutions)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_pay as m  # noqa: E402

bp = m.bp


def r(x, d=2):
    return round(float(x), d)


def test_hook_and_hand_numbers():
    h = m.hook()
    assert (r(100 * h["p_20_or_more"], 1), r(100 * h["p_minus2_or_less"], 1), h["pay_20"]) == (11.5, 15.9, 3.0)
    assert r(1 / h["p_20_or_more"], 1) == 8.7 and r(1 / h["p_minus2_or_less"], 1) == 6.3
    assert bp.pool_from_profit(100, 60, 10, 0.2) == 6.0 and r(bp.pool_from_revenue(100, 0.06)) == 6.0
    assert bp.pool_from_profit(70, 60, 10, 0.2) == 0.0 and r(bp.pool_from_revenue(70, 0.06)) == 4.2
    assert r(bp.pool_from_profit(120, 60, 10, 0.2)) == 10.0 and r(bp.pool_from_revenue(120, 0.06)) == 7.2
    plan = bp.DeferralPlan(0.6, 4)
    assert r(sum(bp.schedule(1.0, plan)[k] for k in range(5))) == 1.0 and m.retention() == 1.0


def test_closed_forms():
    assert r(100 * bp.luck_share_linear(4, 10), 1) == 86.2 and r(bp.years_for_correlation(4, 10, 0.8), 1) == 11.1
    assert r(100 * bp.luck_share_linear(8, 10), 1) == 61.0 and r(bp.years_for_correlation(8, 10, 0.8), 2) == 2.78


@pytest.mark.reference
def test_simulated():
    c = m.correlations()
    assert [r(c[k][1]) for k in m.RULES] == [0.35, 0.34, 0.37] and [r(c[k][0]) for k in m.RULES] == [0.64, 0.63, 0.61]
    assert r(100 * m.luck_share_formulaic(), 0) == 87
    sim, lin = m.corr_by_years()
    assert (r(sim[0]), r(sim[4]), r(sim[11], 1)) == (0.35, 0.64, 0.8)
    assert r(m.correlations(n_desks=500, years=10)["formulaic"][0]) == 0.76


def test_small_runs():
    c = m.correlations(n_desks=60)
    assert all(c[k][0] > c[k][1] > 0 for k in m.RULES)
