"""Tutorial of Book 6, chapter 12: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_mbs as m


def test_negative_convexity_and_extension():
    b = m.base()
    assert b["convexity"] < 0 < b["option_cost"]
    assert m.duration_at(0.01, b["oas"])["duration"] > b["duration"]
