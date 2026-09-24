"""Tutorial of Book 6, chapter 16: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_energy as e


def test_value_ordering_of_storage_and_swing():
    s = e.storage()
    assert s["intrinsic"] < s["rolling"] and s["intrinsic"] < s["lsm"]
    w = e.swing()
    assert w["intrinsic"] < w["lsm"] < w["strip"]


def test_the_fast_facility_captures_the_storm():
    st = e.storm()
    assert st["fast"]["value"] > 5 * st["slow"]["value"]
