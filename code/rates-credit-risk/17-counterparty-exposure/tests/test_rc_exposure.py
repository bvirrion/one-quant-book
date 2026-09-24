"""Tutorial of Book 6, chapter 17: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_exposure as m


def test_trades_start_at_zero_and_fx_is_a_martingale():
    a, b = m.time0_values()
    assert abs(a) < 1e-3 and abs(b) < 1e-3
    assert abs(m.fx_martingale() - 1.0) < 2e-3


def test_ordering_of_profiles():
    ps = m.profile_set()
    assert ps["csa10"][1]["peak_ee"] < ps["csa20"][1]["peak_ee"] < ps["csa_th"][1]["peak_ee"] < ps["net"][1]["peak_ee"]
