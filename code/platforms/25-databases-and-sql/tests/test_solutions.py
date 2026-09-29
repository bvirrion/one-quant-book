"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 25 (text and solutions)."""
import csv
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_tradedb as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/25-databases-and-sql"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs():
    r = P.report(per_day=2_000)
    assert len(r["diff"]) <= 48 and r["in_place_equals_corrected"]
    assert r["versions"] - r["n_trades"] == 40                       # 30 + 10 closed versions
    assert len(r["conn"].execute(P.CHANGED).fetchall()) == 40            # exercise 7
    assert P.lost_updates("transaction", n=50) == 0 and P.lost_updates("one statement", n=50) == 0
    assert P.lost_updates("autocommit", n=60) > 0


def test_csvs():
    s = _csv("summary.csv")[0]
    assert (s["trades"], s["versions"], s["rows_differ"], s["in_place_equals_corrected"]) == ("500008", "500048", "48", "True")
    assert [r["lost_per_1000"] for r in _csv("lost.csv")] == ["636", "0", "0"]
    d = _csv("report_diff.csv")
    assert [sum(1 for r in d if r["kind"] == k) for k in ("qty", "cancel", "late")] == [30, 10, 8]
    assert (d[0]["account"], d[0]["as_was"], d[0]["corrected"]) == ("ACC10", "2000", "1100")
    v = _csv("versions.csv")
    assert [(r["qty"], r["sys_to"]) for r in v] == [("700", "208800"), ("70", "1000000000000")]
    m = {(r["engine"], r["query"]): float(r["ms"]) for r in _csv("measured_queries.csv")}
    assert m[("SQLite no index", "point")] > 100 * m[("SQLite index account-instrument", "point")]
    assert m[("DuckDB", "analytic")] < m[("SQLite no index", "analytic")]
    # the printed values (text, caption, solutions)
    assert [round(m[(e, q)], 1) for e, q in (("SQLite no index", "point"), ("DuckDB", "report"), ("DuckDB", "analytic"),
                                              ("DuckDB", "point"))] == [13.7, 9.8, 2.8, 1.0]
    assert (round(m[("SQLite no index", "report")]), round(m[("SQLite no index", "analytic")])) == (150, 148)
    assert m[("SQLite index account-instrument", "point")] == 0.01
    assert (round(m[("SQLite no index", "report")] / m[("DuckDB", "report")]),
            round(m[("SQLite no index", "analytic")] / m[("DuckDB", "analytic")])) == (15, 53)


@pytest.mark.reference
def test_full_report():
    r = P.report()
    assert (r["n_trades"], len(r["diff"])) == (500008, 48)
    assert P.lost_updates("autocommit") == 636
