"""Tests of the Chapter 21 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_perpdex as m


def test_replay():
    assert m.replay("arrival")[-1] == (1000, 610, 940.0)
    assert m.replay("cancels_first")[-1] == (1000, 0, 0.0)
    assert m.replay("arrival", p_taker_first=0.0)[-1][1] == 0      # maker always first: nothing picked off


def test_squeeze():
    b = m.BUFFER_3X
    assert round(b, 4) == 0.1111
    assert round(m.squeeze_loss(10e6, 4.0, b) / 1e6, 2) == 38.89 and m.squeeze_loss(10e6, 0.05, b) == 0
    assert round(m.oi_cap_for(5e6, 5.0, b) / 1e6, 3) == 1.023
