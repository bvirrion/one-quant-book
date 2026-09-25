import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_combine import (
    blend,
    equal,
    ic_matrix,
    ic_series,
    ic_weights,
    lasso,
    max_icir,
    nnls,
    orth_sequential,
    orth_symmetric,
    residualise_on,
    ridge,
    stack,
    time_folds,
    toward_equal,
    zscore,
)


def _panel(seed=0, T=80, N=400):
    rng = np.random.default_rng(seed)
    f = rng.standard_normal((T, N))
    y = 0.2 * f + rng.standard_normal((T, N))
    X = np.stack([f + rng.standard_normal((T, N)), f + 2 * rng.standard_normal((T, N)), rng.standard_normal((T, N))], -1)
    return X, y


def test_zscore_and_ic():
    z = zscore(np.array([[1.0, 2.0, 3.0], [5.0, 5.0, 5.0]]))
    assert np.allclose(z[0], [-1.2247, 0.0, 1.2247], atol=1e-4) and np.allclose(z[1], 0.0)
    y = np.arange(12.0).reshape(2, 6)
    assert np.allclose(ic_series(y, y), 1.0) and np.allclose(ic_series(-y, y), -1.0)


def test_blenders_order():
    X, y = _panel()
    ic = ic_matrix(X, y)
    assert ic[:, 0].mean() > ic[:, 1].mean() > abs(ic[:, 2].mean())
    w = ic_weights(ic)
    assert np.isclose(w.sum(), 1.0) and w[0] > w[1] >= w[2] >= 0
    m = max_icir(ic, 0.0)
    assert m[0] > 0 and np.isclose(np.abs(m).sum(), 1.0)
    d = max_icir(ic, 1.0)
    assert np.allclose(d / d[0], (ic.mean(0) / ic.var(0, ddof=1)) / (ic.mean(0)[0] / ic.var(0, ddof=1)[0]))
    b = ridge(X, y, 0.0)
    assert b[0] > b[1] > abs(b[2]) and np.all(np.abs(ridge(X, y, 10.0)) < np.abs(b))
    assert lasso(X, y, 0.5)[2] == 0.0 and np.allclose(lasso(X, y, 0.0), b, atol=1e-4)
    assert ic_series(blend(X, ic_weights(ic)), y).mean() > ic_series(equal(X), y).mean()
    assert np.allclose(toward_equal([3.0, 1.0], 0.0), [0.75, 0.25]) and np.allclose(toward_equal([3.0, 1.0], 1.0), 0.5)


def test_nnls_and_stack():
    A = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    assert np.allclose(nnls(A, np.array([1.0, -1.0, 0.0])), [0.5, 0.0], atol=1e-8)         # (x-1)^2 + x^2
    assert np.allclose(nnls(A, A @ np.array([0.5, 2.0])), [0.5, 2.0])
    folds = time_folds(100, 4)
    assert len(folds) == 4 and folds[0][0][-1] + 1 == folds[0][1][0] and folds[-1][1][-1] == 99
    X, y = _panel(1)
    good, noise = (lambda tr: X[:, :, 0]), (lambda tr: X[:, :, 2])
    w = stack([good, noise], y, time_folds(80, 3))
    assert w[0] > 0.9 and np.isclose(w.sum(), 1.0)


def test_orthogonalisers():
    rng = np.random.default_rng(2)
    a = rng.standard_normal(500)
    X = np.column_stack([a, 0.8 * a + 0.6 * rng.standard_normal(500), rng.standard_normal(500)])
    for Q in (orth_sequential(X), orth_symmetric(X)):
        assert np.allclose(Q.T @ Q / 500, np.eye(3), atol=1e-8)
    Qs, Qq = orth_symmetric(X), orth_sequential(X)
    Xc = (X - X.mean(0)) / X.std(0)
    assert np.sum((Qs - Xc) ** 2) < np.sum((Qq - Xc) ** 2)          # the closest orthonormal set
    assert np.allclose(Qq[:, 0], Xc[:, 0])                              # the first column is kept
    r = residualise_on(X[:, 1:2], X[:, :1])
    assert abs(np.corrcoef(r[:, 0], X[:, 0])[0, 1]) < 1e-10
