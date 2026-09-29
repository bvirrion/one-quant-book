"""Acceptance tests of firm.refdata (One Quant Book 15, chapter 6)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_refdata import CounterpartyMaster, RefData


def service():
    rd = RefData({"ticker": ("A", "B"), "name": ("B", "A")})
    rd.ingest("A", 0, 0, "ISIN1", "ticker", "OLD")
    rd.ingest("B", 0, 0, "ISIN1", "ticker", "OLD")
    rd.ingest("A", 10, 10, "ISIN1", "ticker", "NEW")        # renamed on day 10
    rd.ingest("B", 12, 10, "ISIN1", "ticker", "NEW")        # B learns it on day 12
    rd.ingest("A", 20, 20, "ISIN2", "ticker", "OLD")        # the old ticker is reused on day 20
    rd.ingest("A", 0, 0, "ISIN1", "name", "ACME INC")
    rd.ingest("B", 0, 0, "ISIN1", "name", "Acme Inc")
    return rd


def test_permanent_ids_and_effective_values():
    rd = service()
    assert (rd.pid("ISIN1"), rd.pid("ISIN2")) == (1, 2)
    assert rd.value("A", 1, "ticker", 9, 99) == "OLD" and rd.value("A", 1, "ticker", 10, 99) == "NEW"
    assert rd.value("B", 1, "ticker", 10, 11) == "OLD" and rd.value("B", 1, "ticker", 10, 12) == "NEW"


def test_golden_copy_precedence_provenance_and_conflicts():
    rd = service()
    assert rd.golden(1, "name", 5, 5) == ("Acme Inc", "B")
    assert rd.golden(1, "ticker", 11, 11) == ("NEW", "A")
    assert rd.conflicts("ticker", 11, 11) == [(1, {"A": "NEW", "B": "OLD"})]
    assert rd.conflicts("ticker", 11, 12) == []
    assert rd.golden(2, "ticker", 25, 25) == ("OLD", "A")             # only A has it: fallback not needed


def test_symbol_resolution_point_in_time():
    rd = service()
    assert rd.resolve("ticker", "OLD", 5, 5) == [1]
    assert rd.resolve("ticker", "OLD", 15, 15) == []
    assert rd.resolve("ticker", "OLD", 25, 25) == [2]
    assert rd.resolve("ticker", "OLD", 5, 99) == [1]                  # history asked today still says listing 1
    assert rd.resolve("ticker", "NEW", 5, 99) == []


def test_corrections_are_versions():
    rd = RefData({})
    rd.ingest("A", 100, 100, "K", "lot", 10)                           # a typo
    rd.ingest("A", 106, 100, "K", "lot", 100)                          # corrected on day 106
    assert rd.value("A", 1, "lot", 103, 103) == 10 and rd.value("A", 1, "lot", 103, 106) == 100


def test_corporate_action_versions_and_factor():
    rd = RefData({})
    p = rd.ingest("A", 0, 0, "K", "ticker", "X")
    rd.add_action("E1", p, "split", 2.0, 50, "announced", 30)
    rd.add_action("E1", p, "split", 2.0, 50, "confirmed", 33)
    rd.add_action("E2", p, "split", 3.0, 80, "announced", 60)
    rd.add_action("E2", p, "split", 3.0, 80, "cancelled", 65)
    assert rd.factor(p, 0, 100, 31) == 1.0 and rd.factor(p, 0, 100, 33) == 2.0
    assert rd.factor(p, 0, 100, 61) == 2.0 and rd.factor(p, 0, 49, 99) == 1.0 and rd.factor(p, 0, 100, 99) == 2.0
    assert [a[4] for a in rd.actions(p, 99)] == ["confirmed", "cancelled"]


def test_counterparty_parents_are_bitemporal():
    cm = CounterpartyMaster()
    cm.add("H", "Holding", None, 0, 0)
    cm.add("S", "Sub", "H", 0, 0)
    cm.add("F", "Fund", None, 0, 0)
    cm.add("F", "Fund", "S", 50, 55)
    assert cm.ultimate_parent("F", 60, 54) == "F" and cm.ultimate_parent("F", 60, 55) == "H"
    assert cm.ultimate_parent("F", 40, 99) == "F" and cm.name("S", 10, 10) == "Sub"
