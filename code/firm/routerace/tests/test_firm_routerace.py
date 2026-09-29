import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_routerace as r  # noqa: E402


def test_marginals_and_first_arrival():
    a, b = r.Route("a", 1000, 1500), r.Route("b", 1000, 1500)
    first, draws = r.first_arrival([a, b], 0.3, n=100_000)
    assert np.median(draws[:, 0]) == pytest.approx(1000, rel=0.01) and np.percentile(draws[:, 1], 99) == pytest.approx(1500, rel=0.02)
    assert (first <= draws.min(axis=1) + 1e-9).all()
    assert r.percentile_gain([a, b], 0.0, n=100_000) > r.percentile_gain([a, b], 0.9, n=100_000) > 0


def test_perfect_correlation_gains_nothing():
    a = r.Route("a", 1000, 1500)
    assert r.percentile_gain([a, a], 1.0, n=20_000) == pytest.approx(0.0, abs=1e-9)


def test_duplicates_and_inflation():
    d = np.array([[10.0, 11.0, 30.0]])
    assert r.duplicates(d, 5.0) == {"accepted_duplicates": 1.0, "rejected": 1.0}
    assert r.duplicates(d, 50.0)["accepted_duplicates"] == 0.0
    assert r.duplicates(d, 0.0, rule="ever") == {"accepted_duplicates": 0.0, "rejected": 2.0}
    assert r.path_inflation(2 * 1.462 / r.C0 * 1e12, 1e6) == pytest.approx(1.0)
    assert r.break_even_price(100, 10) == 1000
