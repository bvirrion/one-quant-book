"""firm.dealterms -- deal packages as data, their value to each side, reservation values, the zone of possible agreement
and a Nash bargaining split (build of One Quant Book 16, chapter 23).

A market-maker programme pays an extra rebate per share added to members whose added volume exceeds a share of
consolidated volume and who quote at the NBBO in enough symbols. A firm that trades less must pad its volume (at a loss
per padded share) and quote in symbols it would not otherwise quote (at a cost per symbol-day); or pay a shortfall
penalty instead. The programme's net value to the firm is the rebate on its added volume less those costs. The venue
values the firm's liquidity by the extra taking flow it attracts, at the venue's net capture per share.

Bargaining: the rebate is a transfer; the joint gain is the venue's value of the firm's liquidity less the firm's
costs of meeting the obligations. With reservation values r_f (the firm's best alternative, e.g. another venue's
programme) and r_v, the zone of possible agreement is the set of transfers giving each side at least its reservation
value; the Nash split gives the firm r_f + beta (G - r_f - r_v).

API (stable):
    Programme(rebate, volume_share, symbols, penalty) ; Firm(added_share, symbols, pad_loss, symbol_cost)
    daily_value(prog, firm, tcv) -> dict ; breakeven_share(prog, firm_of_share, tcv, lo, hi)
    venue_value(firm, tcv, attract, capture) ; zopa(joint, cost, r_f, r_v) ; nash_transfer(...)
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Programme:
    rebate: float               # extra rebate per share added
    volume_share: float         # added volume required, share of consolidated volume
    symbols: int                # symbols with the required NBBO presence
    penalty: float = 0.0        # per share of volume shortfall, if the programme charges one instead of disqualifying


@dataclass(frozen=True)
class Firm:
    added_share: float          # natural added volume, share of consolidated volume
    symbols: int                # symbols it quotes at the NBBO naturally
    pad_loss: float = 0.001     # loss per padded share
    symbol_cost: float = 2.0    # cost per extra symbol-day of NBBO presence


def daily_value(prog, firm, tcv):
    """The programme's daily net value when the firm pads up to the requirements (dollars a day)."""
    need = max(0.0, prog.volume_share - firm.added_share) * tcv
    extra_symbols = max(0, prog.symbols - firm.symbols)
    rebate = prog.rebate * (firm.added_share * tcv + need)
    pad = need * firm.pad_loss
    quote = extra_symbols * firm.symbol_cost
    return {"rebate": rebate, "padding": pad, "quoting": quote, "net": rebate - pad - quote,
            "padded_shares": need, "extra_symbols": extra_symbols}


def breakeven_share(prog, firm_of_share, tcv, lo=1e-5, hi=0.05, tol=1e-9):
    """The natural added-volume share above which the programme's net value is positive; firm_of_share(a) builds the
    firm's profile at share a. Bisection; None if the value is negative over the whole range."""
    f = lambda a: daily_value(prog, firm_of_share(a), tcv)["net"]  # noqa: E731
    if f(hi) <= 0:
        return None
    if f(lo) > 0:
        return lo
    while hi - lo > tol:
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) <= 0 else (lo, mid)
    return hi


def venue_value(firm, prog, tcv, attract, capture):
    """The venue's daily gain before paying the rebate: the extra taking flow the firm's liquidity attracts, at the
    venue's net capture per share."""
    added = max(firm.added_share, prog.volume_share) * tcv
    return attract * added * capture


def zopa(venue_gain, firm_cost, r_f, r_v):
    """(lowest transfer the firm accepts, highest the venue offers) in dollars a day; empty if low > high."""
    return firm_cost + r_f, venue_gain - r_v


def nash_transfer(venue_gain, firm_cost, r_f, r_v, beta=0.5):
    """The transfer (rebate paid) that gives the firm r_f + beta times the joint surplus over reservations."""
    surplus = venue_gain - firm_cost - r_f - r_v
    if surplus < 0:
        return None
    return firm_cost + r_f + beta * surplus
