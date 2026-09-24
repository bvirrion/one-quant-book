"""Numbers gate: every numerical answer printed in Book 6, chapter 3 (text and solutions)."""
import itertools
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_ratesrisk as m
from firm_curvebuild import Swap
from firm_ratesrisk import min_variance_hedge, par_ladder, zero_ladder

BOOK, EXTRA = m.balanced_book()
H = m.hedge(BOOK)
G = H["ladder"]
W, V, S = m.components()
MOVE = m.MOVE_2022_10_21
C = m.curve().curve


def unit_ladders():
    return np.column_stack([par_ladder(m.SPOT, m.instruments(), m.KIND,
                                       m.book_pv([(n, 1e8, Swap(m.SPOT, n, 0.0).model(C), True)])) for n in m.TENORS])


def test_text():
    assert len(BOOK) == 202 and round(sum(q for _, q, _, _ in BOOK) / 1e9) == 12
    assert [(n, round(q / 1e6)) for n, q, _, p in EXTRA if p] == [(2, 1471), (30, 281)]
    assert abs(G.sum()) < 1e-3
    assert [round(x) for x in G[[1, 4, 5, 6, 7]]] == [212_010, 249_817, -279_791, -1_135_816, 958_308]
    pv10 = m.book_pv([(10, 1e8, Swap(m.SPOT, 10, 0.0).model(C), True)])
    assert round(par_ladder(m.SPOT, m.instruments(), m.KIND, pv10)[5]) == 83_778
    assert [round(x) for x in zero_ladder(C, pv10)[:6]] == [367, 713, 1_531, 3_205, 5_120, 74_016]
    z = m.zero_and_key_ladders(BOOK)
    assert round(z["zero"].sum()) == 11_408
    np.testing.assert_allclose(z["par_to_zero"], z["zero"], atol=10)
    assert [round(x * 100, 1) for x in S[:3]] == [85.1, 11.0, 2.1] and round(S[:3].sum() * 100, 1) == 98.2
    assert [round(x, 1) for x in np.sqrt(W[:3])] == [13.6, 4.9, 2.1]
    assert np.argmax(V[:, 2]) == 0 and V[0, 0] < V[3, 0]
    _, ch = m.treasury_changes()
    assert len(ch) == 2_681
    np.testing.assert_allclose(m.move_on("2022-10-21"), MOVE, atol=1e-9)
    sc, ex = V.T @ MOVE, V.T @ G
    assert round(sc[1], 1) == 21.2 and round(sc[1] * ex[1] / 1e6, 2) == -3.09
    assert [round(x / 1e6, 2) for x in (sc * ex)[[3, 5, 6]]] == [0.72, 0.69, -1.48]
    assert round(H["daily_sd"]) == 1_288_843 and round(H["residual_share"] * 100, 1) == 4.2
    assert round(m.hedge(BOOK, (1, 5, 7))["residual_share"] * 100, 1) == 58.3
    p3 = V[:, :3]
    r = G - p3 @ (p3.T @ G)
    assert round(r @ H["cov"] @ r / (G @ H["cov"] @ G) * 100, 1) == 68.9
    assert [round(u * 100) for u in H["units"]] == [-1196, 801, -515]
    assert round(H["daily_sd"] * np.sqrt(H["residual_share"])) == 264_554
    assert round(G @ MOVE) == -3_000_000 and round(m.full_revaluation(BOOK, MOVE)) == -3_077_970
    gm = m.gamma_matrix(BOOK)
    assert round(0.5 * MOVE @ gm @ MOVE) == -78_189 and round(gm.sum()) == -377
    assert abs(0.5 * MOVE @ gm @ MOVE - (m.full_revaluation(BOOK, MOVE) + 3e6)) < 220


def test_exercises():
    assert 50 - 120 + 80 == 10 and 50 * -5 - 120 * 2 + 80 * 6 == -10
    assert round(100 - 98.2, 1) == 1.8
    assert 367 + 713 + 1531 + 3205 + 5120 + 74016 == 84_952 and round(84_952 / 83_778, 3) == 1.014
    lad, cov = unit_ladders(), H["cov"]
    one = min((min_variance_hedge(G, lad[:, [k]], cov)[1], k) for k in range(8))
    four = min((min_variance_hedge(G, lad[:, list(c)], cov)[1], c) for c in itertools.combinations(range(8), 4))
    assert (round(one[0] * 100, 1), m.TENORS[one[1]]) == (86.5, 20)
    assert (round(four[0] * 100, 2), [m.TENORS[k] for k in four[1]]) == (2.85, [2, 7, 20, 30])


def test_problem():
    contrib = G * MOVE
    assert [round(x / 1e6, 2) for x in contrib[[7, 6, 1, 4]]] == [8.62, -7.95, -2.76, -2.0]
    assert round(21.16 / np.sqrt(W[1]), 1) == 4.3
    assert round(H["hedged"] @ MOVE) == HEDGED_DAY


HEDGED_DAY = -315_044
