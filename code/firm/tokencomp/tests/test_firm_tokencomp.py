import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_tokencomp as tc  # noqa: E402


def test_schedule_sums_to_one():
    s = tc.schedule(tc.Grant(1.0))
    assert abs(sum(f for _, f in s) - 1) < 1e-12 and s[0] == (12, 0.25) and s[-1][0] == 48


def test_zero_vol_equals_cash():
    g = tc.Grant(100.0, tax=0.3)
    s = tc.summary(tc.simulate(g, 1e-12, 0.0, 10, np.random.default_rng(0)))
    assert abs(s["median"] - 70.0) < 1e-6 and s["p_any_tax_exceeds"] == 0.0


def test_volatility_spreads_and_lowers_median():
    g = tc.Grant(100.0)
    s = tc.summary(tc.simulate(g, 0.8, 0.0, 4000, np.random.default_rng(1)))
    assert s["p10"] < s["median"] < s["cash"] < s["p90"] and 0 < s["p_any_tax_exceeds"] < 1
    assert abs(s["mean"] - s["cash"]) < 0.1 * s["cash"]
