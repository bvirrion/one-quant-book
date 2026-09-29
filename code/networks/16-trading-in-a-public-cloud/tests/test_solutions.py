"""Numbers gate: every number printed in Book 14, chapter 16 (text and solutions)."""
import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_cloud as c  # noqa: E402

cp = c.cp


def test_names():
    a, b = c.ACCOUNTS["a"], c.ACCOUNTS["b"]
    assert [n for n in a if cp.same_physical(a, b, n)] == ["us-east-1e", "us-east-1f"]
    assert (a["us-east-1e"], a["us-east-1f"]) == ("use1-az3", "use1-az5")
    assert a["us-east-1a"] == "use1-az4" and cp.locate(b, "use1-az4") == "us-east-1b"
    rows = {n: (p, d) for n, p, d in c.penalty_rows()}
    assert (round(rows[3][1], 1), rows[6][1], rows[4][0]) == (190.0, 237.5, 0.25) and round(rows[6][0], 4) == round(1 / 6, 4)
    assert 555 - 270 == 285


@pytest.mark.reference
def test_percentiles_table():
    s, x, n = c.percentiles("same zone"), c.percentiles("cross zone"), c.percentiles("shared host, noisy neighbour")
    assert [round(s[q]) for q in c.QUANTILES] == [270, 333, 396, 463, 743]
    assert [round(x[q]) for q in c.QUANTILES] == [555, 657, 755, 851, 1908]
    assert [round(n[q]) for q in c.QUANTILES] == [270, 333, 400, 7474, 13940]
    assert round(n[99.9] / s[99.9]) == 16 and round(100 * (1 - s[99.99] / 760)) == 2 and round(100 * (x[99.99] / 1905 - 1), 1) == 0.2


@pytest.mark.reference
def test_spike_threshold():
    cross = c.percentiles("cross zone")[99.9]
    first = next(p for p in np.arange(0.0008, 0.00101, 0.00002)
                 if np.percentile(cp.sample_rtt(cp.Rtt(270, 395, p, 5, 50), 400000, 1), 99.9) > cross)
    assert round(100 * first, 3) == 0.092 and round(1 / first, -1) == 1090


def test_costs():
    k = c.plan_costs()
    assert round(k["four c7i.4xlarge in one zone"]["compute"], 2) == 2084.88
    assert k["four c7i.4xlarge over two zones"]["transfer"] == 400
    assert round(k["two c7i.metal-24xl in one zone"]["compute"], 2) == 6254.64
    assert round(k["four c7i.4xlarge in one zone"]["compute"]) == 2085 and round(k["two c7i.metal-24xl in one zone"]["compute"]) == 6255
    assert 5000 * 0.01 * 2 == 100


def test_small_runs():
    x = cp.sample_rtt(c.CASES["cross zone"], 2000, seed=5)
    assert 400 < np.median(x) < 700
