"""Restructuring offers, holdouts and loss absorption (build of Book 2, Chapter 26).

An exchange offer is valued at an exit yield: the present value of the new instruments per 100 of
old face value, and its haircut against the old claim. A holdout's value is a probability tree:
paid in full soon, which becomes likelier as fewer creditors hold out; or, if not, a lawsuit that
may recover the whole claim years later; or a defaulted bond that stays defaulted. A collective
action clause with threshold tau binds every holder to the offer once participation reaches tau.
Bank losses are absorbed by a capital stack in a given order.
"""
from dataclasses import dataclass


def bond_pv(face: float, coupon: float, years: int, y: float) -> float:
    """Present value of an annual-coupon bullet bond at yield y."""
    return sum(face * coupon / (1 + y) ** t for t in range(1, years + 1)) + face / (1 + y) ** years


def npv_haircut(value: float, claim: float = 100.0) -> float:
    return 1.0 - value / claim


@dataclass(frozen=True)
class Offer:
    new_face: float                  # per 100 of old face
    coupon: float
    years: int
    cash: float = 0.0                # paid only to those who tender

    def value(self, y: float) -> float:
        return bond_pv(self.new_face, self.coupon, self.years, y) + self.cash


@dataclass(frozen=True)
class Holdout:
    paid_soon: float                 # PV of being paid in full soon
    lawsuit_prob: float
    lawsuit_pv: float                # PV of the whole claim recovered by litigation
    stuck: float                     # value of a bond that stays in default
    power: float = 8.0               # P(paid soon) = participation ** power

    def value(self, p: float) -> float:
        paid = p ** self.power
        return paid * self.paid_soon + (1 - paid) * (self.lawsuit_prob * self.lawsuit_pv
                                                     + (1 - self.lawsuit_prob) * self.stuck)


def holdout_payoff(p: float, h: Holdout, bound_value: float, cac: float | None) -> float:
    """Value of holding out at participation p; above a CAC threshold the holdout is bound to the offer
    (without the cash reserved for tendering)."""
    return bound_value if cac is not None and p >= cac else h.value(p)


def breakeven_participation(h: Holdout, tender_value: float) -> float:
    """Participation at which holding out, not yet bound, is worth as much as tendering."""
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if h.value(mid) < tender_value else (lo, mid)
    return 0.5 * (lo + hi)


def absorb(stack: list[tuple[str, float]], loss: float) -> dict[str, float]:
    """Losses taken by each layer, the first-listed absorbing first; returns what each layer keeps."""
    kept = {}
    for name, size in stack:
        hit = min(size, loss)
        loss -= hit
        kept[name] = size - hit
    return kept
