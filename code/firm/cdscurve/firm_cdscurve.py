"""Hazard-rate curves and default swaps on a discount curve (build of One Quant Book 6, chapter 13).

Extends Book 2's flat-hazard `firm_cds` (imported for the standard-coupon conversion) to:
- a piecewise-constant hazard curve bootstrapped from a term structure of par CDS spreads, legs
  discounted on any discount curve (`df_t`), quarterly premiums with half-period accrual on default;
- the standard-model conversion between a quoted spread and an upfront at a standard coupon (flat
  hazard from the quote, as the ISDA standard model does);
- risky discount factors and annuities, bucketed CS01 by bump-and-rebootstrap, jump-to-default;
- a fixed-coupon bond priced on the hazard curve with recovery of par.
Amounts per unit notional; spreads and rates decimals.
"""
import math
import pathlib
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "cds"))
from firm_cds import Cds, hazard_from_spread, upfront  # noqa: E402


@dataclass
class HazardCurve:
    times: list[float]            # pillar times (years), increasing
    hazards: list[float]          # hazard on (times[i-1], times[i]]; flat after the last

    def cum(self, t: float) -> float:
        tot, prev = 0.0, 0.0
        for T, h in zip(self.times, self.hazards, strict=True):
            if t <= T:
                return tot + h * (t - prev)
            tot += h * (T - prev)
            prev = T
        return tot + self.hazards[-1] * (t - prev)

    def survival(self, t: float) -> float:
        return math.exp(-self.cum(t))


def legs(curve: HazardCurve, disc, maturity: float, recovery: float = 0.4, freq: int = 4) -> tuple[float, float]:
    """(risky annuity per unit of running coupon, protection leg) with defaults settled at period ends."""
    dt, ann, prot = 1.0 / freq, 0.0, 0.0
    for k in range(1, round(maturity * freq) + 1):
        q0, q1 = curve.survival((k - 1) * dt), curve.survival(k * dt)
        df = disc.df_t(k * dt)
        ann += dt * df * (q1 + 0.5 * (q0 - q1))
        prot += (1.0 - recovery) * df * (q0 - q1)
    return ann, prot


def par_spread(curve: HazardCurve, disc, maturity: float, recovery: float = 0.4) -> float:
    a, p = legs(curve, disc, maturity, recovery)
    return p / a


def bootstrap(disc, tenors: Sequence[float], spreads: Sequence[float], recovery: float = 0.4) -> HazardCurve:
    """Piecewise-constant hazards, one per tenor, so that each par CDS reprices (bisection)."""
    times, hz = [], []
    for T, s in zip(tenors, spreads, strict=True):
        times.append(T)
        hz.append(0.0)
        lo, hi = 0.0, 3.0
        for _ in range(100):
            mid = 0.5 * (lo + hi)
            hz[-1] = mid
            lo, hi = (mid, hi) if par_spread(HazardCurve(times, hz), disc, T, recovery) < s else (lo, mid)
        hz[-1] = 0.5 * (lo + hi)
    return HazardCurve(times, hz)


def standard_upfront(maturity: float, quoted_spread: float, coupon: float, rate: float,
                     recovery: float = 0.4) -> float:
    """Upfront (per unit, paid by the protection buyer) of a standard-coupon CDS from its quoted spread,
    with a flat hazard and a flat rate, as in the standard model's conversion (Book 2's firm_cds)."""
    c = Cds(maturity, coupon, recovery)
    return upfront(c, hazard_from_spread(c, quoted_spread, rate), rate)


def cds_value(curve: HazardCurve, disc, maturity: float, coupon: float, recovery: float = 0.4,
              buyer: bool = True) -> float:
    """Mark-to-market of a CDS paying `coupon` running, to the protection buyer (or seller)."""
    a, p = legs(curve, disc, maturity, recovery)
    v = p - coupon * a
    return v if buyer else -v


def risky_bond(curve: HazardCurve, disc, maturity: float, coupon: float, recovery: float = 0.4,
               freq: int = 2) -> float:
    """Fixed-coupon bond per unit face: coupons and principal if alive, recovery of par at default."""
    dt, v = 1.0 / freq, 0.0
    for k in range(1, round(maturity * freq) + 1):
        q0, q1 = curve.survival((k - 1) * dt), curve.survival(k * dt)
        df = disc.df_t(k * dt)
        v += coupon * dt * df * q1 + recovery * df * (q0 - q1)
    return v + disc.df_t(maturity) * curve.survival(maturity)


def bucketed_cs01(disc, tenors, spreads, recovery: float, pv: Callable[[HazardCurve], float],
                  bump: float = 1e-4) -> list[float]:
    """Change in pv when each quoted par spread rises by `bump` and the hazard curve is re-bootstrapped."""
    base = pv(bootstrap(disc, tenors, spreads, recovery))
    out = []
    for k in range(len(spreads)):
        sh = [s + (bump if i == k else 0.0) for i, s in enumerate(spreads)]
        out.append(pv(bootstrap(disc, tenors, sh, recovery)) - base)
    return out


def jump_to_default(mtm: float, notional: float, recovery: float, long_protection: bool) -> float:
    """P&L if the name defaults now: protection pays (1-R) N, and the position's MtM disappears."""
    payout = (1.0 - recovery) * notional
    return payout - mtm if long_protection else -payout - mtm
