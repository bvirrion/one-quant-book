"""Acceptance tests of the Book 3, Chapter 7 build (carbon)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_carbon import ComplianceAccount, clean_spread, emissions_per_mwh, msr_intake, switching_price


def test_msr_rule_matches_published_decisions():
    assert msr_intake(1_148_049_585) == 275_531_900        # TNAC 2024 -> Sept 2025 to Aug 2026
    assert msr_intake(1_023_494_202) == 190_494_202        # TNAC 2025 -> Sept 2026 to Aug 2027
    assert msr_intake(600_000_000) == 0 and msr_intake(300_000_000) == -100_000_000


def test_spreads_and_switching():
    assert math.isclose(emissions_per_mwh(0.55, 0.202), 0.202 / 0.55)
    p = switching_price(35.0, 12.0, 0.55, 0.40)
    gas = clean_spread(100.0, 35.0, p, 0.55, 0.202)
    coal = clean_spread(100.0, 12.0, p, 0.40, 0.341)
    assert math.isclose(gas, coal)


def test_compliance_shortfall():
    a = ComplianceAccount()
    a.buy(900)
    a.emit(1000)
    assert a.surrender() == 100 and a.held == 0
    a.buy(100)
    assert a.surrender() == 0 and a.surrendered == 1000
