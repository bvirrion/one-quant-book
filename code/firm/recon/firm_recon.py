"""Reconstitution predictor (build of Book 1, Chapter 15).

Ranks a universe by total capitalisation on the rank day, applies a buffer rule, and converts the
predicted additions and deletions into the trades of the funds that track the index.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Security:
    symbol: str
    shares: int                     # total shares outstanding
    price: float                    # rank-day close
    float_factor: float             # fraction of shares in the free float
    adv_shares: int                 # average daily volume
    member: bool                    # in the index today

    @property
    def cap(self) -> float:
        return self.shares * self.price

    @property
    def float_cap(self) -> float:
        return self.cap * self.float_factor


@dataclass(frozen=True)
class Prediction:
    members: tuple[str, ...]
    adds: tuple[str, ...]
    deletes: tuple[str, ...]


@dataclass(frozen=True)
class TrackerTrade:
    symbol: str
    dollars: float                  # positive = trackers buy
    shares: int
    adv_multiple: float


def predict(universe: list[Security], n: int, buffer: int) -> Prediction:
    ranked = sorted(universe, key=lambda s: (-s.cap, s.symbol))
    rank = {s.symbol: k + 1 for k, s in enumerate(ranked)}
    chosen = {s.symbol for s in ranked
              if (s.member and rank[s.symbol] <= n + buffer) or (not s.member and rank[s.symbol] <= n - buffer)}
    for s in ranked:                                         # fill by rank
        if len(chosen) >= n:
            break
        chosen.add(s.symbol)
    for s in reversed(ranked):                               # trim from the bottom, outsiders first
        if len(chosen) <= n:
            break
        if s.symbol in chosen and not (s.member and rank[s.symbol] <= n):
            chosen.discard(s.symbol)
    members = tuple(s.symbol for s in ranked if s.symbol in chosen)
    adds = tuple(s.symbol for s in ranked if s.symbol in chosen and not s.member)
    deletes = tuple(s.symbol for s in ranked if s.member and s.symbol not in chosen)
    return Prediction(members, adds, deletes)


def weights(universe: list[Security], members: tuple[str, ...]) -> dict[str, float]:
    caps = {s.symbol: s.float_cap for s in universe if s.symbol in members}
    total = sum(caps.values())
    return {k: v / total for k, v in caps.items()}


def tracker_trades(universe: list[Security], pred: Prediction, tracked_assets: float) -> list[TrackerTrade]:
    """Trades in the additions and deletions only (the small re-weighting of survivors is ignored)."""
    by = {s.symbol: s for s in universe}
    old = weights(universe, tuple(s.symbol for s in universe if s.member))
    new = weights(universe, pred.members)
    out = []
    for sym in pred.adds + pred.deletes:
        dollars = tracked_assets * (new.get(sym, 0.0) - old.get(sym, 0.0))
        s = by[sym]
        n_shares = round(dollars / s.price)
        out.append(TrackerTrade(sym, dollars, n_shares, abs(n_shares) / s.adv_shares))
    return out
