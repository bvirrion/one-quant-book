"""Funding, margin and capital adjustments (build of One Quant Book 6, chapter 19).

FCA = sum_k s_f DEE(t_k) S(t_k) dt,  FBA = sum_k s_b DNE(t_k) S(t_k) dt   (S: joint survival or 1),
MVA = sum_k (s_f - r_im) E[IM(t_k)] D(t_k) S dt,   with IM from Book 2's `firm_ccpbasis` margin model,
KVA = h sum_k K(t_k) D(t_k) S dt,   K = counterparty-credit capital + CVA capital.
Capital: SA-CCR (BCBS 279) exposure at default for interest rate and FX hedging sets,
  EAD = alpha (RC + multiplier AddOn), alpha = 1.4, supervisory duration SD = (e^{-0.05 S} - e^{-0.05 E}) / 0.05,
  maturity factor sqrt(min(M, 1)) unmargined, 1.5 sqrt(MPOR / 1y) margined, IR factor 0.5% with the
  three-bucket aggregation, FX factor 4%; and the reduced basic approach to CVA capital (BCBS, July 2020):
  SCVA = RW M EAD DF / alpha, DF = (1 - e^{-0.05 M}) / (0.05 M), K = DS sqrt((rho sum SCVA)^2 + (1 - rho^2) sum SCVA^2),
  rho = 0.5, DS = 0.65. Risk weight for counterparty credit capital and hurdle rate are inputs.
"""
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "ccpbasis"))
import firm_ccpbasis as ccp  # noqa: E402

ALPHA, SF_IR, SF_FX, FLOOR = 1.4, 0.005, 0.04, 0.05


def fca(dee: np.ndarray, times: np.ndarray, spread: float, survival: np.ndarray | None = None) -> float:
    """Funding cost of the discounted positive exposure (trapezoid on the grid)."""
    s = np.ones_like(dee) if survival is None else survival
    f = dee * s
    return float(spread * np.sum(0.5 * (f[1:] + f[:-1]) * np.diff(times)))


def fba(dne: np.ndarray, times: np.ndarray, spread: float, survival: np.ndarray | None = None) -> float:
    return fca(dne, times, spread, survival)


def supervisory_duration(start: float, end: float) -> float:
    s, e = start, max(end, 10 / 250)       # a started trade has S = 0
    return (math.exp(-0.05 * s) - math.exp(-0.05 * e)) / 0.05


def maturity_factor(maturity: float, mpor_days: float | None = None) -> float:
    if mpor_days is None:
        return math.sqrt(min(max(maturity, 10 / 250), 1.0))
    return 1.5 * math.sqrt(mpor_days / 250)


@dataclass(frozen=True)
class IrTrade:
    currency: str
    notional: float
    start: float          # years from today (0 if started)
    end: float
    delta: float          # +1 long the floating rate (pay fixed), -1 short, option delta otherwise
    maturity: float       # remaining maturity for the maturity factor

    def bucket(self) -> int:
        return 1 if self.end < 1 else (2 if self.end <= 5 else 3)


def ir_addon(trades: list[IrTrade], mpor_days: float | None = None) -> float:
    total = 0.0
    for ccy in sorted({t.currency for t in trades}):
        D = {1: 0.0, 2: 0.0, 3: 0.0}
        for t in trades:
            if t.currency == ccy:
                D[t.bucket()] += (t.delta * t.notional * supervisory_duration(t.start, t.end)
                                  * maturity_factor(t.maturity, mpor_days))
        en2 = (D[1] ** 2 + D[2] ** 2 + D[3] ** 2 + 1.4 * D[1] * D[2] + 1.4 * D[2] * D[3] + 0.6 * D[1] * D[3])
        total += SF_IR * math.sqrt(max(en2, 0.0))
    return total


def fx_addon(pairs: dict[str, float], maturity: float = 1.0, mpor_days: float | None = None) -> float:
    """pairs: net notional (domestic currency, signed) per currency pair; one maturity factor for simplicity."""
    return SF_FX * sum(abs(v) for v in pairs.values()) * maturity_factor(maturity, mpor_days)


def multiplier(v_minus_c: float, addon: float) -> float:
    if addon <= 0:
        return 1.0
    return min(1.0, FLOOR + (1 - FLOOR) * math.exp(v_minus_c / (2 * (1 - FLOOR) * addon)))


def sa_ccr_ead(v: float, addon: float, collateral: float = 0.0, th: float | None = None, mta: float = 0.0,
               nica: float = 0.0) -> float:
    """EAD = alpha (RC + multiplier AddOn); RC unmargined max(V - C, 0), margined max(V - C, TH + MTA - NICA, 0)."""
    rc = max(v - collateral, 0.0) if th is None else max(v - collateral, th + mta - nica, 0.0)
    return ALPHA * (rc + multiplier(v - collateral, addon) * addon)


def ba_cva_capital(scva: list[float], rho: float = 0.5, ds: float = 0.65) -> float:
    return ds * math.sqrt((rho * sum(scva)) ** 2 + (1 - rho ** 2) * sum(s * s for s in scva))


def scva(rw: float, maturity: float, ead: float) -> float:
    df = (1 - math.exp(-0.05 * maturity)) / (0.05 * maturity) if maturity > 0 else 1.0
    return rw * maturity * ead * df / ALPHA


def kva(capital: np.ndarray, times: np.ndarray, hurdle: float, discount: np.ndarray,
        survival: np.ndarray | None = None) -> float:
    s = np.ones_like(capital) if survival is None else survival
    f = capital * discount * s
    return float(hurdle * np.sum(0.5 * (f[1:] + f[:-1]) * np.diff(times)))


def mva(notional: float, maturity: float, rate: float, funding_spread: float, sigma_bp_day: float = 7.0,
        mpor_days: float = 10.0, z: float = 2.326) -> float:
    """MVA of a swap's initial margin (both parties post; this is one side's cost), Book 2's margin model:
    IM = z sigma sqrt(MPOR) DV01, funded at `funding_spread` over the rate paid on margin."""
    return ccp.mva(notional, maturity, rate, ccp.MarginModel(sigma_bp_day, mpor_days, z), funding_spread)


def im_profile(notional: float, maturity: float, rate: float, sigma_bp_day: float = 7.0, mpor_days: float = 10.0,
               z: float = 2.326, step: float = 0.25) -> list[tuple[float, float]]:
    return ccp.im_path(notional, maturity, rate, ccp.MarginModel(sigma_bp_day, mpor_days, z), step)


def effective_maturity(remaining: float) -> float:
    """Effective maturity of a swap for CVA capital: the average time of its remaining annual payments
    (a cash-flow-weighted maturity with equal payments), floored at one payment."""
    times = [remaining - j for j in range(math.ceil(remaining - 1e-9)) if remaining - j > 1e-9]
    return sum(times) / len(times) if times else remaining
