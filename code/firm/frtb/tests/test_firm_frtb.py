import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_frtb as f


def test_girr_correlation_matches_the_standard():
    assert round(f.girr_rho(1, 5), 4) == 0.8869            # MAR21.46 footnote example: 88.69%
    assert round(f.girr_rho(2, 10), 3) == 0.887 and f.girr_rho(0.25, 30) == 0.40
    assert f.scenario(0.9, "high") == 1.0 and math.isclose(f.scenario(0.4, "low"), 0.3)


def test_aggregation_and_fallback():
    assert math.isclose(f.within(np.array([3.0, 4.0]), np.eye(2)), 5.0)
    # opposite-signed buckets with gamma making the sum negative trigger the clipped specification
    v = f.across([1.0, 1.0], [5.0, -5.0], 0.6)
    assert v >= 0.0 and math.isclose(v, math.sqrt(2 - 2 * 0.6))


def test_curvature_and_capital_helpers():
    up, dn = f.cvr(0.0, -3.0, -1.0, 0.1, 10.0)
    assert (up, dn) == (4.0, 0.0)
    assert f.fx_curvature({"x": (4.0, 0.0)}) == 4.0
    assert math.isclose(f.ima_capital(10.0, 8.0), 12.0) and f.amber_surcharge(10.0, 4.0) == 3.0
    assert math.isclose(f.es_liquidity([3.0]), 3.0)
    assert math.isclose(f.es_liquidity([3.0, 2.0]), math.sqrt(9 + 4 * 1.0))


def test_pla_statistics_and_zones():
    a = np.random.default_rng(1).normal(size=250)
    assert math.isclose(f.spearman(a, a ** 3), 1.0) and f.ks_stat(a, a) == 0.0
    assert f.pla_zone(0.85, 0.05) == "green" and f.pla_zone(0.75, 0.05) == "amber"
    assert f.pla_zone(0.85, 0.10) == "amber" and f.pla_zone(0.69, 0.05) == "red" and f.pla_zone(0.9, 0.13) == "red"


def test_risk_factor_eligibility():
    assert f.rfet(list(range(0, 365, 14)))                      # every two weeks: 27 observations
    assert not f.rfet(list(range(0, 100, 3)) + [300, 330])      # 36 observations but a long gap
    assert not f.rfet(list(range(0, 365, 20)))                  # 19 observations
