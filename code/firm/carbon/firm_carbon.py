"""Carbon compliance and clean spreads (build of Book 3, Chapter 7).

Prices: power in EUR/MWh of electricity, fuels in EUR/MWh of fuel (thermal), allowances in EUR per
tonne of CO2. Emission factors in tonnes of CO2 per MWh of fuel; efficiencies are electrical
output over fuel input.
"""
from dataclasses import dataclass

MILLION = 1_000_000


def msr_intake(tnac: int) -> int:
    """Allowances placed in (positive) or released from (negative) the market stability reserve over
    the next twelve months from September, given the published TNAC (rules in force from 2024):
    24% of the TNAC above 1,096 million; the excess over 833 million between 833 and 1,096
    million; a release of 100 million below 400 million; nothing otherwise."""
    if tnac > 1_096 * MILLION:
        return round(0.24 * tnac)
    if tnac > 833 * MILLION:
        return tnac - 833 * MILLION
    if tnac < 400 * MILLION:
        return -100 * MILLION
    return 0


def emissions_per_mwh(efficiency: float, factor: float) -> float:
    """Tonnes of CO2 per MWh of electricity."""
    return factor / efficiency


def clean_spread(power: float, fuel: float, carbon: float, efficiency: float, factor: float) -> float:
    """Power price minus fuel and carbon cost of one MWh of electricity: the clean spark spread for
    gas, the clean dark spread for coal."""
    return power - (fuel + factor * carbon) / efficiency


def switching_price(gas: float, coal: float, eff_gas: float, eff_coal: float, ef_gas: float = 0.202,
                    ef_coal: float = 0.341) -> float:
    """Allowance price at which a gas plant and a coal plant have the same marginal cost."""
    return (gas / eff_gas - coal / eff_coal) / (ef_coal / eff_coal - ef_gas / eff_gas)


@dataclass
class ComplianceAccount:
    """An operator's allowances against its verified emissions, in tonnes."""
    held: int = 0
    emitted: int = 0
    surrendered: int = 0

    def buy(self, qty: int) -> None:
        self.held += qty

    def emit(self, tonnes: int) -> None:
        self.emitted += tonnes

    def surrender(self) -> int:
        """Surrender allowances for all emissions not yet covered; returns the shortfall (tonnes
        that could not be covered), which the operator must buy before the deadline."""
        due = self.emitted - self.surrendered
        paid = min(due, self.held)
        self.held -= paid
        self.surrendered += paid
        return due - paid
