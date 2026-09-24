"""Tutorial of Book 6, chapter 22: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_stress as m


def test_every_episode_exceeds_the_ten_day_var():
    assert all(-p > m.var10() for _, _, p in m.historical_table())
