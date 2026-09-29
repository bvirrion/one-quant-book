"""Numbers gate: every number printed in Book 14, chapter 19 (text and solutions)."""
import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_race as n  # noqa: E402

rr = n.rr


def test_hubs():
    h = {r["hub"]: r for r in n.hub_rows()}
    want = {"aws-hkg": (2883, 19.2, 28.1), "aws-sin": (5311, 35.4, 51.8), "aws-iad": (10895, 72.7, 106.3),
            "aws-fra": (9359, 62.4, 91.3), "aws-lon": (9586, 64.0, 93.5), "aws-sto": (8194, 54.7, 79.9)}
    for k, (km, v, f) in want.items():
        assert (round(h[k]["km"]), round(h[k]["vac_rtt"], 1), round(h[k]["fib_rtt"], 1)) == (km, v, f), k
    infl = {k: (round(h[k]["infl_bb"], 2), round(h[k]["infl_sp"], 2)) for k in n.PUBLISHED}
    assert infl == {"aws-sin": (1.31, 1.26), "aws-iad": (1.41, 1.27), "aws-fra": (2.46, 1.50), "aws-lon": (2.25, 1.49),
                    "aws-sto": (3.07, 1.56)}
    assert [round(n.PUBLISHED[k][0] - n.PUBLISHED[k][1], 1) for k in ("aws-fra", "aws-lon", "aws-sto")] == [87.8, 70.4, 121.0]
    assert round(65.4 - h["aws-sin"]["fib_rtt"], 1) == 13.6 and round(124.3 / h["aws-sto"]["vac_rtt"], 1) == 2.3


@pytest.mark.reference
def test_race_and_break_even():
    rows = {rho: (a, b) for rho, a, b in n.race_rows()}
    assert [round(rows[r][0]) for r in (0.0, 0.5, 0.9)] == [1623, 771, 53]
    assert [round(rows[r][1]) for r in (0.0, 0.5, 0.9)] == [2141, 861, 53]
    assert [round(rows[r][1] - rows[r][0]) for r in (0.0, 0.5, 0.9)] == [518, 90, 0]
    assert [round(n.break_even(r)) for r in (0.0, 0.5, 0.9)] == [5182, 902, 0]
    g = {r: rr.percentile_gain(n.ROUTES, r) - rr.percentile_gain(n.ROUTES[:2], r) for r in (0.46, 0.48)}
    assert (round(g[0.46]), round(g[0.48])) == (110, 98)
    for rho, want in ((0.0, 536), (0.5, 290)):
        f, d = rr.first_arrival(n.ROUTES[:2], rho)
        assert round(np.percentile(d[:, 0], 50) - np.percentile(f, 50)) == want


@pytest.mark.reference
def test_duplicates():
    d = dict(n.duplicate_rows())
    assert (d[0], round(d[1000], 2), round(d[4000], 2), round(d[8000], 2)) == (2.0, 1.57, 0.50, 0.07)


def test_small_runs():
    f, d = rr.first_arrival(n.ROUTES, 0.5, n=2000)
    assert d.shape == (2000, 3) and (f <= d[:, 0]).all()
