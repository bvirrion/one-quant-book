import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_casebook as cb  # noqa: E402


def test_ltcm_reconstruction_matches_the_record():
    r = cb.ltcm_returns()
    path = cb.capital_path(list(r.values()), cb.LTCM["nav_1997"])
    assert path[2] == pytest.approx(cb.LTCM["nav_aug_1998"])
    assert path[3] + cb.LTCM["recap"] == pytest.approx(cb.LTCM["recap"] / cb.LTCM["recap_share_of_nav"])


def test_helpers_and_unwind():
    assert cb.capital_path([0.1, -0.2], 1.0, 1.0) == pytest.approx([1.0, 1.1, 0.88])
    assert cb.days_to_liquidate(1000, 100, 0.1) == pytest.approx(100.0)
    u = cb.quant_unwind(n=50, horizon=8, days=3)
    assert len(u["seller"]) == 8 and u["seller"][-1] < 0 and u["holder"][-1] < 0


def test_exit_race_is_zero_sum_in_the_fall():
    shares = [0.1, 0.3, 0.2, 0.4]
    falls = [cb.exit_race([s], [0.0], 0.6)[0] for s in shares]      # alone: each sells from the top
    race = cb.exit_race(shares, [0.0] * 4, 0.6)
    assert sum(race) == pytest.approx(0.6 / 2)                        # total fall independent of order
    assert race[-1] > race[0] and sum(falls) < sum(race)
    k = cb.race_impact(race[2], 0.2, 0.0, 0.4)
    assert k == pytest.approx(0.6)


def test_rescue_margin_and_ftx():
    x = cb.rescue(1000, 400, 300, 300, 100)
    assert x["old_fraction"] == pytest.approx(0.25) and x["old_book"] == pytest.approx(225)
    assert cb.margin_call(10, 100, 150) == 500 and cb.break_price(10, 500, 100) == 150
    b = cb.ftx_balances()
    assert b["located_a"] < b["payables_a"] and len(cb.ftx_flows()["date"]) == 11
