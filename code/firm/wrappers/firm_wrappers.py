"""Wrapper-cost comparator (build of Book 1, Chapter 17).

Ranks the ways of holding one exposure by all-in cost for a given investor and horizon, long or
short, and reports the breakdown so that the choice can be explained.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class WrapperTerms:
    name: str
    synthetic: bool                 # financing is inside the price (future, swap, CFD)
    entry_bp: float
    exit_bp: float
    purchase_tax_bp: float
    running_bp: float
    funding_spread_bp: float        # long: paid over the benchmark
    short_spread_bp: float          # short: benchmark minus what the short earns, excluding borrow
    roll_bp: float
    rolls_per_year: int
    dividend_leak: float            # share of the dividend lost by a long holder
    shortable: bool = True


@dataclass(frozen=True)
class Investor:
    financed: float                 # fraction of a physical long that is borrowed
    dividend_leak_override: dict[str, float] | None = None   # e.g. a tax-exempt holder: {"shares": 0.0}


@dataclass(frozen=True)
class Quote:
    name: str
    total_bp: float
    parts: dict[str, float]


def cost(w: WrapperTerms, inv: Investor, years: float, div_yield_bp: float, side: int = 1,
         borrow_fee_bp: float = 0.0) -> Quote:
    if side not in (1, -1):
        raise ValueError("side must be +1 or -1")
    if side == -1 and not w.shortable:
        raise ValueError(f"{w.name} cannot be shorted")
    leak = (inv.dividend_leak_override or {}).get(w.name, w.dividend_leak)
    parts = {
        "trading": w.entry_bp + w.exit_bp + w.roll_bp * w.rolls_per_year * years,
        "tax": w.purchase_tax_bp if side == 1 else 0.0,
        "running": w.running_bp * years * side,              # a short of a fund earns its fee
    }
    if side == 1:
        parts["funding"] = w.funding_spread_bp * (1.0 if w.synthetic else inv.financed) * years
        parts["dividends"] = leak * div_yield_bp * years
    else:
        parts["funding"] = (w.short_spread_bp + borrow_fee_bp) * years
        parts["dividends"] = 0.0                              # a short pays the gross dividend: no leak, no gain
    return Quote(w.name, sum(parts.values()), parts)


def rank(wrappers: list[WrapperTerms], inv: Investor, years: float, div_yield_bp: float, side: int = 1,
         borrow_fee_bp: float = 0.0) -> list[Quote]:
    quotes = [cost(w, inv, years, div_yield_bp, side, borrow_fee_bp) for w in wrappers if side == 1 or w.shortable]
    return sorted(quotes, key=lambda q: (q.total_bp, q.name))
