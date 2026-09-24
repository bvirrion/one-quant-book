"""Tutorial of Book 6, chapter 8: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_lmm as m


def test_caplets_within_two_standard_errors():
    assert all(abs(mc - tg) <= 2 * err for _, tg, mc, err in m.caplet_check())
