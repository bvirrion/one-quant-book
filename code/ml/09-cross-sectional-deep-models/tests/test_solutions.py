"""Numbers gate: every numerical answer printed in Book 12, chapter 9 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_xsnet as m  # noqa: E402


def pct(x, d=1):
    return round(100 * float(x), d)


def r(x, d=2):
    return round(float(x), d)


def test_truth_and_models():
    assert (pct(m.truth()[0]), pct(m.truth()[1], 2)) == (31.3, 1.09)
    assert [pct(m.pca(K)[0]) for K in (1, 3, 5)] == [22.0, 22.5, 23.0]
    assert [pct(m.ipca(K)[0]) for K in (1, 3, 5)] == [25.1, 27.6, 28.1]
    assert [pct(m.cae(K)[0]) for K in (1, 3, 5)] == [26.9, 30.4, 30.8]
    assert (pct(m.pca(3)[1], 2), pct(m.ipca(3)[1], 2), pct(m.cae(3)[1], 2)) == (1.01, 1.11, 1.23)
    assert tuple(r(x) for x in m.pca(3)[2]) == (0.03, -0.00) and tuple(r(x) for x in m.ipca(3)[2]) == (0.71, -0.03)
    assert tuple(r(x) for x in m.cae(3)[2]) == (0.95, 0.59)
    assert [pct(m.cae(3, s)[0]) for s in (2, 3)] == [30.5, 30.6] and [r(m.cae(3, s)[2][0]) for s in (2, 3)] == [0.95, 0.96]


def test_embedding():
    e = m.embedding()
    assert (pct(e["no industry"]["r2"], 3), pct(e["embedding"]["r2"], 2)) == (0.004, 0.15)
    assert (r(e["no industry"]["corr_truth"]), r(e["embedding"]["corr_truth"]), r(e["embedding_vs_premia"])) == (
        0.52, 0.75, 0.86)
    d = m.embedding(emb_init=None)
    assert (r(d["embedding_vs_premia"]), r(d["embedding"]["corr_truth"])) == (0.05, 0.53)
    import numpy as np

    dd = m.data()
    rng = np.random.default_rng(51)
    ind = rng.integers(0, 30, 300)
    prem = 0.004 * rng.standard_normal(30)
    y = dd["r"] + prem[ind]
    y = y - y.mean(axis=1, keepdims=True)
    means = np.array([y[m.FIT][:, ind == j].mean() for j in range(30)])
    assert r(np.corrcoef(means, prem)[0, 1]) == 0.88


def test_exercises():
    assert (11 * 3, 300 * 3) == (33, 900)
    assert round((0.5 * 2 + 0.5 * 1 + 1.0 * 3) / 3, 2) == 1.5
    assert (30 * 32, 30 + 32) == (960, 62)
