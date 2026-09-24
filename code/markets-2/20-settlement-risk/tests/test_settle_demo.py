"""Chapter 20 of Book 2: the book's exposure behaves as the text says."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from settle_demo import profiles


def test_exposure_ordering():
    p = profiles()
    for (t, g), (_, n), (_, v) in zip(p["gross"], p["net"], p["pvp"], strict=True):
        assert g >= n >= v >= 0, t
    assert p["gross"][-1][1] == 0
