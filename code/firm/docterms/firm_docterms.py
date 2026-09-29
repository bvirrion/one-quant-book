"""firm.docterms -- agreement terms as data: collateral-annex calls, NAV-trigger monitoring and close-out with set-off
(analytical tool of One Quant Book 16, chapter 18; the subject is legal documentation and has no build in the
running-project sense). Illustrative terms; not a reading of any actual agreement.

Collateral annex: the credit support amount is the exposure plus the independent amount less the threshold (not
below zero); the call is that amount less the haircut value of the collateral already held, made only if it
reaches the minimum transfer amount, and rounded up (a delivery) or down (a return) to the rounding amount.
NAV triggers: an additional termination event if the net asset value falls by more than a fraction over a look-back
window (in days), or below a floor. Close-out: each agreement's close-out amount (positive: owed to the
non-defaulting party) less the collateral it holds; with set-off, the balances of agreements with the same
counterparty are netted into one amount.

API (stable):
    Annex(threshold, mta, rounding, independent_amount, haircuts) ; held_value(annex, collateral)
    call(annex, exposure, collateral)
    Trigger(name, drops, floor) ; first_trip(nav, trigger) -> (day, reason) or None
    close_out(amounts, collateral, set_off) -> dict
"""
import math
from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Annex:
    threshold: float = 0.0
    mta: float = 0.0
    rounding: float = 0.0
    independent_amount: float = 0.0
    haircuts: dict = field(default_factory=lambda: {"cash": 0.0})


def held_value(annex, collateral):
    """collateral: {asset: market value} held by the secured party."""
    return sum(v * (1 - annex.haircuts.get(a, 1.0)) for a, v in collateral.items())


def call(annex, exposure, collateral):
    """Positive: the secured party calls a delivery; negative: it must return collateral; 0 below the MTA."""
    need = max(exposure + annex.independent_amount - annex.threshold, 0.0) - held_value(annex, collateral)
    if abs(need) < annex.mta or need == 0:
        return 0.0
    if annex.rounding:
        r = annex.rounding
        need = math.ceil(need / r) * r if need > 0 else -math.floor(-need / r) * r
    return need


@dataclass(frozen=True)
class Trigger:
    name: str
    drops: tuple = ()              # ((window in days, fraction), ...)
    floor: float | None = None


def first_trip(nav, trigger):
    nav = np.asarray(nav, float)
    for t in range(len(nav)):
        if trigger.floor is not None and nav[t] < trigger.floor:
            return t, f"below floor {trigger.floor:g}"
        for w, x in trigger.drops:
            if t >= w and nav[t] / nav[t - w] - 1 <= -x:
                return t, f"fall of {100 * x:g}% over {w} days"
    return None


def close_out(amounts, collateral, set_off=True):
    """amounts, collateral: {agreement: value} for one counterparty; amounts positive when owed to the non-defaulting
    party, collateral positive when held by the non-defaulting party. Returns the per-agreement balances and the net."""
    bal = {k: amounts[k] - collateral.get(k, 0.0) for k in amounts}
    net = sum(bal.values()) if set_off else None
    return {"balances": bal, "net": net, "gross_claims": sum(v for v in bal.values() if v > 0),
            "gross_owed": -sum(v for v in bal.values() if v < 0)}
