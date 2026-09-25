import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_powergas import PowerConfig, battery, forecast_trade, intraday  # noqa: E402

DAY = np.array([[0.0] * 12 + [100.0] * 12])


def test_intraday_without_errors_is_day_ahead():
    idp, err = intraday(np.tile(DAY, (5, 1)), PowerConfig(err_sd=0.0, id_noise=0.0))
    assert np.allclose(idp, np.tile(DAY, (5, 1))) and np.allclose(err, 0.0)


def test_perfect_forecast_never_loses_without_costs():
    cfg = PowerConfig(skill=1.0, threshold=0.0, id_cost=0.0, id_noise=0.0)
    da = np.full((50, 24), 50.0)
    idp, err = intraday(da, cfg)
    assert (forecast_trade(da, idp, err, cfg)["pnl"] >= -1e-9).all()


def test_battery_by_hand():
    assert abs(battery(DAY, PowerConfig(eff=1.0))["cash"][0] - 200.0) < 1e-9
    assert abs(battery(DAY, PowerConfig())["cash"][0] - 200.0 * math.sqrt(0.88)) < 1e-9
    b = battery(DAY, PowerConfig())
    assert abs(battery(DAY, PowerConfig(), committed=b["grid"])["cash"][0]) < 1e-9
