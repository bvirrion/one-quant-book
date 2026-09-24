"""Chapter 24 of Book 6: a stylised bank (USD billion) that funded a long fixed-rate securities portfolio
with non-maturity deposits while rates were low: 15 of cash, 25 of five-year Treasuries, 90 of agency
MBS (level-pay over 12 years, duration about 6.2 at purchase, the duration the Federal Reserve's review
reports for SVB's HTM book), 70 of floating-rate loans; 173 of deposits (94% uninsured in SVB's case),
11 of five-year term debt, equity the rest. Rates rise from 1.0% to 4.5%. EVE under the six supervisory
shocks, NII sensitivity with two deposit betas, the LCR, an FTP curve, the unrealised loss on the HTM book
as a share of equity, and the one-day outflow that exhausts the liquid assets."""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/alm"))
from firm_alm import (  # noqa: E402
    SCENARIOS,
    BalanceSheet,
    Deposits,
    Position,
    eve_ratio,
    ftp_rate,
    lcr,
    market_value,
    run_capacity,
    shock_curve,
)

R0, R1 = 0.010, 0.045          # market rate when the book was built, and a year later


def positions():
    return [Position("cash", "asset", 15.0, 0.0, 0.0, "cash", hqla="L1"),
            Position("Treasuries (AFS)", "asset", 25.0, 0.015, 5.0, "bullet", hqla="L1"),
            Position("agency MBS (HTM)", "asset", 90.0, 0.018, 12.0, "amortising", hqla="L2A"),
            Position("loans", "asset", 70.0, 0.030, 0.25, "floating"),
            Position("term debt", "liability", 11.0, 0.030, 5.0, "bullet")]


def deposits(beta: float = 0.35) -> Deposits:
    return Deposits(amount=173.0, core_share=0.60, core_life=5.0, rate=0.002, beta=beta, runoff=0.40)


def bank(rate: float = R0, beta: float = 0.35) -> BalanceSheet:
    return BalanceSheet(positions(), deposits(beta), rate)


def equity_book() -> float:
    ps = positions()
    return sum(p.amount for p in ps if p.side == "asset") - sum(p.amount for p in ps if p.side == "liability") - 173.0


def htm_loss() -> dict:
    """Mark of the HTM book when its yield rises by the market move, from its purchase yield (the coupon)."""
    p = positions()[2]
    mv0, mv1 = market_value(p, p.rate), market_value(p, p.rate + R1 - R0)
    loss = mv1 / mv0 * p.amount - p.amount
    return {"loss": loss, "pct": mv1 / mv0 - 1, "of_equity": -loss / equity_book()}


def afs_loss() -> float:
    p = positions()[1]
    return (market_value(p, p.rate + R1 - R0) / market_value(p, p.rate) - 1) * p.amount


def eve_table(rate: float = R0) -> dict:
    b = bank(rate)
    d = b.delta_eve()
    return {"base": b.pv()["eve"], "delta": d, "ratio": eve_ratio(d, equity_book())}


def nii_table() -> dict:
    out = {}
    for beta in (0.35, 0.80):
        b = bank(R0, beta)
        out[beta] = {"base": b.nii(0.0), "up200": b.nii(0.02) - b.nii(0.0), "up350": b.nii(R1 - R0) - b.nii(0.0)}
    return out


def lcr_now() -> dict:
    """LCR a year later at market values: deposits split 6% insured stable (5%), 94% uninsured (40%)."""
    d = [(173.0 * 0.06, 0.05), (173.0 * 0.94, 0.40)]
    return lcr(positions(), d, R1)


def liquid_same_day() -> dict:
    """Cash plus the AFS Treasuries at market value: what can be paid out on the day without the HTM book."""
    liquid = 15.0 + 25.0 + afs_loss()
    return {"liquid": liquid, "share": run_capacity(liquid, 173.0)}


def ftp_curve():
    def base(t):
        return R1

    def lp(t):
        return 0.0015 * math.sqrt(t)            # illustrative term liquidity premium

    return [(t, 100 * ftp_rate(base, lp, t)) for t in (0.25, 0.5, 1, 2, 3, 5, 7, 10)]


def shock_table():
    ts = [0.25, 0.5, 1, 2, 3, 5, 7, 10, 15, 20]
    return [(t, *(1e4 * shock_curve(s)(t) for s in SCENARIOS)) for t in ts]


def nii_path(beta: float):
    b = bank(R0, beta)
    base = b.nii(0.0)
    return [(bp, b.nii(bp * 1e-4) - base) for bp in range(0, 401, 25)]
