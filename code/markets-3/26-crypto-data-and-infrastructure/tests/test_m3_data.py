"""Tests of the Chapter 26 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_data as m


def test_no_loss_no_error():
    r = m.simulate(0.0, n=20_000)
    assert r["silent_wrong"] == 0 and r["stale"] == 0


def test_rates_scale_as_proposition():
    r = m.simulate(0.001)
    assert round(r["silent_wrong"], 4) == 0.0190 and round(r["stale"], 4) == 0.0475
    assert 18 < r["mean_error_msgs"] < 24                         # about K = 20 levels
