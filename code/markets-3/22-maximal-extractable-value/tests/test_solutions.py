"""Numbers in the solutions of Book 3, Chapter 22."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_mev as m
from firm_amm import cp_amount_out


def test_exercises():
    r = {t: x for t, *x in m.by_tolerance()}
    assert round(r[100][1] / r[50][1], 2) == 2.0 and round(r[100][3] / r[50][3], 2) == 2.0
    net90 = {t: x for t, *x in m.by_tolerance(builder_share_bps=9_000)}
    assert round(net90[100][2], 2) == 992.96
    k = next(k for k in range(1, 2_000) if m.cex_dex_arbitrage(3_000 * (1 + k / 10_000))[1] >= 20)
    assert k == 54


def test_problem():
    q = cp_amount_out(m.SWAP, m.RA, m.RB) / m.E18
    assert round(q, 2) == 311.62 and round(1e6 / q, 2) == 3_209.03
    assert round(q * 0.995, 2) == 310.06 and round(q * 0.99, 2) == 308.50
    r = {t: x for t, *x in m.by_tolerance()}
    assert (round(r[50][0]), round(r[100][0])) == (38_912, 78_119)
    assert (round(r[50][1]), round(r[100][1])) == (5_067, 10_130)
    assert (round(r[50][3] * 3_000), round(r[100][3] * 3_000)) == (4_674, 9_349)
    assert (round(r[50][2], 2), round(r[100][2], 2)) == (5_046.72, 10_109.57)
    n = {t: x for t, *x in m.by_tolerance(builder_share_bps=9_000)}
    assert (round(n[50][2], 2), round(n[100][2], 2)) == (486.67, 992.96)
