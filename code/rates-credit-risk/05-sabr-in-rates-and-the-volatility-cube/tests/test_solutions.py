"""Numbers gate: every numerical answer printed in Book 6, chapter 5 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_sabrcube as m
from firm_sabrcube import Sabr, density, hagan_normal_beta0

FITS = m.neg_fits()
DEEP = m.deep_receiver()


def test_text():
    _, q = m.neg_quotes()
    assert [round(v * 1e4, 1) for v in q] == [29.3, 26.5, 25.7, 27.8, 31.4, 39.8]
    assert [round(FITS[k][1] * 1e4, 2) for k in ("shift0.01", "shift0.03")] == [0.77, 0.11]
    assert FITS["normal"][1] < 1e-8
    assert [round(DEEP[k], 3) for k in ("shift0.01", "shift0.03", "normal")] == [0.177, 0.280, 0.295]
    assert round((1 - DEEP["shift0.01"] / DEEP["shift0.03"]) * 100) == 37
    cube, err = m.build_cube()
    assert (round(min(err.values()) * 1e4, 2), round(max(err.values()) * 1e4, 2)) == (0.21, 0.78)
    mt = {row[0]: row[1:] for row in m.matrix_table()}
    assert (round(mt[1.0][0], 1), round(mt[10.0][3], 1)) == (69.9, 74.0)
    ms = m.missing_section()
    assert round(ms["f"] * 100, 3) == 2.905 and round(ms["max_err"], 2) == 0.93
    lf = m.long_fits()
    assert [round(lf[s][1] * 1e4, 2) for s in (0.01, 0.03)] == [1.28, 0.35]
    ks = [m.LONG_F + d * 1e-4 for d in m.LONG_OFFSETS]
    q = [hagan_normal_beta0(m.LONG_F, k, m.LONG_T, m.LONG_TRUE) * 1e4 for k in ks]
    assert (round(min(q)), round(max(q))) == (86, 96)
    grid = [x * 1e-4 for x in range(-95, 700, 5)]
    d1 = density(m.LONG_F, m.LONG_T, lf[0.01][0], grid)
    neg = [k for k, v in zip(grid, d1, strict=True) if v < 0]
    assert (round(neg[0] * 100, 2), round(neg[-1] * 100, 2), round(min(d1))) == (-0.95, 0.35, -158)
    g3 = [x * 1e-4 for x in range(-295, 700, 5)]
    d3 = density(m.LONG_F, m.LONG_T, lf[0.03][0], g3)
    assert round(max(k for k, v in zip(g3, d3, strict=True) if v < 0) * 100, 2) == -2.15


def test_exercises():
    assert round(25 * (1 + (2 - 3 * 0.01) / 24 * 0.36 * 1.0), 2) == 25.74
    assert m.smallest_positive_shift() == 0.009


def test_problem():
    prem = {k: v * 1e-4 * 2.0 * 5e8 for k, v in DEEP.items()}
    assert [round(prem[k]) for k in ("shift0.01", "shift0.03", "normal")] == [17_717, 27_999, 29_477]
    assert round(prem["shift0.03"] - prem["shift0.01"]) == 10_282
    assert np.isclose(-0.003 - (-0.009), 0.006) and np.isclose(-0.008 - (-0.009), 0.001)
    assert Sabr(1, 0, 0, 0).shift == 0.0


def test_caption_max_miss():
    from firm_sabrcube import normal_vol
    ks, q = m.neg_quotes()
    p = FITS["shift0.01"][0]
    assert round(max(abs(normal_vol(m.NEG_F, k, m.NEG_T, p) - v) for k, v in zip(ks, q, strict=True)) * 1e4, 1) == 1.2
