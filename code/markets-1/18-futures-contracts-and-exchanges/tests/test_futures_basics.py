import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from futures_basics import SPECS, hedge, leverage, roll_open_interest

S = {s.root: s for s in SPECS}


def test_tick_values_and_notionals():
    assert S["ES"].tick_value == 12.5 and S["ZN"].tick_value == 15.625 and S["FGBL"].tick_value == 10.0
    assert S["ES"].notional == 300_000 and S["CL"].notional == 70_000
    assert S["ES"].tick_bp == pytest.approx(0.4167, abs=1e-4)


def test_leverage_and_hedge():
    assert leverage(S["ES"], 20_000.0) == 15.0
    n, resid = hedge(10_000_000, 1.2, S["ES"])
    assert n == 40 and resid == 0.0
    n, resid = hedge(1_000_000, 1.0, S["ES"])
    assert n == 3 and resid == pytest.approx(100_000)


def test_roll_conserves_open_interest_roughly():
    front, nxt = roll_open_interest(40, 22, 1.6, 2.4, 18)
    assert front[0] > 2.3 and nxt[-1] > 2.3 and abs(front[22] - nxt[22]) < 0.1
