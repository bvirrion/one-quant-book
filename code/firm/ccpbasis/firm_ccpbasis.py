"""Margin funding and the clearing-house basis (build of Book 2, Chapter 10).

A stylised initial-margin model: a clearing house margins a swap position at z standard deviations
of its value over the margin period of risk, IM = z * sigma_bp_per_day * sqrt(mpor) * DV01. The DV01
of a swap decays with its remaining annuity. Posting IM costs the funding spread (what the dealer
pays for the cash or bonds posted, less what the clearing house pays on them); its present value
over the swap's life is the margin valuation adjustment (MVA). Expressed per unit of the swap's
DV01, the MVA is the running basis, in basis points, that a dealer needs to be paid for the trade.
Flat curve, annual periods; amounts in currency, rates decimal.
"""
import math
from dataclasses import dataclass


def annuity_remaining(t: float, maturity: float, rate: float) -> float:
    """Value at t of 1 a year paid on the remaining annual dates up to maturity (flat rate)."""
    out, k = 0.0, math.floor(t) + 1
    while k <= maturity + 1e-9:
        out += 1.0 / (1.0 + rate) ** (k - t)
        k += 1
    return out


@dataclass(frozen=True)
class MarginModel:
    sigma_bp_day: float = 7.0      # daily standard deviation of the swap rate, bp
    mpor_days: float = 5.0         # margin period of risk
    z: float = 2.326               # 99% one-sided

    def im_per_dv01(self) -> float:
        """Initial margin per unit of DV01 (i.e. in basis points of rate)."""
        return self.z * self.sigma_bp_day * math.sqrt(self.mpor_days)


def dv01_path(notional: float, maturity: float, rate: float, step: float) -> list[tuple[float, float]]:
    """(t, DV01 per bp) at each step until maturity."""
    out, t = [], 0.0
    while t < maturity - 1e-9:
        out.append((t, notional * annuity_remaining(t, maturity, rate) * 1e-4))
        t += step
    return out


def im_path(notional: float, maturity: float, rate: float, model: MarginModel, step: float = 0.25):
    return [(t, d * model.im_per_dv01()) for t, d in dv01_path(notional, maturity, rate, step)]


def mva(notional: float, maturity: float, rate: float, model: MarginModel, funding_spread: float,
        step: float = 0.25) -> float:
    """Present value of funding the initial margin over the swap's life."""
    return sum(funding_spread * m * step / (1.0 + rate) ** t for t, m in im_path(notional, maturity, rate, model, step))


def basis_bp(notional: float, maturity: float, rate: float, model: MarginModel, funding_spread: float,
             ccps: int = 1) -> float:
    """Running spread (bp a year on the swap) that pays for the MVA of `ccps` one-way positions."""
    dv01 = notional * annuity_remaining(0.0, maturity, rate) * 1e-4
    return ccps * mva(notional, maturity, rate, model, funding_spread) / dv01
