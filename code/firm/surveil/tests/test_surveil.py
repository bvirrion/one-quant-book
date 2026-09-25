import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_surveil import (  # noqa: E402
    SurveilConfig,
    spoof_scores,
    spoofing_days,
    tpr_at_fpr,
    wash_scores,
)


def test_tpr_at_fpr_by_hand():
    score = np.array([0.1, 0.2, 0.3, 0.4, 0.9, 0.3])
    label = np.array([0, 0, 0, 0, 1, 1])
    r = tpr_at_fpr(score, label, 0.25)
    assert r["tpr"] == 0.5 and r["fpr"] <= 0.25


def test_scores_on_two_account_days():
    d = {"n_small": np.array([100, 600]), "n_large": np.array([300, 150]), "f_small": np.array([52, 30]),
         "f_large": np.array([1, 6]), "c_large": np.array([299, 144]), "linked": np.array([240, 4])}
    s = spoof_scores(d)
    assert s["fill-rate gap"][0] > 3 > s["fill-rate gap"][1] and s["cancel after fill"][0] > 0.5 > s["cancel after fill"][1]
    assert s["order-to-trade"][1] > s["order-to-trade"][0]            # the market maker cancels more


def test_combined_detector_beats_each_part():
    d = spoofing_days(SurveilConfig())
    s = spoof_scores(d)
    tpr = {k: tpr_at_fpr(v, d["label"])["tpr"] for k, v in s.items()}
    assert tpr["gap x cancel"] > max(tpr["fill-rate gap"], tpr["cancel after fill"]) and tpr["order-to-trade"] < 0.05


def test_wash_share_by_hand():
    s = wash_scores({"trades": np.array([100, 0]), "self": np.array([25, 0])})
    assert s["self-match share"].tolist() == [0.25, 0.0]
