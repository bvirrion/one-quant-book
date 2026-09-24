"""Structural credit models (build of One Quant Book 6, chapter 14).

Merton (1974): the firm's assets V follow a geometric Brownian motion with volatility sigma; debt is
one zero-coupon bond of face D due at T; equity is a European call on V struck at D, debt is V minus
equity. Asset value and volatility are backed out from the equity value and equity volatility.
Black and Cox (1976) first passage: default the first time V touches a barrier B < V (a constant
barrier, or B e^{g t}); survival probabilities in closed form from the reflection principle.
Both models give a survival curve, turned into a model CDS spread by chapter 13's `firm_cdscurve`.
Rates: a flat continuously compounded r. Amounts in any currency unit.
"""
import math
import pathlib
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "cdscurve"))
from firm_cdscurve import HazardCurve, par_spread  # noqa: E402


def ncdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


@dataclass(frozen=True)
class FlatDisc:
    r: float

    def df_t(self, t: float) -> float:
        return math.exp(-self.r * t)


def _d12(V: float, D: float, T: float, r: float, sigma: float) -> tuple[float, float]:
    d1 = (math.log(V / D) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    return d1, d1 - sigma * math.sqrt(T)


def merton_equity(V: float, D: float, T: float, r: float, sigma: float) -> float:
    d1, d2 = _d12(V, D, T, r, sigma)
    return V * ncdf(d1) - D * math.exp(-r * T) * ncdf(d2)


def merton_debt(V: float, D: float, T: float, r: float, sigma: float) -> float:
    return V - merton_equity(V, D, T, r, sigma)


def merton_spread(V: float, D: float, T: float, r: float, sigma: float) -> float:
    """Yield of the risky zero over r (continuously compounded)."""
    return -math.log(merton_debt(V, D, T, r, sigma) / D) / T - r


def merton_pd(V: float, D: float, T: float, drift: float, sigma: float) -> float:
    """P(V_T < D) with asset drift `drift` (r for risk-neutral, mu for real-world)."""
    return ncdf(-distance_to_default(V, D, T, drift, sigma))


def distance_to_default(V: float, D: float, T: float, mu: float, sigma: float) -> float:
    return (math.log(V / D) + (mu - 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))


def equity_vol(V: float, D: float, T: float, r: float, sigma: float) -> float:
    """sigma_E = N(d1) sigma V / E (Ito on E = C(V))."""
    return ncdf(_d12(V, D, T, r, sigma)[0]) * sigma * V / merton_equity(V, D, T, r, sigma)


def invert(E: float, sigma_E: float, D: float, T: float, r: float) -> tuple[float, float]:
    """Asset value and volatility matching equity value and equity volatility (Newton in two unknowns)."""
    V, s = E + D * math.exp(-r * T), sigma_E * E / (E + D * math.exp(-r * T))
    for _ in range(50):
        f1 = merton_equity(V, D, T, r, s) - E
        f2 = equity_vol(V, D, T, r, s) - sigma_E
        if abs(f1) < 1e-12 * E and abs(f2) < 1e-13:
            break
        hV, hs = 1e-6 * V, 1e-7
        a = (merton_equity(V + hV, D, T, r, s) - E - f1) / hV
        b = (merton_equity(V, D, T, r, s + hs) - E - f1) / hs
        c = (equity_vol(V + hV, D, T, r, s) - sigma_E - f2) / hV
        d = (equity_vol(V, D, T, r, s + hs) - sigma_E - f2) / hs
        det = a * d - b * c
        V -= (d * f1 - b * f2) / det
        s -= (a * f2 - c * f1) / det
    return V, s


def asset_from_equity(E: float, sigma: float, D: float, T: float, r: float) -> float:
    """Asset value giving equity value E at a fixed asset volatility (the model's equity delta holds sigma)."""
    lo, hi = E, E + D
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if merton_equity(mid, D, T, r, sigma) < E else (lo, mid)
    return 0.5 * (lo + hi)


def first_passage_survival(V: float, B: float, t: float, r: float, sigma: float, growth: float = 0.0) -> float:
    """P(min_{u<=t} V_u / (B e^{growth u}) > 1) for V with risk-neutral drift r (Black-Cox, reflection)."""
    if t <= 0.0:
        return 1.0
    nu = r - growth - 0.5 * sigma * sigma
    x = math.log(V / B)
    st = sigma * math.sqrt(t)
    return ncdf((x + nu * t) / st) - math.exp(-2.0 * nu * x / (sigma * sigma)) * ncdf((-x + nu * t) / st)


def hazard_curve_from_survival(q, horizon: float, freq: int = 4) -> HazardCurve:
    """Piecewise-constant hazards that match a survival function q(t) on the premium grid."""
    times, hz, prev = [], [], 1.0
    for k in range(1, round(horizon * freq) + 1):
        t = k / freq
        qt = max(q(t), 1e-300)
        times.append(t)
        hz.append(max(math.log(prev / qt) * freq, 0.0))
        prev = qt
    return HazardCurve(times, hz)


def model_cds_spread(q, r: float, maturity: float, recovery: float = 0.4) -> float:
    """Par CDS spread (quarterly premiums, chapter 13's legs) implied by a survival function q."""
    return par_spread(hazard_curve_from_survival(q, maturity), FlatDisc(r), maturity, recovery)
