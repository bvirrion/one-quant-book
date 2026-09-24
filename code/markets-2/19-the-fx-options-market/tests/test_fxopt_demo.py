"""Chapter 19 of Book 2: the smiles and the barrier behave as the text says."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from fxopt_demo import USDJPY, barrier_curve, smile, smile_curve


def test_premium_adjustment_lowers_strikes():
    reg, pa = smile(USDJPY, "spot", False), smile(USDJPY, "spot_pa", True)
    assert pa["k_c"] < reg["k_c"] and pa["k_p"] < reg["k_p"] and pa["k_atm"] < pa["fwd"] < reg["k_atm"]


def test_smile_curve_passes_through_anchors():
    sm = smile(USDJPY, "spot", False)
    curve = dict(smile_curve(USDJPY, "spot", False, n=3))
    assert len(curve) == 3 and sm["vol_p"] > USDJPY["atm"]


def test_barrier_value_and_delta():
    rows = barrier_curve()
    assert all(v == 0 for s, v, _ in rows if s <= 1.12) and all(d > 0.5 for s, _, d in rows if s > 1.1205)
