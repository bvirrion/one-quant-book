"""Acceptance tests for firm.filings: a synthetic inline-XBRL document and a synthetic company-facts JSON."""
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import firm_filings as ff  # noqa: E402

E = "Example Trading Limited"


@pytest.fixture(scope="module")
def facts():
    return ff.parse_ixbrl((HERE / "fixture_accounts.xhtml").read_text(), E, "fixture")


def test_number_formats():
    assert ff.number("1,234", "ixt:numcommadot", 3) == 1_234_000
    assert ff.number("1.234,5", "ixt-sec:numdotcomma", 3, "-") == -1_234_500
    assert ff.number("-", "ixt:zerodash", 3) == 0.0
    assert ff.number(" 12 ", "", 0) == 12.0


def test_contexts_units_scale(facts):
    s = ff.Snapshot(facts)
    assert s.series(E, "Revenue") == [("2023-12-31", 987_000.0), ("2024-12-31", 1_234_000.0)]
    rev = [f for f in facts if f.concept == "Revenue" and f.end == "2024-12-31"][0]
    assert (rev.start, rev.unit, rev.locator, rev.note) == ("2024-01-01", "GBP", "cy", "TurnoverRevenue")
    assert s.get(E, "Equity", "2024-12-31") == 2_000_000 and s.get(E, "AverageEmployees", "2024-12-31") == 12


def test_sign_is_the_tags_not_the_brackets(facts):
    s = ff.Snapshot(facts)
    assert s.get(E, "AdministrativeExpenses", "2024-12-31") == 900_000  # shown in brackets, tagged positive
    assert s.get(E, "OtherOperatingIncome", "2024-12-31") == -16_000   # sign="-" on an income line
    assert s.get(E, "GainLossOnInvestments", "2024-12-31") == -1_234_500


def test_duplicates_dimensions_privacy_nil(facts):
    assert sum(1 for f in facts if f.concept == "StaffCosts") == 1
    dim = [f for f in facts if f.dims]
    assert len(dim) == 1 and dim[0].dims == ("e:EmployeeCategoryDimension=e:Trading",) and dim[0].value == 5
    assert not any("Director" in f.note for f in facts)
    assert any("Director" in f.note for f in ff.parse_ixbrl((HERE / "fixture_accounts.xhtml").read_text(),
                                                             keep_private=True))
    assert not any(f.note == "DividendsPaid" for f in facts)


def test_reconcile_catches_the_sign(facts):
    s = ff.Snapshot(facts)
    parts = [("Revenue", 1), ("AdministrativeExpenses", -1), ("OtherOperatingIncome", 1)]
    assert s.reconcile(E, "OperatingProfit", parts) == [("2024-12-31", 350_000.0, 318_000.0)]


def test_companyfacts_latest_filing_annual_only():
    doc = json.loads((HERE / "fixture_companyfacts.json").read_text())
    fs = ff.companyfacts(doc, ["Revenues", "LaborAndRelatedExpense"])
    rev = [(f.end, f.value, f.locator) for f in fs if f.concept == "Revenue"]
    assert rev == [("2023-12-31", 1010.0, "A-25"), ("2024-12-31", 1200.0, "A-25")]
    assert [f.value for f in fs if f.concept == "StaffCosts"] == [240.0]
    assert fs[0].entity == "Example Markets Inc."


def test_snapshot_roundtrip_problems_perhead_statement(facts, tmp_path):
    s = ff.Snapshot([f for f in facts if not f.dims])
    s.save(tmp_path / "s.csv")
    t = ff.Snapshot.load(tmp_path / "s.csv")
    assert t.series(E, "Revenue") == s.series(E, "Revenue") and t.problems() == []
    assert ff.per_head(t, E, "StaffCosts", "AverageEmployees") == [("2024-12-31", 50_000.0)]
    bad = ff.Snapshot(t.facts + [ff.Fact(E, "Revenue", 1.0, "GBP", "2024-01-01", "2024-12-31", "", "")])
    assert any("no provenance" in p for p in bad.problems()) and any("two values" in p for p in bad.problems())
    mapping = {"net_revenue": [("Revenue", 1)], "comp": [("StaffCosts", 1)],
               "other_fixed": [("AdministrativeExpenses", 1), ("StaffCosts", -1)]}
    st = ff.to_statement(t, E, "2024-12-31", mapping, headcount="AverageEmployees")
    assert (st.year, st.net_revenue, st.comp, st.other_fixed, st.headcount) == (2024, 1_234_000, 600_000, 300_000, 12)


def test_months():
    assert ff.months("2021-10-25", "2022-12-31") == 14 and ff.months("2024-02-01", "2025-01-31") == 12


def test_excerpt_of_a_real_tag():
    text = (HERE / "excerpt_quadrature_turnover.xhtml").read_text()
    f = ff.parse_ixbrl(text, "Quadrature Capital Limited", "excerpt")
    assert len(f) == 1 and f[0].concept == "Revenue" and f[0].value == 1_224_817_000.0 and f[0].locator == "c2"
