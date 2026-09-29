"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 5 (text and solutions)."""
import csv
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "tsbench"))
from firm_tsbench import Params
from pl_tsbench import DAY_NS, answers

WIDE = pathlib.Path(__file__).resolve().parents[4] / (
    "figdata/platforms/05-time-series-databases-and-the-alternatives/measured_tsbench_wide.csv")


def test_small_runs(tmp_path):
    a = answers(tmp_path / "d", symbols=6, days=3, per=300, trades_per_day=100,
                params=Params("S002", 1, DAY_NS + 36_000 * 10**9, DAY_NS + 39_600 * 10**9, DAY_NS + 43_200 * 10**9))
    assert all(a["check"].values()) and a["sizes"]["xsection"] == 6 and a["sizes"]["asof"] == 100


@pytest.mark.reference
def test_answers():
    a = answers()
    assert all(a["check"].values())
    assert a["sizes"] == {"point": 1, "range": 153, "bars": 359, "asof": 2000, "xsection": 50}
    p = Params("S023", 12, 12 * DAY_NS + 36_000 * 10**9, 12 * DAY_NS + 39_600 * 10**9, 12 * DAY_NS + 43_200 * 10**9)
    b = answers(params=p)
    assert all(b["check"].values())
    assert b["sizes"] == {"point": 1, "range": 171, "bars": 358, "asof": 2000, "xsection": 50}
    assert 390 - 359 == 31 and 6.5 * 60 == 390


def test_measured_numbers_in_text():
    m = {r["query"]: {k: float(v) for k, v in r.items() if k not in ("k", "query")} for r in csv.DictReader(open(WIDE))}
    sq, du = m["point"]["sqlite"], m["point"]["duckdb"]
    assert round(sq, 2) == 0.05 and round(du, 1) == 3.8 and round(m["range"]["sqlite"], 1) == 0.3
    assert round(m["range"]["duckdb"], 1) == 2.2
    assert round(m["xsection"]["sqlite"]) == 313 and round(m["xsection"]["duckdb"]) == 7
    assert round(du / sq, -1) == 80 and 40 < m["xsection"]["sqlite"] / m["xsection"]["duckdb"] < 50
    f = (du - sq) / ((du - sq) + (m["xsection"]["sqlite"] - m["xsection"]["duckdb"]))
    assert round(100 * f, 1) == 1.2
    # pandas slowest on four shapes; numpy fastest on range, bars and cross-section
    slowest = [max(m[q], key=m[q].get) for q in m]
    assert slowest.count("pandas") == 4
    assert all(min(m[q], key=m[q].get) == "numpy" for q in ("range", "bars", "xsection"))
    assert m["bars"]["polars"] > m["bars"]["duckdb"] and m["xsection"]["polars"] > m["xsection"]["duckdb"]
