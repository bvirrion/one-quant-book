"""All-in cost of delta-one wrappers, and the conversion band of a depositary receipt (Chapter 17).
Every parameter value here is illustrative: the point is the structure of the comparison."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Wrapper:
    name: str
    entry_bp: float                 # commission, half spread and impact, paid once
    exit_bp: float
    purchase_tax_bp: float          # stamp duty or transaction tax on entry
    running_bp: float               # management fee or similar, per year
    funding_spread_bp: float        # over the benchmark rate, per year, on the financed amount
    roll_bp: float                  # cost of one roll
    rolls_per_year: int
    dividend_leak: float            # fraction of the dividend yield lost to withholding


WRAPPERS = (
    Wrapper("shares", 5.0, 5.0, 50.0, 0.0, 50.0, 0.0, 0, 0.15),
    Wrapper("ETF", 3.0, 3.0, 0.0, 7.0, 50.0, 0.0, 0, 0.15),
    Wrapper("future", 1.0, 1.0, 0.0, 0.0, 30.0, 1.5, 4, 0.15),
    Wrapper("swap", 3.0, 3.0, 0.0, 0.0, 40.0, 0.0, 0, 0.05),
    Wrapper("CFD", 8.0, 8.0, 0.0, 0.0, 250.0, 0.0, 0, 0.15),
)


def breakdown(w: Wrapper, years: float, div_yield_bp: float, financed: float) -> dict[str, float]:
    """Cost in basis points of notional over the whole holding period.
    `financed` is the fraction of the notional the investor borrows (1 = fully leveraged).
    Synthetic wrappers finance the whole notional inside their price whatever the investor does;
    an investor with cash earns the benchmark on it, so only the spread is a cost."""
    synthetic = w.name in ("future", "swap", "CFD")
    funded_fraction = 1.0 if synthetic else financed
    return {
        "trading": w.entry_bp + w.exit_bp + w.roll_bp * w.rolls_per_year * years,
        "tax": w.purchase_tax_bp,
        "running": w.running_bp * years,
        "funding": w.funding_spread_bp * funded_fraction * years,
        "dividends": w.dividend_leak * div_yield_bp * years,
    }


def total(w: Wrapper, years: float, div_yield_bp: float, financed: float) -> float:
    return sum(breakdown(w, years, div_yield_bp, financed).values())


def crossover_years(a: Wrapper, b: Wrapper, div_yield_bp: float, financed: float) -> float | None:
    """Holding period at which the two wrappers cost the same (None if one always wins)."""
    fixed = total(a, 0.0, div_yield_bp, financed) - total(b, 0.0, div_yield_bp, financed)
    slope = (total(a, 1.0, div_yield_bp, financed) - total(a, 0.0, div_yield_bp, financed)) - (
        total(b, 1.0, div_yield_bp, financed) - total(b, 0.0, div_yield_bp, financed))
    if slope == 0 or -fixed / slope <= 0:
        return None
    return -fixed / slope


@dataclass(frozen=True)
class DrTerms:
    ratio: float                    # ordinary shares per receipt
    issue_fee: float                # depositary fee per receipt issued, in receipt currency
    cancel_fee: float
    entry_tax_bp: float             # charge on depositing ordinary shares (0 if none)
    trading_bp: float               # both legs' half spreads plus the currency trade


def parity(ordinary_price: float, fx: float, terms: DrTerms) -> float:
    """Receipt price at which holding the receipt and the ordinaries is the same thing."""
    return ordinary_price * terms.ratio * fx


def dr_band_bp(ordinary_price: float, fx: float, terms: DrTerms) -> tuple[float, float]:
    """(lower, upper) premium of the receipt over parity, in bp, beyond which conversion pays.
    Above the upper bound: buy ordinaries, deposit, sell receipts. Below the lower: the reverse."""
    p = parity(ordinary_price, fx, terms)
    upper = terms.trading_bp + terms.entry_tax_bp + terms.issue_fee / p * 1e4
    lower = -(terms.trading_bp + terms.cancel_fee / p * 1e4)
    return lower, upper
