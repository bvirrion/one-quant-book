import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_fxlp as fx  # noqa: E402


def test_fair_price_and_venues():
    p, w = fx.fair_price([1.0, 2.0], [0.3, 0.6], [0.0, 0.0], 0.05)
    assert math.isclose(w[0], 0.8) and math.isclose(p, 1.2)
    _, w2 = fx.fair_price([1.0, 2.0], [0.3, 0.3], [100.0, 0.0], 0.05)       # a stale venue loses weight
    assert w2[1] > w2[0]
    e = fx.venue_errors(n=5000)
    assert e["consolidated"] < e["primary"]


def test_stream_last_look():
    tiers = {"a": (0.3, 1.0, 0.3, 0.6)}
    none = fx.stream(tiers, policy="none", n=4000)
    asym = fx.stream(tiers, policy="asymmetric", n=4000)
    assert none["a"]["reject"] == 0.0 and asym["a"]["reject_informed"] == 1.0
    assert asym["a"]["capture"] > none["a"]["capture"]


def test_internalise_and_cross():
    full = fx.internalise(1.0, trades=2000)
    assert full["risk_sd"] == 0.0 and math.isclose(full["hedge"], 2000 * 0.25)
    loose, tight = fx.internalise(0.0, trades=4000, skew=0.0005), fx.internalise(0.0, trades=4000, skew=0.005)
    assert tight["mean_abs_inventory"] < loose["mean_abs_inventory"]
    bid, ask = fx.synthetic_cross(1.0850, 1.0851, 150.20, 150.21)
    assert math.isclose(bid, 1.0850 * 150.20) and math.isclose(ask, 1.0851 * 150.21)
    b2, a2 = fx.synthetic_cross(1.0850, 1.0851, 0.8500, 0.8501, invert_b=True)
    assert math.isclose(b2, 1.0850 / 0.8501) and math.isclose(a2, 1.0851 / 0.8500)
