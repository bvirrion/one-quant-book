"""Numbers gate: every number printed in Book 14, chapter 18 (text and solutions)."""
import dataclasses
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_private as n  # noqa: E402

pl = n.pl


@pytest.mark.reference
def test_paths_table():
    rows = {r["key"]: r for r in n.path_rows()}
    want = {"peering_cpg": (150, 220), "peering": (270, 396), "endpoint_same": (310, 436),
            "endpoint_other": (595, 797), "internet": (2270, 2396)}
    for k, (a, b) in want.items():
        assert (round(rows[k]["p50"]), round(rows[k]["p99"])) == (a, b), k
    assert (round(rows["endpoint_same"]["per_million"], 3), round(rows["endpoint_other"]["per_million"], 3)) == (0.004, 0.012)
    assert round(rows["endpoint_same"]["fixed"], 2) == 10.22
    w = n.wrong_zone()
    assert (round(w["p50_added"]), round(w["p99_added"]), round(w["cost_added_per_million"], 3)) == (285, 360, 0.008)
    assert round(285 / 40) == 7


def test_costs():
    c = dict((v, (a, b)) for v, a, b in n.monthly_curve())
    assert (round(c[10000][0], 2), round(c[10000][1], 2)) == (50.22, 130.22)
    assert round(pl.monthly_fixed(n.PATHS["endpoint_same"], zones=3), 2) == 30.66
    assert round(0.014 * 730, 2) == 10.22 and round(0.4 * 0.01 * 2, 3) == 0.008
    assert not pl.aligned(n.ALIGN["instance"], n.ALIGN["endpoint"])


@pytest.mark.reference
def test_exercise_hop():
    peer99 = pl.rtt_percentiles(n.PATHS["peering"])[99]
    lo, hi = 0.0, 400.0
    for _ in range(40):
        mid = (lo + hi) / 2
        q = pl.rtt_percentiles(dataclasses.replace(n.PATHS["endpoint_same"], extra_hop_us=mid))[50]
        lo, hi = (mid, hi) if q < peer99 else (lo, mid)
    assert round(mid) == 126 and round(peer99) == 396


def test_small_runs():
    q = pl.rtt_percentiles(n.PATHS["endpoint_other"], qs=(50,), n=5000)
    assert 500 < q[50] < 700
