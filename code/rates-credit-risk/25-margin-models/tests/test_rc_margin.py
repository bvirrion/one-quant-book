"""Tutorial of Book 6, chapter 25: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_margin as m


def test_filtered_model_is_the_most_procyclical():
    r = m.replay_2020()
    assert r["fhs_ratio"] > r["buffer_ratio"] > 1 and r["fhs_ratio"] > r["hs_ratio"]
