"""Forward points, FX swaps and the cross-currency basis (build of Book 2, Chapter 16).

S is the spot rate of a pair BASEQUOTE, in units of the quote currency per unit of the base.
Money-market rates are simple, on an actual/360 basis unless `basis_days` says otherwise. The
cross-currency basis b is quoted, as in the market, as a spread on the non-dollar currency's rate:
lending that currency through FX swaps earns its rate plus b.
"""


def forward(spot: float, r_quote: float, r_base: float, days: int, basis_quote: float = 0.0,
            basis_base: float = 0.0, dc_quote: int = 360, dc_base: int = 360) -> float:
    """Outright forward by covered interest parity, with a basis on either leg."""
    return spot * (1.0 + (r_quote + basis_quote) * days / dc_quote) / (1.0 + (r_base + basis_base) * days / dc_base)


def points(fwd: float, spot: float, pip: float) -> float:
    """Forward points: F - S in pips."""
    return (fwd - spot) / pip


def implied_rate_quote(spot: float, fwd: float, r_base: float, days: int, dc_quote: int = 360,
                       dc_base: int = 360) -> float:
    """The quote currency's rate implied by the swap: (F/S)(1 + r_base t) - 1, annualised."""
    return ((fwd / spot) * (1.0 + r_base * days / dc_base) - 1.0) * dc_quote / days


def basis_on_quote(spot: float, fwd: float, r_quote: float, r_base: float, days: int, dc_quote: int = 360,
                   dc_base: int = 360) -> float:
    """Cross-currency basis on the quote currency implied by market spot and forward."""
    return implied_rate_quote(spot, fwd, r_base, days, dc_quote, dc_base) - r_quote


def fx_swap_legs(notional_base: float, spot: float, fwd: float) -> dict[str, float]:
    """Cash flows of a party that buys the base currency at spot and sells it forward."""
    return {"near_base": notional_base, "near_quote": -notional_base * spot,
            "far_base": -notional_base, "far_quote": notional_base * fwd}


def hedge_cost(r_usd: float, r_other: float, basis_other: float) -> float:
    """Annualised cost, to a holder of dollar assets funded in another currency, of rolling a short-dated
    FX hedge: the dollar rate less the other currency's rate plus its basis."""
    return r_usd - (r_other + basis_other)


def hedged_yield(y_usd: float, r_usd: float, r_other: float, basis_other: float) -> float:
    """Yield of a dollar bond hedged back into the other currency with rolling short-dated swaps."""
    return y_usd - hedge_cost(r_usd, r_other, basis_other)
