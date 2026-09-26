import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_algos import (  # noqa: E402
    PCAARMA,
    LevelAR,
    Profile,
    close,
    decompose,
    pov,
    profile,
    shortfall,
    tracking,
    twap,
    vwap,
)


def test_models_and_vwaps():
    p = profile(np.array([[2.0, 1.0, 1.0], [4.0, 2.0, 2.0]]))
    assert np.allclose(p, [0.5, 0.25, 0.25])
    m = Profile(p, 100.0)
    assert np.allclose(vwap(100, m, [0, 0, 0], False), [50, 25, 25])
    assert np.allclose(vwap(100, m, [90, 5, 5], True), [50, 25, 25])       # a static model: dynamic changes nothing
    a = LevelAR(p, 100.0, 0.8, 0.3, 0.3)
    assert np.allclose(vwap(100, a, [50, 25, 25], True), [50, 25, 25])     # a day on profile
    q = vwap(100, a, [100, 25, 25], True)                                  # a hot first bin tilts the second
    assert q[1] > 25 and np.isclose(q.sum(), 100)
    busy = vwap(100, LevelAR(p, 100.0, 0.8, 1e3, 0.3), [100, 50, 50], True)
    assert np.allclose(busy, [50, 25, 25], atol=3)                          # a busy day on profile: a level, no tilt
    rng = np.random.default_rng(1)
    shape = np.linspace(1.0, 3.0, 13)
    hist = shape * np.exp(0.3 * rng.standard_normal((200, 1)) + 0.1 * rng.standard_normal((200, 13)))
    f = LevelAR.fit(hist)
    assert abs(f.s_level - 0.3) < 0.05 and abs(f.s_dev - 0.1) < 0.02 and abs(f.rho) < 0.2


def test_pca_arma_recovers_a_common_shape():
    rng = np.random.default_rng(0)
    shape = np.array([3.0, 1.0, 1.0, 2.0])
    w = shape[None, :, None] * np.exp(0.1 * rng.standard_normal((30, 4, 5)))
    m = PCAARMA(w).model(2)
    f = m.remaining(np.zeros(0))
    assert np.allclose(f / f.sum(), shape / shape.sum(), atol=0.02)
    assert len(m.remaining(np.array([3.0]))) == 3


def test_other_schedules_and_accounting():
    assert np.allclose(twap(90, 3), 30) and np.isclose(shortfall(100, 4, 0.0).sum(), 100)
    assert np.allclose(pov(0.2, [100, 200, 300], own_counted=False), [0, 25, 50])
    q = pov(0.2, [100.0] * 40)
    assert np.allclose(pov(0.5, [100, 100, 100]), [0, 50, 75]) and np.isclose(q[-1] / (100 + q[-1]), 0.2)
    b, moc = close(100, Profile([1.0, 1.0, 1.0, 1.0], 4.0), 0.2, start=2)
    assert np.allclose(b, [0, 0, 40, 40]) and moc == 20
    # buying on a day whose VWAP is 10.75: the schedule part is the cost of the wrong weights
    ex, sch = decompose([2, 2], [10.1, 11.0], [1, 3], [10.0, 11.0])
    assert np.isclose(ex, 0.05) and np.isclose(sch, 10.5 - 10.75)
    assert np.isclose(tracking([1, 3], [1, 3]), 0.0) and np.isclose(tracking([2, 2], [1, 3]), 0.0625)
