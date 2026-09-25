"""Numbers gate: every numerical answer printed in Book 8, chapter 27 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_crypto import flows, ftx, funding, momentum_table, venues  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_funding():
    got = [(y, r(100 * f, 2), r(100 * c, 1), r(100 * n, 1)) for y, f, c, n in funding()]
    assert got == [(2020, 17.19, 14.2, 14.3), (2021, 30.61, 25.3, 7.3), (2022, 4.16, 3.3, 22.1), (2023, 7.87, 6.4, 10.1),
                   (2024, 11.92, 9.8, 8.4), (2025, 5.13, 4.1, 12.9), (2026, 2.94, 2.3, 26.1)]


def test_ftx():
    f = ftx()
    assert (f["payables"], f["located"], r(100 * f["lgd"], 1), f["net_customer"], f["worst_day"], f["worst_net"]) == \
        (11235.0, 2156.0, 80.8, -7013.0, "2022-11-07", -3306.0)


def test_momentum_flows():
    m = {k: (r(v[0]), r(100 * v[1], 1)) for k, v in momentum_table().items()}
    assert m == {(7, 0.0): (0.85, 16.2), (7, 0.001): (0.42, 8.0), (7, 0.002): (-0.01, -0.2),
                 (28, 0.0): (1.56, 29.0), (28, 0.001): (1.35, 25.0), (28, 0.002): (1.13, 21.0),
                 (56, 0.0): (1.29, 23.3), (56, 0.001): (1.13, 20.4), (56, 0.002): (0.97, 17.6)}
    ic, t = flows()
    assert (r(ic, 3), r(t, 1)) == (-0.031, -10.2)


def test_venues():
    v = {k: (r(100 * x["one"], 1), r(100 * x["any"], 1), r(100 * x["mean"], 1), r(100 * x["q99"], 1))
         for k, x in venues().items()}
    assert v == {1: (80.8, 5.0, 4.1, 80.8), 2: (40.4, 9.9, 4.1, 40.4), 4: (20.2, 18.7, 4.1, 40.4), 8: (10.1, 34.0, 4.1, 20.2)}


def test_exercises():
    assert r((0.3061 - 0.002) / 1.2, 3) == 0.253 and r(0.05 * 0.808, 3) == 0.04
    assert (r(1 - 0.95**4, 3), r(1 - 0.95**8, 3)) == (0.185, 0.337)
    assert r(0.0010 * 3 * 365, 4) == 1.095 and r(0.0001 * 3 * 365, 4) == 0.1095
    assert r(0.253 - 0.040, 3) == 0.213 and r(0.033 - 0.040, 3) == -0.007
    assert math.isclose(0.808 / 4, 0.202)


def test_contagion():
    from s1_crypto import venues_correlated
    v = venues_correlated()
    assert (r(100 * v["mean"], 1), r(100 * v["q99"], 1), r(100 * v["any"], 1)) == (7.4, 60.6, 18.7)
