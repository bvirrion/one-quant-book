"""Tutorial of Book 4, Chapter 2: paths, reflection and quadratic variation."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_brownian import Phi, envelope_paths, qv_table, reflection_example, stop_table


def test_envelope_paths_shape():
    w = envelope_paths()
    assert w.shape == (6, 251) and np.all(w[:, 0] == 0)


def test_reflected_path_is_a_mirror_after_tau():
    e = reflection_example()
    k = int(round(e["tau"] * (e["w"].size - 1)))
    assert np.allclose(e["w"][: k + 1], e["refl"][: k + 1])
    assert np.allclose(e["w"][k:] + e["refl"][k:], 2 * e["w"][k])


def test_running_max_law_by_simulation():
    rng = np.random.default_rng(11)
    w = np.cumsum(rng.standard_normal((20_000, 2000)) / np.sqrt(2000), axis=1)
    assert abs((w.max(axis=1) >= 1).mean() - 2 * (1 - Phi(1))) < 0.02


def test_tables():
    rows = stop_table(dists=(0.02,))
    assert rows[0][1] > rows[0][4] - 0.02 and rows[0][2] < rows[0][1]
    assert len(qv_table(levels=8)) == 7
