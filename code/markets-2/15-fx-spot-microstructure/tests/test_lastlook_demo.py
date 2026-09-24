"""Chapter 15 of Book 2: the simulated stream behaves as the text says."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from lastlook_demo import THRESHOLD, by_hold, no_last_look


def test_informed_rejected_more_than_uninformed():
    for _, t in by_hold("asymmetric", THRESHOLD)[1:] + by_hold("symmetric", THRESHOLD)[1:]:
        assert t["reject_informed"] > t["reject_uninformed"]


def test_asymmetric_markout_rises_with_hold_symmetric_does_not():
    a = [t["markout"] for _, t in by_hold("asymmetric", THRESHOLD)]
    s = [t["markout"] for _, t in by_hold("symmetric", THRESHOLD)]
    assert a == sorted(a) and max(s) - min(s) < 0.002
    assert min(s) > no_last_look()["markout"]
