"""Trade surveillance for unauthorised trading (build of One Quant Book 6, chapter 28).

Rules on a blotter of trades, each returning the trades it flags:
  late booking        booked more than `hours` after execution;
  cancel-and-amend    cancelled or amended within `days` of a reporting date;
  off-market price    more than `k` bid-offer spreads from the market mid;
  internal unmatched  booked against an internal counterparty with no mirror trade;
  deferred settlement settlement date far in the future (never meant to settle).
Alerts are scored by the number of rules a trade breaks; hit and false-alarm rates are measured against
known labels. An append-only audit log chains each entry to the previous one by a hash, so that a later
edit of any entry breaks the chain.
"""
import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Trade:
    trade_id: str
    trader: str
    executed: float            # hours since the start of the sample
    booked: float              # hours
    price: float
    mid: float
    spread: float              # market bid-offer spread
    counterparty: str          # "EXT:<name>" or "INT:<book>"
    mirror: str | None         # id of the mirror trade for internal deals
    settle_days: int           # days from trade to settlement
    status: str = "live"       # live, cancelled, amended
    status_time: float | None = None
    fraud: bool = False        # label, for measuring the rules


def late_booking(t: Trade, hours: float = 4.0) -> bool:
    return t.booked - t.executed > hours


def cancel_amend_near(t: Trade, reporting_times: Sequence[float], days: float = 2.0) -> bool:
    if t.status == "live" or t.status_time is None:
        return False
    return any(abs(t.status_time - r) <= 24.0 * days for r in reporting_times)


def off_market(t: Trade, k: float = 3.0) -> bool:
    return abs(t.price - t.mid) > k * t.spread


def internal_unmatched(t: Trade, ids: set[str]) -> bool:
    return t.counterparty.startswith("INT:") and (t.mirror is None or t.mirror not in ids)


def deferred_settlement(t: Trade, days: int = 30) -> bool:
    return t.settle_days > days


def run_rules(blotter: Sequence[Trade], reporting_times: Sequence[float]) -> dict[str, Callable[[Trade], bool]]:
    ids = {t.trade_id for t in blotter}
    return {"late booking": late_booking,
            "cancel/amend near reporting": lambda t: cancel_amend_near(t, reporting_times),
            "off-market price": off_market,
            "internal unmatched": lambda t: internal_unmatched(t, ids),
            "deferred settlement": deferred_settlement}


def evaluate(blotter: Sequence[Trade], rules: dict[str, Callable[[Trade], bool]], min_score: int = 1) -> dict:
    """Per-rule and combined hit rate (flagged fraud / all fraud) and false-alarm rate (flagged clean / all clean)."""
    fraud = [t for t in blotter if t.fraud]
    clean = [t for t in blotter if not t.fraud]
    out = {}
    for name, r in rules.items():
        out[name] = {"hit": sum(map(r, fraud)) / len(fraud), "false": sum(map(r, clean)) / len(clean)}

    def score(t):
        return sum(r(t) for r in rules.values())

    out["combined"] = {"hit": sum(score(t) >= min_score for t in fraud) / len(fraud),
                       "false": sum(score(t) >= min_score for t in clean) / len(clean)}
    return out


class AuditLog:
    """Append-only log; each entry stores the hash of the previous one."""

    def __init__(self):
        self.entries: list[dict] = []

    def append(self, event: dict) -> str:
        prev = self.entries[-1]["hash"] if self.entries else "0" * 64
        body = json.dumps({"event": event, "prev": prev}, sort_keys=True)
        h = hashlib.sha256(body.encode()).hexdigest()
        self.entries.append({"event": event, "prev": prev, "hash": h})
        return h

    def verify(self) -> bool:
        prev = "0" * 64
        for e in self.entries:
            body = json.dumps({"event": e["event"], "prev": prev}, sort_keys=True)
            if e["prev"] != prev or hashlib.sha256(body.encode()).hexdigest() != e["hash"]:
                return False
            prev = e["hash"]
        return True


def trade_event(t: Trade) -> dict:
    return asdict(t)
