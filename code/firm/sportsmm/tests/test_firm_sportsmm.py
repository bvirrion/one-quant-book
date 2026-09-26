import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_sportsmm as sm  # noqa: E402


def test_home_win():
    p0 = sm.home_win(1.5, 1.1, 1.0, 0)
    draw = sum(sm._pois(k, 1.5) * sm._pois(k, 1.1) for k in range(12))
    away = sm.home_win(1.1, 1.5, 1.0, 0)
    assert math.isclose(p0 + draw + away, 1.0, abs_tol=1e-6)            # 12 goals a side truncate the sum
    assert sm.home_win(1.5, 1.1, 0.0, 1) == 1.0 and sm.home_win(1.5, 1.1, 0.0, 0) == 0.0
    assert sm.home_win(1.5, 1.1, 0.5, 1) > p0


def test_delay_and_caps():
    no, long = sm.season(300, 0.0), sm.season(300, 10.0)
    assert no["sniped_share"] == 1.0 and long["loss_per_goal"] < 1e-9
    assert math.isclose(long["net_per_match"], 90.0)
    capped = sm.season(300, 0.0, cap=100.0)
    assert math.isclose(capped["loss_per_goal"], no["loss_per_goal"] / 10.0, rel_tol=1e-9)


def test_odds_quote():
    back_home, back_not, over = sm.odds_quote(0.46, 0.01)
    assert math.isclose(back_home, 1 / 0.47) and math.isclose(back_not, 1 / 0.55) and math.isclose(over, 0.02)
