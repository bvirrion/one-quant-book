"""firm.ledger -- the revenue-and-cost ledger every later component posts to.

Reference implementation of the Chapter 1 build (One Quant Book 1).
Amounts are integers in the currency's minor unit times 100 (hundredths of a
cent for USD), so that sub-cent fees and rebates add up exactly.
"""
from collections import defaultdict
from dataclasses import dataclass

CATEGORIES = ("spread", "position", "fee", "rebate", "commission", "financing", "other")
SCALE = 10_000  # ledger units per currency unit


@dataclass(frozen=True)
class Entry:
    ts: int          # nanoseconds since the epoch
    account: str     # e.g. "desk.mm.equities"
    category: str    # one of CATEGORIES
    currency: str    # ISO 4217
    amount: int      # signed, in 1/SCALE of the currency unit; + is revenue
    ref: str = ""    # free reference (fill id, invoice, ...)


class Ledger:
    def __init__(self) -> None:
        self._entries: list[Entry] = []

    def post(self, e: Entry) -> None:
        if e.category not in CATEGORIES:
            raise ValueError(f"unknown category {e.category!r}")
        if len(e.currency) != 3 or not e.currency.isupper():
            raise ValueError(f"bad currency {e.currency!r}")
        if not isinstance(e.amount, int):
            raise TypeError("amount must be an integer number of ledger units")
        if self._entries and e.ts < self._entries[-1].ts:
            raise ValueError("entries must be posted in time order")
        self._entries.append(e)

    def balance(self, account_prefix: str = "", currency: str = "USD") -> int:
        return sum(e.amount for e in self._entries
                   if e.currency == currency and e.account.startswith(account_prefix))

    def by_category(self, account_prefix: str = "", currency: str = "USD") -> dict[str, int]:
        out: dict[str, int] = defaultdict(int)
        for e in self._entries:
            if e.currency == currency and e.account.startswith(account_prefix):
                out[e.category] += e.amount
        return dict(out)

    def __len__(self) -> int:
        return len(self._entries)


def to_units(x: float) -> int:
    """Currency amount -> ledger units, rounded half away from zero."""
    v = abs(x) * SCALE
    n = int(v + 0.5)
    return n if x >= 0 else -n
