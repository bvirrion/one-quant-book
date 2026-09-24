"""Tutorial of Book 6, chapter 21: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_var as m


def test_delta_gamma_tracks_full_revaluation():
    o = m.measures()
    assert abs(o["dg"][0][0] / o["hs"][0][0] - 1) < 0.01
    assert o["delta_only"][0] < o["hs"][0][0]
