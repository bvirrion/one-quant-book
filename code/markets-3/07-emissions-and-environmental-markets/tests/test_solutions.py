"""Numbers gate: every numerical answer printed in Book 3, Chapter 7 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/carbon"))
from firm_carbon import ComplianceAccount, clean_spread, emissions_per_mwh, msr_intake, switching_price
from m3_carbon import msr_cases, utility

U = utility()


def test_text():
    assert msr_cases() == {2024: 275_531_900, 2025: 190_494_202}
    assert round(emissions_per_mwh(0.55, 0.202), 3) == 0.367 and round(emissions_per_mwh(0.40, 0.341), 3) == 0.853
    assert round(U["switch"], 2) == 69.32
    assert round(clean_spread(100, 35, 70, 0.55, 0.202), 2) == 10.65 and round(clean_spread(100, 12, 70, 0.40, 0.341), 2) == 10.32
    assert round(0.8525 / 0.3673, 1) == 2.3
    assert round(switching_price(20, 12, 0.55, 0.40), 2) == 13.11 and round(switching_price(50, 12, 0.55, 0.40), 2) == 125.53


def test_exercises():
    a = ComplianceAccount(held=900, emitted=1000)
    a.buy(100)
    assert a.surrender() == 0 and a.surrendered == 1000
    assert msr_intake(1_200_000_000) == 288_000_000 and msr_intake(900_000_000) == 67_000_000
    assert msr_intake(350_000_000) == -100_000_000
    assert round(switching_price(35, 12, 0.55, 0.38), 2) == 60.47
    assert round(10 * emissions_per_mwh(0.55, 0.202), 2) == 3.67
    assert round((1096 - 833) / 1096 * 100, 3) == 23.996
    assert msr_intake(1_096_000_000) == 263_000_000 and round(0.24 * 1_096_000_000) == 263_040_000


def test_problem():
    assert round(U["coal_t_per_mwh"], 4) == 0.8525 and round(U["gas_t_per_mwh"], 4) == 0.3673
    assert round(U["tonnes"] / 1e6, 3) == 6.584 and round(U["cost"] / 1e6, 1) == 460.9
    gas_mc, coal_mc = (35 + 0.202 * 70) / 0.55, (12 + 0.341 * 70) / 0.40
    assert (round(gas_mc, 2), round(coal_mc, 2), round(coal_mc - gas_mc, 2)) == (89.35, 89.68, 0.33)
    assert round((0.8525 - 0.202 / 0.55) * 1e6) == 485_227
