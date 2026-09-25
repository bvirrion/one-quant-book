import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_qis import QISConfig, deflated, example_path, launch, simulate_teams  # noqa: E402

CFG = QISConfig(teams=400)


def test_estimation_noise_has_the_right_size():
    s = simulate_teams(QISConfig(teams=4000))
    assert abs((s["backtest"] - s["true"]).std() - 1 / np.sqrt(10)) < 0.01
    assert abs((s["live"] - s["true"]).std() - 1 / np.sqrt(5)) < 0.01


def test_selection_inflates_the_backtest_not_the_truth():
    s = simulate_teams(CFG)
    L = launch(s, CFG, 3)
    assert L["backtest"].mean() > L["true"].mean() + 0.2 and abs(L["live"].mean() - L["true"].mean()) < 0.05
    assert np.allclose(L["net"], L["live"] - 0.07)


def test_deflated_probabilities_and_the_example_path():
    d = deflated(simulate_teams(CFG), CFG)
    assert ((d["prob"] >= 0) & (d["prob"] <= 1)).all() and d["bt_pass"] > d["bt_fail"]
    e = example_path(CFG)
    sr = e["backtest"].mean() / e["backtest"].std() * np.sqrt(252)
    assert abs(sr - e["sr_backtest"]) < 1e-9
