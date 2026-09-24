"""Tutorial of Book 6, chapter 26: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_modelval as m


def test_finer_steps_reduce_failures():
    v = m.validation()["by_dt"]
    assert v[1 / 12]["failures"] < v[0.25]["failures"]
