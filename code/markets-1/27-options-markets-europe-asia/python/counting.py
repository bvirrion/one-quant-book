"""Three rankings of the same four markets, and what a regional volume table hides (Chapter 27).
The four markets are invented, in realistic proportions; the regional totals are the industry
association's published 2025 figures, from which 2024 is derived."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/turnover"))
from firm_turnover import MarketStats, shares

MARKETS = [
    MarketStats("M1: weekly index options, small lots", "option", 90e9, 25, 22_000.0, 35.0, 0.012),
    MarketStats("M2: index options, large contract", "option", 0.85e9, 100, 5_600.0, 16.0, 1.0),
    MarketStats("M3: index options, mid-size contract", "option", 0.35e9, 10, 5_200.0, 45.0, 1.08),
    MarketStats("M4: index futures", "future", 0.50e9, 50, 5_600.0, 0.0, 1.0),
]

# region: (billion contracts in 2025, change on 2024 in percent), as published
REGIONS_2025 = {"Asia-Pacific": (75.59, -55.6), "North America": (24.50, 24.0), "Latin America": (11.39, 14.2),
                "Europe": (4.38, 5.4), "Other": (3.43, 50.2)}


def derive_2024() -> dict[str, float]:
    return {k: v / (1.0 + chg / 100.0) for k, (v, chg) in REGIONS_2025.items()}


def three_rankings() -> dict[str, dict[str, float]]:
    return {m: shares(MARKETS, m) for m in ("contracts", "notional_usd", "premium_usd")}
