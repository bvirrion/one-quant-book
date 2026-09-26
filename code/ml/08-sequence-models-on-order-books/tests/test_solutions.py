"""Numbers gate: every numerical answer printed in Book 12, chapter 8 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_lobseq as m  # noqa: E402


def r(x, d=3):
    return round(float(x), d)


def test_data():
    d = m.datasets()
    assert d["train"][0].shape == (8808, 20, 40)
    yt = np.concatenate([x[1] for x in d["test"]])
    sh = np.bincount(yt) / len(yt)
    assert (r(100 * sh[1], 1), r(100 * sh[0], 1), r(100 * sh[2], 1)) == (72.7, 14.7, 12.5)
    assert r(100 * (sh**2).sum(), 1) == 56.6


def test_table():
    tb = m.table()
    got = {k: (r(v.reshape(-1, 2)[:, 0].mean()), r(v.reshape(-1, 2)[:, 1].mean())) for k, v in tb.items()}
    assert got == {"logistic (OFI, imbalance)": (0.781, 0.543), "CNN": (0.727, 0.060), "LSTM": (0.729, 0.292),
                   "TCN": (0.766, 0.366), "attention": (0.775, 0.426)}
    sds = {k: r(v.reshape(-1, 2)[:, 1].std(), 2) for k, v in tb.items()}
    assert sds["logistic (OFI, imbalance)"] == 0.09 and min(sds[k] for k in m.MODELS) == 0.15
    assert max(sds[k] for k in m.MODELS) == 0.20
    epochs = [m.sequence(n, s)[1] for n in m.MODELS for s in (1, 2)]
    assert min(epochs) == 1 and max(epochs) == 4


def test_scaling():
    assert [tuple(r(x, 2) for x in m.scaling(n)) for n in (4, 8, 16)] == [(0.13, 0.55), (0.30, 0.54), (0.44, 0.57)]
    assert r(m.scaling(16, name="LSTM")[0]) == 0.381 and r(m.scaling(16)[0]) == 0.441 and r(m.scaling(16)[1]) == 0.568


def test_exercises():
    assert (1 + 2 * 15, 1 + 4 * 15) == (31, 61)
    assert 20 * 20 * 32 == 12800
