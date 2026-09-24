"""Tests of the Chapter 25 demo: chart data and the behaviour of the deal."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from clo_demo import PATH_CDRS, deal, irr_table, paths
from firm_waterfall import run


def test_irr_falls_with_defaults_and_diversions_start_after_the_cushion():
    rows = irr_table()
    assert all(a[1] > b[1] for a, b in zip(rows, rows[1:], strict=False))
    assert all(r[2] == 0 for r in rows if r[0] <= 0.035) and all(r[2] > 0 for r in rows if r[0] >= 0.04)


def test_aaa_always_repaid():
    for cdr, *_ in irr_table():
        assert run(deal(), cdr)[-1].balances[0] == 0


def test_paths_shapes():
    ps = paths()
    assert sorted(ps) == list(PATH_CDRS) and all(len(v) == 20 for v in ps.values())
