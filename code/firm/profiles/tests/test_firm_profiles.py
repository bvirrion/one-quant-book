import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_profiles as fp  # noqa: E402

T = dt.date(2026, 9, 29)


def F(**k):
    d = dict(firm="A", field="employees", low=10.0, high=20.0, unit="people", as_of="2026-01", scope="firm", ledger="F1")
    d.update(k)
    return fp.Fact(**d)


def test_admissible_fact_has_no_problem():
    assert fp.problems([F()], {"F1"}, T) == []


def test_each_rule_fires():
    assert "missing" in fp.problems([F(ledger="F9")], {"F1"}, T)[0]
    assert "no date" in fp.problems([F(as_of="")], {"F1"}, T)[0]
    assert "low above high" in fp.problems([F(low=30.0)], {"F1"}, T)[0]
    assert "no value" in fp.problems([F(low=None, high=None)], {"F1"}, T)[0]
    assert "older" in fp.problems([F(as_of="2025-01")], {"F1"}, T, max_age_days=60)[0]
    assert "scope" in fp.problems([F(scope="brand")], {"F1"}, T)[0]


def test_widen_and_coverage():
    assert fp.widen(300, 100) == (250, 350)
    fs = [F(), F(field="revenue", scope="entity"), F(firm="B", field="revenue")]
    assert fp.coverage(fs, {"employees", "revenue"}) == {"A": {"employees"}, "B": {"revenue"}}
    g = fp.gap(fs, {"employees", "revenue"}, listed={"B"})
    assert g["listed"] == [1] and g["private"] == [1] and g["revenue_private"] == 0


def test_table_cells():
    rows = fp.table([F(), F(field="founded", low=2000.0, high=2000.0, unit="year"), F(field="x", unit="text", text="t")],
                    ["founded", "employees", "x"])
    assert rows == [["A", "2000", "10-20 (2026-01)", "t"]]
