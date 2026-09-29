"""firm.fundterms -- a fund's terms: fees by investor, crystallisation, liquidity and redemptions
(build of One Quant Book 16, chapter 4). Wraps One Quant Book 1's firm.fees for the per-period fee arithmetic.

Fees. A pooled fund with one net asset value per share and one high-water mark charges every investor the same
performance fee, whatever they paid: an investor who bought below the mark rides free until the mark is regained,
one who bought above it pays on gains that are not theirs. Series accounting (one series, hence one mark, per
subscription date) or equalisation removes both. `pooled_vs_series` measures the difference; `crystallised`
computes performance fees crystallised every k months.

Liquidity. A portfolio is a ladder of buckets (days to sell, share of NAV, cost of selling as a fraction of
value). A redemption request is met by selling liquid assets first or a slice of every bucket; a gate caps what
is paid on one dealing date; swing pricing charges the cost of selling to the redeemers instead of the investors
who stay. `max_redemption` is the most a fund can pay within its notice period at no more than a cost cap.

API (stable):
    pooled_vs_series(returns, entries, terms) -> dict        entries: list of (period, amount)
    crystallised(returns, perf, every) -> total fee per unit of starting capital
    Bucket(days, share, cost); ladder_share_within(ladder, days)
    redeem(ladder, request, notice_days, policy="liquid_first"|"pro_rata", gate=None, swing=False, fire=3.0)
        -> dict(paid, deferred, cost, dilution_stayers, ladder_after)
    max_redemption(ladder, notice_days, max_cost)
"""
import pathlib
import sys
from dataclasses import dataclass, replace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "fees"))
import firm_fees as ff  # noqa: E402


def pooled_vs_series(returns, entries, terms: ff.FeeTerms) -> dict:
    """Performance fees paid by each investor under a pooled NAV with one high-water mark, and under series
    accounting (each subscription its own mark). returns: per-period gross returns; entries: (period, amount),
    the amount subscribed at the start of that period. Management fees are zero here to isolate the effect."""
    t0 = replace(terms, mgmt=0.0)
    n = len(returns)
    series = {}
    for k, (p, amt) in enumerate(entries):
        st = ff.InvestorState(1.0, 1.0)
        fee = 0.0
        for t in range(p, n):
            st, _, pf = ff.accrue(t0, st, returns[t])
            fee += pf
        series[k] = fee * amt
    # pooled: one share price and one mark; fees charged per share to whoever holds shares
    nav, hw = 1.0, 1.0
    shares = {k: 0.0 for k in range(len(entries))}
    pooled = {k: 0.0 for k in range(len(entries))}
    for t in range(n):
        for k, (p, amt) in enumerate(entries):
            if p == t:
                shares[k] += amt / nav
        st, _, pf = ff.accrue(t0, ff.InvestorState(nav, hw), returns[t])
        for k in shares:
            pooled[k] += pf * shares[k]
        nav, hw = st.nav, st.high_water
    return {"series": series, "pooled": pooled}


def crystallised(returns, perf: float, every: int) -> float:
    """Performance fee per unit of starting capital, crystallised every `every` periods against a high-water
    mark (fees crystallised are paid and never returned; between crystallisations the accrual can reverse)."""
    nav, hw, paid = 1.0, 1.0, 0.0
    for t, r in enumerate(returns):
        nav *= 1 + r
        if (t + 1) % every == 0:
            fee = perf * max(nav - hw, 0.0)
            nav -= fee
            paid += fee
            hw = max(hw, nav)
    return paid


@dataclass(frozen=True)
class Bucket:
    days: int        # days needed to sell the bucket at its normal cost
    share: float     # share of NAV
    cost: float      # cost of selling it within `days`, fraction of value


def ladder_share_within(ladder, days: int) -> float:
    return sum(b.share for b in ladder if b.days <= days)


def redeem(ladder, request: float, notice_days: int, policy: str = "liquid_first", gate: float | None = None,
           swing: bool = False, fire: float = 3.0) -> dict:
    """Meet a redemption of `request` (share of NAV) within notice_days. Buckets slower than the notice period
    can be sold only at `fire` times their cost. The gate caps the payment; the rest is deferred. Without swing
    pricing redeemers are paid at a NAV that ignores the selling cost, so the investors who stay bear all of it
    (their dilution); with it, the redeemers bear it. Returns shares of the starting NAV."""
    pay = request if gate is None else min(request, gate)
    order = sorted(ladder, key=lambda b: b.days)
    sold = {b: 0.0 for b in order}
    if policy == "liquid_first":
        need = pay
        for b in order:
            x = min(b.share, need)
            sold[b] = x
            need -= x
    elif policy == "pro_rata":
        for b in order:
            sold[b] = b.share * pay
    else:
        raise ValueError(policy)
    cost = sum(x * b.cost * (fire if b.days > notice_days else 1.0) for b, x in sold.items())
    stayers = 1.0 - pay
    # redeemers are paid at a NAV that ignores the cost of selling: without swing pricing the stayers bear all of it
    dilution = 0.0 if swing else cost / max(stayers, 1e-12)
    left = sum(b.share - sold[b] for b in order)
    after = [Bucket(b.days, (b.share - sold[b]) / max(left, 1e-12), b.cost) for b in order]
    return {"paid": pay, "deferred": request - pay, "cost": cost, "dilution_stayers": dilution, "ladder_after": after}


def max_redemption(ladder, notice_days: int, max_cost: float) -> float:
    """Largest share of NAV payable within the notice period, liquid first, without selling any bucket whose
    cost (with the fire-sale multiplier if slower than the notice) exceeds max_cost."""
    return sum(b.share for b in ladder if b.days <= notice_days and b.cost <= max_cost)
