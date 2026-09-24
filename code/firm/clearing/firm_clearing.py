"""firm.clearing -- multilateral netting engine (build of Chapter 5, One Quant Book 1).

Prices are integers in ledger units (1/10 000 of the currency unit), so cash is exact.
"""
from collections import defaultdict
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class ClearedTrade:
    trade_id: str
    buyer: str
    seller: str
    symbol: str
    quantity: int
    price_units: int
    currency: str = "USD"


@dataclass(frozen=True)
class SettlementInstructions:
    shares: MappingProxyType      # (member, symbol) -> signed quantity, + receives
    cash: MappingProxyType        # (member, currency) -> signed ledger units, + receives
    netted: MappingProxyType      # member -> tuple of trade ids


class NettingEngine:
    def __init__(self) -> None:
        self._trades: dict[str, ClearedTrade] = {}
        self._closed = False

    def add(self, t: ClearedTrade) -> None:
        if self._closed:
            raise RuntimeError("session closed")
        if t.buyer == t.seller:
            raise ValueError("buyer equals seller")
        if t.quantity <= 0 or t.price_units <= 0:
            raise ValueError("quantity and price must be positive")
        if t.trade_id in self._trades:
            raise ValueError(f"duplicate trade id {t.trade_id}")
        self._trades[t.trade_id] = t

    def close(self) -> SettlementInstructions:
        self._closed = True
        shares: dict[tuple[str, str], int] = defaultdict(int)
        cash: dict[tuple[str, str], int] = defaultdict(int)
        netted: dict[str, list[str]] = defaultdict(list)
        for t in self._trades.values():
            value = t.quantity * t.price_units
            shares[(t.buyer, t.symbol)] += t.quantity
            shares[(t.seller, t.symbol)] -= t.quantity
            cash[(t.buyer, t.currency)] -= value
            cash[(t.seller, t.currency)] += value
            netted[t.buyer].append(t.trade_id)
            netted[t.seller].append(t.trade_id)
        by_symbol: dict[str, int] = defaultdict(int)
        by_ccy: dict[str, int] = defaultdict(int)
        for (_, sym), q in shares.items():
            by_symbol[sym] += q
        for (_, ccy), c in cash.items():
            by_ccy[ccy] += c
        if any(by_symbol.values()) or any(by_ccy.values()):
            raise AssertionError("netting invariant violated: positions do not sum to zero")
        return SettlementInstructions(MappingProxyType(dict(shares)), MappingProxyType(dict(cash)),
                                      MappingProxyType({m: tuple(v) for m, v in netted.items()}))
