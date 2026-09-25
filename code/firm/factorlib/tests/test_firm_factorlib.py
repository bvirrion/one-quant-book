import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_factorlib import bab_book, book_to_price, char_book, composite, sort_book  # noqa: E402


def test_sorts_and_characteristic_weights():
    s = np.arange(10.0)[None, :]
    W = sort_book(s, np.ones((1, 10), bool), 0.2)
    assert W[0].tolist() == [-0.25, -0.25] + [0.0] * 6 + [0.25, 0.25]
    Wv = sort_book(s, np.ones((1, 10), bool), 0.2, cap=np.arange(1.0, 11.0)[None, :])
    assert abs(Wv[0, 9] - 0.5 * 10 / 19) < 1e-12 and abs(Wv[0, 0] + 0.5 * 1 / 3) < 1e-12
    C = char_book(s, np.ones((1, 10), bool))
    assert abs(C[0].sum()) < 1e-12 and abs(np.abs(C[0]).sum() - 1) < 1e-12 and C[0, 9] == -C[0, 0]


def test_composite_and_bab():
    a = np.array([[1.0, 2.0, 3.0, np.nan, np.nan]])
    b = np.array([[3.0, 2.0, 1.0, np.nan, np.nan]])
    c = composite(a, b)
    assert np.allclose(c[0, :3], 0.0) and np.isnan(c[0, 3])
    c2 = composite(a, np.array([[1.0, 2.0, 3.0, 4.0, 5.0]]))
    assert np.isfinite(c2[0, 3]) and c2[0, 0] < c2[0, 2]
    beta = np.array([[0.5, 0.6, 1.0, 1.4, 1.6]])
    W = bab_book(beta, np.ones((1, 5), bool), 0.4)
    assert abs(W[0] @ beta[0]) < 1e-12 and W[0, :2].sum() > 1.0 and W[0, 3:].sum() > -1.0


def test_book_to_price_timing():
    cum = np.log(np.array([[1.0], [1.1], [1.2], [0.9]]))
    anchor = np.full((4, 1), np.nan)
    anchor[1, 0] = np.log(0.5) + cum[1, 0]                       # B/P = 0.5 at day 1
    cur = book_to_price(anchor, cum, np.ones((4, 1), bool), True)
    fixed = book_to_price(anchor, cum, np.ones((4, 1), bool), False)
    assert np.isnan(cur[0, 0]) and np.allclose(np.exp(cur[1:, 0]), [0.5, 0.5 * 1.1 / 1.2, 0.5 * 1.1 / 0.9])
    assert np.allclose(np.exp(fixed[1:, 0]), 0.5)
