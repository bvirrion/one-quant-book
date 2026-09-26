import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tape"))
from firm_lobstats import compare, kaplan_meier, report  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402

TAPE = simulate(TapeConfig(seconds=900.0, seed=4, news_at=None))


def test_kaplan_meier_by_hand():
    # durations 1, 2, 3, 4 with the second censored: S(1)=3/4, S(2)=3/4, S(3)=3/4*1/2, S(4)=0
    assert kaplan_meier([1, 2, 3, 4], [True, False, True, True], (1, 2, 3, 4)) == [0.25, 0.25, 0.625, 1.0]
    assert kaplan_meier([5.0], [True], (1.0,)) == [0.0]


def test_report_on_a_simulated_session():
    rep = report(TAPE)
    assert rep["depth"].shape == (2, 10) and rep["depth"][0].argmax() >= 1          # humped profile
    assert 0.9 < rep["spread"]["one"] <= 1.0 and 1.0 <= rep["spread"]["mean"] < 1.2
    assert rep["cancel_rates"][0] > rep["cancel_rates"][2]
    assert rep["relative"]["max"] <= 10 and rep["relative"]["at_best"] > 0.1
    cl, tl = rep["cancel_life"], rep["trade_life"]
    assert all(np.diff(cl) >= 0) and all(np.diff(tl) >= 0) and cl[-1] > tl[-1]
    assert 5 < rep["cancel_to_trade"] < 40 and 0 < rep["fleeting"] < 0.5 and rep["resilience"] < 5


def test_compare():
    rep = report(TAPE)
    got = compare(rep, {"spread.one": (0.9, 1.0), "cancel_life[3]": (0.5, 1.0), "cancel_to_trade": (10, 25)})
    assert got["spread.one"][3] and not got["cancel_life[3]"][3]            # the simulator cancels too slowly
