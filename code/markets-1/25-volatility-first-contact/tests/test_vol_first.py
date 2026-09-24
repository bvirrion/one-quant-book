import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from vol_first import DIVIDEND, chain, index_style, read_chain, true_forward, true_vol


def test_the_chain_gives_back_what_was_put_in():
    strikes = [float(k) for k in range(80, 121, 5)]
    forwards, f, div, vols = read_chain(chain(strikes))
    assert f == pytest.approx(true_forward(), abs=0.01) and max(forwards) - min(forwards) < 0.03
    assert div == pytest.approx(DIVIDEND, abs=0.02)
    assert vols[2] == pytest.approx(true_vol(90.0), abs=0.004) and vols[0] > vols[4] > vols[8]


def test_index_style_volatility_sits_above_the_at_the_money_volatility_when_there_is_skew():
    v = index_style([float(k) for k in range(50, 181)])
    assert 20.5 < v < 24.0
