"""Inverse options and coin-margined conversions, and basis annualisation (build of Book 3, Chapter 19);
prices from firm.parity (Black 1976 on the future).

An inverse option is a standard option on the dollar price of the coin whose premium is quoted and paid
in coin: premium in coin = dollar price / F, with F the underlying future. Its holder's delta in coin
terms includes the premium, since the premium itself is a coin amount whose dollar value moves with F.
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "parity"))
from firm_parity import _phi, price  # noqa: E402


def coin_premium(forward: float, strike: float, years: float, vol: float, right: str, rate: float = 0.0) -> float:
    """Premium in coin of an inverse option (the dollar price divided by the future)."""
    return price(forward, strike, years, rate, vol, right) / forward


def usd_premium(coin_prem: float, forward: float) -> float:
    return coin_prem * forward


def forward_delta(forward: float, strike: float, years: float, vol: float, right: str) -> float:
    """Dollar-price delta to the future: N(d1) for a call, N(d1) - 1 for a put."""
    s = vol * math.sqrt(years)
    d1 = math.log(forward / strike) / s + 0.5 * s
    return _phi(d1) if right == "C" else _phi(d1) - 1.0


def premium_adjusted_delta(forward: float, strike: float, years: float, vol: float, right: str) -> float:
    """Delta, in coin per option, of an option whose premium is paid in the coin: the dollar delta less the
    coin premium (a buyer who paid the premium in coin is already short that much coin's dollar value)."""
    return forward_delta(forward, strike, years, vol, right) - coin_premium(forward, strike, years, vol, right)


def annualised_basis(future: float, spot: float, days: float, compounding: str = "simple") -> float:
    """Basis per year: simple (F/S - 1) x 365/days, or continuous ln(F/S) x 365/days."""
    if compounding == "simple":
        return (future / spot - 1) * 365 / days
    return math.log(future / spot) * 365 / days


def etf_basis_carry(basis_annual: float, financing: float, etf_fee: float, futures_costs: float) -> float:
    """Annual carry of long spot ETF, short future: the basis less financing of the ETF purchase, the fund's
    fee and the futures' annualised trading and roll costs, per unit of ETF notional."""
    return basis_annual - financing - etf_fee - futures_costs


def return_on_margin(carry: float, margin: float, haircut: float) -> float:
    """Carry over the capital tied up: futures margin plus the haircut on the financed ETF, per unit notional."""
    return carry / (margin + haircut)


def weighted_median(prices_sizes: list[tuple[float, float]]) -> float:
    """Volume-weighted median: the price at which cumulative size first reaches half the total."""
    rows = sorted(prices_sizes)
    half, cum = 0.5 * sum(s for _, s in rows), 0.0
    for p, s in rows:
        cum += s
        if cum >= half:
            return p
    raise ValueError("no trades")


def reference_rate(trades: list[tuple[float, float, float]], start: float, end: float, parts: int = 12) -> float:
    """Benchmark in the style of a published bitcoin reference rate: trades (time, price, size) inside
    [start, end) are split into equal time partitions; the rate is the equally weighted average of the
    partitions' volume-weighted medians (empty partitions are skipped)."""
    width = (end - start) / parts
    meds = []
    for i in range(parts):
        lo, hi = start + i * width, start + (i + 1) * width
        part = [(p, s) for t, p, s in trades if lo <= t < hi]
        if part:
            meds.append(weighted_median(part))
    if not meds:
        raise ValueError("no trades in the window")
    return sum(meds) / len(meds)
