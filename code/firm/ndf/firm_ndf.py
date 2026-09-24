"""Non-deliverable forwards, onshore/offshore basis, bands and leveraged losses (build of Book 2,
Chapter 18).

Rates are quoted as units of the local currency per US dollar. An NDF on a notional of N dollars at
contract rate K settles in dollars only, two business days after its fixing date, against the fixing
rate S published by the agreed source: the dollar buyer receives N (S - K) / S, or pays it if negative.
"""
import datetime as dt


def ndf_settlement(notional_usd: float, contract: float, fixing: float, buyer: bool = True) -> float:
    """Dollar amount received by the dollar buyer (paid if negative); the seller's is the opposite."""
    amount = notional_usd * (fixing - contract) / fixing
    return amount if buyer else -amount


def fixing_date(settlement: dt.date, holidays: set[dt.date], lag: int = 2) -> dt.date:
    """The fixing (valuation) date: `lag` business days before settlement."""
    d, n = settlement, 0
    while n < lag:
        d -= dt.timedelta(days=1)
        if d.weekday() < 5 and d not in holidays:
            n += 1
    return d


def implied_local_rate(spot: float, fwd: float, r_usd: float, days: int, dc_usd: int = 360,
                       dc_local: int = 365) -> float:
    """The local-currency rate implied by spot, forward and the dollar rate (covered parity)."""
    return ((fwd / spot) * (1.0 + r_usd * days / dc_usd) - 1.0) * dc_local / days


def onshore_offshore_basis(spot_on: float, fwd_on: float, spot_off: float, fwd_off: float, r_usd: float,
                           days: int) -> float:
    """Offshore implied local rate minus onshore implied local rate."""
    return implied_local_rate(spot_off, fwd_off, r_usd, days) - implied_local_rate(spot_on, fwd_on, r_usd, days)


def band(central: float, width: float) -> tuple[float, float]:
    """Trading band of +/- width (a fraction) around a central parity."""
    return central * (1.0 - width), central * (1.0 + width)


def leveraged_loss(move: float, leverage: float) -> float:
    """Loss as a multiple of the margin deposited, for a position of `leverage` times the margin and
    an adverse relative price move `move` (0.1 = 10%)."""
    return move * leverage
