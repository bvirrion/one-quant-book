"""Tutorial of Book 6, chapter 24: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_alm as m


def test_long_duration_bank():
    e = m.eve_table()["delta"]
    assert e["parallel_up"] < 0 < e["parallel_down"]
    assert m.htm_loss()["loss"] < 0
