import pathlib
import sys

import numpy as np
import torch

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_mlinfer as mi  # noqa: E402
import make_mlinfer_fixture as fx  # noqa: E402


def test_fixture_reproducible_and_export_exact(tmp_path):
    forest, mlp, X, _ = fx.models()
    f = mi.export_forest(forest)
    V = np.loadtxt(HERE / "data" / "vectors.csv", delimiter=",")
    assert np.array_equal(mi.forest_predict(f, V[:, :16]), forest.predict(V[:, :16]))
    mi.write_forest(f, tmp_path / "f.txt")
    assert (tmp_path / "f.txt").read_text() == (HERE / "data" / "forest.txt").read_text()
    g = mi.read_forest(tmp_path / "f.txt")
    assert np.array_equal(mi.forest_predict(g, V[:5, :16]), V[:5, 16])
    q = mi.quantise(mlp, X[:2000])
    mi.write_mlp(q, tmp_path / "m.txt")
    assert (tmp_path / "m.txt").read_text() == (HERE / "data" / "mlp.txt").read_text()
    assert np.array_equal(mi.int8_forward(q, V[:, :16]), V[:, 17])


def test_int8_close_to_float_and_requant_rounding():
    _, mlp, X, _ = fx.models()
    q = mi.quantise(mlp, X[:2000])
    with torch.no_grad():
        f32 = mlp(torch.as_tensor(X[:1000], dtype=torch.float32)).numpy()
    assert np.sqrt(np.mean((mi.int8_forward(q, X[:1000]) - f32) ** 2)) < 0.1 * f32.std()
    assert mi._requant(np.array([3, -3]), 1, 1).tolist() == [2, -2]
    M, sh = mi._multiplier(0.3)
    assert abs(M / 2**sh - 0.3) < 1e-9


def test_generated_branches_compile_to_same_logic():
    forest, _, _, _ = fx.models()
    f = mi.export_forest(forest)
    src = mi.cpp_branches(f, "g")
    assert src.count("if (") == len(f["feature"]) and src.count("s += ") == len(f["value"])
