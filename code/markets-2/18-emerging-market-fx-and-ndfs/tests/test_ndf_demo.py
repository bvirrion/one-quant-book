"""Chapter 18 of Book 2: the data and demo behave as the text says."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from ndf_demo import load_eurchf, unpeg


def test_floor_held_in_the_ecb_data():
    r = load_eurchf()
    during = [v for d, v in r if "2011-09-07" <= d <= "2015-01-14"]
    assert min(during) >= 1.20 and len(r) == 1794


def test_leverage_multiples_scale():
    u = unpeg()
    m = u["by_leverage"]
    assert abs(m[50] / m[5] - 10) < 1e-12 and m[5] < 1 < m[10]
