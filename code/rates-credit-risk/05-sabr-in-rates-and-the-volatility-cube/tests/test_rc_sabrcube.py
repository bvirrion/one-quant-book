"""Tutorial of Book 6, chapter 5: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_sabrcube as m


def test_cube_fits_every_section_within_a_basis_point():
    _, err = m.build_cube()
    assert len(err) == 16 and max(err.values()) < 1e-4


def test_shift_orders_the_deep_receiver():
    d = m.deep_receiver()
    assert d["shift0.01"] < d["shift0.03"] < d["normal"]
