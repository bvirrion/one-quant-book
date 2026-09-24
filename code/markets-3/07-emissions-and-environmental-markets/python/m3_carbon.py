"""Chapter 7 of Book 3: emissions markets. The market stability reserve rule applied to the published
TNAC figures, the coal-to-gas switching price, clean spreads, and a utility's allowance needs. Fuel
prices, efficiencies and emission factors are illustrative round numbers."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/carbon"))
from firm_carbon import clean_spread, emissions_per_mwh, msr_intake, switching_price

TNAC = {2024: 1_148_049_585, 2025: 1_023_494_202}      # published May 2025 and May 2026
GAS, COAL, EFF_GAS, EFF_COAL, EF_GAS, EF_COAL = 35.0, 12.0, 0.55, 0.40, 0.202, 0.341


def msr_cases() -> dict[int, int]:
    return {y: msr_intake(t) for y, t in TNAC.items()}


def switching_curve(gas_prices: list[float]) -> list[tuple[float, float]]:
    return [(g, switching_price(g, COAL, EFF_GAS, EFF_COAL)) for g in gas_prices]


def spreads_curve(power: float, carbons: list[float]) -> list[tuple[float, float, float]]:
    return [(c, clean_spread(power, GAS, c, EFF_GAS, EF_GAS), clean_spread(power, COAL, c, EFF_COAL, EF_COAL))
            for c in carbons]


def utility(coal_mwh: float = 6e6, gas_mwh: float = 4e6, carbon: float = 70.0) -> dict[str, float]:
    """A utility's allowance needs for next year's planned output, and their cost."""
    t = coal_mwh * emissions_per_mwh(EFF_COAL, EF_COAL) + gas_mwh * emissions_per_mwh(EFF_GAS, EF_GAS)
    return {"tonnes": t, "cost": t * carbon, "switch": switching_price(GAS, COAL, EFF_GAS, EFF_COAL),
            "coal_t_per_mwh": emissions_per_mwh(EFF_COAL, EF_COAL), "gas_t_per_mwh": emissions_per_mwh(EFF_GAS, EF_GAS)}
