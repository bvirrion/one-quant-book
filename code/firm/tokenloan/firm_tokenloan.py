"""Token market-making agreement valuation (build of Book 3, Chapter 24); posts to firm.ledger.

A project lends a market maker N tokens for a term, to be returned, and grants it European calls on
tranches of tokens at several strikes. The calls are valued by Monte Carlo on a driftless lognormal
price (with the closed form as a check); their value over the loaned tokens' value is the fee the
deal implies; their delta is what the market maker must sell on day one to be hedged, since the loan
itself (tokens received, tokens owed) carries no net exposure.
"""
import math
import pathlib
import random
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "ledger"))
from firm_ledger import Entry, Ledger, to_units  # noqa: E402


def _phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


@dataclass(frozen=True)
class Deal:
    tokens_loaned: float
    price: float                       # token price at signing, dollars
    years: float
    vol: float
    tranches: tuple                    # ((tokens, strike), ...)


def call_bs(s: float, k: float, t: float, vol: float) -> tuple[float, float]:
    """Driftless Black-Scholes call value and delta (no discounting: short-dated, dollar-rate-free)."""
    sd = vol * math.sqrt(t)
    d1 = math.log(s / k) / sd + 0.5 * sd
    return s * _phi(d1) - k * _phi(d1 - sd), _phi(d1)


def package_value_mc(deal: Deal, paths: int = 200_000, seed: int = 24) -> float:
    """Monte Carlo value of the call package: antithetic pairs and the terminal price as a control
    variate (its expectation is the price at signing)."""
    rng = random.Random(seed)
    sd = deal.vol * math.sqrt(deal.years)
    pays, ends = [], []
    for _ in range(paths // 2):
        z = rng.gauss(0, 1)
        for zz in (z, -z):
            st = deal.price * math.exp(-0.5 * sd * sd + sd * zz)
            pays.append(sum(n * max(st - k, 0.0) for n, k in deal.tranches))
            ends.append(st)
    n = len(pays)
    mp, me = sum(pays) / n, sum(ends) / n
    cov = sum((p - mp) * (e - me) for p, e in zip(pays, ends, strict=True)) / n
    var = sum((e - me) ** 2 for e in ends) / n
    return mp - cov / var * (me - deal.price)


def package_value(deal: Deal) -> float:
    return sum(n * call_bs(deal.price, k, deal.years, deal.vol)[0] for n, k in deal.tranches)


def implied_fee(deal: Deal) -> float:
    """Call value as a share of the loaned tokens' value."""
    return package_value(deal) / (deal.tokens_loaned * deal.price)


def day_one_hedge(deal: Deal) -> float:
    """Tokens to sell at signing so that the calls are delta-hedged."""
    return sum(n * call_bs(deal.price, k, deal.years, deal.vol)[1] for n, k in deal.tranches)


def delta_schedule(deal: Deal, prices: list[float], t_left: float) -> list[tuple[float, float]]:
    """Tokens the hedge should be short at each price with t_left years to expiry."""
    return [(s, sum(n * call_bs(s, k, t_left, deal.vol)[1] for n, k in deal.tranches)) for s in prices]


def obligations_met(spread_bp: float, depth_usd: float, uptime: float, max_spread_bp: float = 100.0,
                    min_depth_usd: float = 50_000.0, min_uptime: float = 0.95) -> bool:
    """Typical quoting obligations: spread within a maximum, depth at least a minimum, for a share of time."""
    return spread_bp <= max_spread_bp and depth_usd >= min_depth_usd and uptime >= min_uptime


def post_fee(ledger: Ledger, deal: Deal, ts: int, account: str = "desk.crypto.tokenmm") -> int:
    """Book the implied fee (the calls' value at signing) as fee revenue; returns the ledger units posted."""
    amount = to_units(package_value(deal))
    ledger.post(Entry(ts, account, "fee", "USD", amount, "token loan-plus-call"))
    return amount
