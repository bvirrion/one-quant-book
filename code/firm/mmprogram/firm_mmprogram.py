"""Market-maker programme monitor and venue fee arithmetic (build of Book 3, Chapter 25).

Crypto venues price by thirty-day volume tiers with maker and taker rates in basis points (the tier
logic of firm.feesched, keyed on volume instead of a share of consolidated volume). A market-maker
programme pays a rebate on maker volume if the firm's quotes meet an uptime requirement: the share of
sampled moments at which both its bid and its offer are within a maximum spread and carry a minimum
depth within a band around the mid. The quoting budget comes from the venue's order-count limit
(firm.ratelimit).
"""
import pathlib
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "ratelimit"))
from firm_ratelimit import Governor  # noqa: E402


@dataclass(frozen=True)
class VolTier:
    min_volume: float           # thirty-day volume, USD
    maker_bp: float
    taker_bp: float


def tier_for(volume: float, tiers: list[VolTier]) -> VolTier:
    return max((t for t in tiers if volume >= t.min_volume), key=lambda t: t.min_volume)


def monthly_fees(volume: float, maker_share: float, tiers: list[VolTier], matched: VolTier | None = None) -> float:
    """Fees in USD for a month; a tier match, if granted, replaces the tier when it is better."""
    t = tier_for(volume, tiers)
    if matched is not None and matched.maker_bp + matched.taker_bp < t.maker_bp + t.taker_bp:
        t = matched
    return volume * (maker_share * t.maker_bp + (1 - maker_share) * t.taker_bp) / 1e4


@dataclass(frozen=True)
class Snapshot:
    mid: float
    bid: float | None           # the firm's best bid (None if not quoting)
    ask: float | None
    bid_depth: float            # USD of the firm's bids within the band below the mid
    ask_depth: float


def compliant(s: Snapshot, max_spread_bp: float, min_depth_usd: float) -> bool:
    if s.bid is None or s.ask is None:
        return False
    return 1e4 * (s.ask - s.bid) / s.mid <= max_spread_bp and min(s.bid_depth, s.ask_depth) >= min_depth_usd


def uptime(snaps: list[Snapshot], max_spread_bp: float, min_depth_usd: float) -> float:
    return sum(compliant(s, max_spread_bp, min_depth_usd) for s in snaps) / len(snaps)


def rebate(maker_volume: float, rebate_bp: float, measured_uptime: float, required: float) -> float:
    """Programme rebate in USD: paid on all maker volume if the uptime requirement is met, else nothing."""
    return maker_volume * rebate_bp / 1e4 if measured_uptime >= required else 0.0


def requote_budget(gov: Governor, instruments: int) -> float:
    """Order messages per second per instrument the tightest order-count rule allows."""
    order_rules = [r for r in gov.rules if r.kind == "orders"]
    per_sec = min(r.limit / (r.interval_ms / 1000) for r in order_rules)
    return per_sec / instruments
