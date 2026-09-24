"""Implied dividends, a dividend-futures strip and a total return future (Chapter 22). Illustrative."""


def implied_dividends(spot: float, future: float, rate: float, years: float) -> float:
    """Dividend points to expiry implied by an index future, simple interest, reinvestment ignored."""
    return spot * (1.0 + rate * years) - future


def implied_growth(strip: list[float]) -> list[float]:
    """Year-on-year growth implied by consecutive annual dividend futures."""
    return [b / a - 1.0 for a, b in zip(strip[:-1], strip[1:], strict=True)]


def future_pnl_on_dividend_cut(multiplier: float, contracts: int, cut_points: float) -> float:
    """A LONG index future gains when expected dividends fall: the index will drop less on ex-dates.
    First-order P&L of the repricing, for a cut of `cut_points` in dividends before expiry."""
    return multiplier * contracts * cut_points


def trf_price(index_close: float, accrued_distributions: float, accrued_funding: float,
              spread_bp: float, years_to_expiry: float) -> float:
    """Total return future in index points: close plus what has accrued, plus the traded spread
    (annualised, in basis points) applied to the index level for the remaining life."""
    return index_close + accrued_distributions - accrued_funding + index_close * spread_bp * 1e-4 * years_to_expiry


def trf_pnl_from_spread(index_level: float, multiplier: float, contracts: int, d_spread_bp: float,
                        years_to_expiry: float) -> float:
    """P&L of a long TRF when the traded spread moves by d_spread_bp: a pure financing position."""
    return multiplier * contracts * index_level * d_spread_bp * 1e-4 * years_to_expiry


REGIONS_2025 = (("Asia-Pacific", 75.59), ("North America", 24.50), ("Latin America", 11.39),
                ("Europe", 4.38), ("Other", 3.43))          # billion contracts, FIA, full year 2025
