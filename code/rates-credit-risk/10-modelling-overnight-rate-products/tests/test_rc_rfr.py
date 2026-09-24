"""Tutorial of Book 6, chapter 10: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_rfr as m


def test_backward_cap_dominates_and_monte_carlo_agrees():
    t = m.cap_totals()
    assert t["backward"] > t["forward"]
    cf, mc, se = m.mc_check()
    assert abs(mc - cf) < 3 * se
