"""Fee-schedule engine (build of Book 1, Chapter 29).

An exchange fee schedule is a function from a month of activity to a bill. Rates are per share,
positive = the member pays, negative = the member is paid (a rebate). Tiers are qualified on the
member's average daily ADDED volume as a fraction of total consolidated volume, and the tier's
rate applies to EVERY share added that month, which is what makes thresholds cliffs.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Tier:
    name: str
    min_adav_share: float           # ADAV / TCV needed, e.g. 0.0020 for 0.20%
    add_rate: float                 # per share; negative = rebate


@dataclass(frozen=True)
class Schedule:
    venue: str
    base_add_rate: float
    remove_rate: float
    tiers: tuple[Tier, ...] = ()

    def tier_for(self, adav: float, tcv: float) -> Tier | None:
        share = adav / tcv
        ok = [t for t in self.tiers if share >= t.min_adav_share]
        return min(ok, key=lambda t: t.add_rate) if ok else None

    def add_rate(self, adav: float, tcv: float) -> float:
        t = self.tier_for(adav, tcv)
        return t.add_rate if t else self.base_add_rate

    def daily_bill(self, added: float, removed: float, tcv: float) -> float:
        """Net exchange fees for an average day (negative = the exchange pays the member)."""
        return added * self.add_rate(added, tcv) + removed * self.remove_rate

    def next_tier(self, adav: float, tcv: float) -> Tier | None:
        current = self.add_rate(adav, tcv)
        better = [t for t in self.tiers if t.add_rate < current]
        return min(better, key=lambda t: t.min_adav_share) if better else None


def extra_volume_worth_adding(s: Schedule, adav: float, tcv: float, loss_per_extra_share: float) -> tuple[float, float]:
    """To reach the next tier a member can add volume it would not otherwise trade, at a loss per
    share (before rebate). Returns (extra shares a day needed, daily gain from doing so); the gain
    counts the better rate on ALL added shares and the rebate earned on the extra ones."""
    nxt = s.next_tier(adav, tcv)
    if nxt is None:
        return 0.0, 0.0
    extra = max(0.0, nxt.min_adav_share * tcv - adav)
    now = -adav * s.add_rate(adav, tcv)
    then = -(adav + extra) * nxt.add_rate - extra * loss_per_extra_share
    return extra, then - now


def breakeven_natural_volume(current_rebate: float, next_rebate: float, threshold: float, loss: float) -> float | None:
    """Natural added volume v above which padding up to `threshold` pays, rebates given as positive
    numbers: threshold * next - (threshold - v) * loss - v * current > 0. None if padding never pays
    (the loss per padded share is below the current rebate, so padding pays at any volume: return 0)."""
    if loss <= next_rebate:
        return 0.0                                   # each padded share is profitable in itself
    if loss <= current_rebate:
        return 0.0
    v = threshold * (loss - next_rebate) / (loss - current_rebate)
    return v if v < threshold else None


@dataclass(frozen=True)
class AllIn:
    exchange: float
    clearing: float
    regulatory: float

    @property
    def total(self) -> float:
        return self.exchange + self.clearing + self.regulatory


def all_in_per_share(s: Schedule, adav: float, tcv: float, passive: bool, clearing_per_share: float,
                     regulatory_per_share: float) -> AllIn:
    rate = s.add_rate(adav, tcv) if passive else s.remove_rate
    return AllIn(rate, clearing_per_share, regulatory_per_share)
