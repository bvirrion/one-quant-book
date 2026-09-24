"""Weight-based rate-limit governor (build of Book 3, Chapter 15): Python reference of the C++20 and
Rust twins.

A venue limits requests in fixed windows aligned on the epoch (for example 6,000 units of weight per
minute per IP, 100 orders per 10 seconds per account). Each request consumes its weight in the
weight rules and, if it is an order, one unit in the order rules. The governor refuses a request that
would exceed any rule and says how long to wait; after the venue answers 429 (too many requests) it
stops for the advertised retry time, and after 418 (banned) until the ban ends. Times in milliseconds.
"""
from dataclasses import dataclass, field


@dataclass
class Rule:
    kind: str            # "weight" or "orders"
    interval_ms: int
    limit: int
    window: int = -1
    used: int = 0

    def room(self, now: int) -> int:
        w = now // self.interval_ms
        return self.limit if w != self.window else self.limit - self.used

    def consume(self, now: int, units: int) -> None:
        w = now // self.interval_ms
        if w != self.window:
            self.window, self.used = w, 0
        self.used += units

    def wait_ms(self, now: int) -> int:
        return (now // self.interval_ms + 1) * self.interval_ms - now


@dataclass
class Governor:
    rules: list[Rule]
    blocked_until: int = 0
    log: list[str] = field(default_factory=list)

    def try_send(self, now: int, weight: int, is_order: bool) -> tuple[bool, int]:
        """(allowed, milliseconds to wait if not)."""
        if now < self.blocked_until:
            return False, self.blocked_until - now
        need = {"weight": weight, "orders": 1 if is_order else 0}
        for r in self.rules:
            if need[r.kind] and r.room(now) < need[r.kind]:
                return False, r.wait_ms(now)
        for r in self.rules:
            if need[r.kind]:
                r.consume(now, need[r.kind])
        return True, 0

    def on_status(self, now: int, status: int, retry_after_ms: int = 0) -> None:
        """React to the venue: 429 pauses for retry_after; 418 is a ban for retry_after."""
        if status in (429, 418):
            self.blocked_until = max(self.blocked_until, now + retry_after_ms)
            self.log.append(f"{status}@{now}")


def binance_like() -> Governor:
    """The limits a large spot venue's exchange-information endpoint returned on 24 September 2026
    (weight per minute, orders per 10 seconds, orders per day)."""
    return Governor([Rule("weight", 60_000, 6_000), Rule("orders", 10_000, 100), Rule("orders", 86_400_000, 200_000)])
