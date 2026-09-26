import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_onlinelearn import (  # noqa: E402
    ADWIN,
    CUSUM,
    RLS,
    OnlineSGD,
    PageHinkley,
    alarm_times,
    calibrate,
    drift_stream,
    prequential,
    retrain_schedule,
)


def test_rls_without_forgetting_is_ridge_then_ols():
    rng = np.random.default_rng(0)
    X = rng.standard_normal((300, 4))
    y = X @ np.array([1.0, -2.0, 0.5, 0.0]) + rng.standard_normal(300)
    for delta in (0.5, 1e8):
        m = RLS(4, 1.0, delta)
        prequential(m, X, y)
        ridge = np.linalg.solve(X.T @ X + np.eye(4) / delta, X.T @ y)
        assert np.allclose(m.b, ridge, atol=1e-6)
    assert np.allclose(m.b, np.linalg.lstsq(X, y, rcond=None)[0], atol=1e-6)


def test_effective_memory():
    for lam in (0.99, 0.998):
        m = RLS(1, lam, 1e6)
        x = np.ones(1)
        for _ in range(5000):
            m.update(x, 0.0)
        n = round(1 / (1 - lam))
        for _ in range(n):
            m.update(x, 1.0)
        assert abs(m.b[0] - (1 - lam**n)) < 1e-3
        assert abs(m.b[0] - (1 - np.exp(-1))) < 0.01


def test_prequential_predicts_before_learning():
    X = np.ones((3, 1))
    out = prequential(OnlineSGD(1, 0.5), X, np.array([2.0, 2.0, 2.0]))
    assert out.tolist() == [0.0, 1.0, 1.5]


def test_stream():
    s = drift_stream(20000, 3, 1000.0, 0.1, seed=4)
    f = np.einsum("tp,tp->t", s["X"], s["beta"])
    assert abs(f.var() / s["y"].var() - 0.1) < 0.01
    assert 10 <= len(s["changes"]) <= 35
    s = drift_stream(100, 2, 1e9, 0.1, seed=1, flip_at=40)
    assert s["changes"] == [40] and np.allclose(s["beta"][40], -s["beta"][39])


def test_detectors_calibrated_and_find_a_shift():
    rng = np.random.default_rng(1)
    null = rng.standard_normal(20000)
    makers = {"cusum": (lambda h: CUSUM(0.0, 0.1, h), np.arange(2.0, 30.0, 0.5)),
              "ph": (lambda h: PageHinkley(0.1, h), np.arange(2.0, 40.0, 0.5)),
              "adwin": (lambda d: ADWIN(d, 1000), np.array([10.0 ** -e for e in np.arange(1.0, 10.0, 0.5)]))}
    test = rng.standard_normal(20000)
    shifted = np.concatenate([rng.standard_normal(1000), rng.standard_normal(1000) - 1.0])
    for make, grid in makers.values():
        th = calibrate(make, grid, null, 1 / 252)
        assert len(alarm_times(lambda th=th, make=make: make(th), null)) / len(null) <= 1 / 252
        assert len(alarm_times(lambda th=th, make=make: make(th), test)) / len(test) < 2 / 252
        al = [a for a in alarm_times(lambda th=th, make=make: make(th), shifted) if a >= 1000]
        assert al and al[0] - 1000 < 60


def test_calendar_schedule():
    s = drift_stream(3000, 2, 1e9, 0.1, seed=2)
    pred, rt = retrain_schedule(s["X"], s["y"], "calendar", every=250, window=500, warm=1000)
    assert rt == list(range(1250, 3000, 250))
    assert np.isnan(pred[:1000]).all() and not np.isnan(pred[1000:]).any()
    _, rt = retrain_schedule(s["X"], s["y"], "never", warm=1000)
    assert rt == []
