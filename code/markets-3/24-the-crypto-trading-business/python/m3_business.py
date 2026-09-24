"""Book 3, Chapter 24: a listing deal (a year's loan of 2% of a token's supply plus three call tranches),
the fee it implies at several volatilities, and the market maker's hedge through the year."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/tokenloan"))
from firm_tokenloan import (  # noqa: E402
    Deal,
    day_one_hedge,
    delta_schedule,
    implied_fee,
    package_value,
    package_value_mc,
)

SUPPLY = 100_000_000


def listing_deal(vol: float = 1.2) -> Deal:
    """2% of supply lent for a year at a listing price of USD 0.50; calls on a third each at 0.75, 1.00, 1.50."""
    n = 0.02 * SUPPLY
    return Deal(n, 0.50, 1.0, vol, ((n / 3, 0.75), (n / 3, 1.00), (n / 3, 1.50)))


def summary(vol: float = 1.2) -> dict:
    d = listing_deal(vol)
    return {"loan_usd": d.tokens_loaned * d.price, "calls_usd": package_value(d), "calls_mc_usd": package_value_mc(d),
            "fee": implied_fee(d), "hedge_tokens": day_one_hedge(d), "hedge_share": day_one_hedge(d) / d.tokens_loaned}


def fee_by_vol() -> list[tuple[float, float]]:
    return [(v / 100, implied_fee(listing_deal(v / 100))) for v in range(40, 241, 10)]


def hedge_curves() -> list[tuple[float, float, float]]:
    """Tokens short to hedge the calls, against the token price, at signing and with half a year left."""
    d = listing_deal()
    prices = [p / 100 for p in range(10, 301, 5)]
    a, b = delta_schedule(d, prices, 1.0), delta_schedule(d, prices, 0.5)
    return [(p, x, y) for (p, x), (_, y) in zip(a, b, strict=True)]
