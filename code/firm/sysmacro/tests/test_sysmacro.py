import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "synthfut"))
from firm_sysmacro import MacroConfig, _within_class, combine, macro_market, signal  # noqa: E402


def test_within_class_weights_are_neutral_with_unit_gross():
    x = np.arange(6.0)
    w = _within_class(x, np.array([0, 0, 0, 1, 1, 1]))
    assert abs(w[:3].sum()) < 1e-12 and abs(np.abs(w[:3]).sum() - 1) < 1e-12 and w[2] > 0 > w[0]


def test_market_shapes_and_signals():
    m = macro_market(MacroConfig())
    assert m["r"].shape[1] == 30 and set(np.unique(m["cls"])) == {0, 1, 2}
    assert (m["country"][:10] == np.arange(10)).all() and (m["country"][20:] == np.arange(10)).all()
    t = 6 * 252
    assert np.allclose(signal(m, "value", t), -m["anchor_gap"][t])
    assert np.allclose(signal(m, "surprise", t)[:10], m["seen"][t])


def test_combine_targets_volatility():
    rng = np.random.default_rng(1)
    books = [rng.normal(0, 0.01, 2000) for _ in range(3)]
    c = combine(books, MacroConfig())
    assert abs(c[500:].std() * np.sqrt(252) - 0.10) < 0.02
