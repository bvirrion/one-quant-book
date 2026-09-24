import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_cva as f
from firm_cdscurve import HazardCurve, bootstrap


class Flat:
    def df_t(self, t):
        return math.exp(-0.03 * t)


T = np.linspace(0.0, 5.0, 21)


def test_flat_exposure_and_hazard():
    c = HazardCurve([5.0], [0.02])
    assert math.isclose(f.cva(np.full(21, 1e6), T, c, 0.4), 0.6 * 1e6 * (1 - math.exp(-0.1)), rel_tol=1e-12)


def test_pathwise_with_deterministic_hazard_matches_profile_cva():
    rng = np.random.default_rng(1)
    E = rng.normal(0.0, 1e6, (500, 21))
    D = np.exp(-0.03 * T)[None, :].repeat(500, axis=0)
    dee, _ = f.discounted_profiles(E, D)
    c = HazardCurve([5.0], [0.02])
    assert math.isclose(f.cva_pathwise(E, D, T, np.full((500, 21), 0.02), 0.4), f.cva(dee, T, c, 0.4), rel_tol=1e-10)


def test_first_to_default_is_smaller_and_buckets_add_up():
    dee = np.linspace(0, 2e6, 21)
    c, own = HazardCurve([5.0], [0.03]), HazardCurve([5.0], [0.01])
    assert f.cva(dee, T, c, 0.4, own=own) < f.cva(dee, T, c, 0.4)
    tenors, spreads = [1.0, 3.0, 5.0], [0.01, 0.012, 0.015]
    b = f.cs01_buckets(dee, T, Flat(), tenors, spreads, 0.4)
    par = (f.cva(dee, T, bootstrap(Flat(), tenors, [s + 1e-4 for s in spreads], 0.4), 0.4)
           - f.cva(dee, T, bootstrap(Flat(), tenors, spreads, 0.4), 0.4))
    assert abs(sum(b) - par) < 1e-3 * abs(par)
