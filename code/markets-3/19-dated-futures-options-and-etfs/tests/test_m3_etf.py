"""Tests of the Chapter 19 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_etf as m


def test_basis_table():
    b = {e: round(100 * x, 1) for e, _, x in m.basis_table()}
    assert b == {"25DEC26": 4.9, "26MAR27": 5.2, "25JUN27": 5.3, "24SEP27": 5.3}


def test_deltas_and_premiums():
    rows = {k: r for k, *r in m.delta_table()}
    assert abs(rows[90_000][0] - 0.0492) < 1e-4
    assert rows[60_000][3] < rows[70_000][3]            # premium-adjusted delta falls deep in the money
    assert all(r[3] < r[2] for r in rows.values())


def test_expiry_values():
    assert m.expiry_value_coin(180_000, 90_000, "C") == 0.5
    assert m.expiry_value_coin(30_000, 90_000, "P") == 2.0


def test_scenarios():
    s = m.scenarios()
    assert round(100 * s["rich"][0], 2) == 4.95 and round(100 * s["rich"][1], 2) == 14.14
    assert round(100 * s["snapshot"][0], 2) == -0.13
